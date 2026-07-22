import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import hash_password
from app.models.deck import Deck
from app.models.follow import Follow
from app.models.user import User, UserRole
from app.routes.auth import get_current_user
from app.routes.decks import _save_count
from app.schemas.deck import DeckOut, DeckWithStatsOut
from app.schemas.user import (
    FollowStatusResponse,
    UserProfileResponse,
    UserPublicResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


async def _get_user_or_404(user_id: uuid.UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _ensure_can_modify_user(current_user: User, target_user_id: uuid.UUID) -> None:
    if current_user.id == target_user_id:
        return
    if current_user.role == UserRole.SUPERADMIN:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


async def _build_profile_response(user: User, db: AsyncSession) -> UserProfileResponse:
    followers_count = await db.scalar(
        select(func.count()).select_from(Follow).where(Follow.following_id == user.id)
    )
    following_count = await db.scalar(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
    )

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        created_at=user.created_at,
        followers_count=followers_count or 0,
        following_count=following_count or 0,
    )


@router.get(
    "/",
    response_model=list[UserPublicResponse],
    summary="List users",
    description="Returns a paginated list of public user profiles. Use `skip` and `limit` to page through results (default: first 20).",
)
async def list_users(
    skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.get(
    "/search",
    response_model=list[UserPublicResponse],
    summary="Search users",
    description="Case-insensitive partial search on username. Returns up to `limit` results.",
)
async def search_users(
    q: str = "",
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.username.ilike(f"%{q}%"))
        .order_by(User.username)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Get a user profile",
    description="Fetches a user's public profile with follower/following counts. Returns **404** if no user with that ID exists.",
)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await _get_user_or_404(user_id, db)
    return await _build_profile_response(user, db)


@router.get(
    "/{user_id}/follow-status",
    response_model=FollowStatusResponse,
    summary="Get follow status",
    description="Returns whether the authenticated user follows the given user.",
)
async def get_follow_status(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        return FollowStatusResponse(is_following=False)

    await _get_user_or_404(user_id, db)

    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id,
        )
    )
    return FollowStatusResponse(is_following=result.scalar_one_or_none() is not None)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    description=(
        "Partially updates a user's profile. Requires authentication. "
        "Users may update their own email, username, and password. "
        "Only superadmins may change `is_active`. "
        "Returns **403** if not allowed, **404** if the user doesn't exist, "
        "**409** if the new email or username is already taken by another account."
    ),
)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await _get_user_or_404(user_id, db)

    if payload.is_active is not None:
        if current_user.role != UserRole.SUPERADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    elif current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if payload.email is not None:
        conflict = await db.execute(
            select(User).where(User.email == payload.email, User.id != user_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
            )
        user.email = payload.email

    if payload.username is not None:
        conflict = await db.execute(
            select(User).where(User.username == payload.username, User.id != user_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already in use"
            )
        user.username = payload.username

    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)

    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description=(
        "Permanently deletes a user account. Requires authentication. "
        "Users may delete their own account; superadmins may delete any account. "
        "Returns **403** if not allowed, **204** on success, **404** if the user doesn't exist."
    ),
)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_modify_user(current_user, user_id)
    user = await _get_user_or_404(user_id, db)
    await db.delete(user)
    await db.commit()


@router.post(
    "/{user_id}/follow",
    response_model=FollowStatusResponse,
    summary="Toggle follow",
    description="Follow or unfollow a user. Returns the new follow status.",
)
async def toggle_follow(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself",
        )

    await _get_user_or_404(user_id, db)

    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id,
        )
    )
    follow = result.scalar_one_or_none()

    if follow:
        await db.delete(follow)
        is_following = False
    else:
        db.add(Follow(follower_id=current_user.id, following_id=user_id))
        is_following = True

    await db.commit()
    return FollowStatusResponse(is_following=is_following)


@router.get(
    "/{user_id}/followers",
    response_model=list[UserPublicResponse],
    summary="Get a user's followers",
    description="Returns users who follow the given user.",
)
async def get_followers(
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(user_id, db)

    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)
        .order_by(Follow.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/{user_id}/following",
    response_model=list[UserPublicResponse],
    summary="Get users a user is following",
    description="Returns users that the given user follows.",
)
async def get_following(
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(user_id, db)

    result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(Follow.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/{user_id}/decks",
    response_model=list[DeckWithStatsOut],
    summary="Get a user's public decks",
    description="Returns all decks (with cards) belonging to the given user. No authentication required.",
)
async def get_user_decks(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _get_user_or_404(user_id, db)

    result = await db.execute(
        select(Deck)
        .where(Deck.user_id == user_id)
        .options(selectinload(Deck.cards))
        .order_by(Deck.created_at_ms.desc())
    )
    decks = result.scalars().all()
    out = []
    for deck in decks:
        out.append(
            DeckWithStatsOut(
                id=deck.id,
                name=deck.name,
                description=deck.description,
                cards=deck.cards,
                createdAt=deck.created_at_ms,
                save_count=await _save_count(deck.id, db),
            )
        )
    return out

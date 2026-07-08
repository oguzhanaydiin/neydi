import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import hash_password
from app.models.deck import Deck
from app.models.user import User
from app.schemas.deck import DeckOut
from app.schemas.user import UserPublicResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List users",
    description="Returns a paginated list of all users. Use `skip` and `limit` to page through results (default: first 20).",
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
    response_model=UserResponse,
    summary="Get a user",
    description="Fetches a single user by their UUID. Returns **404** if no user with that ID exists.",
)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    description=(
        "Partially updates a user's profile. All fields are optional — only provided fields are changed. "
        "Returns **404** if the user doesn't exist, **409** if the new email or username is already taken by another account."
    ),
)
async def update_user(
    user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    description="Permanently deletes a user account. Returns **204** on success, **404** if the user doesn't exist.",
)
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()


@router.get(
    "/{user_id}/decks",
    response_model=list[DeckOut],
    summary="Get a user's public decks",
    description="Returns all decks (with cards) belonging to the given user. No authentication required.",
)
async def get_user_decks(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(Deck)
        .where(Deck.user_id == user_id)
        .options(selectinload(Deck.cards))
        .order_by(Deck.created_at_ms.desc())
    )
    return result.scalars().all()

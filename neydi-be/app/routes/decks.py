import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.deck import Card, Deck
from app.models.deck_pin import DeckPin
from app.models.user import User, UserRole
from app.models.user_card_progress import UserCardProgress
from app.routes.auth import get_current_user
from app.schemas.deck import (
    CardIn,
    CardOut,
    CardPatch,
    ConfidencePatch,
    DeckCopyIn,
    DeckIn,
    DeckOut,
    DeckPatch,
    DeckPublicOut,
    PinStatusResponse,
    PinnedDeckOut,
    ReorderPatch,
)

router = APIRouter(prefix="/decks", tags=["decks"])


async def _get_deck_or_404(deck_id: uuid.UUID, db: AsyncSession) -> Deck:
    result = await db.execute(
        select(Deck).where(Deck.id == deck_id).options(selectinload(Deck.cards))
    )
    deck = result.scalar_one_or_none()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


async def _get_deck(
    deck_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Deck:
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id, Deck.user_id == current_user.id)
        .options(selectinload(Deck.cards))
    )
    deck = result.scalar_one_or_none()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


def _build_cards(card_inputs: list[CardIn], deck_id: uuid.UUID) -> list[Card]:
    return [
        Card(
            id=c.id or uuid.uuid4(),
            deck_id=deck_id,
            front=c.front,
            back=c.back,
            confidence=c.confidence,
            position=i,
        )
        for i, c in enumerate(card_inputs)
    ]


async def _save_count(deck_id: uuid.UUID, db: AsyncSession) -> int:
    pin_count = await db.scalar(
        select(func.count()).select_from(DeckPin).where(DeckPin.deck_id == deck_id)
    ) or 0
    copy_count = await db.scalar(
        select(func.count()).select_from(Deck).where(Deck.source_deck_id == deck_id)
    ) or 0
    return pin_count + copy_count


async def _apply_user_card_progress(deck: Deck, user_id: uuid.UUID, db: AsyncSession) -> None:
    if deck.user_id == user_id:
        return
    card_ids = [c.id for c in deck.cards]
    if not card_ids:
        return
    result = await db.execute(
        select(UserCardProgress).where(
            UserCardProgress.user_id == user_id,
            UserCardProgress.card_id.in_(card_ids),
        )
    )
    progress_map = {p.card_id: p.confidence for p in result.scalars().all()}
    for card in deck.cards:
        card.confidence = progress_map.get(card.id, 0)


async def _get_pinned_deck_or_404(
    deck_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Deck:
    result = await db.execute(
        select(DeckPin).where(
            DeckPin.user_id == current_user.id,
            DeckPin.deck_id == deck_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pinned deck not found")
    return await _get_deck_or_404(deck_id, db)


def _pinned_deck_out(deck: Deck, save_count: int) -> PinnedDeckOut:
    return PinnedDeckOut(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        cards=deck.cards,
        createdAt=deck.created_at_ms,
        owner_id=deck.user_id,
        owner_username=deck.owner.username,
        save_count=save_count,
    )


# ---------------------------------------------------------------------------
# Public deck discovery
# ---------------------------------------------------------------------------


@router.get(
    "/explore",
    response_model=list[DeckPublicOut],
    summary="Explore decks",
    description=(
        "Returns decks from all users, newest first. "
        "Each deck includes its owner's username and role — "
        "use `owner.role == 'superadmin'` to badge official decks on the frontend. "
        "No authentication required."
    ),
)
async def explore_decks(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deck)
        .options(selectinload(Deck.cards), selectinload(Deck.owner))
        .order_by(Deck.created_at_ms.desc())
        .offset(skip)
        .limit(limit)
    )
    decks = result.scalars().all()
    out = []
    for deck in decks:
        out.append(
            DeckPublicOut(
                id=deck.id,
                name=deck.name,
                description=deck.description,
                cards=deck.cards,
                createdAt=deck.created_at_ms,
                owner_username=deck.owner.username,
                is_official=deck.owner.role == UserRole.SUPERADMIN,
                save_count=await _save_count(deck.id, db),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Deck endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[DeckOut])
async def list_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deck)
        .where(Deck.user_id == current_user.id)
        .options(selectinload(Deck.cards))
        .order_by(Deck.created_at_ms)
    )
    return result.scalars().all()


@router.get("/pinned", response_model=list[PinnedDeckOut])
async def list_pinned_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeckPin)
        .where(DeckPin.user_id == current_user.id)
        .options(
            selectinload(DeckPin.deck).selectinload(Deck.cards),
            selectinload(DeckPin.deck).selectinload(Deck.owner),
        )
        .order_by(DeckPin.pinned_at.desc())
    )
    pins = result.scalars().all()
    out = []
    for pin in pins:
        deck = pin.deck
        await _apply_user_card_progress(deck, current_user.id, db)
        out.append(_pinned_deck_out(deck, await _save_count(deck.id, db)))
    return out


@router.post("/{deck_id}/copy", response_model=DeckOut, status_code=status.HTTP_201_CREATED)
async def copy_deck(
    deck_id: uuid.UUID,
    payload: DeckCopyIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await _get_deck_or_404(deck_id, db)
    if source.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot copy your own deck",
        )

    import time

    new_id = uuid.uuid4()
    new_deck = Deck(
        id=new_id,
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description if payload.description is not None else source.description,
        created_at_ms=int(time.time() * 1000),
        source_deck_id=source.id,
    )
    new_deck.cards = [
        Card(
            id=uuid.uuid4(),
            deck_id=new_id,
            front=card.front,
            back=card.back,
            confidence=0,
            position=i,
        )
        for i, card in enumerate(source.cards)
    ]
    db.add(new_deck)
    await db.commit()
    await db.refresh(new_deck, ["cards"])
    return new_deck


@router.post("/{deck_id}/pin", response_model=PinnedDeckOut, status_code=status.HTTP_201_CREATED)
async def pin_deck(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck_or_404(deck_id, db)
    if deck.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pin your own deck",
        )

    existing = await db.execute(
        select(DeckPin).where(
            DeckPin.user_id == current_user.id,
            DeckPin.deck_id == deck_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deck already pinned",
        )

    db.add(DeckPin(user_id=current_user.id, deck_id=deck_id))
    await db.commit()

    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards), selectinload(Deck.owner))
    )
    deck = result.scalar_one()
    await _apply_user_card_progress(deck, current_user.id, db)
    return _pinned_deck_out(deck, await _save_count(deck.id, db))


@router.delete("/{deck_id}/pin", status_code=status.HTTP_204_NO_CONTENT)
async def unpin_deck(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeckPin).where(
            DeckPin.user_id == current_user.id,
            DeckPin.deck_id == deck_id,
        )
    )
    pin = result.scalar_one_or_none()
    if pin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pinned deck not found")
    await db.delete(pin)
    await db.commit()


@router.get("/{deck_id}/pin-status", response_model=PinStatusResponse)
async def get_pin_status(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_deck_or_404(deck_id, db)
    result = await db.execute(
        select(DeckPin).where(
            DeckPin.user_id == current_user.id,
            DeckPin.deck_id == deck_id,
        )
    )
    return PinStatusResponse(is_pinned=result.scalar_one_or_none() is not None)


@router.post("", response_model=DeckOut, status_code=status.HTTP_201_CREATED)
async def create_deck(
    payload: DeckIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import time

    deck_id = payload.id or uuid.uuid4()
    created_ms = payload.createdAt if payload.createdAt is not None else int(time.time() * 1000)

    deck = Deck(
        id=deck_id,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        created_at_ms=created_ms,
    )
    deck.cards = _build_cards(payload.cards, deck_id)
    db.add(deck)
    await db.commit()
    await db.refresh(deck, ["cards"])
    return deck


@router.put("/{deck_id}", response_model=DeckOut)
async def replace_deck(
    deck_id: uuid.UUID,
    payload: DeckIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full replacement used during guest→auth migration. Returns 404 if the deck
    doesn't exist yet so the caller can fall back to POST /decks."""
    deck = await _get_deck(deck_id, current_user, db)

    deck.name = payload.name
    deck.description = payload.description
    if payload.createdAt is not None:
        deck.created_at_ms = payload.createdAt

    # Replace cards entirely.
    for card in list(deck.cards):
        await db.delete(card)
    await db.flush()

    deck.cards = _build_cards(payload.cards, deck_id)
    await db.commit()
    await db.refresh(deck, ["cards"])
    return deck


@router.patch("/{deck_id}", response_model=DeckOut)
async def update_deck(
    deck_id: uuid.UUID,
    payload: DeckPatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(deck_id, current_user, db)
    deck.name = payload.name
    deck.description = payload.description
    await db.commit()
    await db.refresh(deck, ["cards"])
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(deck_id, current_user, db)
    await db.delete(deck)
    await db.commit()


# ---------------------------------------------------------------------------
# Card endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{deck_id}/cards",
    response_model=CardOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_card(
    deck_id: uuid.UUID,
    payload: CardIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(deck_id, current_user, db)
    position = len(deck.cards)
    card = Card(
        id=payload.id or uuid.uuid4(),
        deck_id=deck_id,
        front=payload.front,
        back=payload.back,
        confidence=payload.confidence,
        position=position,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


# NOTE: /reorder must be declared before /{card_id} to avoid route shadowing.
@router.patch("/{deck_id}/cards/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_cards(
    deck_id: uuid.UUID,
    payload: ReorderPatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(deck_id, current_user, db)
    card_map = {c.id: c for c in deck.cards}
    for position, card_id in enumerate(payload.order):
        if card_id in card_map:
            card_map[card_id].position = position
    await db.commit()


@router.patch("/{deck_id}/cards/{card_id}", response_model=CardOut)
async def update_card(
    deck_id: uuid.UUID,
    card_id: uuid.UUID,
    payload: CardPatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(deck_id, current_user, db)
    card = next((c for c in deck.cards if c.id == card_id), None)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    card.front = payload.front
    card.back = payload.back
    await db.commit()
    await db.refresh(card)
    return card


@router.patch(
    "/{deck_id}/cards/{card_id}/confidence",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_card_confidence(
    deck_id: uuid.UUID,
    card_id: uuid.UUID,
    payload: ConfidencePatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned_result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id, Deck.user_id == current_user.id)
        .options(selectinload(Deck.cards))
    )
    owned_deck = owned_result.scalar_one_or_none()
    if owned_deck is not None:
        card = next((c for c in owned_deck.cards if c.id == card_id), None)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        card.confidence = payload.confidence
        await db.commit()
        return

    await _get_pinned_deck_or_404(deck_id, current_user, db)
    deck = await _get_deck_or_404(deck_id, db)
    card = next((c for c in deck.cards if c.id == card_id), None)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

    result = await db.execute(
        select(UserCardProgress).where(
            UserCardProgress.user_id == current_user.id,
            UserCardProgress.card_id == card_id,
        )
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        db.add(
            UserCardProgress(
                user_id=current_user.id,
                card_id=card_id,
                confidence=payload.confidence,
            )
        )
    else:
        progress.confidence = payload.confidence
    await db.commit()


@router.delete("/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    deck_id: uuid.UUID,
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(deck_id, current_user, db)
    card = next((c for c in deck.cards if c.id == card_id), None)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    await db.delete(card)
    await db.commit()

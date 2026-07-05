import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.deck import Card, Deck
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.deck import (
    CardIn,
    CardOut,
    CardPatch,
    ConfidencePatch,
    DeckIn,
    DeckOut,
    DeckPatch,
    ReorderPatch,
)

router = APIRouter(prefix="/decks", tags=["decks"])


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
    deck = await _get_deck(deck_id, current_user, db)
    card = next((c for c in deck.cards if c.id == card_id), None)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    card.confidence = payload.confidence
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

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.deck import Deck
from app.models.user import User, UserRole
from app.core.security import hash_password
from scripts.seed_official_decks import DATA_DIR, load_deck_files, seed_official_decks


def test_official_deck_json_files_are_valid():
    decks = load_deck_files(DATA_DIR)
    names = {d["name"] for d in decks}

    assert "German A1 — Core Words" in names
    assert "German A2 — Everyday Words" in names
    assert "German B1 — Intermediate Words" in names
    assert all(len(d["cards"]) >= 40 for d in decks)


@pytest.mark.asyncio
async def test_seed_creates_official_decks(test_session_factory):
    async with test_session_factory() as db:
        db.add(
            User(
                email="admin@test.com",
                username="neydi",
                hashed_password=hash_password("adminpass123"),
                role=UserRole.SUPERADMIN,
            )
        )
        await db.commit()

        stats = await seed_official_decks(db)
        assert stats["created"] == 3
        assert stats["skipped"] == 0

        result = await db.execute(
            select(Deck).options(selectinload(Deck.cards)).where(Deck.name.like("German%"))
        )
        decks = result.scalars().all()
        assert len(decks) == 3
        assert all(len(d.cards) >= 40 for d in decks)

        # Idempotent: second run skips
        stats2 = await seed_official_decks(db)
        assert stats2["created"] == 0
        assert stats2["skipped"] == 3


@pytest.mark.asyncio
async def test_seed_force_replaces_cards(test_session_factory, tmp_path: Path):
    deck_file = tmp_path / "tiny.json"
    deck_file.write_text(
        '{"name": "Tiny Official", "description": "t", "cards": [{"front": "a", "back": "b"}]}',
        encoding="utf-8",
    )

    async with test_session_factory() as db:
        db.add(
            User(
                email="admin2@test.com",
                username="neydi2",
                hashed_password=hash_password("adminpass123"),
                role=UserRole.SUPERADMIN,
            )
        )
        await db.commit()

        await seed_official_decks(db, data_dir=tmp_path)
        deck_file.write_text(
            '{"name": "Tiny Official", "description": "t2", '
            '"cards": [{"front": "x", "back": "y"}, {"front": "m", "back": "n"}]}',
            encoding="utf-8",
        )
        stats = await seed_official_decks(db, force=True, data_dir=tmp_path)
        assert stats["updated"] == 1

        result = await db.execute(
            select(Deck)
            .where(Deck.name == "Tiny Official")
            .options(selectinload(Deck.cards))
        )
        deck = result.scalar_one()
        assert deck.description == "t2"
        assert {c.front for c in deck.cards} == {"x", "m"}

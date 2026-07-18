"""Seed official decks onto the superadmin account from JSON files.

Usage (from neydi-be/):
    python -m scripts.seed_official_decks
    python -m scripts.seed_official_decks --force   # replace cards if deck exists
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deck import Card, Deck
from app.models.user import User, UserRole

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "official_decks"


def load_deck_files(data_dir: Path | None = None) -> list[dict]:
    directory = data_dir or DATA_DIR
    files = sorted(directory.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {directory}")

    decks: list[dict] = []
    for path in files:
        with path.open(encoding="utf-8") as f:
            payload = json.load(f)
        if not payload.get("name") or not isinstance(payload.get("cards"), list):
            raise ValueError(f"Invalid deck file (need name + cards): {path.name}")
        for i, card in enumerate(payload["cards"]):
            if "front" not in card or "back" not in card:
                raise ValueError(f"{path.name}: card[{i}] missing front/back")
        decks.append(payload)
    return decks


async def get_superadmin(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.role == UserRole.SUPERADMIN).limit(1))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise RuntimeError(
            "No superadmin user found. Set SUPERADMIN_EMAIL + SUPERADMIN_PASSWORD "
            "and start the API once so the account is bootstrapped."
        )
    return admin


async def seed_official_decks(
    db: AsyncSession,
    *,
    force: bool = False,
    data_dir: Path | None = None,
) -> dict[str, int]:
    """Insert official decks for the superadmin. Idempotent by deck name."""
    payloads = load_deck_files(data_dir)
    admin = await get_superadmin(db)

    created = 0
    skipped = 0
    updated = 0

    for payload in payloads:
        name = payload["name"].strip()
        description = payload.get("description")
        cards_data = payload["cards"]

        result = await db.execute(
            select(Deck)
            .where(Deck.user_id == admin.id, Deck.name == name)
            .options(selectinload(Deck.cards))
        )
        existing = result.scalar_one_or_none()

        if existing is not None and not force:
            skipped += 1
            continue

        if existing is not None and force:
            for card in list(existing.cards):
                await db.delete(card)
            await db.flush()
            existing.description = description
            existing.cards = [
                Card(
                    id=uuid.uuid4(),
                    deck_id=existing.id,
                    front=c["front"],
                    back=c["back"],
                    confidence=0,
                    position=i,
                )
                for i, c in enumerate(cards_data)
            ]
            updated += 1
            continue

        deck_id = uuid.uuid4()
        deck = Deck(
            id=deck_id,
            user_id=admin.id,
            name=name,
            description=description,
            created_at_ms=int(time.time() * 1000),
        )
        deck.cards = [
            Card(
                id=uuid.uuid4(),
                deck_id=deck_id,
                front=c["front"],
                back=c["back"],
                confidence=0,
                position=i,
            )
            for i, c in enumerate(cards_data)
        ]
        db.add(deck)
        created += 1

    await db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


async def _run_cli(force: bool) -> None:
    from app.core.database import SessionLocal, engine

    print(f"Reading decks from {DATA_DIR}")
    for path in sorted(DATA_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            payload = json.load(f)
        print(f"  loaded {path.name} ({len(payload.get('cards', []))} cards)")

    try:
        async with SessionLocal() as db:
            admin = await get_superadmin(db)
            print(f"Seeding as superadmin: {admin.email} (@{admin.username})")
            stats = await seed_official_decks(db, force=force)
            print(
                f"Done. created={stats['created']} "
                f"updated={stats['updated']} skipped={stats['skipped']}"
            )
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed official decks for the superadmin account")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace cards on decks that already exist (matched by name)",
    )
    args = parser.parse_args(argv)

    import asyncio

    try:
        asyncio.run(_run_cli(force=args.force))
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main(sys.argv[1:])

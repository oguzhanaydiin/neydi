# neydi — backend

FastAPI REST API for neydi. Async SQLAlchemy + PostgreSQL.

## API overview

| Prefix | Description |
|--------|-------------|
| `/auth` | Register, login (OAuth2 password flow), current user |
| `/users` | Profiles, search, follow/unfollow, public deck listings |
| `/decks` | CRUD, cards, reorder, confidence, pin/copy |
| `/decks/explore` | Public deck feed (no auth required) |
| `/health` | Health check with database connectivity |

## Confidence model

Each card has a confidence score **0–5**. During study:

- **Know** → confidence +1 (max 5)
- **Don't know** → confidence −2 (min 0)

For **pinned decks** (decks you don't own), progress is stored per-user in `user_card_progress` so the original deck stays untouched.

## Pin vs copy

| Action | Effect |
|--------|--------|
| **Pin** | Add someone else's deck to your dashboard; study with your own progress |
| **Copy** | Fork the deck into your library; full ownership, editable |

## Official decks

Curated decks (German A1, A2, B1) live as JSON in `data/official_decks/` and are seeded onto the superadmin account via `scripts/seed_official_decks.py`. Decks owned by the superadmin are marked as official in the explore feed.

## Project layout

```
neydi-be/
├── main.py                 # FastAPI app, lifespan, CORS
├── app/
│   ├── core/               # config, database, security, schema migration
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # auth, users, decks
│   └── schemas/            # Pydantic request/response models
├── data/official_decks/    # JSON seed data
├── scripts/                # seed_official_decks
└── tests/
```

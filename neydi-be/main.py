from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Card, Deck, User  # noqa: F401 — ensures models are registered with Base
from app.models.user import UserRole
from app.routes import auth_router, decks_router, user_router


async def _ensure_superadmin(db: AsyncSession) -> None:
    """Create the superadmin account if SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD are set."""
    if not settings.SUPERADMIN_EMAIL or not settings.SUPERADMIN_PASSWORD:
        return

    result = await db.execute(select(User).where(User.email == settings.SUPERADMIN_EMAIL))
    existing = result.scalar_one_or_none()

    if existing is None:
        admin = User(
            email=settings.SUPERADMIN_EMAIL,
            username=settings.SUPERADMIN_USERNAME,
            hashed_password=hash_password(settings.SUPERADMIN_PASSWORD),
            role=UserRole.SUPERADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"✓ Superadmin account created ({settings.SUPERADMIN_EMAIL})")
    elif existing.role != UserRole.SUPERADMIN:
        existing.role = UserRole.SUPERADMIN
        await db.commit()
        print(f"✓ Superadmin role granted to existing account ({settings.SUPERADMIN_EMAIL})")
    else:
        print(f"✓ Superadmin account already exists ({settings.SUPERADMIN_EMAIL})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database connection successful, tables ensured")

    async with SessionLocal() as db:
        await _ensure_superadmin(db)

    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(decks_router)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}


@app.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

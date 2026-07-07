import os
import uuid as _uuid_mod

# set before any app import
os.environ.setdefault("JWT_SECRET", "test-secret-key-not-for-production")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

# asyncpg handles str→UUID coercion natively; aiosqlite doesn't, so patch it
from sqlalchemy.dialects.postgresql import UUID as _pgUUID  # noqa: E402


def _uuid_bind_processor(self, dialect):
    if self.as_uuid:
        def process(value):
            if value is not None:
                if isinstance(value, str):
                    value = _uuid_mod.UUID(value)
                value = value.hex
            return value
        return process
    return None


_pgUUID.bind_processor = _uuid_bind_processor

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


_USER = {"email": "alice@test.com", "username": "alice", "password": "alicepass123"}


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    await client.post("/auth/register", json=_USER)
    resp = await client.post(
        "/auth/token",
        content=f"username={_USER['email']}&password={_USER['password']}",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client

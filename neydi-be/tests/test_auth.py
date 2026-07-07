from httpx import AsyncClient

_REG = {"email": "user@test.com", "username": "testuser", "password": "password123"}
_LOGIN = f"username={_REG['email']}&password={_REG['password']}"
_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


async def test_register_returns_user(client: AsyncClient):
    resp = await client.post("/auth/register", json=_REG)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == _REG["email"]
    assert data["username"] == _REG["username"]
    assert "hashed_password" not in data


async def test_register_duplicate_returns_409(client: AsyncClient):
    await client.post("/auth/register", json=_REG)
    resp = await client.post("/auth/register", json=_REG)
    assert resp.status_code == 409


async def test_login_returns_token(client: AsyncClient):
    await client.post("/auth/register", json=_REG)
    resp = await client.post("/auth/token", content=_LOGIN, headers=_HEADERS)
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post("/auth/register", json=_REG)
    resp = await client.post(
        "/auth/token",
        content=f"username={_REG['email']}&password=wrongpassword",
        headers=_HEADERS,
    )
    assert resp.status_code == 401


async def test_me_returns_current_user(auth_client: AsyncClient):
    resp = await auth_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@test.com"


async def test_me_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401

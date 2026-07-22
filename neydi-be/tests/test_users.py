import uuid

from httpx import AsyncClient

_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


async def _register(client: AsyncClient, email: str, username: str) -> dict:
    await client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": "password123"},
    )
    users = (await client.get("/users/")).json()
    return next(u for u in users if u["username"] == username)


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/auth/token",
        content=f"username={email}&password=password123",
        headers=_HEADERS,
    )
    return resp.json()["access_token"]


async def test_list_users(auth_client: AsyncClient):
    resp = await auth_client.get("/users/")
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) == 1
    assert "email" not in users[0]
    assert users[0]["username"] == "alice"


async def test_get_user(auth_client: AsyncClient):
    me = (await auth_client.get("/auth/me")).json()
    resp = await auth_client.get(f"/users/{me['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == me["id"]


async def test_get_nonexistent_user_returns_404(client: AsyncClient):
    resp = await client.get(f"/users/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_user_email_conflict_returns_409(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    bob = await _register(client, "bob@test.com", "bob")

    token = await _login(client, "bob@test.com")
    resp = await client.patch(
        f"/users/{bob['id']}",
        json={"email": "alice@test.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_update_own_profile(client: AsyncClient):
    user = await _register(client, "alice@test.com", "alice")
    token = await _login(client, "alice@test.com")

    resp = await client.patch(
        f"/users/{user['id']}",
        json={"username": "alice2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice2"


async def test_update_user_requires_auth(client: AsyncClient):
    user = await _register(client, "alice@test.com", "alice")
    resp = await client.patch(f"/users/{user['id']}", json={"username": "hacked"})
    assert resp.status_code == 401


async def test_update_other_user_forbidden(client: AsyncClient):
    alice = await _register(client, "alice@test.com", "alice")
    bob = await _register(client, "bob@test.com", "bob")
    alice_token = await _login(client, "alice@test.com")

    resp = await client.patch(
        f"/users/{bob['id']}",
        json={"username": "hacked"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert resp.status_code == 403


async def test_update_is_active_requires_superadmin(auth_client: AsyncClient):
    me = (await auth_client.get("/auth/me")).json()

    resp = await auth_client.patch(f"/users/{me['id']}", json={"is_active": False})
    assert resp.status_code == 403


async def test_superadmin_can_deactivate_user(
    superadmin_client: AsyncClient, client: AsyncClient
):
    user = await _register(client, "alice@test.com", "alice")

    resp = await superadmin_client.patch(
        f"/users/{user['id']}",
        json={"is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_delete_user(client: AsyncClient):
    user = await _register(client, "alice@test.com", "alice")
    token = await _login(client, "alice@test.com")

    resp = await client.delete(
        f"/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    resp = await client.get(f"/users/{user['id']}")
    assert resp.status_code == 404


async def test_delete_user_requires_auth(client: AsyncClient):
    user = await _register(client, "alice@test.com", "alice")
    resp = await client.delete(f"/users/{user['id']}")
    assert resp.status_code == 401


async def test_delete_other_user_forbidden(client: AsyncClient):
    alice = await _register(client, "alice@test.com", "alice")
    bob = await _register(client, "bob@test.com", "bob")
    alice_token = await _login(client, "alice@test.com")

    resp = await client.delete(
        f"/users/{bob['id']}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert resp.status_code == 403


async def test_superadmin_can_delete_user(superadmin_client: AsyncClient, client: AsyncClient):
    user = await _register(client, "alice@test.com", "alice")

    resp = await superadmin_client.delete(f"/users/{user['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/users/{user['id']}")
    assert resp.status_code == 404

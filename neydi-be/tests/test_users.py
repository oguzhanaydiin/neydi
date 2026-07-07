import uuid

from httpx import AsyncClient


async def test_list_users(auth_client: AsyncClient):
    resp = await auth_client.get("/users/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_user(auth_client: AsyncClient):
    me = (await auth_client.get("/auth/me")).json()
    resp = await auth_client.get(f"/users/{me['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == me["id"]


async def test_get_nonexistent_user_returns_404(client: AsyncClient):
    resp = await client.get(f"/users/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_user_email_conflict_returns_409(client: AsyncClient):
    await client.post("/auth/register", json={
        "email": "alice@test.com", "username": "alice", "password": "password123",
    })
    await client.post("/auth/register", json={
        "email": "bob@test.com", "username": "bob", "password": "password123",
    })

    users = (await client.get("/users/")).json()
    bob = next(u for u in users if u["username"] == "bob")

    resp = await client.patch(f"/users/{bob['id']}", json={"email": "alice@test.com"})
    assert resp.status_code == 409


async def test_delete_user(client: AsyncClient):
    await client.post("/auth/register", json={
        "email": "alice@test.com", "username": "alice", "password": "password123",
    })
    users = (await client.get("/users/")).json()
    user_id = users[0]["id"]

    resp = await client.delete(f"/users/{user_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/users/{user_id}")
    assert resp.status_code == 404

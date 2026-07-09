import uuid

from httpx import AsyncClient


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
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return resp.json()["access_token"]


async def test_follow_and_unfollow(client: AsyncClient):
    alice = await _register(client, "alice@test.com", "alice")
    bob = await _register(client, "bob@test.com", "bob")

    token = await _login(client, "alice@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(f"/users/{bob['id']}/follow", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_following"] is True

    status = (await client.get(f"/users/{bob['id']}/follow-status", headers=headers)).json()
    assert status["is_following"] is True

    profile = (await client.get(f"/users/{bob['id']}")).json()
    assert profile["followers_count"] == 1
    assert profile["following_count"] == 0
    assert "is_following" not in profile

    followers = (await client.get(f"/users/{bob['id']}/followers")).json()
    assert len(followers) == 1
    assert followers[0]["username"] == "alice"

    following = (await client.get(f"/users/{alice['id']}/following")).json()
    assert len(following) == 1
    assert following[0]["username"] == "bob"

    resp = await client.post(f"/users/{bob['id']}/follow", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_following"] is False

    profile = (await client.get(f"/users/{bob['id']}")).json()
    assert profile["followers_count"] == 0

    status = (await client.get(f"/users/{bob['id']}/follow-status", headers=headers)).json()
    assert status["is_following"] is False


async def test_cannot_follow_yourself(auth_client: AsyncClient):
    me = (await auth_client.get("/auth/me")).json()
    resp = await auth_client.post(f"/users/{me['id']}/follow")
    assert resp.status_code == 400


async def test_follow_requires_auth(client: AsyncClient):
    bob = await _register(client, "bob@test.com", "bob")

    resp = await client.post(f"/users/{bob['id']}/follow")
    assert resp.status_code == 401

    profile = (await client.get(f"/users/{bob['id']}")).json()
    assert profile["followers_count"] == 0


async def test_follow_status_requires_auth(client: AsyncClient):
    bob = await _register(client, "bob@test.com", "bob")
    resp = await client.get(f"/users/{bob['id']}/follow-status")
    assert resp.status_code == 401


async def test_follow_nonexistent_user_returns_404(auth_client: AsyncClient):
    resp = await auth_client.post(f"/users/{uuid.uuid4()}/follow")
    assert resp.status_code == 404


async def test_follow_status_for_own_profile(auth_client: AsyncClient):
    me = (await auth_client.get("/auth/me")).json()
    status = (await auth_client.get(f"/users/{me['id']}/follow-status")).json()
    assert status["is_following"] is False


async def test_deleting_user_removes_follows(client: AsyncClient):
    alice = await _register(client, "alice@test.com", "alice")
    bob = await _register(client, "bob@test.com", "bob")

    token = await _login(client, "alice@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"/users/{bob['id']}/follow", headers=headers)

    assert (await client.get(f"/users/{bob['id']}")).json()["followers_count"] == 1

    await client.delete(f"/users/{bob['id']}")

    profile = (await client.get(f"/users/{alice['id']}")).json()
    assert profile["following_count"] == 0

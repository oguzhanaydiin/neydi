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


async def _create_deck(client: AsyncClient, headers: dict, **kwargs) -> dict:
    resp = await client.post("/decks", json=kwargs, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def test_copy_deck_with_custom_name(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    bob = await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(
        client,
        alice_headers,
        name="Spanish Basics",
        description="Core vocabulary",
        cards=[
            {"front": "Hola", "back": "Hello", "confidence": 4},
            {"front": "Adiós", "back": "Goodbye", "confidence": 2},
        ],
    )

    resp = await client.post(
        f"/decks/{source['id']}/copy",
        json={"name": "My Spanish", "description": "Personal copy"},
        headers=bob_headers,
    )
    assert resp.status_code == 201
    copy = resp.json()
    assert copy["name"] == "My Spanish"
    assert copy["description"] == "Personal copy"
    assert copy["id"] != source["id"]
    assert len(copy["cards"]) == 2
    assert all(card["confidence"] == 0 for card in copy["cards"])
    assert {c["front"] for c in copy["cards"]} == {"Hola", "Adiós"}

    bob_decks = (await client.get("/decks", headers=bob_headers)).json()
    assert len(bob_decks) == 1
    assert bob_decks[0]["id"] == copy["id"]

    alice_decks = (await client.get("/decks", headers=alice_headers)).json()
    assert len(alice_decks) == 1
    assert alice_decks[0]["id"] == source["id"]


async def test_copy_deck_keeps_source_description_when_omitted(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(
        client,
        alice_headers,
        name="Original",
        description="From Alice",
    )

    resp = await client.post(
        f"/decks/{source['id']}/copy",
        json={"name": "Bob's version"},
        headers=bob_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["description"] == "From Alice"


async def test_cannot_copy_own_deck(auth_client: AsyncClient):
    deck = await _create_deck(auth_client, {}, name="Mine")
    resp = await auth_client.post(
        f"/decks/{deck['id']}/copy",
        json={"name": "Duplicate"},
    )
    assert resp.status_code == 400


async def test_copy_requires_auth(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    token = await _login(client, "alice@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    deck = await _create_deck(client, headers, name="Deck")

    resp = await client.post(f"/decks/{deck['id']}/copy", json={"name": "Copy"})
    assert resp.status_code == 401


async def test_copy_nonexistent_deck_returns_404(auth_client: AsyncClient):
    resp = await auth_client.post(
        f"/decks/{uuid.uuid4()}/copy",
        json={"name": "Copy"},
    )
    assert resp.status_code == 404

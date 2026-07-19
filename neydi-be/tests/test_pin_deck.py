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


async def test_pin_deck_appears_on_dashboard(client: AsyncClient):
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
        cards=[{"front": "Hola", "back": "Hello"}],
    )

    resp = await client.post(f"/decks/{source['id']}/pin", headers=bob_headers)
    assert resp.status_code == 201
    pinned = resp.json()
    assert pinned["id"] == source["id"]
    assert pinned["name"] == "Spanish Basics"
    assert pinned["owner_username"] == "alice"
    assert pinned["cards"][0]["confidence"] == 0

    bob_owned = (await client.get("/decks", headers=bob_headers)).json()
    assert bob_owned == []

    bob_pinned = (await client.get("/decks/pinned", headers=bob_headers)).json()
    assert len(bob_pinned) == 1
    assert bob_pinned[0]["id"] == source["id"]


async def test_unpin_deck(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(client, alice_headers, name="Deck")
    deck_id = source["id"]

    await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    resp = await client.delete(f"/decks/{deck_id}/pin", headers=bob_headers)
    assert resp.status_code == 204

    bob_pinned = (await client.get("/decks/pinned", headers=bob_headers)).json()
    assert bob_pinned == []


async def test_cannot_pin_own_deck(auth_client: AsyncClient):
    deck = await _create_deck(auth_client, {}, name="Mine")
    resp = await auth_client.post(f"/decks/{deck['id']}/pin")
    assert resp.status_code == 400


async def test_cannot_pin_twice(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(client, alice_headers, name="Deck")
    deck_id = source["id"]

    resp1 = await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    assert resp1.status_code == 201
    resp2 = await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    assert resp2.status_code == 409


async def test_pin_status(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(client, alice_headers, name="Deck")
    deck_id = source["id"]

    status = (await client.get(f"/decks/{deck_id}/pin-status", headers=bob_headers)).json()
    assert status["is_pinned"] is False

    await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    status = (await client.get(f"/decks/{deck_id}/pin-status", headers=bob_headers)).json()
    assert status["is_pinned"] is True


async def test_pinned_deck_confidence_is_per_user(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(
        client,
        alice_headers,
        name="Deck",
        cards=[{"front": "Q", "back": "A", "confidence": 0}],
    )
    deck_id = source["id"]
    card_id = source["cards"][0]["id"]

    await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    resp = await client.patch(
        f"/decks/{deck_id}/cards/{card_id}/confidence",
        json={"confidence": 4},
        headers=bob_headers,
    )
    assert resp.status_code == 204

    bob_pinned = (await client.get("/decks/pinned", headers=bob_headers)).json()
    assert bob_pinned[0]["cards"][0]["confidence"] == 4

    alice_decks = (await client.get("/decks", headers=alice_headers)).json()
    assert alice_decks[0]["cards"][0]["confidence"] == 0


async def test_save_count_includes_pins_and_copies(client: AsyncClient):
    alice = await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")
    await _register(client, "carol@test.com", "carol")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    carol_token = await _login(client, "carol@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    carol_headers = {"Authorization": f"Bearer {carol_token}"}

    source = await _create_deck(client, alice_headers, name="Popular Deck")
    deck_id = source["id"]

    await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    await client.post(
        f"/decks/{deck_id}/copy",
        json={"name": "Carol's copy"},
        headers=carol_headers,
    )

    decks = (await client.get(f"/users/{alice['id']}/decks")).json()
    popular = next(d for d in decks if d["id"] == deck_id)
    assert popular["save_count"] == 2


async def test_copy_does_not_affect_pin(client: AsyncClient):
    """Copy and pin are independent — bob can pin without owning a copy."""
    await _register(client, "alice@test.com", "alice")
    await _register(client, "bob@test.com", "bob")

    alice_token = await _login(client, "alice@test.com")
    bob_token = await _login(client, "bob@test.com")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    source = await _create_deck(client, alice_headers, name="Deck")
    deck_id = source["id"]

    await client.post(f"/decks/{deck_id}/pin", headers=bob_headers)
    await client.post(f"/decks/{deck_id}/copy", json={"name": "Bob's copy"}, headers=bob_headers)

    bob_owned = (await client.get("/decks", headers=bob_headers)).json()
    assert len(bob_owned) == 1
    assert bob_owned[0]["id"] != deck_id

    bob_pinned = (await client.get("/decks/pinned", headers=bob_headers)).json()
    assert len(bob_pinned) == 1
    assert bob_pinned[0]["id"] == deck_id


async def test_pin_requires_auth(client: AsyncClient):
    await _register(client, "alice@test.com", "alice")
    token = await _login(client, "alice@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    deck = await _create_deck(client, headers, name="Deck")

    resp = await client.post(f"/decks/{deck['id']}/pin")
    assert resp.status_code == 401


async def test_pin_nonexistent_deck_returns_404(auth_client: AsyncClient):
    resp = await auth_client.post(f"/decks/{uuid.uuid4()}/pin")
    assert resp.status_code == 404

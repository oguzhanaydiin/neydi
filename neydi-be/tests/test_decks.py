import uuid

from httpx import AsyncClient

_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


async def _create_deck(client: AsyncClient, name: str = "Test Deck", **kwargs) -> dict:
    resp = await client.post("/decks", json={"name": name, **kwargs})
    assert resp.status_code == 201
    return resp.json()


async def _deck_with_cards(client: AsyncClient) -> dict:
    return await _create_deck(
        client,
        cards=[{"front": "Q1", "back": "A1"}, {"front": "Q2", "back": "A2"}],
    )



async def test_list_decks_empty(auth_client: AsyncClient):
    resp = await auth_client.get("/decks")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_deck(auth_client: AsyncClient):
    resp = await auth_client.post("/decks", json={"name": "My Deck", "description": "Desc"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Deck"
    assert data["description"] == "Desc"
    assert data["cards"] == []
    assert "id" in data
    assert "createdAt" in data


async def test_deck_appears_in_list(auth_client: AsyncClient):
    await _create_deck(auth_client)
    resp = await auth_client.get("/decks")
    assert len(resp.json()) == 1


async def test_deck_ownership_isolation(auth_client: AsyncClient):
    await _create_deck(auth_client, name="Alice's deck")

    await auth_client.post("/auth/register", json={
        "email": "bob@test.com", "username": "bob", "password": "bobpassword1",
    })
    token_resp = await auth_client.post(
        "/auth/token",
        content="username=bob@test.com&password=bobpassword1",
        headers=_HEADERS,
    )
    token_b = token_resp.json()["access_token"]

    resp = await auth_client.get("/decks", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_patch_deck(auth_client: AsyncClient):
    deck = await _create_deck(auth_client, name="Old Name")
    resp = await auth_client.patch(
        f"/decks/{deck['id']}",
        json={"name": "New Name", "description": "Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["description"] == "Updated"


async def test_put_deck_replaces_cards(auth_client: AsyncClient):
    deck = await _create_deck(auth_client, cards=[{"front": "Q", "back": "A"}])
    resp = await auth_client.put(
        f"/decks/{deck['id']}",
        json={"name": "Replaced", "cards": []},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Replaced"
    assert resp.json()["cards"] == []


async def test_put_nonexistent_deck_returns_404(auth_client: AsyncClient):
    resp = await auth_client.put(
        f"/decks/{uuid.uuid4()}",
        json={"name": "X", "cards": []},
    )
    assert resp.status_code == 404


async def test_delete_deck(auth_client: AsyncClient):
    deck = await _create_deck(auth_client)
    resp = await auth_client.delete(f"/decks/{deck['id']}")
    assert resp.status_code == 204

    decks = (await auth_client.get("/decks")).json()
    assert decks == []


async def test_delete_deck_cascades_cards(auth_client: AsyncClient):
    deck = await _deck_with_cards(auth_client)
    await auth_client.delete(f"/decks/{deck['id']}")
    resp = await auth_client.delete(f"/decks/{deck['id']}")
    assert resp.status_code == 404



async def test_add_card(auth_client: AsyncClient):
    deck = await _create_deck(auth_client)
    resp = await auth_client.post(
        f"/decks/{deck['id']}/cards",
        json={"front": "Question", "back": "Answer"},
    )
    assert resp.status_code == 201
    assert resp.json()["front"] == "Question"
    assert resp.json()["confidence"] == 0


async def test_update_card(auth_client: AsyncClient):
    deck = await _deck_with_cards(auth_client)
    card_id = deck["cards"][0]["id"]
    resp = await auth_client.patch(
        f"/decks/{deck['id']}/cards/{card_id}",
        json={"front": "Updated Q", "back": "Updated A"},
    )
    assert resp.status_code == 200
    assert resp.json()["front"] == "Updated Q"


async def test_update_card_confidence_clamped(auth_client: AsyncClient):
    deck = await _deck_with_cards(auth_client)
    card_id = deck["cards"][0]["id"]

    resp = await auth_client.patch(
        f"/decks/{deck['id']}/cards/{card_id}/confidence",
        json={"confidence": 10},
    )
    assert resp.status_code == 204

    fetched = (await auth_client.get("/decks")).json()[0]
    saved = next(c for c in fetched["cards"] if c["id"] == card_id)
    assert saved["confidence"] == 5


async def test_reorder_cards(auth_client: AsyncClient):
    deck = await _deck_with_cards(auth_client)
    card_ids = [c["id"] for c in deck["cards"]]

    resp = await auth_client.patch(
        f"/decks/{deck['id']}/cards/reorder",
        json={"order": list(reversed(card_ids))},
    )
    assert resp.status_code == 204


async def test_delete_card(auth_client: AsyncClient):
    deck = await _deck_with_cards(auth_client)
    card_id = deck["cards"][0]["id"]
    resp = await auth_client.delete(f"/decks/{deck['id']}/cards/{card_id}")
    assert resp.status_code == 204


async def test_delete_nonexistent_card_returns_404(auth_client: AsyncClient):
    deck = await _create_deck(auth_client)
    resp = await auth_client.delete(f"/decks/{deck['id']}/cards/{uuid.uuid4()}")
    assert resp.status_code == 404

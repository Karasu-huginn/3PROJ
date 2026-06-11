from conftest import login_as


def create_list(client, name, is_public=True):
    """Create a custom list and return its id."""
    return client.post("/collections", json={"name": name, "is_public": is_public}).json()["id"]


def test_add_item(client, seeded_media):
    """Adding a media to an owned list succeeds."""
    collection_id = create_list(client, "Lecture")
    response = client.post(f"/collections/{collection_id}/item/{seeded_media.id}")
    assert response.status_code == 201


def test_add_item_duplicate_409(client, seeded_media):
    """The same media cannot be added twice to one list."""
    collection_id = create_list(client, "Lecture")
    client.post(f"/collections/{collection_id}/item/{seeded_media.id}")
    response = client.post(f"/collections/{collection_id}/item/{seeded_media.id}")
    assert response.status_code == 409


def test_add_item_not_owned_404(client, user_two, seeded_media):
    """Adding into another user's list is rejected."""
    collection_id = create_list(client, "Lecture")
    login_as(user_two)
    response = client.post(f"/collections/{collection_id}/item/{seeded_media.id}")
    assert response.status_code == 404


def test_remove_item(client, seeded_media):
    """Removing an existing item succeeds."""
    collection_id = create_list(client, "Lecture")
    client.post(f"/collections/{collection_id}/item/{seeded_media.id}")
    response = client.delete(f"/collections/{collection_id}/item/{seeded_media.id}")
    assert response.status_code == 200


def test_remove_item_missing_404(client, seeded_media):
    """Removing an absent item returns 404."""
    collection_id = create_list(client, "Lecture")
    response = client.delete(f"/collections/{collection_id}/item/{seeded_media.id}")
    assert response.status_code == 404


def test_get_items_joins_media(client, seeded_media):
    """Items come back with title and cover from the Media cache."""
    collection_id = create_list(client, "Lecture")
    client.post(f"/collections/{collection_id}/item/{seeded_media.id}")
    response = client.get(f"/collections/{collection_id}/items")
    assert response.status_code == 200
    payload = response.json()
    assert payload["collection"]["item_count"] == 1
    assert payload["items"] == [{
        "media_id": seeded_media.id,
        "title": "Berserk",
        "cover_url": "http://example.com/berserk.jpg",
    }]


def test_get_items_public_visible_to_others(client, user_two, seeded_media):
    """A public list's items are readable by another user."""
    collection_id = create_list(client, "Publique", is_public=True)
    login_as(user_two)
    response = client.get(f"/collections/{collection_id}/items")
    assert response.status_code == 200


def test_get_items_private_hidden_from_others(client, user_two):
    """A private list's items return 403 for another user."""
    collection_id = create_list(client, "Privée", is_public=False)
    login_as(user_two)
    response = client.get(f"/collections/{collection_id}/items")
    assert response.status_code == 403


def test_move_item_between_own_lists(client, seeded_media):
    """Moving an item relocates it to the target list."""
    source_id = create_list(client, "Source")
    target_id = create_list(client, "Cible")
    client.post(f"/collections/{source_id}/item/{seeded_media.id}")
    response = client.patch(
        f"/collections/{source_id}/item/{seeded_media.id}",
        json={"to_collection_id": target_id},
    )
    assert response.status_code == 200
    target_items = client.get(f"/collections/{target_id}/items").json()["items"]
    assert [item["media_id"] for item in target_items] == [seeded_media.id]


def test_move_item_duplicate_in_target_409(client, seeded_media):
    """Moving onto a list that already has the media is rejected."""
    source_id = create_list(client, "Source")
    target_id = create_list(client, "Cible")
    client.post(f"/collections/{source_id}/item/{seeded_media.id}")
    client.post(f"/collections/{target_id}/item/{seeded_media.id}")
    response = client.patch(
        f"/collections/{source_id}/item/{seeded_media.id}",
        json={"to_collection_id": target_id},
    )
    assert response.status_code == 409


def test_get_items_nonexistent_collection_404(client):
    """Items of a collection that does not exist return 404."""
    response = client.get("/collections/999999/items")
    assert response.status_code == 404

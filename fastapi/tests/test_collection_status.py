def get_default_ids(client):
    """Return name→id mapping of the caller's default lists."""
    payload = client.get("/collections/me").json()
    return {collection["name"]: collection["id"] for collection in payload if collection["is_default"]}


def get_membership(client, media_id):
    """Return the caller's collection ids containing the media."""
    return client.get(f"/collections/me/membership/{media_id}").json()["collection_ids"]


def test_set_status_adds_to_default(client, seeded_media):
    """Setting a status puts the media in that default list."""
    default_ids = get_default_ids(client)
    response = client.put(
        f"/collections/me/status/{seeded_media.id}",
        json={"collection_id": default_ids["En cours"]},
    )
    assert response.status_code == 200
    assert get_membership(client, seeded_media.id) == [default_ids["En cours"]]


def test_switch_status_is_exclusive(client, seeded_media):
    """Switching status removes the media from the previous default list."""
    default_ids = get_default_ids(client)
    client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": default_ids["À voir/lire"]})
    client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": default_ids["Terminé"]})
    assert get_membership(client, seeded_media.id) == [default_ids["Terminé"]]


def test_null_clears_status(client, seeded_media):
    """A null collection_id removes the media from all default lists."""
    default_ids = get_default_ids(client)
    client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": default_ids["En cours"]})
    response = client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": None})
    assert response.status_code == 200
    assert get_membership(client, seeded_media.id) == []


def test_status_target_must_be_default_403(client, seeded_media):
    """A custom list cannot be a status target."""
    custom_id = client.post("/collections", json={"name": "Perso"}).json()["id"]
    response = client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": custom_id})
    assert response.status_code == 403


def test_status_switch_leaves_custom_lists_alone(client, seeded_media):
    """Switching status never touches custom-list memberships."""
    default_ids = get_default_ids(client)
    custom_id = client.post("/collections", json={"name": "Perso"}).json()["id"]
    client.post(f"/collections/{custom_id}/item/{seeded_media.id}")
    client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": default_ids["En cours"]})
    membership_ids = get_membership(client, seeded_media.id)
    assert custom_id in membership_ids
    assert default_ids["En cours"] in membership_ids


def test_set_status_is_idempotent(client, seeded_media):
    """Setting the same status twice keeps a single item row."""
    default_ids = get_default_ids(client)
    client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": default_ids["En cours"]})
    client.put(f"/collections/me/status/{seeded_media.id}", json={"collection_id": default_ids["En cours"]})
    assert get_membership(client, seeded_media.id) == [default_ids["En cours"]]

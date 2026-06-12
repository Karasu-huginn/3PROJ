import models
from conftest import login_as


def test_create_collection(client):
    """A custom list is created and returned serialized."""
    response = client.post("/collections", json={"name": "Coups de coeur", "is_public": False})
    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Coups de coeur"
    assert payload["is_public"] is False
    assert payload["is_default"] is False
    assert payload["item_count"] == 0


def test_create_collection_duplicate_name_409(client):
    """The same user cannot have two lists with the same name."""
    client.post("/collections", json={"name": "Coups de coeur"})
    response = client.post("/collections", json={"name": "Coups de coeur"})
    assert response.status_code == 409


def test_create_collection_same_name_other_user(client, user_two):
    """Two different users can use the same list name."""
    client.post("/collections", json={"name": "Coups de coeur"})
    login_as(user_two)
    response = client.post("/collections", json={"name": "Coups de coeur"})
    assert response.status_code == 201


def get_default_ids(client):
    """Return name→id mapping of the caller's default lists."""
    payload = client.get("/collections/me").json()
    return {collection["name"]: collection["id"] for collection in payload if collection["is_default"]}


def test_rename_custom_collection(client):
    """Renaming a custom list works."""
    created = client.post("/collections", json={"name": "Avant"}).json()
    response = client.patch(f"/collections/{created['id']}", json={"name": "Après"})
    assert response.status_code == 200
    assert response.json()["name"] == "Après"


def test_rename_default_collection_403(client):
    """Default lists cannot be renamed."""
    default_ids = get_default_ids(client)
    response = client.patch(f"/collections/{default_ids['En cours']}", json={"name": "Hacké"})
    assert response.status_code == 403


def test_toggle_visibility_on_default(client):
    """is_public can be changed even on a default list."""
    default_ids = get_default_ids(client)
    response = client.patch(f"/collections/{default_ids['En cours']}", json={"is_public": False})
    assert response.status_code == 200
    assert response.json()["is_public"] is False


def test_rename_to_existing_name_409(client):
    """Renaming onto another of the user's list names is rejected."""
    client.post("/collections", json={"name": "Liste A"})
    created_b = client.post("/collections", json={"name": "Liste B"}).json()
    response = client.patch(f"/collections/{created_b['id']}", json={"name": "Liste A"})
    assert response.status_code == 409


def test_patch_not_owned_404(client, user_two):
    """Another user's list looks nonexistent."""
    created = client.post("/collections", json={"name": "La mienne"}).json()
    login_as(user_two)
    response = client.patch(f"/collections/{created['id']}", json={"name": "Volée"})
    assert response.status_code == 404


def test_delete_custom_collection(client):
    """Deleting a custom list removes it from /me."""
    created = client.post("/collections", json={"name": "À jeter"}).json()
    response = client.delete(f"/collections/{created['id']}")
    assert response.status_code == 200
    names = [collection["name"] for collection in client.get("/collections/me").json()]
    assert "À jeter" not in names


def test_delete_default_collection_403(client):
    """Default lists cannot be deleted."""
    default_ids = get_default_ids(client)
    response = client.delete(f"/collections/{default_ids['Terminé']}")
    assert response.status_code == 403


def test_delete_cascades_items(client, db_session):
    """Deleting a list also deletes its item rows."""
    created = client.post("/collections", json={"name": "Avec items"}).json()
    db_session.add(models.CollectionsItems(collection_id=created["id"], media_id="abc-123"))
    db_session.commit()
    client.delete(f"/collections/{created['id']}")
    orphan_items = db_session.query(models.CollectionsItems).filter(
        models.CollectionsItems.collection_id == created["id"]).all()
    assert orphan_items == []


def test_delete_not_owned_404(client, user_two):
    """Another user's list looks nonexistent on delete too."""
    created = client.post("/collections", json={"name": "La mienne"}).json()
    login_as(user_two)
    response = client.delete(f"/collections/{created['id']}")
    assert response.status_code == 404

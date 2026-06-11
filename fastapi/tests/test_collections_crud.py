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

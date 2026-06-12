from fastapi.testclient import TestClient

import models
from main import app
from auth.dependencies import get_current_user
from conftest import override_current_user


def test_me_creates_three_default_lists(client):
    """First call creates the three default lists in canonical order."""
    response = client.get("/collections/me")
    assert response.status_code == 200
    payload = response.json()
    assert [collection["name"] for collection in payload] == ["À voir/lire", "En cours", "Terminé"]
    assert all(collection["is_default"] for collection in payload)
    assert all(collection["item_count"] == 0 for collection in payload)


def test_me_is_idempotent(client):
    """Calling twice never duplicates the defaults."""
    client.get("/collections/me")
    response = client.get("/collections/me")
    assert len(response.json()) == 3


def test_me_lists_defaults_before_customs(client, db_session, user_one):
    """Custom lists come after the three defaults."""
    client.get("/collections/me")
    db_session.add(models.Collections(user_id=user_one.id, name="Coups de coeur"))
    db_session.commit()
    response = client.get("/collections/me")
    names = [collection["name"] for collection in response.json()]
    assert names == ["À voir/lire", "En cours", "Terminé", "Coups de coeur"]


def test_me_requires_authentication():
    """Without a bearer token the route is rejected."""
    app.dependency_overrides.pop(get_current_user, None)
    try:
        response = TestClient(app).get("/collections/me")
        assert response.status_code in (401, 403)  #* because HTTPBearer rejects a missing header; exact code varies by FastAPI version
    finally:
        app.dependency_overrides[get_current_user] = override_current_user


def test_old_global_listing_is_gone(client):
    """GET /collections (all users' lists) no longer exists."""
    response = client.get("/collections")
    assert response.status_code in (404, 405)

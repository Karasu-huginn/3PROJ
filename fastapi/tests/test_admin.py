"""
Tests des routes d'administration (/admin/*)

Couverture :
- Contrôle d'accès : un utilisateur normal reçoit 403 sur toutes les routes admin
- GET  /admin/flagged-reviews       : liste les critiques signalées
- POST /admin/reviews/{id}/unflag   : retire le signalement
- POST /admin/reviews/{id}/feature  : bascule le statut "coup de cœur"
- DELETE /admin/reviews/{id}        : supprime une critique
- GET  /admin/users                 : liste les utilisateurs (+ recherche)
- POST /admin/users/{id}/ban        : bannit un utilisateur
- POST /admin/users/{id}/unban      : réactive un utilisateur banni
- Cas limites : introuvable, bannir un admin, se bannir soi-même
"""

import pytest
import models
from conftest import login_as



@pytest.fixture()
def admin_user(db_session):
    user = models.Users(
        pseudo="admin", email="admin@example.com", password="x", role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def regular_user(db_session):
    user = models.Users(
        pseudo="regular", email="regular@example.com", password="x", role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def seeded_review(db_session, seeded_media, regular_user):
    review = models.Reviews(
        media_id=seeded_media.id,
        user_id=regular_user.id,
        title="Super manga",
        content="J'ai adoré ce manga, vraiment top !",
        spoiler_flag=False,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


@pytest.fixture()
def flagged_review(db_session, seeded_review):
    seeded_review.is_flagged = True
    seeded_review.flag_reason = "Insultes"
    db_session.commit()
    db_session.refresh(seeded_review)
    return seeded_review



class TestAdminAccessControl:
    def test_user_cannot_list_flagged_reviews(self, client, regular_user):
        login_as(regular_user)
        r = client.get("/admin/flagged-reviews")
        assert r.status_code == 403

    def test_user_cannot_unflag_review(self, client, regular_user, flagged_review):
        login_as(regular_user)
        r = client.post(f"/admin/reviews/{flagged_review.id}/unflag")
        assert r.status_code == 403

    def test_user_cannot_feature_review(self, client, regular_user, seeded_review):
        login_as(regular_user)
        r = client.post(f"/admin/reviews/{seeded_review.id}/feature")
        assert r.status_code == 403

    def test_user_cannot_delete_review(self, client, regular_user, seeded_review):
        login_as(regular_user)
        r = client.delete(f"/admin/reviews/{seeded_review.id}")
        assert r.status_code == 403

    def test_user_cannot_list_users(self, client, regular_user):
        login_as(regular_user)
        r = client.get("/admin/users")
        assert r.status_code == 403

    def test_user_cannot_ban(self, client, regular_user, admin_user):
        login_as(regular_user)
        r = client.post(f"/admin/users/{admin_user.id}/ban")
        assert r.status_code == 403




class TestListFlaggedReviews:
    def test_returns_empty_when_no_flags(self, client, admin_user, seeded_review):
        login_as(admin_user)
        r = client.get("/admin/flagged-reviews")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["reviews"] == []

    def test_returns_flagged_review(self, client, admin_user, flagged_review):
        login_as(admin_user)
        r = client.get("/admin/flagged-reviews")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        rev = data["reviews"][0]
        assert rev["id"] == flagged_review.id
        assert rev["flag_reason"] == "Insultes"
        assert rev["author"]["username"] == "regular"

    def test_non_flagged_not_included(self, client, admin_user, seeded_review, flagged_review):
        login_as(admin_user)
        r = client.get("/admin/flagged-reviews")
        assert r.json()["total"] == 1




class TestUnflagReview:
    def test_unflag_clears_flag(self, client, admin_user, flagged_review, db_session):
        login_as(admin_user)
        r = client.post(f"/admin/reviews/{flagged_review.id}/unflag")
        assert r.status_code == 200
        db_session.refresh(flagged_review)
        assert flagged_review.is_flagged is False
        assert flagged_review.flag_reason is None

    def test_unflag_unknown_review_404(self, client, admin_user):
        login_as(admin_user)
        r = client.post("/admin/reviews/99999/unflag")
        assert r.status_code == 404



class TestFeatureReview:
    def test_feature_activates(self, client, admin_user, seeded_review, db_session):
        login_as(admin_user)
        r = client.post(f"/admin/reviews/{seeded_review.id}/feature")
        assert r.status_code == 200
        assert r.json()["is_featured"] is True
        db_session.refresh(seeded_review)
        assert seeded_review.is_featured is True

    def test_feature_toggles_off(self, client, admin_user, seeded_review, db_session):
        login_as(admin_user)
        client.post(f"/admin/reviews/{seeded_review.id}/feature")
        r = client.post(f"/admin/reviews/{seeded_review.id}/feature")
        assert r.json()["is_featured"] is False
        db_session.refresh(seeded_review)
        assert seeded_review.is_featured is False

    def test_feature_unknown_review_404(self, client, admin_user):
        login_as(admin_user)
        r = client.post("/admin/reviews/99999/feature")
        assert r.status_code == 404


class TestAdminDeleteReview:
    def test_delete_removes_review(self, client, admin_user, seeded_review, db_session):
        login_as(admin_user)
        review_id = seeded_review.id
        r = client.delete(f"/admin/reviews/{review_id}")
        assert r.status_code == 204
        db_session.expire_all()
        assert db_session.get(models.Reviews, review_id) is None

    def test_delete_unknown_review_404(self, client, admin_user):
        login_as(admin_user)
        r = client.delete("/admin/reviews/99999")
        assert r.status_code == 404


class TestListUsers:
    def test_returns_all_users(self, client, admin_user, regular_user):
        login_as(admin_user)
        r = client.get("/admin/users")
        assert r.status_code == 200
        data = r.json()
        pseudos = {u["pseudo"] for u in data["users"]}
        assert "admin" in pseudos
        assert "regular" in pseudos

    def test_search_filters_by_pseudo(self, client, admin_user, regular_user):
        login_as(admin_user)
        r = client.get("/admin/users?q=regu")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["users"][0]["pseudo"] == "regular"

    def test_search_no_match_returns_empty(self, client, admin_user):
        login_as(admin_user)
        r = client.get("/admin/users?q=zzznomatch")
        assert r.json()["total"] == 0

    def test_user_fields_present(self, client, admin_user, regular_user):
        login_as(admin_user)
        data = client.get("/admin/users").json()
        user = next(u for u in data["users"] if u["pseudo"] == "regular")
        assert "email" in user
        assert "role" in user
        assert "is_active" in user
        assert "created_at" in user



class TestBanUser:
    def test_ban_deactivates_user(self, client, admin_user, regular_user, db_session):
        login_as(admin_user)
        r = client.post(f"/admin/users/{regular_user.id}/ban")
        assert r.status_code == 200
        db_session.refresh(regular_user)
        assert regular_user.is_active is False

    def test_ban_unknown_user_404(self, client, admin_user):
        login_as(admin_user)
        r = client.post("/admin/users/99999/ban")
        assert r.status_code == 404

    def test_cannot_ban_self(self, client, admin_user):
        login_as(admin_user)
        r = client.post(f"/admin/users/{admin_user.id}/ban")
        assert r.status_code == 400

    def test_cannot_ban_another_admin(self, client, admin_user, db_session):
        other_admin = models.Users(
            pseudo="admin2", email="admin2@example.com", password="x", role="admin"
        )
        db_session.add(other_admin)
        db_session.commit()
        db_session.refresh(other_admin)
        login_as(admin_user)
        r = client.post(f"/admin/users/{other_admin.id}/ban")
        assert r.status_code == 400



class TestUnbanUser:
    def test_unban_reactivates_user(self, client, admin_user, regular_user, db_session):
        regular_user.is_active = False
        db_session.commit()
        login_as(admin_user)
        r = client.post(f"/admin/users/{regular_user.id}/unban")
        assert r.status_code == 200
        db_session.refresh(regular_user)
        assert regular_user.is_active is True

    def test_unban_unknown_user_404(self, client, admin_user):
        login_as(admin_user)
        r = client.post("/admin/users/99999/unban")
        assert r.status_code == 404

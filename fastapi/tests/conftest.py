import os

os.environ["DATABASE_URL"] = "sqlite:///./test_library.db"  #* because database.py reads the env at import time and load_dotenv never overrides existing vars

import pytest
from fastapi.testclient import TestClient

import database
import models
from main import app
from auth.dependencies import get_current_user

current_test_user = {"user": None}


def override_current_user():
    """Return the test user injected by the client fixture or login_as."""
    return current_test_user["user"]


app.dependency_overrides[get_current_user] = override_current_user


def login_as(user):
    """Switch the authenticated user for subsequent client calls."""
    current_test_user["user"] = user


@pytest.fixture()
def db_session():
    """Yield a session on freshly recreated tables."""
    models.Base.metadata.drop_all(bind=database.engine)
    models.Base.metadata.create_all(bind=database.engine)
    session = database.SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def user_one(db_session):
    """Create and return the primary test user."""
    user = models.Users(pseudo="testeur", email="testeur@example.com", password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def user_two(db_session):
    """Create and return a second user for ownership tests."""
    user = models.Users(pseudo="intrus", email="intrus@example.com", password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def client(db_session, user_one):
    """Return a TestClient authenticated as user_one."""
    current_test_user["user"] = user_one
    return TestClient(app)

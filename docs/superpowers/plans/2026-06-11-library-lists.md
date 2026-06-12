# Library / Lists Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Library ("Bibliothèque") feature — per-user default reading-status lists plus custom lists, manageable from a new frontend tab and quick-add buttons on the manga details modal.

**Architecture:** Backend (FastAPI + SQLAlchemy, `fastapi` branch in a git worktree): JWT-secured collections router with lazy "ensure-on-read" creation of three undeletable default lists, an atomic status-switch endpoint, and a membership endpoint. Frontend (React 19 + Vite, `Antoine` branch in the main working tree): a typed `api/collections.ts` fetch layer, the manga modal extracted into a shared `MangaDetailModal` with a `LibraryActions` quick-add block, and a `Bibliotheque` tab with dashboard + list detail views.

**Tech Stack:** FastAPI 0.129, SQLAlchemy 2.x, pytest + TestClient (SQLite test DB), React 19, TypeScript, Vite.

**Spec:** `docs/superpowers/specs/2026-06-11-library-lists-design.md`

---

## Ground rules for every task

- **Branch/directory discipline:** Tasks 1–9 (backend) run inside the worktree `C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi`, on branch `fastapi`. Tasks 10–14 (frontend) run in the main tree `C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ`, on branch `Antoine`.
- **Commits:** NO `Co-Authored-By` or any AI-attribution trailer — ever (project rule).
- **Python style (project + user rules):** functions ≤ 40 lines, one-line docstring on every function, verbose names, plural list names, `is_`/`has_` booleans, guard clauses over nesting. Comments only explain WHY, written as trailing `#* because ...` (the `#*` marker is the project convention).
- **TypeScript style:** match the existing codebase (inline `fetch` style error handling, `err: any` in catches, French UI strings, existing CSS classes).
- **Backend tests** must run from the worktree's `fastapi/` directory (flat imports): `pytest tests/ -v`.

---

### Task 1: Backend worktree + pytest harness

**Files:**
- Create: worktree `..\3PROJ-fastapi` (branch `fastapi` from `main`)
- Create: `fastapi/requirements-dev.txt` (worktree)
- Create: `fastapi/tests/conftest.py` (worktree)
- Create: `fastapi/tests/test_smoke.py` (worktree)
- Modify: `fastapi/.gitignore` (worktree)

- [ ] **Step 1: Create the worktree**

There is no local `fastapi` branch; `origin/fastapi` is fully merged into `main` and 8 commits behind it, so the branch restarts from `main` (pushing later is a fast-forward).

```powershell
git -C "C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ" worktree add ..\3PROJ-fastapi -b fastapi main
```

Expected: `Preparing worktree (new branch 'fastapi')`.

- [ ] **Step 2: Copy the gitignored .env into the worktree**

```powershell
Copy-Item "C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ\fastapi\.env" "C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi\.env"
```

- [ ] **Step 3: Create `requirements-dev.txt`**

⚠️ Do NOT append to `requirements.txt` — it is UTF-16 encoded and easy to corrupt. Create a separate dev file (UTF-8). `httpx` (needed by TestClient) is already in the main requirements.

Create `C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi\requirements-dev.txt`:

```
pytest==8.3.4
```

Install:

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi
pip install -r requirements-dev.txt
```

- [ ] **Step 4: Ignore the test database**

Append to `C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi\.gitignore`:

```
test_library.db
```

- [ ] **Step 5: Write `tests/conftest.py`**

How it works: `database.py` calls `load_dotenv()` then `os.getenv("DATABASE_URL")` at import time, and `load_dotenv` never overrides pre-existing env vars — so setting the env var before any project import points the whole app at a throwaway SQLite file. Auth is bypassed by overriding `get_current_user` with a function that returns whichever user the test selected via `current_test_user` (so swapping users mid-test is just a dict write).

Create `fastapi/tests/conftest.py`:

```python
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
```

- [ ] **Step 6: Write the smoke test**

Create `fastapi/tests/test_smoke.py`:

```python
def test_root_endpoint_responds(client):
    """The app boots and serves the root route under the test harness."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SCRUM TEAM"}
```

- [ ] **Step 7: Run the smoke test**

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi
pytest tests/ -v
```

Expected: `1 passed`. (If import fails on `DATABASE_URL`, the env assignment in conftest is not before the project imports — fix the ordering.)

- [ ] **Step 8: Commit**

```powershell
git add tests/ requirements-dev.txt .gitignore
git commit -m "test: add pytest harness with sqlite test db and auth override"
```

---

### Task 2: `is_default` column + new collection schemas

**Files:**
- Modify: `fastapi/models.py:49-56` (worktree)
- Modify: `fastapi/schemas.py` (worktree)
- Create: `fastapi/tests/test_models.py` (worktree)

- [ ] **Step 1: Write the failing test**

Create `fastapi/tests/test_models.py`:

```python
import models


def test_collections_has_is_default_column(db_session, user_one):
    """is_default persists and defaults to False."""
    default_list = models.Collections(user_id=user_one.id, name="En cours", is_default=True)
    custom_list = models.Collections(user_id=user_one.id, name="Perso")
    db_session.add_all([default_list, custom_list])
    db_session.commit()
    db_session.refresh(default_list)
    db_session.refresh(custom_list)
    assert default_list.is_default is True
    assert custom_list.is_default is False
```

- [ ] **Step 2: Run it — verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `TypeError: 'is_default' is an invalid keyword argument for Collections`

- [ ] **Step 3: Add the column**

In `fastapi/models.py`, class `Collections`, add one line after `is_public`:

```python
class Collections(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poster_url = Column(String)
    is_public = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    name = Column(String)
```

- [ ] **Step 4: Add the new request schemas**

In `fastapi/schemas.py`: change the first line to import `Optional`, and add the three new models after `CollectionsItemsBase` (keep `CollectionsBase`/`CollectionsItemsBase` for now — the old router still imports them until Task 3):

```python
from typing import Optional
from pydantic import BaseModel
```

```python
class CollectionCreate(BaseModel):
    name : str
    is_public : bool = True

class CollectionUpdate(BaseModel):
    name : Optional[str] = None
    is_public : Optional[bool] = None

class CollectionStatusUpdate(BaseModel):
    collection_id : Optional[int] = None
```

(`CollectionItemMove` stays unchanged.)

- [ ] **Step 5: Run tests — verify pass**

Run: `pytest tests/ -v`
Expected: `2 passed`

- [ ] **Step 6: Commit**

```powershell
git add models.py schemas.py tests/test_models.py
git commit -m "feat(collections): add is_default column and new request schemas"
```

---

### Task 3: Router rewrite — auth + `GET /collections/me` (ensure-on-read)

**Files:**
- Rewrite: `fastapi/routers/collections.py` (worktree)
- Modify: `fastapi/schemas.py` (worktree — delete `CollectionsBase`, `CollectionsItemsBase`)
- Create: `fastapi/tests/test_collections_me.py` (worktree)

This task replaces the whole router file. The old routes (create/update/delete/items/move) disappear here and come back secured in Tasks 4–8 — nothing else in the app imports them, and the frontend doesn't call collections yet.

- [ ] **Step 1: Write the failing tests**

Create `fastapi/tests/test_collections_me.py`:

```python
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
        assert response.status_code == 403  #* because HTTPBearer rejects a missing header with 403, not 401
    finally:
        app.dependency_overrides[get_current_user] = override_current_user


def test_old_global_listing_is_gone(client):
    """GET /collections (all users' lists) no longer exists."""
    response = client.get("/collections")
    assert response.status_code in (404, 405)
```

- [ ] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_collections_me.py -v`
Expected: 4 FAIL (404 on `/collections/me`), `test_old_global_listing_is_gone` FAILS too (old route returns 200).

- [ ] **Step 3: Replace `fastapi/routers/collections.py` entirely**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated

import models
from auth.dependencies import get_current_user
from database import get_db
from schemas import CollectionCreate, CollectionUpdate, CollectionStatusUpdate, CollectionItemMove

router = APIRouter(prefix="/collections", tags=["collections"])

db_dep = Annotated[Session, Depends(get_db)]
user_dep = Annotated[models.Users, Depends(get_current_user)]

DEFAULT_COLLECTION_NAMES = ["À voir/lire", "En cours", "Terminé"]


def ensure_default_collections(db: Session, user_id: int) -> None:
    """Create the user's missing default collections, if any."""
    existing_names = {
        collection.name
        for collection in db.query(models.Collections)
        .filter(and_(models.Collections.user_id == user_id, models.Collections.is_default == True))
        .all()
    }
    missing_names = [name for name in DEFAULT_COLLECTION_NAMES if name not in existing_names]
    if not missing_names:
        return
    for name in missing_names:
        db.add(models.Collections(user_id=user_id, name=name, is_default=True, is_public=True))
    db.commit()


def derive_poster_url(db: Session, collection_id: int):
    """Return the cover of the collection's first item, or None."""
    first_row = (
        db.query(models.Media.cover_url)
        .join(models.CollectionsItems, models.CollectionsItems.media_id == models.Media.id)
        .filter(models.CollectionsItems.collection_id == collection_id)
        .order_by(models.CollectionsItems.id.asc())
        .first()
    )
    return first_row.cover_url if first_row else None


def serialize_collection(db: Session, collection: models.Collections) -> dict:
    """Return the API representation of a collection."""
    item_count = (
        db.query(func.count(models.CollectionsItems.id))
        .filter(models.CollectionsItems.collection_id == collection.id)
        .scalar()
    )
    return {
        "id": collection.id,
        "name": collection.name,
        "is_default": collection.is_default,
        "is_public": collection.is_public,
        "item_count": item_count,
        "poster_url": collection.poster_url or derive_poster_url(db, collection.id),
    }


def get_owned_collection(db: Session, user_id: int, collection_id: int) -> models.Collections:
    """Return the user's collection by id, raising 404 if absent or not owned."""
    collection = (
        db.query(models.Collections)
        .filter(and_(models.Collections.id == collection_id, models.Collections.user_id == user_id))
        .first()
    )
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liste introuvable")
    return collection


@router.get("/me")
def get_my_collections(db: db_dep, current_user: user_dep):
    """Return the caller's collections, defaults first, creating defaults if missing."""
    ensure_default_collections(db, current_user.id)
    collections = (
        db.query(models.Collections)
        .filter(models.Collections.user_id == current_user.id)
        .order_by(models.Collections.is_default.desc(), models.Collections.id.asc())
        .all()
    )
    return [serialize_collection(db, collection) for collection in collections]
```

Invariant for all later tasks: every new `/me/...` route is inserted **directly after `get_my_collections`**, and every `/{collection_id}/...` route goes after the `/me` block — so `me` can never be captured by an integer path param.

- [ ] **Step 4: Delete the dead schemas**

In `fastapi/schemas.py`, delete the `CollectionsBase` and `CollectionsItemsBase` classes (nothing imports them anymore).

- [ ] **Step 5: Run the tests — verify pass**

Run: `pytest tests/ -v`
Expected: `7 passed`

- [ ] **Step 6: Commit**

```powershell
git add routers/collections.py schemas.py tests/test_collections_me.py
git commit -m "feat(collections): JWT-secured GET /collections/me with ensure-on-read defaults"
```

---

### Task 4: `POST /collections`

**Files:**
- Modify: `fastapi/routers/collections.py` (worktree)
- Create: `fastapi/tests/test_collections_crud.py` (worktree)

- [ ] **Step 1: Write the failing tests**

Create `fastapi/tests/test_collections_crud.py`:

```python
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
```

- [ ] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_collections_crud.py -v`
Expected: 3 FAIL (405 Method Not Allowed — no POST route yet)

- [ ] **Step 3: Add the route**

Append to `fastapi/routers/collections.py` (after the `/me` block):

```python
@router.post("", status_code=status.HTTP_201_CREATED)
def create_collection(db: db_dep, current_user: user_dep, collection_create: CollectionCreate):
    """Create a custom collection owned by the caller."""
    duplicate = (
        db.query(models.Collections)
        .filter(and_(models.Collections.user_id == current_user.id, models.Collections.name == collection_create.name))
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Une liste porte déjà ce nom")
    collection = models.Collections(
        user_id=current_user.id,
        name=collection_create.name,
        is_public=collection_create.is_public,
        is_default=False,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return serialize_collection(db, collection)
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/ -v`
Expected: `10 passed`

- [ ] **Step 5: Commit**

```powershell
git add routers/collections.py tests/test_collections_crud.py
git commit -m "feat(collections): authenticated POST /collections with per-user duplicate check"
```

---

### Task 5: `PATCH /collections/{collection_id}`

**Files:**
- Modify: `fastapi/routers/collections.py` (worktree)
- Modify: `fastapi/tests/test_collections_crud.py` (worktree)

- [ ] **Step 1: Write the failing tests**

Append to `fastapi/tests/test_collections_crud.py`:

```python
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
```

- [ ] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_collections_crud.py -v`
Expected: the 5 new tests FAIL with 405 (no PATCH route)

- [ ] **Step 3: Add the route**

Append to `fastapi/routers/collections.py`:

```python
@router.patch("/{collection_id}")
def update_collection(db: db_dep, current_user: user_dep, collection_id: int, collection_update: CollectionUpdate):
    """Rename a collection and/or change its visibility."""
    collection = get_owned_collection(db, current_user.id, collection_id)
    if collection_update.name is not None:
        if collection.is_default:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Les listes par défaut ne peuvent pas être renommées")
        duplicate = (
            db.query(models.Collections)
            .filter(and_(
                models.Collections.user_id == current_user.id,
                models.Collections.name == collection_update.name,
                models.Collections.id != collection_id,
            ))
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Une liste porte déjà ce nom")
        collection.name = collection_update.name
    if collection_update.is_public is not None:
        collection.is_public = collection_update.is_public
    db.commit()
    db.refresh(collection)
    return serialize_collection(db, collection)
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/ -v`
Expected: `15 passed`

- [ ] **Step 5: Commit**

```powershell
git add routers/collections.py tests/test_collections_crud.py
git commit -m "feat(collections): owner-only PATCH with default-list rename protection"
```

---

### Task 6: `DELETE /collections/{collection_id}`

**Files:**
- Modify: `fastapi/routers/collections.py` (worktree)
- Modify: `fastapi/tests/test_collections_crud.py` (worktree)

- [ ] **Step 1: Write the failing tests**

Append to `fastapi/tests/test_collections_crud.py` (add `import models` at the top of the file):

```python
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
```

- [ ] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_collections_crud.py -v`
Expected: the 4 new tests FAIL with 405

- [ ] **Step 3: Add the route**

Append to `fastapi/routers/collections.py`:

```python
@router.delete("/{collection_id}")
def rm_collection(db: db_dep, current_user: user_dep, collection_id: int):
    """Delete a custom collection and its items."""
    collection = get_owned_collection(db, current_user.id, collection_id)
    if collection.is_default:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Les listes par défaut ne peuvent pas être supprimées")
    db.query(models.CollectionsItems).filter(
        models.CollectionsItems.collection_id == collection_id
    ).delete(synchronize_session=False)
    db.delete(collection)
    db.commit()
    return {"detail": "Liste supprimée"}
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/ -v`
Expected: `19 passed`

- [ ] **Step 5: Commit**

```powershell
git add routers/collections.py tests/test_collections_crud.py
git commit -m "feat(collections): owner-only DELETE with default protection and item cascade"
```

---

### Task 7: Items — add / remove / list + secured move

**Files:**
- Modify: `fastapi/routers/collections.py` (worktree)
- Modify: `fastapi/tests/conftest.py` (worktree — add `seeded_media` fixture)
- Create: `fastapi/tests/test_collection_items.py` (worktree)

- [ ] **Step 1: Add the media fixture**

Append to `fastapi/tests/conftest.py`:

```python
@pytest.fixture()
def seeded_media(db_session):
    """Create and return a cached media row."""
    media = models.Media(
        id="11111111-1111-1111-1111-111111111111",
        type="manga",
        title_original="Berserk",
        cover_url="http://example.com/berserk.jpg",
    )
    db_session.add(media)
    db_session.commit()
    return media
```

- [ ] **Step 2: Write the failing tests**

Create `fastapi/tests/test_collection_items.py`:

```python
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
```

- [ ] **Step 3: Run them — verify they fail**

Run: `pytest tests/test_collection_items.py -v`
Expected: 10 FAIL (404/405 — routes don't exist)

- [ ] **Step 4: Add the routes**

Append to `fastapi/routers/collections.py`:

```python
@router.get("/{collection_id}/items")
def get_collection_items(db: db_dep, current_user: user_dep, collection_id: int):
    """Return the collection's items joined with their media info."""
    collection = db.query(models.Collections).filter(models.Collections.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liste introuvable")
    if collection.user_id != current_user.id and not collection.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette liste est privée")
    rows = (
        db.query(
            models.CollectionsItems.media_id,
            models.Media.title_fr,
            models.Media.title_en,
            models.Media.title_original,
            models.Media.cover_url,
        )
        .outerjoin(models.Media, models.Media.id == models.CollectionsItems.media_id)  #* because an item must stay visible even if its Media cache row vanished
        .filter(models.CollectionsItems.collection_id == collection_id)
        .order_by(models.CollectionsItems.id.asc())
        .all()
    )
    items = [
        {
            "media_id": row.media_id,
            "title": row.title_fr or row.title_en or row.title_original or "Titre inconnu",
            "cover_url": row.cover_url,
        }
        for row in rows
    ]
    return {"collection": serialize_collection(db, collection), "items": items}


@router.post("/{collection_id}/item/{media_id}", status_code=status.HTTP_201_CREATED)
def add_item_to_collection(db: db_dep, current_user: user_dep, collection_id: int, media_id: str):
    """Add a media to the caller's collection."""
    get_owned_collection(db, current_user.id, collection_id)
    duplicate = (
        db.query(models.CollectionsItems)
        .filter(and_(models.CollectionsItems.collection_id == collection_id, models.CollectionsItems.media_id == media_id))
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce manga est déjà dans la liste")
    db.add(models.CollectionsItems(collection_id=collection_id, media_id=media_id))
    db.commit()
    return {"detail": "Manga ajouté à la liste"}


@router.delete("/{collection_id}/item/{media_id}")
def rm_item_from_collection(db: db_dep, current_user: user_dep, collection_id: int, media_id: str):
    """Remove a media from the caller's collection."""
    get_owned_collection(db, current_user.id, collection_id)
    item_query = db.query(models.CollectionsItems).filter(
        and_(models.CollectionsItems.collection_id == collection_id, models.CollectionsItems.media_id == media_id)
    )
    if not item_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manga absent de la liste")
    item_query.delete(synchronize_session=False)
    db.commit()
    return {"detail": "Manga retiré de la liste"}


@router.patch("/{from_id}/item/{media_id}")
def move_item_between_collections(db: db_dep, current_user: user_dep, from_id: int, media_id: str, move: CollectionItemMove):
    """Move a media's item from one of the caller's collections to another."""
    get_owned_collection(db, current_user.id, from_id)
    get_owned_collection(db, current_user.id, move.to_collection_id)
    source_query = db.query(models.CollectionsItems).filter(
        and_(models.CollectionsItems.collection_id == from_id, models.CollectionsItems.media_id == media_id)
    )
    source_row = source_query.first()
    if not source_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manga absent de la liste source")
    duplicate = (
        db.query(models.CollectionsItems)
        .filter(and_(models.CollectionsItems.collection_id == move.to_collection_id, models.CollectionsItems.media_id == media_id))
        .first()
    )
    if duplicate:  #* because this also covers from_id == to_id (the source row IS the duplicate)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce manga est déjà dans la liste cible")
    source_row.collection_id = move.to_collection_id
    db.commit()
    return {"detail": "Manga déplacé"}
```

- [ ] **Step 5: Run tests — verify pass**

Run: `pytest tests/ -v`
Expected: `29 passed`

- [ ] **Step 6: Commit**

```powershell
git add routers/collections.py tests/conftest.py tests/test_collection_items.py
git commit -m "feat(collections): owner-only item add/remove/move and media-joined items listing"
```

---

### Task 8: Status switch + membership endpoints

**Files:**
- Modify: `fastapi/routers/collections.py` (worktree — insert **directly after `get_my_collections`**, before any `/{collection_id}` route)
- Create: `fastapi/tests/test_collection_status.py` (worktree)

- [ ] **Step 1: Write the failing tests**

Create `fastapi/tests/test_collection_status.py`:

```python
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
```

- [ ] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_collection_status.py -v`
Expected: 6 FAIL — note the failures are 404/405, NOT 422; if you see routes half-matching, the new routes were declared after `/{collection_id}` — fix placement.

- [ ] **Step 3: Add the routes**

Insert into `fastapi/routers/collections.py` **directly after the `get_my_collections` function** (before `create_collection`):

```python
@router.get("/me/membership/{media_id}")
def get_media_membership(db: db_dep, current_user: user_dep, media_id: str):
    """Return the ids of the caller's collections containing the media."""
    rows = (
        db.query(models.CollectionsItems.collection_id)
        .join(models.Collections, models.Collections.id == models.CollectionsItems.collection_id)
        .filter(and_(models.Collections.user_id == current_user.id, models.CollectionsItems.media_id == media_id))
        .all()
    )
    return {"collection_ids": [row.collection_id for row in rows]}


@router.put("/me/status/{media_id}")
def set_media_status(db: db_dep, current_user: user_dep, media_id: str, status_update: CollectionStatusUpdate):
    """Place the media in one default collection, or clear its status with null."""
    ensure_default_collections(db, current_user.id)
    default_collections = (
        db.query(models.Collections)
        .filter(and_(models.Collections.user_id == current_user.id, models.Collections.is_default == True))
        .all()
    )
    default_ids = [collection.id for collection in default_collections]
    target_id = status_update.collection_id
    if target_id is not None and target_id not in default_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La cible doit être une de tes listes par défaut")
    other_default_ids = [collection_id for collection_id in default_ids if collection_id != target_id]
    db.query(models.CollectionsItems).filter(
        and_(models.CollectionsItems.media_id == media_id, models.CollectionsItems.collection_id.in_(other_default_ids))
    ).delete(synchronize_session=False)
    if target_id is not None:
        already_present = (
            db.query(models.CollectionsItems)
            .filter(and_(models.CollectionsItems.collection_id == target_id, models.CollectionsItems.media_id == media_id))
            .first()
        )
        if not already_present:
            db.add(models.CollectionsItems(collection_id=target_id, media_id=media_id))
    db.commit()
    return {"collection_id": target_id}
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/ -v`
Expected: `35 passed`

- [ ] **Step 5: Commit**

```powershell
git add routers/collections.py tests/test_collection_status.py
git commit -m "feat(collections): atomic status switch and membership endpoints"
```

---

### Task 9: Backend wrap-up — dev DB column, smoke test, push

**Files:** none (operations only, in the worktree)

- [ ] **Step 1: Full suite green**

Run: `pytest tests/ -v`
Expected: `35 passed`, zero failures.

- [ ] **Step 2: Add the column to the dev PostgreSQL database**

`create_all` does not add columns to existing tables (no Alembic in this project). From the worktree `fastapi/` directory (uses the dev `.env`):

```powershell
python -c "from sqlalchemy import text; from database import engine; connection = engine.connect(); connection.execute(text('ALTER TABLE collections ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE')); connection.commit(); connection.close(); print('column added')"
```

Expected: `column added`.

- [ ] **Step 3: Boot the server and smoke-test manually**

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi
uvicorn main:app --reload
```

In a second terminal:

```powershell
$registration = Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/register -ContentType "application/json" -Body '{"email":"smoke@test.fr","password":"Test1234!","pseudo":"smoketest"}'
Invoke-RestMethod -Uri http://localhost:8000/collections/me -Headers @{ Authorization = "Bearer $($registration.access_token)" }
```

Expected: a JSON array of the three default lists. (409 on register means the smoke user already exists — log in via `/auth/login` with the same body minus `pseudo` instead.)

- [ ] **Step 4: Push the branch**

`origin/fastapi` is an ancestor of `main`, so this is a fast-forward plus the new commits:

```powershell
git push -u origin fastapi
```

---

### Task 10: Frontend API client — `src/api/collections.ts`

**Files:**
- Create: `react/src/api/collections.ts` (main tree, branch `Antoine`)

- [ ] **Step 1: Create the module**

Create `react/src/api/collections.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE

export interface Collection {
  id: number
  name: string
  is_default: boolean
  is_public: boolean
  item_count: number
  poster_url: string | null
}

export interface CollectionItem {
  media_id: string
  title: string
  cover_url: string | null
}

export interface CollectionDetail {
  collection: Collection
  items: CollectionItem[]
}

/** Build the auth headers, failing fast when no token is stored. */
function buildAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('token')
  if (!token) throw new Error('Connecte-toi pour utiliser ta bibliothèque')
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
}

/** Run an authenticated request and return the parsed JSON body. */
async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers: buildAuthHeaders() })
  if (response.status === 401) {
    localStorage.removeItem('token')  //* because a 401 means the token is stale; 403 is a permission error and must NOT log the user out
    throw new Error('Connecte-toi pour utiliser ta bibliothèque')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail ?? 'Une erreur est survenue')
  }
  return response.json() as Promise<T>
}

/** Fetch the caller's collections, defaults first. */
export function fetchMyCollections(): Promise<Collection[]> {
  return requestJson<Collection[]>('/collections/me')
}

/** Fetch one collection with its items. */
export function fetchCollectionItems(collectionId: number): Promise<CollectionDetail> {
  return requestJson<CollectionDetail>(`/collections/${collectionId}/items`)
}

/** Create a custom collection. */
export function createCollection(name: string, isPublic: boolean): Promise<Collection> {
  return requestJson<Collection>('/collections', { method: 'POST', body: JSON.stringify({ name, is_public: isPublic }) })
}

/** Rename a custom collection. */
export function renameCollection(collectionId: number, name: string): Promise<Collection> {
  return requestJson<Collection>(`/collections/${collectionId}`, { method: 'PATCH', body: JSON.stringify({ name }) })
}

/** Toggle a collection's public visibility. */
export function setVisibility(collectionId: number, isPublic: boolean): Promise<Collection> {
  return requestJson<Collection>(`/collections/${collectionId}`, { method: 'PATCH', body: JSON.stringify({ is_public: isPublic }) })
}

/** Delete a custom collection and its items. */
export function deleteCollection(collectionId: number): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(`/collections/${collectionId}`, { method: 'DELETE' })
}

/** Add a media to a collection. */
export function addItem(collectionId: number, mediaId: string): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(`/collections/${collectionId}/item/${mediaId}`, { method: 'POST' })
}

/** Remove a media from a collection. */
export function removeItem(collectionId: number, mediaId: string): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(`/collections/${collectionId}/item/${mediaId}`, { method: 'DELETE' })
}

/** Set the media's reading status (null clears it). */
export function setMediaStatus(mediaId: string, collectionId: number | null): Promise<{ collection_id: number | null }> {
  return requestJson<{ collection_id: number | null }>(`/collections/me/status/${mediaId}`, { method: 'PUT', body: JSON.stringify({ collection_id: collectionId }) })
}

/** Fetch the ids of the caller's collections containing the media. */
export function fetchMembership(mediaId: string): Promise<{ collection_ids: number[] }> {
  return requestJson<{ collection_ids: number[] }>(`/collections/me/membership/${mediaId}`)
}
```

- [ ] **Step 2: Typecheck**

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ\react
npm run build
```

Expected: build succeeds (unused-export warnings are fine at this stage).

- [ ] **Step 3: Commit**

```powershell
git add src/api/collections.ts
git commit -m "feat(front): typed collections API client"
```

---

### Task 11: Extract `MangaDetailModal` from `Recherche.tsx`

**Files:**
- Create: `react/src/MangaDetailModal.tsx`
- Modify: `react/src/Recherche.tsx`

- [ ] **Step 1: Create `react/src/MangaDetailModal.tsx`**

This is the modal code moved out of `Recherche.tsx`, with `selectedMangaId` replaced by the `mangaId` prop and close handled by the parent:

```tsx
import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE

interface MangaDetailModalProps {
  mangaId: string
  onClose: () => void
}

export default function MangaDetailModal({ mangaId, onClose }: MangaDetailModalProps) {
  const [mangaDetail, setMangaDetail] = useState<any>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState("")

  const [userScore, setUserScore] = useState<number>(5)
  const [reviewTitle, setReviewTitle] = useState("")
  const [reviewContent, setReviewContent] = useState("")
  const [reviewSpoiler, setReviewSpoiler] = useState(false)
  const [submittingAction, setSubmittingAction] = useState(false)

  const loadMangaDetail = useCallback(async () => {
    setLoadingDetail(true)
    setDetailError("")
    setMangaDetail(null)

    const token = localStorage.getItem("token")
    const headers: any = {}
    if (token) headers["Authorization"] = `Bearer ${token}`

    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}`, { headers })
      if (!res.ok) throw new Error("Impossible de charger les détails du manga.")

      const data = await res.json()
      setMangaDetail(data)

      if (data.media?.user_rating) {
        setUserScore(data.media.user_rating)
      }
    } catch (err: any) {
      setDetailError(err.message || "Erreur de chargement.")
    } finally {
      setLoadingDetail(false)
    }
  }, [mangaId])

  useEffect(() => {
    loadMangaDetail()
  }, [loadMangaDetail])

  const handleRate = async () => {
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour noter !")

    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}/rating`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ score: userScore })
      })
      if (res.ok) {
        alert("Note enregistrée ! ⭐")
        loadMangaDetail()
      } else {
        alert("Erreur lors de l'enregistrement de la note.")
      }
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingAction(false)
    }
  }

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour écrire une critique !")

    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}/reviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          title: reviewTitle,
          content: reviewContent,
          spoiler_flag: reviewSpoiler
        })
      })
      if (res.ok) {
        alert("Critique publiée !")
        setReviewTitle("")
        setReviewContent("")
        loadMangaDetail()
      } else {
        alert("Erreur lors de la publication.")
      }
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingAction(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="search-component-container modal-content-box">

        <button onClick={onClose} className="modal-close-btn">✕</button>

        {loadingDetail && <div className="status-message-centered">⏳ Chargement de la fiche...</div>}
        {detailError && <div className="status-message-centered">⚠️ {detailError}</div>}

        {mangaDetail && mangaDetail.media && !loadingDetail && (
          <div>
            <div className="modal-media-header">
              <img src={mangaDetail.media.cover_url || "https://via.placeholder.com/120x180?text=No+Cover"} alt="" className="modal-media-cover" />
              <div>
                <h2 className="modal-media-title">{mangaDetail.media.title}</h2>
                <p className="modal-media-status">Statut : {mangaDetail.media.status || "Inconnu"}</p>
                <p className="modal-media-description">{mangaDetail.media.description || "Pas de description disponible."}</p>

                <h3 className="modal-community-rating">
                  ⭐ Note : {mangaDetail.community_rating?.average ? `${mangaDetail.community_rating.average.toFixed(1)}/5 (${mangaDetail.community_rating.count || 0} avis)` : "Pas encore noté"}
                </h3>
              </div>
            </div>

            {localStorage.getItem("token") && (
              <div className="modal-action-block">
                <h4 className="modal-action-title">Attribuer une note :</h4>
                <select disabled={submittingAction} value={userScore} onChange={(e) => setUserScore(parseFloat(e.target.value))} className="rating-select-dropdown">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map(v => <option key={v} value={v}>{v} ⭐</option>)}
                </select>
                <button onClick={handleRate} disabled={submittingAction} className="btn-action-submit">
                  {submittingAction ? "Envoi..." : "Noter"}
                </button>
              </div>
            )}

            <h3 className="reviews-section-title">Critiques de la communauté</h3>
            <div className="reviews-scroll-container">
              {!mangaDetail.reviews || mangaDetail.reviews.length === 0 ? (
                <p>Aucun avis pour le moment.</p>
              ) : (
                mangaDetail.reviews.map((rev: any) => (
                  <div key={rev.id} className="review-item-card">
                    <strong className="review-title-text">{rev.title}</strong>
                    <span className="review-item-author"> par {rev.author?.username || "Anonyme"}</span>
                    {(rev.contains_spoiler || rev.spoiler_tag || rev.spoiler_flag) && <span className="review-item-spoiler-tag">⚠️ SPOILER</span>}
                    <p className="review-item-body">{rev.content || rev.body}</p>
                  </div>
                ))
              )}
            </div>

            {localStorage.getItem("token") && (
              <form onSubmit={handleReviewSubmit} className="review-creation-form">
                <h4 className="modal-action-title">Rédiger une critique</h4>
                <input type="text" placeholder="Titre de votre critique" value={reviewTitle} onChange={(e) => setReviewTitle(e.target.value)} required disabled={submittingAction} className="review-form-input" />
                <textarea placeholder="Donnez votre avis détaillé..." value={reviewContent} onChange={(e) => setReviewContent(e.target.value)} required disabled={submittingAction} className="review-form-textarea" />
                <label className="review-form-checkbox-label">
                  <input type="checkbox" checked={reviewSpoiler} onChange={(e) => setReviewSpoiler(e.target.checked)} disabled={submittingAction} /> Signaler comme spoiler
                </label>
                <button type="submit" disabled={submittingAction} className="btn-review-publish">
                  {submittingAction ? "Publication..." : "Publier"}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
```

Note: the modal still uses the CSS classes from `Recherche.css`, which is imported by `Recherche.tsx` and therefore global — no CSS move needed.

- [ ] **Step 2: Slim down `react/src/Recherche.tsx`**

Replace the whole file with:

```tsx
import { useState, useEffect, useRef, useCallback } from 'react'
import MangaDetailModal from './MangaDetailModal'
import './Recherche.css'

const API_BASE = import.meta.env.VITE_API_BASE

export default function Recherche() {
  const [mangas, setMangas] = useState<any[]>([])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const [genres, setGenres] = useState<any[]>([])
  const [selectedGenre, setSelectedGenre] = useState("")
  const [showFilters, setShowFilters] = useState(false)

  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  const [selectedMangaId, setSelectedMangaId] = useState<string | null>(null)

  const observer = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/media/tags`)
      .then(res => {
        if (!res.ok) throw new Error("Impossible de récupérer les filtres.")
        return res.json()
      })
      .then(data => {
        if (data.genres) setGenres(data.genres)
      })
      .catch(err => console.error("Erreur tags:", err))
  }, [])

  useEffect(() => {
    setMangas([])
    setPage(1)
    setHasMore(true)
  }, [query, selectedGenre])


  useEffect(() => {
    executeSearch(page)
  }, [page, query, selectedGenre])

  const executeSearch = async (pageNumber: number) => {
    if (loading || (!hasMore && pageNumber > 1)) return

    setLoading(true)
    setError("")

    try {
      const params = new URLSearchParams()
      if (query.trim() !== "") params.append("title", query)
      if (selectedGenre !== "") params.append("genre", selectedGenre)


       params.append("limit", "20")
       params.append("offset", ((pageNumber - 1) * 20).toString())

      const response = await fetch(`${API_BASE}/media/search?${params.toString()}`)
      if (!response.ok) throw new Error("Erreur serveur lors de la recherche.")

      const data = await response.json()
      const results = data.results || data || []

      if (results.length === 0) {
        setHasMore(false)
      }

      setMangas(prev => pageNumber === 1 ? results : [...prev, ...results])

    } catch (err: any) {
      setError(err.message || "Une erreur est survenue lors de la recherche.")
    } finally {
      setLoading(false)
    }
  }

  const lastMangaElementRef = useCallback((node: HTMLDivElement) => {
    if (loading) return
    if (observer.current) observer.current.disconnect()

    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prevPage => prevPage + 1)
      }
    })

    if (node) observer.current.observe(node)
  }, [loading, hasMore])

  return (
    <div className="search-wrapper-container">

      <div className="search-component-container">
        <form onSubmit={(e) => { e.preventDefault(); setPage(1); executeSearch(1); }}>
          <input
            type="text"
            className="search-input-field"
            placeholder="Rechercher un manga..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn-filters-trigger btn-search-submit">Rechercher</button>
          <button type="button" className="btn-filters-trigger btn-filters-toggle" onClick={() => setShowFilters(!showFilters)}>
            {showFilters ? "🔹 Masquer Filtres" : "🔸 Filtrer par Genre"}
          </button>
        </form>
      </div>

      {showFilters && (
        <div className="search-component-container filters-section">
          <h4 className="filters-title">Genres :</h4>
          <div className="tags-list-container tags-list-container-genres">
            <span
              onClick={() => setSelectedGenre("")}
              className={`tag-item ${selectedGenre === "" ? "active" : ""}`}
            >
              Tous
            </span>
            {genres.map(g => (
              <span
                key={g.id}
                onClick={() => setSelectedGenre(g.id)}
                className={`tag-item ${selectedGenre === g.id ? "active" : ""}`}
              >
                {g.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="manga-results-grid">
        {mangas.map((manga: any, index: number) => {
          const currentCover = manga.coverUrl || manga.cover_url || "https://via.placeholder.com/200x300?text=No+Cover"

          const isLastElement = mangas.length === index + 1

          return (
            <div
              key={`${manga.id}-${index}`}
              ref={isLastElement ? lastMangaElementRef : null}
              className="search-component-container manga-card-clickable"
              onClick={() => setSelectedMangaId(manga.id)}
            >
              <img src={currentCover} alt={manga.title} className="manga-card-cover" />
              <h3 className="manga-card-title">{manga.title}</h3>
            </div>
          )
        })}
      </div>

      {loading && <div className="status-message-centered">🔄 Chargement des mangas...</div>}
      {error && <div className="status-message-centered">⚠️ {error}</div>}
      {!hasMore && mangas.length > 0 && <div className="status-message-centered" style={{opacity: 0.5}}>Fin de la collection. ✨</div>}

      {selectedMangaId && (
        <MangaDetailModal mangaId={selectedMangaId} onClose={() => setSelectedMangaId(null)} />
      )}
    </div>
  )
}
```

- [ ] **Step 3: Build + manual check**

```powershell
npm run build
npm run dev
```

Ensure `react/.env` contains `VITE_API_BASE=http://localhost:8000` and the backend (worktree) is running. In the browser: search a manga, open its card — the modal shows details, rating still saves, review still publishes, ✕ closes.

- [ ] **Step 4: Commit**

```powershell
git add src/MangaDetailModal.tsx src/Recherche.tsx
git commit -m "refactor(front): extract MangaDetailModal from Recherche"
```

---

### Task 12: `LibraryActions` quick-add block

**Files:**
- Create: `react/src/LibraryActions.tsx`
- Modify: `react/src/MangaDetailModal.tsx` (import + one JSX line)
- Modify: `react/src/Recherche.css` (new classes)

- [ ] **Step 1: Create `react/src/LibraryActions.tsx`**

```tsx
import { useState, useEffect, useCallback } from 'react'
import type { Collection } from './api/collections'
import { fetchMyCollections, fetchMembership, setMediaStatus, addItem, removeItem } from './api/collections'

interface LibraryActionsProps {
  mediaId: string
}

export default function LibraryActions({ mediaId }: LibraryActionsProps) {
  const [collections, setCollections] = useState<Collection[]>([])
  const [memberIds, setMemberIds] = useState<number[]>([])
  const [isBusy, setIsBusy] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  const refreshLibraryState = useCallback(async () => {
    try {
      const [myCollections, membership] = await Promise.all([fetchMyCollections(), fetchMembership(mediaId)])
      setCollections(myCollections)
      setMemberIds(membership.collection_ids)
    } catch (err: any) {
      setErrorMessage(err.message)
    }
  }, [mediaId])

  useEffect(() => {
    refreshLibraryState()
  }, [refreshLibraryState])

  const defaultCollections = collections.filter((collection) => collection.is_default)
  const customCollections = collections.filter((collection) => !collection.is_default)
  const activeStatusId = defaultCollections.find((collection) => memberIds.includes(collection.id))?.id ?? null

  const handleStatusClick = async (collectionId: number) => {
    setIsBusy(true)
    setErrorMessage("")
    try {
      await setMediaStatus(mediaId, collectionId === activeStatusId ? null : collectionId)
      await refreshLibraryState()
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsBusy(false)
    }
  }

  const handleCustomToggle = async (collectionId: number) => {
    setIsBusy(true)
    setErrorMessage("")
    try {
      if (memberIds.includes(collectionId)) {
        await removeItem(collectionId, mediaId)
      } else {
        await addItem(collectionId, mediaId)
      }
      await refreshLibraryState()
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="modal-action-block">
      <h4 className="modal-action-title">Ma bibliothèque :</h4>
      <div className="status-buttons-row">
        {defaultCollections.map((collection) => (
          <button
            key={collection.id}
            disabled={isBusy}
            className={`btn-status-segment ${collection.id === activeStatusId ? 'active' : ''}`}
            onClick={() => handleStatusClick(collection.id)}
          >
            {collection.name}
          </button>
        ))}
      </div>

      {customCollections.length > 0 && (
        <div className="custom-lists-block">
          <h4 className="modal-action-title">Listes personnalisées :</h4>
          {customCollections.map((collection) => (
            <label key={collection.id} className="custom-list-checkbox">
              <input
                type="checkbox"
                disabled={isBusy}
                checked={memberIds.includes(collection.id)}
                onChange={() => handleCustomToggle(collection.id)}
              />
              {collection.name}
            </label>
          ))}
        </div>
      )}

      {errorMessage && <div className="library-error-message">⚠️ {errorMessage}</div>}
    </div>
  )
}
```

- [ ] **Step 2: Mount it in the modal**

In `react/src/MangaDetailModal.tsx`:

Add the import:

```tsx
import LibraryActions from './LibraryActions'
```

Insert directly after the rating `</div>` (the `modal-action-block` that contains the "Noter" button) and before `<h3 className="reviews-section-title">`:

```tsx
            {localStorage.getItem("token") && (
              <LibraryActions mediaId={mangaId} />
            )}
```

- [ ] **Step 3: Add the CSS**

Append to `react/src/Recherche.css`:

```css
.status-buttons-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-status-segment {
  padding: 8px 14px;
  border-radius: 20px;
  border: 1px solid var(--text-muted);
  background: var(--bg-inner);
  color: var(--text-main);
  cursor: pointer;
}

.btn-status-segment.active {
  border-color: var(--accent-color);
  color: var(--accent-color);
  font-weight: bold;
}

.btn-status-segment:disabled {
  opacity: 0.5;
  cursor: wait;
}

.custom-lists-block {
  margin-top: 12px;
}

.custom-list-checkbox {
  display: block;
  margin: 6px 0;
  cursor: pointer;
  color: var(--text-sub);
}

.library-error-message {
  color: #ff4757;
  font-size: 0.85rem;
  margin-top: 8px;
}
```

- [ ] **Step 4: Build + manual check**

```powershell
npm run build
npm run dev
```

With the worktree backend running, logged in, open a manga detail: the three status buttons appear; clicking "En cours" highlights it; clicking "Terminé" moves the highlight (exclusive); clicking the active one clears it; custom lists (create one via Bruno or wait for Task 13) toggle independently.

- [ ] **Step 5: Commit**

```powershell
git add src/LibraryActions.tsx src/MangaDetailModal.tsx src/Recherche.css
git commit -m "feat(front): quick-add status buttons and custom-list toggles in manga modal"
```

---

### Task 13: Bibliothèque tab — dashboard, list detail, App wiring

**Files:**
- Create: `react/src/Bibliotheque.tsx`
- Create: `react/src/ListeDetail.tsx`
- Create: `react/src/Bibliotheque.css`
- Modify: `react/src/App.tsx`

- [ ] **Step 1: Create `react/src/ListeDetail.tsx`**

```tsx
import { useState, useEffect, useCallback } from 'react'
import type { CollectionDetail } from './api/collections'
import { fetchCollectionItems, removeItem } from './api/collections'

interface ListeDetailProps {
  collectionId: number
  onBack: () => void
  onOpenManga: (mediaId: string) => void
}

export default function ListeDetail({ collectionId, onBack, onOpenManga }: ListeDetailProps) {
  const [detail, setDetail] = useState<CollectionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [isBusy, setIsBusy] = useState(false)

  const refreshItems = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")
    try {
      setDetail(await fetchCollectionItems(collectionId))
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [collectionId])

  useEffect(() => {
    refreshItems()
  }, [refreshItems])

  const handleRemoveItem = async (mediaId: string) => {
    setIsBusy(true)
    try {
      await removeItem(collectionId, mediaId)
      await refreshItems()
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="search-wrapper-container">
      <div className="search-back-row">
        <h3 style={{ margin: 0 }}>{detail ? detail.collection.name : "Chargement..."}</h3>
        <span onClick={onBack} style={{ cursor: 'pointer' }}>← Retour à la bibliothèque</span>
      </div>

      {isLoading && <div className="status-message-centered">🔄 Chargement...</div>}
      {errorMessage && <div className="status-message-centered">⚠️ {errorMessage}</div>}
      {detail && detail.items.length === 0 && !isLoading && (
        <div className="status-message-centered">Cette liste est vide pour le moment.</div>
      )}

      <div className="manga-results-grid">
        {detail?.items.map((item) => (
          <div key={item.media_id} className="search-component-container manga-card-clickable">
            <img
              src={item.cover_url || "https://via.placeholder.com/200x300?text=No+Cover"}
              alt={item.title}
              className="manga-card-cover"
              onClick={() => onOpenManga(item.media_id)}
            />
            <h3 className="manga-card-title" onClick={() => onOpenManga(item.media_id)}>{item.title}</h3>
            <button
              className="btn-filters-trigger btn-retirer"
              disabled={isBusy}
              onClick={() => handleRemoveItem(item.media_id)}
            >
              Retirer
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create `react/src/Bibliotheque.tsx`**

```tsx
import { useState, useEffect, useCallback } from 'react'
import type { Collection } from './api/collections'
import { fetchMyCollections, createCollection, renameCollection, deleteCollection } from './api/collections'
import ListeDetail from './ListeDetail'
import MangaDetailModal from './MangaDetailModal'
import './Bibliotheque.css'

interface BibliothequeProps {
  onGoToLogin: () => void
}

interface ListeCardProps {
  collection: Collection
  onOpen: () => void
  onRename: () => void
  onDelete: () => void
}

function ListeCard({ collection, onOpen, onRename, onDelete }: ListeCardProps) {
  return (
    <div className="search-component-container liste-card" onClick={onOpen}>
      <img
        src={collection.poster_url || "https://via.placeholder.com/200x300?text=Liste"}
        alt={collection.name}
        className="liste-card-poster"
      />
      <h3 className="liste-card-name">{collection.name}</h3>
      <p className="liste-card-count">
        {collection.item_count} manga{collection.item_count > 1 ? "s" : ""}
        {!collection.is_default && (collection.is_public ? " · 🌐 publique" : " · 🔒 privée")}
      </p>
      {!collection.is_default && (
        <div className="liste-card-actions">
          <button className="btn-liste-action" onClick={(event) => { event.stopPropagation(); onRename(); }}>✏️</button>
          <button className="btn-liste-action" onClick={(event) => { event.stopPropagation(); onDelete(); }}>🗑️</button>
        </div>
      )}
    </div>
  )
}

export default function Bibliotheque({ onGoToLogin }: BibliothequeProps) {
  const isLoggedIn = Boolean(localStorage.getItem('token'))
  const [collections, setCollections] = useState<Collection[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null)
  const [selectedMangaId, setSelectedMangaId] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListName, setNewListName] = useState("")
  const [newListIsPublic, setNewListIsPublic] = useState(true)

  const refreshCollections = useCallback(async () => {
    if (!isLoggedIn) return
    setIsLoading(true)
    setErrorMessage("")
    try {
      setCollections(await fetchMyCollections())
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [isLoggedIn])

  useEffect(() => {
    refreshCollections()
  }, [refreshCollections])

  const handleCreateSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    try {
      await createCollection(newListName, newListIsPublic)
      setNewListName("")
      setNewListIsPublic(true)
      setShowCreateForm(false)
      refreshCollections()
    } catch (err: any) {
      setErrorMessage(err.message)
    }
  }

  const handleRename = async (collection: Collection) => {
    const newName = window.prompt("Nouveau nom :", collection.name)
    if (!newName || newName === collection.name) return
    try {
      await renameCollection(collection.id, newName)
      refreshCollections()
    } catch (err: any) {
      setErrorMessage(err.message)
    }
  }

  const handleDelete = async (collection: Collection) => {
    const isConfirmed = window.confirm(`Supprimer "${collection.name}" et tout son contenu ?`)
    if (!isConfirmed) return
    try {
      await deleteCollection(collection.id)
      refreshCollections()
    } catch (err: any) {
      setErrorMessage(err.message)
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="search-wrapper-container bibliotheque-login-prompt">
        <h2>Ma Bibliothèque</h2>
        <p>Connecte-toi pour gérer tes listes de lecture.</p>
        <button className="btn-filters-trigger" onClick={onGoToLogin}>Se connecter</button>
      </div>
    )
  }

  if (selectedCollection) {
    return (
      <>
        <ListeDetail
          collectionId={selectedCollection.id}
          onBack={() => { setSelectedCollection(null); refreshCollections(); }}
          onOpenManga={(mediaId) => setSelectedMangaId(mediaId)}
        />
        {selectedMangaId && (
          <MangaDetailModal mangaId={selectedMangaId} onClose={() => setSelectedMangaId(null)} />
        )}
      </>
    )
  }

  const defaultCollections = collections.filter((collection) => collection.is_default)
  const customCollections = collections.filter((collection) => !collection.is_default)

  return (
    <div className="search-wrapper-container">
      <div className="bibliotheque-header">
        <h2>Ma Bibliothèque</h2>
        <button className="btn-filters-trigger" onClick={() => setShowCreateForm(!showCreateForm)}>
          ➕ Nouvelle liste
        </button>
      </div>

      {showCreateForm && (
        <form className="search-component-container create-liste-form" onSubmit={handleCreateSubmit}>
          <input
            type="text"
            required
            className="search-input-field"
            placeholder="Nom de la liste"
            value={newListName}
            onChange={(event) => setNewListName(event.target.value)}
          />
          <label className="create-liste-public-label">
            <input
              type="checkbox"
              checked={newListIsPublic}
              onChange={(event) => setNewListIsPublic(event.target.checked)}
            />
            Liste publique
          </label>
          <button type="submit" className="btn-filters-trigger">Créer</button>
        </form>
      )}

      {errorMessage && <div className="status-message-centered">⚠️ {errorMessage}</div>}
      {isLoading && <div className="status-message-centered">🔄 Chargement...</div>}

      <h3 className="bibliotheque-section-title">Mes statuts</h3>
      <div className="manga-results-grid">
        {defaultCollections.map((collection) => (
          <ListeCard
            key={collection.id}
            collection={collection}
            onOpen={() => setSelectedCollection(collection)}
            onRename={() => handleRename(collection)}
            onDelete={() => handleDelete(collection)}
          />
        ))}
      </div>

      <h3 className="bibliotheque-section-title">Mes listes</h3>
      {customCollections.length === 0 && !isLoading && (
        <p className="status-message-centered">Aucune liste personnalisée pour le moment.</p>
      )}
      <div className="manga-results-grid">
        {customCollections.map((collection) => (
          <ListeCard
            key={collection.id}
            collection={collection}
            onOpen={() => setSelectedCollection(collection)}
            onRename={() => handleRename(collection)}
            onDelete={() => handleDelete(collection)}
          />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create `react/src/Bibliotheque.css`**

```css
.bibliotheque-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.bibliotheque-section-title {
  margin: 25px 0 10px;
  color: var(--text-main);
}

.bibliotheque-login-prompt {
  max-width: 500px;
  margin: 60px auto;
  text-align: center;
}

.create-liste-form {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  padding: 15px;
}

.create-liste-public-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-sub);
  cursor: pointer;
}

.liste-card {
  cursor: pointer;
  position: relative;
  text-align: center;
}

.liste-card-poster {
  width: 100%;
  height: 220px;
  object-fit: cover;
  border-radius: 8px;
}

.liste-card-name {
  margin: 10px 0 4px;
  color: var(--text-main);
}

.liste-card-count {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.liste-card-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 6px;
}

.btn-liste-action {
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  background: var(--bg-inner);
}

.btn-retirer {
  margin-top: 8px;
}
```

- [ ] **Step 4: Wire the tab in `react/src/App.tsx`**

Add the import:

```tsx
import Bibliotheque from './Bibliotheque'
```

Change the tab union:

```tsx
const [currentTab, setCurrentTab] = useState<'accueil' | 'recherche' | 'recherche-users' | 'profil' | 'bibliotheque'>('accueil')
```

Replace the dead nav link `<span className="nav-link muted">Bibliothèque</span>` with:

```tsx
            <span
              className={`nav-link ${currentTab === 'bibliotheque' ? 'active' : 'muted'}`}
              onClick={() => setCurrentTab('bibliotheque')}
            >
              Bibliothèque
            </span>
```

Add the tab rendering inside `<main>` (next to the other tabs):

```tsx
        {currentTab === 'bibliotheque' && (
          <Bibliotheque onGoToLogin={() => setCurrentTab('profil')} />
        )}
```

- [ ] **Step 5: Build + manual check**

```powershell
npm run build
npm run dev
```

In the browser, logged in, with the worktree backend running:
- "Bibliothèque" tab shows "Mes statuts" (3 default cards, no ✏️/🗑️) then "Mes listes".
- "➕ Nouvelle liste" creates a list; a duplicate name shows the 409 message.
- ✏️ renames a custom list; 🗑️ asks confirmation then deletes.
- Clicking a card opens the list detail; "Retirer" removes an item; clicking a cover opens the manga modal; the quick-add block works from there.
- Logged out, the tab shows the login prompt and the button jumps to the profile tab.

- [ ] **Step 6: Commit**

```powershell
git add src/Bibliotheque.tsx src/ListeDetail.tsx src/Bibliotheque.css src/App.tsx
git commit -m "feat(front): bibliotheque tab with dashboard, list detail and CRUD"
```

---

### Task 14: Final verification + push

**Files:** none (operations only)

- [ ] **Step 1: Lint and build**

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ\react
npm run lint
npm run build
```

Expected: build succeeds; lint reports no NEW errors versus the pre-existing baseline (the legacy files use `any` liberally — do not fix unrelated lint noise in this feature).

- [ ] **Step 2: Backend suite still green**

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ-fastapi\fastapi
pytest tests/ -v
```

Expected: `35 passed`.

- [ ] **Step 3: End-to-end walkthrough**

Backend running from the worktree, frontend `npm run dev`. With a freshly registered account:
1. Bibliothèque tab → the 3 defaults exist with 0 items.
2. Search a manga → open details → set "En cours" → Bibliothèque → "En cours" has 1 item, its poster is the manga's cover.
3. Back to the manga → click "Terminé" → "En cours" is empty again, "Terminé" has it (exclusivity).
4. Click "Terminé" again on the active button → status cleared everywhere.
5. Create a custom list, add the manga from the modal checklist, remove it from the list detail view.
6. Try deleting a default list → no button exists; (optional) `Invoke-RestMethod -Method Delete` on it → 403.

- [ ] **Step 4: Push the frontend branch**

```powershell
cd C:\Users\Karasu\Desktop\backup_hdd\DOSSIERS\dev\3PROJ
git push origin Antoine
```

- [ ] **Step 5: Clean up the worktree (optional, after merge)**

```powershell
git worktree remove ..\3PROJ-fastapi
```

Keep it as long as the backend branch is being iterated on.

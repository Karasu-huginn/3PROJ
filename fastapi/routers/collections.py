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
        .filter(and_(models.Collections.user_id == user_id, models.Collections.is_default.is_(True)))
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

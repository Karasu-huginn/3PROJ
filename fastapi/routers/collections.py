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

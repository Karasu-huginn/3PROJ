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

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[models.Users, Depends(get_current_user)]

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
def get_my_collections(db: db_dependency, current_user: user_dependency):
    """Return the caller's collections, defaults first, creating defaults if missing."""
    ensure_default_collections(db, current_user.id)
    collections = (
        db.query(models.Collections)
        .filter(models.Collections.user_id == current_user.id)
        .order_by(models.Collections.is_default.desc(), models.Collections.id.asc())
        .all()
    )
    return [serialize_collection(db, collection) for collection in collections]


@router.get("/me/membership/{media_id}")
def get_media_membership(db: db_dependency, current_user: user_dependency, media_id: str):
    """Return the ids of the caller's collections containing the media."""
    rows = (
        db.query(models.CollectionsItems.collection_id)
        .join(models.Collections, models.Collections.id == models.CollectionsItems.collection_id)
        .filter(and_(models.Collections.user_id == current_user.id, models.CollectionsItems.media_id == media_id))
        .all()
    )
    return {"collection_ids": [row.collection_id for row in rows]}


@router.put("/me/status/{media_id}")
def set_media_status(db: db_dependency, current_user: user_dependency, media_id: str, status_update: CollectionStatusUpdate):
    """Place the media in one default collection, or clear its status with null."""
    ensure_default_collections(db, current_user.id)
    default_collections = (
        db.query(models.Collections)
        .filter(and_(models.Collections.user_id == current_user.id, models.Collections.is_default.is_(True)))
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_collection(db: db_dependency, current_user: user_dependency, collection_create: CollectionCreate):
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
def update_collection(db: db_dependency, current_user: user_dependency, collection_id: int, collection_update: CollectionUpdate):
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
def remove_collection(db: db_dependency, current_user: user_dependency, collection_id: int):
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


@router.get("/{collection_id}/items")
def get_collection_items(db: db_dependency, current_user: user_dependency, collection_id: int):
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
def add_item_to_collection(db: db_dependency, current_user: user_dependency, collection_id: int, media_id: str):
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
def remove_item_from_collection(db: db_dependency, current_user: user_dependency, collection_id: int, media_id: str):
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
def move_item_between_collections(db: db_dependency, current_user: user_dependency, from_id: int, media_id: str, move: CollectionItemMove):
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

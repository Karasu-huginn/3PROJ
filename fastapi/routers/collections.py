from fastapi import APIRouter, Depends, HTTPException
from models import Collections, CollectionsItems, Users
from schemas import CollectionsBase, CollectionsItemsBase, CollectionItemMove
from sqlalchemy import and_
from sqlalchemy.orm import Session
from starlette import status
from database import get_db
from typing import Annotated

router = APIRouter(prefix="/collections", tags=["collections"])

db_dep = Annotated[Session, Depends(get_db)]

@router.get("")
def get_collections(db: db_dep):
    collections = db.query(Collections).all()
    return collections

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_collection(db: db_dep, collection_base:CollectionsBase):
    result = db.query(Collections).filter(and_(*[Users.id == collection_base.user_id, Collections.name == collection_base.name])).first()
    if result:
        return {"status":499, "details":"Resource already exists"}  #* because we don't want two collections having the same name
    
    create_collection_model = Collections(
        user_id = collection_base.user_id,
        poster_url = collection_base.poster_url,
        is_public = collection_base.is_public,
        name = collection_base.name
    )
    db.add(create_collection_model)
    db.commit()
    return {"status":201, "details":"Resource created"}

@router.patch("/{collection_id}", status_code=status.HTTP_200_OK)
def update_collection(db: db_dep, collection_id:int, name:str="", is_public:bool=None):
    result_query = db.query(Collections).filter([Collections.id == collection_id])
    if not result_query.first():
        return {"status":404, "details":"Not found"}
    update_dict = {
        "name": name if name else Collections.name,
        "is_public": is_public if is_public is not None else Collections.is_public
    }
    result_query.update(update_dict)
    db.commit()
    return {"status":200, "details":"Resource updated"}

@router.post("/{collection_id}/item/{media_id}", status_code=status.HTTP_201_CREATED)
def add_item_to_collection(db: db_dep, collection_id:int, media_id:str):
    result = db.query(CollectionsItems).filter(and_(CollectionsItems.media_id == media_id, CollectionsItems.collection_id == collection_id)).first()
    if result:
        return {"status":499, "details":"Resource already exists"}
    create_collection_item_model = CollectionsItems(
        collection_id = collection_id,
        media_id = media_id
    )
    db.add(create_collection_item_model)
    db.commit()
    return {"status":201, "details":"Resource created"}

@router.delete("/{collection_id}/item/{media_id}", status_code=status.HTTP_200_OK)
def rm_item_from_collection(db: db_dep, collection_id:int, media_id:str):
    result = db.query(CollectionsItems).filter(and_(CollectionsItems.media_id == media_id, CollectionsItems.collection_id == collection_id))
    if not result.first():
        return {"status":404, "details":"Not found"}
    result.delete()
    db.commit()
    return {"status":200, "details":"Resource deleted"}

@router.delete("/{collection_id}", status_code=status.HTTP_200_OK)
def rm_collection(db: db_dep, collection_id:int):
    result = db.query(Collections).filter(Collections.id == collection_id)
    if not result.first():
        return {"status":404, "details":"Not found"}
    result.delete()
    db.commit()
    return {"status":200, "details":"Resource deleted"}

@router.patch("/{from_id}/item/{media_id}", status_code=status.HTTP_200_OK)
def move_item_between_collections(db: db_dep, from_id:int, media_id:str, move:CollectionItemMove):
    """Move a media's item from one collection to another, returning a body-status response."""
    if not db.query(Collections).filter(Collections.id == move.to_collection_id).first():
        return {"status":404, "details":"Not found"}

    source_query = db.query(CollectionsItems).filter(and_(CollectionsItems.collection_id == from_id, CollectionsItems.media_id == media_id))
    source_row = source_query.first()
    if not source_row:
        return {"status":404, "details":"Not found"}

    duplicate = db.query(CollectionsItems).filter(and_(CollectionsItems.collection_id == move.to_collection_id, CollectionsItems.media_id == media_id)).first()
    if duplicate:                                              #* because this also covers from_id == to_id (source row IS the duplicate)
        return {"status":499, "details":"Resource already exists"}

    source_row.collection_id = move.to_collection_id
    db.commit()
    return {"status":200, "details":"Resource updated"}

from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    username:str
    email:str

class UserResponse(BaseModel):
    id : int
    username: str
    email: str

    class Config:
        from_attributes = True

class CollectionsBase(BaseModel):
    user_id : int
    poster_url : str
    is_public : bool
    name : str

class CollectionsItemsBase(BaseModel):
    collection_id : int
    media_id : str

class CollectionItemMove(BaseModel):
    to_collection_id : int

class CollectionCreate(BaseModel):
    name : str
    is_public : bool = True

class CollectionUpdate(BaseModel):
    name : Optional[str] = None
    is_public : Optional[bool] = None

class CollectionStatusUpdate(BaseModel):
    collection_id : Optional[int] = None
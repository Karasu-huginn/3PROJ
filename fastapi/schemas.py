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
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AuthorBrief(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class FollowOut(BaseModel):
    following: bool
    follower_count: int
    following_count: int

class UserPublicProfile(BaseModel):
    id: int
    pseudo: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    follower_count: int
    following_count: int
    is_followed_by_viewer: bool

    class Config:
        from_attributes = True

class FollowerItem(BaseModel):
    id: int
    pseudo: str
    avatar_url: Optional[str] = None
    is_followed_by_viewer: bool

    class Config:
        from_attributes = True

class ActivityOut(BaseModel):
    id: int
    actor: AuthorBrief
    activity_type: str          
    media_id: Optional[str] = None
    media_title: Optional[str] = None
    media_cover: Optional[str] = None
    review_id: Optional[int] = None
    review_title: Optional[str] = None
    rating_score: Optional[float] = None
    target_user_id: Optional[int] = None
    target_pseudo: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeedResponse(BaseModel):
    activities: list[ActivityOut]
    total: int
    offset: int
    limit: int

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    sender: AuthorBrief
    content: str
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConversationItem(BaseModel):
    other_user: AuthorBrief
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int

    class Config:
        from_attributes = True
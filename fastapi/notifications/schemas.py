from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ActorBrief(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class NotificationOut(BaseModel):
    id: int
    type: str
    actor: Optional[ActorBrief]
    review_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationsResponse(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int
    total: int
    offset: int
    limit: int
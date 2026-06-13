from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class MediaAuthor(BaseModel):
    name: str

class MediaBrief(BaseModel):
    id: str
    title: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    genres: list[str] = []
    average_rating: Optional[float] = None
    rating_count: int = 0


class MediaDetail(MediaBrief):
    title_fr: Optional[str] = None
    title_en: Optional[str] = None
    title_original: str
    description: Optional[str] = None
    author_names: list[str] = []
    content_rating: Optional[str] = None
    cached_at: Optional[datetime] = None
    user_rating: Optional[float] = None
    user_review_id: Optional[int] = None


class RatingCreate(BaseModel):
    score: float = Field(..., ge=0.5, le=5.0, description="Note de 0.5 à 5.0 par pas de 0.5")
    @field_validator("score")
    @classmethod
    def validate_half_step(cls, v: float) -> float:
        if round(v * 2) != v * 2:
            raise ValueError("La note doit être un multiple de 0.5")
        return v


class RatingOut(BaseModel):
    media_id: str
    user_id: int
    score: float
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommunityRating(BaseModel):
    media_id: str
    average: Optional[float] = None
    count: int = 0
    distribution: dict[str, int] = {}

class ReviewCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=256)
    content: str = Field(..., min_length=10)
    spoiler_flag: bool = False

class ReviewUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    spoiler_flag: Optional[bool] = None

class ReviewAuthor(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewOut(BaseModel):
    id: int
    media_id: str
    title: str
    body: Optional[str] = ""                 
    contains_spoiler: bool = False           
    is_featured: bool = False
    is_flagged: bool = False
    like_count: int = 0
    comment_count: int = 0
    author: ReviewAuthor
    created_at: datetime
    updated_at: Optional[datetime] = None
    viewer_has_liked: bool = False

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True


class ReviewFlagCreate(BaseModel):
    reason: str = Field(..., min_length=5, max_length=512,
                        description="Raison du signalement (spoiler non marqué, insulte, etc.)")

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    review_id: int
    content: str
    author: ReviewAuthor
    created_at: datetime

    class Config:
        from_attributes = True

class MediaPageResponse(BaseModel):
    media: MediaDetail
    community_rating: CommunityRating
    reviews: list[ReviewOut]
    reviews_total: int
    featured_review: Optional[ReviewOut] = None

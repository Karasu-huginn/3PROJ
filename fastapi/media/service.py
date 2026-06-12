from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, select
from fastapi import HTTPException, status

from models import Media, Rating, Reviews, Likes, Comments
from media.schemas import (
    RatingCreate, ReviewCreate, ReviewUpdate,
    CommunityRating, ReviewFlagCreate,
)
from media import mangadex as mdx
from models import Activity

logger = logging.getLogger(__name__)

async def get_or_fetch_media(media_id: str, db: Session) -> Media:
    cached: Optional[Media] = db.get(Media, media_id)
    needs_refresh = (
        cached is None
        or cached.cached_at is None
        or (datetime.now(timezone.utc) - cached.cached_at.replace(tzinfo=timezone.utc)).total_seconds() > 86400
    )

    if needs_refresh:
        data = await mdx.fetch_manga_detail(media_id)
        if data is None:
            if cached:
                return cached
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manga '{media_id}' introuvable sur MangaDex."
            )

        if cached is None:
            cached = Media(**data)
            db.add(cached)
        else:
            for key, value in data.items():
                setattr(cached, key, value)
            cached.cached_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(cached)

    return cached

def _parse_json_field(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []

def media_to_detail(manga: Media, user_id: int | None, db: Session) -> dict:
    user_rating = None
    user_review_id = None

    if user_id:
        rating_row = db.execute(
            select(Rating).where(Rating.media_id == manga.id, Rating.user_id == user_id)
        ).scalar_one_or_none()
        if rating_row:
            user_rating = rating_row.score

        review_row = db.execute(
            select(Reviews.id).where(Reviews.media_id == manga.id, Reviews.user_id == user_id)
        ).scalar_one_or_none()
        if review_row:
            user_review_id = review_row

    return {
        "id": manga.id,
        "title": manga.title_fr or manga.title_en or manga.title_original,
        "title_fr": manga.title_fr,
        "title_en": manga.title_en,
        "title_original": manga.title_original,
        "description": manga.description,
        "cover_url": manga.cover_url,
        "author_names": _parse_json_field(manga.author_names),
        "genres": _parse_json_field(manga.genres),
        "status": manga.status,
        "year": manga.year,
        "content_rating": manga.content_rating,
        "cached_at": manga.cached_at,
        "average_rating": manga.average_rating,
        "rating_count": manga.rating_count,
        "user_rating": user_rating,
        "user_review_id": user_review_id,
    }

async def upsert_rating(media_id: str, user_id: int, payload: RatingCreate, db: Session) -> Rating:
    await get_or_fetch_media(media_id, db)
    existing = db.execute(
        select(Rating).where(Rating.media_id == media_id, Rating.user_id == user_id)
    ).scalar_one_or_none()

    if existing:
        existing.score = payload.score
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    rating = Rating(media_id=media_id, user_id=user_id, score=payload.score)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.media_id == media_id,
        Activity.activity_type == "rating",
    ).delete()

    db.add(Activity(
        user_id=user_id,
        activity_type="rating",
        media_id=media_id,
        rating_score=payload.score,
    ))
    db.commit()
    return rating


async def delete_rating(media_id: str, user_id: int, db: Session) -> None:
    rating = db.execute(
        select(Rating).where(Rating.media_id == media_id, Rating.user_id == user_id)
    ).scalar_one_or_none()

    if not rating:
        raise HTTPException(status_code=404, detail="Aucune note à supprimer.")

    db.delete(rating)
    db.commit()

def get_community_rating(media_id: str, db: Session) -> CommunityRating:
    rows = db.execute(
        select(Rating.score).where(Rating.media_id == media_id)
    ).scalars().all()

    if not rows:
        return CommunityRating(media_id=media_id, average=None, count=0, distribution={})

    total = sum(rows)
    count = len(rows)
    average = round(total / count, 2)
    distribution: dict[str, int] = {}
    for score in rows:
        key = str(score)
        distribution[key] = distribution.get(key, 0) + 1

    return CommunityRating(
        media_id=media_id,
        average=average,
        count=count,
        distribution=distribution,
    )

async def create_review(media_id: str, user_id: int, payload: ReviewCreate, db: Session) -> Reviews:
    await get_or_fetch_media(media_id, db)
    existing = db.execute(
        select(Reviews).where(Reviews.media_id == media_id, Reviews.user_id == user_id)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vous avez déjà rédigé une critique pour ce manga. Utilisez PUT pour la modifier."
        )

    review = Reviews(
        media_id=media_id,
        user_id=user_id,
        title=payload.title,
        content=payload.content,
        spoiler_flag=payload.spoiler_flag,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    db.add(Activity(
        user_id=user_id,
        activity_type="review",
        media_id=media_id,
        review_id=review.id,
    ))
    db.commit()
    return review

def update_review(review_id: int, user_id: int, payload: ReviewUpdate, db: Session) -> Reviews:
    review = db.get(Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="Action non autorisée.")

    if payload.title is not None:
        review.title = payload.title
    if payload.content is not None:
        review.content = payload.content
    if payload.spoiler_flag is not None:
        review.spoiler_flag = payload.spoiler_flag

    review.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return review

def delete_review(review_id: int, user_id: int, is_admin: bool, db: Session) -> None:
    review = db.get(Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    if not is_admin and review.user_id != user_id:
        raise HTTPException(status_code=403, detail="Action non autorisée.")

    db.delete(review)
    db.commit()

def flag_review(review_id: int, user_id: int, payload: ReviewFlagCreate, db: Session) -> Reviews:
    review = db.get(Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    if review.user_id == user_id:
        raise HTTPException(status_code=400, detail="Impossible de signaler sa propre critique.")

    review.is_flagged = True
    review.flag_reason = payload.reason
    db.commit()
    db.refresh(review)
    return review

def feature_review(review_id: int, db: Session) -> Reviews:
    review = db.get(Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    review.is_featured = True
    db.commit()
    db.refresh(review)
    return review

def get_reviews_for_media(
    media_id: str,
    viewer_id: int | None,
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort: str = "recent", 
) -> tuple[list[dict], int]:
    q = select(Reviews).where(Reviews.media_id == media_id)

    if sort == "featured":
        q = q.where(Reviews.is_featured == True)
    elif sort == "top":
        like_count_sub = (
            select(Likes.review_id, func.count(Likes.id).label("lc"))
            .group_by(Likes.review_id)
            .subquery()
        )
        q = q.outerjoin(like_count_sub, Reviews.id == like_count_sub.c.review_id)
        q = q.order_by(like_count_sub.c.lc.desc().nulls_last())
    else:
        q = q.order_by(Reviews.created_at.desc())

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    reviews = db.execute(q.offset(skip).limit(limit)).scalars().all()
    viewer_liked_ids: set[int] = set()
    if viewer_id and reviews:
        review_ids = [r.id for r in reviews]
        liked = db.execute(
            select(Likes.review_id).where(
                Likes.user_id == viewer_id,
                Likes.review_id.in_(review_ids),
            )
        ).scalars().all()
        viewer_liked_ids = set(liked)

    results = []
    for r in reviews:
        results.append({
            "id": r.id,
            "media_id": r.media_id,
            "title": r.title,
            "content": r.content,
            "spoiler_flag": r.spoiler_flag,
            "is_featured": r.is_featured,
            "is_flagged": r.is_flagged,
            "like_count": r.like_count,
            "comment_count": r.comments.count(),
            "author": {
                "id": r.user.id,
                "username": r.user.pseudo,
                "avatar_url": getattr(r.user, "avatar_url", None),
            },
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "viewer_has_liked": r.id in viewer_liked_ids,
        })

    return results, total

def toggle_like(review_id: int, user_id: int, db: Session) -> dict:
    review = db.get(Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    existing = db.execute(
        select(Likes).where(Likes.review_id == review_id, Likes.user_id == user_id)
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()
        return {"liked": False, "like_count": review.like_count}

    like = Likes(review_id=review_id, user_id=user_id)
    db.add(like)
    db.commit()
    return {"liked": True, "like_count": review.like_count}

def add_comment(review_id: int, user_id: int, content: str, db: Session) -> Comments:
    review = db.get(Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    comment = Comments(review_id=review_id, user_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def delete_comment(comment_id: int, user_id: int, is_admin: bool, db: Session) -> None:
    comment = db.get(Comments, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable.")
    if not is_admin and comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Action non autorisée.")
    db.delete(comment)
    db.commit()

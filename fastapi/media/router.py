from __future__ import annotations
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_db
from auth.dependencies import get_current_user, get_optional_user

from media import service
from media.schemas import (
    MediaDetail, MediaBrief, MediaPageResponse, CommunityRating,
    RatingCreate, RatingOut,
    ReviewCreate, ReviewUpdate, ReviewOut, ReviewFlagCreate,
    CommentCreate, CommentOut,
)

router = APIRouter(prefix="/media", tags=["Manga — Fiches & Critiques"])

@router.get(
    "/{media_id}",
    summary="Page fiche complète d'un manga",
    response_model=MediaPageResponse,
)
async def get_media_page(
    media_id: str,
    reviews_sort: str = Query("recent", description="recent | top | featured"),
    reviews_limit: int = Query(10, ge=1, le=50),
    reviews_offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    viewer_id: int | None = current_user.id if current_user else None
    media = await service.get_or_fetch_media(media_id, db)
    media_detail = service.media_to_detail(media, viewer_id, db)
    community_rating = service.get_community_rating(media_id, db)
    reviews_data, total = service.get_reviews_for_media(
        media_id=media_id,
        viewer_id=viewer_id,
        db=db,
        skip=reviews_offset,
        limit=reviews_limit,
        sort=reviews_sort,
    )

    featured_list, _ = service.get_reviews_for_media(
        media_id=media_id,
        viewer_id=viewer_id,
        db=db,
        skip=0,
        limit=1,
        sort="featured",
    )
    featured_review = featured_list[0] if featured_list else None

    return MediaPageResponse(
        media=MediaDetail(**media_detail),
        community_rating=community_rating,
        reviews=reviews_data,
        reviews_total=total,
        featured_review=featured_review,
    )


@router.get(
    "/{media_id}/brief",
    summary="Résumé léger d'un media (pour les listes)",
    response_model=MediaBrief,
)
async def get_media_brief(
    media_id: str,
    db: Session = Depends(get_db),
):
    media = await service.get_or_fetch_media(media_id, db)
    return {
        "id": media.id,
        "title": media.title_fr or media.title_en or media.title_original,
        "cover_url": media.cover_url,
        "year": media.year,
        "status": media.status,
        "genres": service._parse_json_field(media.genres),
        "average_rating": media.average_rating,
        "rating_count": media.rating_count,
    }

@router.put(
    "/{media_id}/rating",
    summary="Créer ou mettre à jour sa note (0.5 à 5.0)",
    response_model=RatingOut,
    status_code=status.HTTP_200_OK,
)
async def upsert_rating(
    media_id: str,
    payload: RatingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.upsert_rating(media_id, current_user.id, payload, db)


@router.delete(
    "/{media_id}/rating",
    summary="Supprimer sa note",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rating(
    media_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await service.delete_rating(media_id, current_user.id, db)


@router.get(
    "/{media_id}/rating",
    summary="Note communautaire d'un media",
    response_model=CommunityRating,
)
def get_community_rating(
    media_id: str,
    db: Session = Depends(get_db),
):
    return service.get_community_rating(media_id, db)

@router.get(
    "/{media_id}/reviews",
    summary="Liste des critiques d'un media",
    response_model=dict,
)
def list_reviews(
    media_id: str,
    sort: str = Query("recent", description="recent | top | featured"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    viewer_id = current_user.id if current_user else None
    reviews, total = service.get_reviews_for_media(
        media_id=media_id,
        viewer_id=viewer_id,
        db=db,
        skip=offset,
        limit=limit,
        sort=sort,
    )
    return {"reviews": reviews, "total": total, "offset": offset, "limit": limit}


@router.post(
    "/{media_id}/reviews",
    summary="Poster une critique",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    media_id: str,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    review = await service.create_review(media_id, current_user.id, payload, db)
    return _review_to_out(review, viewer_id=current_user.id, db=db)


@router.put(
    "/reviews/{review_id}",
    summary="Modifier sa critique",
    response_model=ReviewOut,
)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    review = service.update_review(review_id, current_user.id, payload, db)
    return _review_to_out(review, viewer_id=current_user.id, db=db)


@router.delete(
    "/reviews/{review_id}",
    summary="Supprimer une critique (auteur ou admin)",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    is_admin = getattr(current_user, "is_admin", False)
    service.delete_review(review_id, current_user.id, is_admin, db)


@router.post(
    "/reviews/{review_id}/flag",
    summary="Signaler une critique (spoiler non marqué, insulte…)",
    status_code=status.HTTP_200_OK,
)
def flag_review(
    review_id: int,
    payload: ReviewFlagCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service.flag_review(review_id, current_user.id, payload, db)
    return {"detail": "Signalement enregistré. Un modérateur examinera la critique."}


@router.post(
    "/reviews/{review_id}/feature",
    summary="Marquer comme Coup de cœur (admin uniquement)",
    status_code=status.HTTP_200_OK,
)
def feature_review(
    review_id: int,
    db: Session = Depends(get_db),
    #_: None = Depends(require_admin), à mettre quand les rôles seront faits
):
    service.feature_review(review_id, db)
    return {"detail": "Critique mise en avant."}

@router.post(
    "/reviews/{review_id}/like",
    summary="Liker / unliker une critique",
    status_code=status.HTTP_200_OK,
)
def toggle_like(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.toggle_like(review_id, current_user.id, db)


@router.post(
    "/reviews/{review_id}/comments",
    summary="Commenter une critique",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    review_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comment = service.add_comment(review_id, current_user.id, payload.content, db)
    return {
        "id": comment.id,
        "review_id": comment.review_id,
        "content": comment.content,
        "author": {
            "id": comment.user.id,
            "username": comment.user.pseudo,
            "avatar_url": getattr(comment.user, "avatar_url", None),
        },
        "created_at": comment.created_at,
    }


@router.delete(
    "/comments/{comment_id}",
    summary="Supprimer un commentaire (auteur ou admin)",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    is_admin = getattr(current_user, "is_admin", False)
    service.delete_comment(comment_id, current_user.id, is_admin, db)

def _review_to_out(review, viewer_id: int, db: Session) -> dict:
    from models import Likes
    from sqlalchemy import select as sa_select

    viewer_liked = db.execute(
        sa_select(Likes).where(
            Likes.review_id == review.id,
            Likes.user_id == viewer_id,
        )
    ).scalar_one_or_none() is not None

    return {
        "id": review.id,
        "media_id": review.media_id,
        "title": review.title,
        "content": review.content,
        "contains_spoiler": review.spoiler_flag,
        "is_featured": review.is_featured,
        "is_flagged": review.is_flagged,
        "like_count": review.like_count,
        "comment_count": review.comments.count(),
        "author": {
            "id": review.user.id,
            "username": review.user.pseudo,
            "avatar_url": getattr(review.user, "avatar_url", None),
        },
        "created_at": review.created_at,
        "updated_at": review.updated_at,
        "viewer_has_liked": viewer_liked,
    }

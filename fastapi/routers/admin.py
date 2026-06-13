from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

import models
from auth.dependencies import get_db, require_admin

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/flagged-reviews", summary="Lister les critiques signalées")
def list_flagged_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: models.Users = Depends(require_admin),
):
    q = (
        select(models.Reviews)
        .where(models.Reviews.is_flagged == True)
        .order_by(models.Reviews.created_at.desc())
    )
    total = db.execute(
        select(func.count()).select_from(q.subquery())
    ).scalar_one()
    reviews = db.execute(q.offset(skip).limit(limit)).scalars().all()

    return {
        "total": total,
        "reviews": [
            {
                "id": r.id,
                "media_id": r.media_id,
                "title": r.title,
                "content": r.content,
                "flag_reason": r.flag_reason,
                "spoiler_flag": r.spoiler_flag,
                "is_featured": r.is_featured,
                "created_at": r.created_at,
                "author": {
                    "id": r.user.id,
                    "username": r.user.pseudo,
                    "avatar_url": r.user.avatar_url,
                    "is_active": r.user.is_active,
                },
            }
            for r in reviews
        ],
    }


@router.post(
    "/reviews/{review_id}/unflag",
    summary="Retirer le signalement d'une critique (admin)",
    status_code=status.HTTP_200_OK,
)
def unflag_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: models.Users = Depends(require_admin),
):
    review = db.get(models.Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    review.is_flagged = False
    review.flag_reason = None
    db.commit()
    return {"detail": "Signalement retiré."}


@router.post(
    "/reviews/{review_id}/feature",
    summary="Mettre en avant / retirer la mise en avant (admin)",
    status_code=status.HTTP_200_OK,
)
def toggle_feature_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: models.Users = Depends(require_admin),
):
    review = db.get(models.Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    review.is_featured = not review.is_featured
    db.commit()
    return {"detail": "Coup de cœur activé." if review.is_featured else "Coup de cœur retiré.", "is_featured": review.is_featured}


@router.delete(
    "/reviews/{review_id}",
    summary="Supprimer une critique signalée (admin)",
    status_code=status.HTTP_204_NO_CONTENT,
)
def admin_delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: models.Users = Depends(require_admin),
):
    review = db.get(models.Reviews, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Critique introuvable.")
    db.delete(review)
    db.commit()


@router.get("/users", summary="Lister tous les utilisateurs (admin)")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: str = Query(None),
    db: Session = Depends(get_db),
    _: models.Users = Depends(require_admin),
):
    query = select(models.Users)
    if q:
        query = query.where(models.Users.pseudo.ilike(f"%{q}%"))
    query = query.order_by(models.Users.created_at.desc())

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    users = db.execute(query.offset(skip).limit(limit)).scalars().all()

    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "pseudo": u.pseudo,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
                "avatar_url": u.avatar_url,
            }
            for u in users
        ],
    }


@router.post(
    "/users/{user_id}/ban",
    summary="Bannir un utilisateur (admin)",
    status_code=status.HTTP_200_OK,
)
def ban_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.Users = Depends(require_admin),
):
    user = db.get(models.Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se bannir soi-même.")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Impossible de bannir un administrateur.")
    user.is_active = False
    db.commit()
    return {"detail": f"Utilisateur « {user.pseudo} » banni."}


@router.post(
    "/users/{user_id}/unban",
    summary="Réactiver un utilisateur banni (admin)",
    status_code=status.HTTP_200_OK,
)
def unban_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.Users = Depends(require_admin),
):
    user = db.get(models.Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user.is_active = True
    db.commit()
    return {"detail": f"Utilisateur « {user.pseudo} » réactivé."}

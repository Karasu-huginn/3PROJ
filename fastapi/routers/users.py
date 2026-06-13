from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, get_optional_user, get_db
from auth.schemas import UserResponse, UserUpdate
from models import Rating, Media, Users
from social import service as social_service

router = APIRouter(tags=["Utilisateurs"])

@router.get("/users/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user

@router.put("/users/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if data.theme and data.theme not in ("light", "dark"):
        raise HTTPException(status_code=400, detail="Thème invalide, choisir 'light' ou 'dark'.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/users/me/export")
def export_data(
    format: str = Query("json", description="json | csv"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ratings = (
        db.query(Rating, Media)
        .join(Media, Rating.media_id == Media.id)
        .filter(Rating.user_id == current_user.id)
        .all()
    )

    data = [
        {
            "media_id": r.media_id,
            "title": m.title_fr or m.title_en or m.title_original,
            "score": r.score,
            "rated_at": r.created_at.isoformat(),
        }
        for r, m in ratings
    ]

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["media_id", "title", "score", "rated_at"])
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=mes_notes.csv"},
        )

    return StreamingResponse(
        iter([json.dumps(data, ensure_ascii=False, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=mes_notes.json"},
    )

@router.get("/users/{user_id}/profile")
def get_public_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    viewer_id = current_user.id if current_user else None
    return social_service.get_public_profile(user_id, viewer_id, db)

@router.get("/users/search")
def search_users(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    users = db.query(Users).filter(Users.pseudo.ilike(f"%{q}%")).all()
    return [{"id": u.id, "pseudo": u.pseudo, "avatar_url": u.avatar_url} for u in users]
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_db, get_current_user
from notifications import service
from notifications.schemas import NotificationsResponse

router = APIRouter(tags=["Notifications"])

@router.get(
    "/notifications",
    summary="Liste des notifications (polling)",
    response_model=NotificationsResponse,
)
def get_notifications(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_notifications(
        user_id=current_user.id,
        db=db,
        skip=offset,
        limit=limit,
        unread_only=unread_only,
    )

@router.post(
    "/notifications/{notification_id}/read",
    summary="Marquer une notification comme lue",
    status_code=status.HTTP_204_NO_CONTENT,
)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service.mark_as_read(current_user.id, notification_id, db)

@router.post(
    "/notifications/read-all",
    summary="Marquer toutes les notifications comme lues",
    status_code=status.HTTP_200_OK,
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated = service.mark_all_as_read(current_user.id, db)
    return {"marked_as_read": updated}
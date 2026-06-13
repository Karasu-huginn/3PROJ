from __future__ import annotations

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models import Notifications, Users
from notifications.schemas import NotificationOut, ActorBrief, NotificationsResponse

def _to_out(n: Notifications) -> NotificationOut:
    actor = None
    if n.actor:
        actor = ActorBrief(
            id=n.actor.id,
            username=n.actor.pseudo,
            avatar_url=n.actor.avatar_url,
        )
    return NotificationOut(
        id=n.id,
        type=n.type,
        actor=actor,
        review_id=n.review_id,
        is_read=n.is_read,
        created_at=n.created_at,
    )

def create_notification(
    db: Session,
    user_id: int,
    type: str,
    actor_id: int | None = None,
    review_id: int | None = None,
) -> None:
    if actor_id and actor_id == user_id:
        return
    db.add(Notifications(
        user_id=user_id,
        type=type,
        actor_id=actor_id,
        review_id=review_id,
    ))
    db.commit()

def get_notifications(
    user_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
) -> NotificationsResponse:
    base_q = db.query(Notifications).filter(Notifications.user_id == user_id)

    if unread_only:
        base_q = base_q.filter(Notifications.is_read == False)

    total = base_q.count()
    unread_count = db.query(func.count(Notifications.id)).filter(
        Notifications.user_id == user_id,
        Notifications.is_read == False,
    ).scalar() or 0

    rows = (
        base_q
        .order_by(desc(Notifications.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return NotificationsResponse(
        notifications=[_to_out(n) for n in rows],
        unread_count=unread_count,
        total=total,
        offset=skip,
        limit=limit,
    )

def mark_as_read(user_id: int, notification_id: int, db: Session) -> None:
    n = db.query(Notifications).filter(
        Notifications.id == notification_id,
        Notifications.user_id == user_id,
    ).first()
    if n:
        n.is_read = True
        db.commit()

def mark_all_as_read(user_id: int, db: Session) -> int:
    updated = db.query(Notifications).filter(
        Notifications.user_id == user_id,
        Notifications.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return updated
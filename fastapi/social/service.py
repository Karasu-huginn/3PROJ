from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session
from models import (
    Users, Follows, Activity,
    PrivateMessages, Reviews, Rating, Media,
)
from social.schemas import (
    ActivityOut, AuthorBrief, FollowOut, FollowerItem,
    MessageOut, ConversationItem,
)

def _author(user: Users) -> AuthorBrief:
    return AuthorBrief(
        id=user.id,
        username=user.pseudo,
        avatar_url=user.avatar_url,
    )
  
def _follower_count(user_id: int, db: Session) -> int:
    return db.query(func.count(Follows.id)).filter(
        Follows.following_id == user_id
    ).scalar() or 0

def _following_count(user_id: int, db: Session) -> int:
    return db.query(func.count(Follows.id)).filter(
        Follows.follower_id == user_id
    ).scalar() or 0

def _is_following(viewer_id: int, target_id: int, db: Session) -> bool:
    return db.query(Follows).filter(
        Follows.follower_id == viewer_id,
        Follows.following_id == target_id,
    ).first() is not None

def toggle_follow(current_user_id: int, target_id: int, db: Session) -> FollowOut:
    if current_user_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas vous suivre vous-même.",
        )

    target = db.query(Users).filter(Users.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    existing = db.query(Follows).filter(
        Follows.follower_id == current_user_id,
        Follows.following_id == target_id,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        following = False
    else:
        db.add(Follows(follower_id=current_user_id, following_id=target_id))
        db.add(Activity(
            user_id=current_user_id,
            activity_type="follow",
            target_user_id=target_id,
        ))
        db.commit()
        following = True

    return FollowOut(
        following=following,
        follower_count=_follower_count(target_id, db),
        following_count=_following_count(target_id, db),
    )

def get_followers(user_id: int, viewer_id: Optional[int], db: Session) -> list[FollowerItem]:
    rows = (
        db.query(Users)
        .join(Follows, Follows.follower_id == Users.id)
        .filter(Follows.following_id == user_id)
        .all()
    )
    return [
        FollowerItem(
            id=u.id,
            pseudo=u.pseudo,
            avatar_url=u.avatar_url,
            is_followed_by_viewer=_is_following(viewer_id, u.id, db) if viewer_id else False,
        )
        for u in rows
    ]

def get_following(user_id: int, viewer_id: Optional[int], db: Session) -> list[FollowerItem]:
    rows = (
        db.query(Users)
        .join(Follows, Follows.following_id == Users.id)
        .filter(Follows.follower_id == user_id)
        .all()
    )
    return [
        FollowerItem(
            id=u.id,
            pseudo=u.pseudo,
            avatar_url=u.avatar_url,
            is_followed_by_viewer=_is_following(viewer_id, u.id, db) if viewer_id else False,
        )
        for u in rows
    ]

def get_public_profile(user_id: int, viewer_id: Optional[int], db: Session):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return {
        "id": user.id,
        "pseudo": user.pseudo,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "follower_count": _follower_count(user_id, db),
        "following_count": _following_count(user_id, db),
        "is_followed_by_viewer": _is_following(viewer_id, user_id, db) if viewer_id else False,
    }

def _activity_to_out(row: Activity, db: Session) -> ActivityOut:
    actor = db.query(Users).filter(Users.id == row.user_id).first()

    media_title = media_cover = None
    if row.media_id:
        media = db.query(Media).filter(Media.id == row.media_id).first()
        if media:
            media_title = media.title_fr or media.title_en or media.title_original
            media_cover = media.cover_url

    review_title = None
    if row.review_id:
        review = db.query(Reviews).filter(Reviews.id == row.review_id).first()
        if review:
            review_title = review.title

    target_pseudo = None
    if row.target_user_id:
        target = db.query(Users).filter(Users.id == row.target_user_id).first()
        if target:
            target_pseudo = target.pseudo

    return ActivityOut(
        id=row.id,
        actor=_author(actor),
        activity_type=row.activity_type,
        media_id=row.media_id,
        media_title=media_title,
        media_cover=media_cover,
        review_id=row.review_id,
        review_title=review_title,
        rating_score=row.rating_score,
        target_user_id=row.target_user_id,
        target_pseudo=target_pseudo,
        created_at=row.created_at,
    )

def get_feed(current_user_id: int, db: Session, skip: int = 0, limit: int = 20):
    followed_ids = [
        r.following_id
        for r in db.query(Follows.following_id)
        .filter(Follows.follower_id == current_user_id)
        .all()
    ]

    if not followed_ids:
        return [], 0

    base_q = db.query(Activity).filter(Activity.user_id.in_(followed_ids))
    total = base_q.count()
    rows = (
        base_q
        .order_by(desc(Activity.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_activity_to_out(r, db) for r in rows], total

def _mutual_follow(user_a: int, user_b: int, db: Session) -> bool:
    a_follows_b = _is_following(user_a, user_b, db)
    b_follows_a = _is_following(user_b, user_a, db)
    return a_follows_b and b_follows_a

def send_message(sender_id: int, receiver_id: int, content: str, db: Session) -> MessageOut:
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous envoyer un message.")

    receiver = db.query(Users).filter(Users.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Destinataire introuvable.")

    if not _mutual_follow(sender_id, receiver_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous devez vous suivre mutuellement pour échanger des messages.",
        )

    msg = PrivateMessages(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    sender = db.query(Users).filter(Users.id == sender_id).first()
    return MessageOut(
        id=msg.id,
        sender=_author(sender),
        content=msg.content,
        created_at=msg.created_at,
        read_at=msg.read_at,
    )

def get_conversation(
    user_id: int,
    other_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[MessageOut], int]:
    receiver = db.query(Users).filter(Users.id == other_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    base_q = db.query(PrivateMessages).filter(
        or_(
            and_(PrivateMessages.sender_id == user_id, PrivateMessages.receiver_id == other_id),
            and_(PrivateMessages.sender_id == other_id, PrivateMessages.receiver_id == user_id),
        )
    )
    total = base_q.count()
    messages = (
        base_q
        .order_by(PrivateMessages.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )

    now = datetime.now(timezone.utc)
    for msg in messages:
        if msg.receiver_id == user_id and msg.read_at is None:
            msg.read_at = now
    db.commit()

    result = []
    for msg in messages:
        sender = db.query(Users).filter(Users.id == msg.sender_id).first()
        result.append(MessageOut(
            id=msg.id,
            sender=_author(sender),
            content=msg.content,
            created_at=msg.created_at,
            read_at=msg.read_at,
        ))
    return result, total

def list_conversations(user_id: int, db: Session) -> list[ConversationItem]:
    sent = db.query(PrivateMessages.receiver_id.label("other_id")).filter(
        PrivateMessages.sender_id == user_id
    )
    received = db.query(PrivateMessages.sender_id.label("other_id")).filter(
        PrivateMessages.receiver_id == user_id
    )
    partner_ids = {r.other_id for r in sent.union(received).all()}

    conversations = []
    for other_id in partner_ids:
        other = db.query(Users).filter(Users.id == other_id).first()
        if not other:
            continue

        last_msg = (
            db.query(PrivateMessages)
            .filter(
                or_(
                    and_(PrivateMessages.sender_id == user_id, PrivateMessages.receiver_id == other_id),
                    and_(PrivateMessages.sender_id == other_id, PrivateMessages.receiver_id == user_id),
                )
            )
            .order_by(desc(PrivateMessages.created_at))
            .first()
        )

        unread = db.query(func.count(PrivateMessages.id)).filter(
            PrivateMessages.sender_id == other_id,
            PrivateMessages.receiver_id == user_id,
            PrivateMessages.read_at.is_(None),
        ).scalar() or 0

        conversations.append(ConversationItem(
            other_user=_author(other),
            last_message=last_msg.content if last_msg else None,
            last_message_at=last_msg.created_at if last_msg else None,
            unread_count=unread,
        ))

    conversations.sort(key=lambda c: c.last_message_at or datetime.min, reverse=True)
    return conversations
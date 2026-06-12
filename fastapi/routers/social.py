from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_db, get_current_user, get_optional_user
from social import service
from social.schemas import (
    FollowOut, FollowerItem, UserPublicProfile,
    FeedResponse,
    MessageCreate, MessageOut, ConversationItem,
)

router = APIRouter(tags=["Social"])

@router.get(
    "/users/{user_id}/profile",
    summary="Profil public d'un utilisateur",
    response_model=UserPublicProfile,
)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    viewer_id = current_user.id if current_user else None
    return service.get_public_profile(user_id, viewer_id, db)

@router.post(
    "/users/{user_id}/follow",
    summary="Suivre ou ne plus suivre un utilisateur (toggle)",
    response_model=FollowOut,
    status_code=status.HTTP_200_OK,
)
def toggle_follow(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.toggle_follow(current_user.id, user_id, db)

@router.get(
    "/users/{user_id}/followers",
    summary="Liste des abonnés d'un utilisateur",
    response_model=list[FollowerItem],
)
def list_followers(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    viewer_id = current_user.id if current_user else None
    return service.get_followers(user_id, viewer_id, db)

@router.get(
    "/users/{user_id}/following",
    summary="Liste des abonnements d'un utilisateur",
    response_model=list[FollowerItem],
)
def list_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    viewer_id = current_user.id if current_user else None
    return service.get_following(user_id, viewer_id, db)

@router.get(
    "/feed",
    summary="Fil d'actualité (activités des personnes suivies)",
    response_model=FeedResponse,
)
def get_feed(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    activities, total = service.get_feed(current_user.id, db, skip=offset, limit=limit)
    return FeedResponse(activities=activities, total=total, offset=offset, limit=limit)

@router.get(
    "/messages",
    summary="Liste de toutes les conversations",
    response_model=list[ConversationItem],
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.list_conversations(current_user.id, db)

@router.get(
    "/messages/{other_user_id}",
    summary="Historique d'une conversation",
    response_model=dict,
)
def get_conversation(
    other_user_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    messages, total = service.get_conversation(
        current_user.id, other_user_id, db, skip=offset, limit=limit
    )
    return {"messages": messages, "total": total, "offset": offset, "limit": limit}

@router.post(
    "/messages/{receiver_id}",
    summary="Envoyer un message privé",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    receiver_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.send_message(current_user.id, receiver_id, payload.content, db)
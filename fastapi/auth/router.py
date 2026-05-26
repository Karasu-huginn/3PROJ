from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Annotated
import httpx
import os
from dotenv import load_dotenv
import models
from auth import service as auth_service
from auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, MessageResponse
from auth.utils import create_access_token, decode_access_token
from auth.dependencies import get_current_user, get_db

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/auth", tags=["Authentification"])

bearer_scheme = HTTPBearer()

db_dependency = Annotated[Session, Depends(get_db)]
current_user_dependency = Annotated[models.Users, Depends(get_current_user)]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: db_dependency):
    user = auth_service.register_user(db, data)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: db_dependency):
    user = auth_service.authenticate_user(db, data.email, data.password)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    db: db_dependency,
    current_user: current_user_dependency,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
):
    payload = decode_access_token(credentials.credentials)
    jti = payload.get("jti")
    if jti:
        auth_service.revoke_token(db, jti)
    return MessageResponse(message="Deconnexion reussie")


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: current_user_dependency):
    return current_user

@router.get("/google")
def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth Google non configure sur ce serveur",
        )

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)

@router.get("/google/callback")
async def google_callback(code: str, db: db_dependency):
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_res.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Echec de l'echange du code Google",
        )

    google_access_token = token_res.json().get("access_token")

    async with httpx.AsyncClient() as client:
        profile_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

    if profile_res.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de recuperer le profil Google",
        )

    profile = profile_res.json()
    user = auth_service.get_or_create_oauth_user(
        db,
        email=profile["email"],
        pseudo=profile.get("name", profile["email"].split("@")[0]),
        avatar_url=profile.get("picture"),
        oauth_provider="google",
        oauth_id=str(profile["id"]),
    )

    token = create_access_token(user.id)
    return RedirectResponse(url=f"{FRONTEND_URL}/oauth/callback?token={token}")
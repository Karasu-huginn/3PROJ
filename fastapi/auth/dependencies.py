from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Annotated, Optional

import models
from database import SessionLocal
from auth.utils import decode_access_token
from auth import service as auth_service

bearer_scheme = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> models.Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if user_id is None or jti is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception
    if auth_service.is_token_revoked(db, jti):
        raise credentials_exception

    user = db.query(models.Users).filter(models.Users.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user

def get_optional_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(HTTPBearer(auto_error=False)),  # auto_error=False → None si pas de header
    ] = None,
) -> Optional[models.Users]:
    if credentials is None:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if user_id is None or jti is None:
            return None

    except JWTError:
        return None

    if auth_service.is_token_revoked(db, jti):
        return None

    user = db.query(models.Users).filter(models.Users.id == int(user_id)).first()
    if user is None or not user.is_active:
        return None

    return user
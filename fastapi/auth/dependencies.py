from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Annotated

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
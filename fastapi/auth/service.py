from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
import models
from auth.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def register_user(db: Session, data: UserCreate) -> models.Users:
    existing = db.query(models.Users).filter(models.Users.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email",
        )

    pseudo_taken = db.query(models.Users).filter(models.Users.pseudo == data.pseudo).first()
    if pseudo_taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce pseudo est déjà utilisé",
        )

    user = models.Users(
        email=data.email,
        pseudo=data.pseudo,
        password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> models.Users:
    user = db.query(models.Users).filter(models.Users.email == email).first()
    password_ok = verify_password(password, user.password) if (user and user.password) else False

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été banni",
        )

    return user

def get_or_create_oauth_user(
    db: Session,
    *,
    email: str,
    pseudo: str,
    avatar_url: str | None,
    oauth_provider: str,
    oauth_id: str,
) -> models.Users:
    user = (
        db.query(models.Users)
        .filter(
            models.Users.oauth_provider == oauth_provider,
            models.Users.oauth_id == oauth_id,
        )
        .first()
    )
    if user:
        return user

    user = db.query(models.Users).filter(models.Users.email == email).first()
    if user:
        user.oauth_provider = oauth_provider
        user.oauth_id = oauth_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user

    base_pseudo = pseudo.replace(" ", "_").lower()
    final_pseudo = base_pseudo
    counter = 1
    while db.query(models.Users).filter(models.Users.pseudo == final_pseudo).first():
        final_pseudo = f"{base_pseudo}_{counter}"
        counter += 1

    user = models.Users(
        email=email,
        pseudo=final_pseudo,
        avatar_url=avatar_url,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        password=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def revoke_token(db: Session, jti: str) -> None:
    revoked = models.RevokedTokens(jti=jti)
    db.add(revoked)
    db.commit()


def is_token_revoked(db: Session, jti: str) -> bool:
    return db.query(models.RevokedTokens).filter(models.RevokedTokens.jti == jti).first() is not None
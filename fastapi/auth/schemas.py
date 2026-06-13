import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    pseudo: str
    email: EmailStr
    password: str

    @field_validator("pseudo")
    @classmethod
    def pseudo_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Le pseudo doit faire au moins 2 caractères")
        if len(v) > 30:
            raise ValueError("Le pseudo ne peut pas dépasser 30 caractères")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit faire au moins 8 caractères")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"\d", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial")
        return v
class UserUpdate(BaseModel):
    pseudo: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website_url: Optional[str] = None
    theme: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    pseudo: str
    email: str
    avatar_url: str | None
    bio: str | None
    role: str
    website_url: str | None = None
    theme: str = "light"
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str
from fastapi import APIRouter, FastAPI, HTTPException, Depends
from typing import List, Annotated
import models
from schemas import UserCreate, UserResponse
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from database import get_db

import routers.collections as CR


app = FastAPI()

app.include_router(CR.router)

origins = [                                 #autoriser connexion depuis localhost 3000
    'http://localhost:3000'
]

app.add_middleware(                         #ajouter middleware à l'app
    CORSMiddleware,
    allow_origins=origins,
)

db_dependency = Annotated[Session, Depends(get_db)]  #la db dépend de la session et aussi de ce que l'on récupère via Db

models.Base.metadata.create_all(bind=engine)

@app.get('/')
def root():
    return {"message" : "SCRUM TEAM"}

@app.post("/users/", response_model=UserResponse)                   # créer user via le model dans schemas
def create_user(user: UserCreate, db :db_dependency):
    db_user = models.Users(username=user.username, email = user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserResponse])              #afficher user via la liste 
def get_users(db: db_dependency):
    return db.query(models.Users).all()
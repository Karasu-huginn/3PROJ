from fastapi import FastAPI, HTTPException, Depends
from typing import List, Annotated
import models
from database import engine, get_db
from sqlalchemy.orm import Session
from auth.router import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from media.router import router as media_router
from routers.social import router as social_router
import routers.collections as CR


app = FastAPI()

origins = [                                 #autoriser connexion depuis localhost 3000
    'http://localhost:3000'
]

app.add_middleware(                         #ajouter middleware à l'app
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
models.Base.metadata.create_all(bind=engine)

@app.get('/')
def root():
    return {"message" : "SCRUM TEAM"}

app.include_router(auth_router)
app.include_router(media_router)
app.include_router(CR.router)
app.include_router(social_router)

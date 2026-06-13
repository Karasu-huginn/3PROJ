from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
URL_DATABASE = os.getenv("DATABASE_URL")

if not URL_DATABASE:
    raise RuntimeError("DATABASE_URL manquant dans le fichier .env")

connect_args = {"check_same_thread": False} if URL_DATABASE.startswith("sqlite") else {}
engine = create_engine(URL_DATABASE, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
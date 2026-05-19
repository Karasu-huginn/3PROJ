from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

def get_db_url():
    load_dotenv(".env.local.db")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")
    port = os.getenv("PORT")
    db_name = os.getenv("DB_NAME")
    host = os.getenv("HOST")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

URL_DATABASE = get_db_url()

engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
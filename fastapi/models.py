from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func
from database import Base
from datetime import datetime, timezone

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    pseudo = Column(String, index=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default='user')
    bio = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer)
    type = Column(String)
    title = Column(String)
    poster_url = Column(String)

class Collections(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poster_url = Column(String)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CollectionsItems(Base):
    __tablename__ = 'collectionsItems'
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String)
    title = Column(String)
    poster_url = Column(String)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Reviews(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    media_id = Column(Integer, ForeignKey('media.id'))
    rating = Column(Integer)
    content = Column(String)
    spoiler_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=func.now())

class Likes(Base):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    review_id = Column(Integer, ForeignKey('reviews.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Comments(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    review_id = Column(Integer, ForeignKey('reviews.id'))
    content = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Follows(Base):
    __tablename__ = 'follows'
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey('users.id'))
    following_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Notifications(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PrivateMessages(Base):
    __tablename__ = 'privateMessages'
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    receiver_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime, nullable=True)

class ReportMessages(Base):
    __tablename__ = 'reportMessages'
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey('users.id'))
    admin_id = Column(Integer, ForeignKey('users.id'))
    reason = Column(String)
    status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ReportComments(Base):
    __tablename__ = 'reportComments'
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey('users.id'))
    admin_id = Column(Integer, ForeignKey('users.id'))
    reason = Column(String)
    status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, Text , func
from database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)
    pseudo = Column(String, index=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default='user')
    bio = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    ratings  = relationship("Rating", back_populates="user", lazy="dynamic")
    reviews  = relationship("Reviews", back_populates="user", foreign_keys="Reviews.user_id", lazy="dynamic")
    followers  = relationship("Follows", foreign_keys="Follows.following_id", back_populates="followed_user", lazy="dynamic")
    followings = relationship("Follows", foreign_keys="Follows.follower_id",  back_populates="follower_user",  lazy="dynamic")


class Media(Base):
    __tablename__ = 'media'
    id = Column(String(36), primary_key=True)
    external_id = Column(String(36))
    type = Column(String)
    title_fr = Column(String(512), nullable=True)
    title_en = Column(String(512), nullable=True)
    title_original = Column(String(512))
    description = Column(Text, nullable=True)
    cover_url = Column(String(1024), nullable=True)
    author_names = Column(String(512), nullable=True)
    genres = Column(String(512), nullable=True)
    status = Column(String(64), nullable=True)
    year = Column(Integer, nullable=True)
    content_rating = Column(String(32), nullable=True)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ratings = relationship("Rating", lazy="dynamic")
    
    @property
    def average_rating(self):
        result = self.ratings.with_entities(func.avg(Rating.score)).scalar()
        return round(float(result), 2) if result else None

    @property
    def rating_count(self):
        return self.ratings.count()

class Collections(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poster_url = Column(String)
    is_public = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    name = Column(String)

class CollectionsItems(Base):
    __tablename__ = 'collectionsItems'
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    media_id = Column(String(36), ForeignKey('media.id'))

class Reviews(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    media_id = Column(String(36), ForeignKey('media.id'))
    rating = Column(Integer)
    content = Column(String)
    is_flagged = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    spoiler_flag = Column(Boolean, default=False)
    flag_reason = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=func.now())
    user = relationship("Users", back_populates="reviews", foreign_keys=[user_id])
    likes = relationship("Likes", lazy="dynamic")
    comments = relationship("Comments", lazy="dynamic")

    @property
    def like_count(self):
        return self.likes.count()

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
    user = relationship("Users")

class Follows(Base):
    __tablename__ = 'follows'
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey('users.id'))
    following_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    follower_user  = relationship("Users", foreign_keys=[follower_id],  back_populates="followings")
    followed_user  = relationship("Users", foreign_keys=[following_id], back_populates="followers")

class Notifications(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable = False)
    type = Column(String(32), nullable= False)
    actor_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    review_id = Column(Integer, ForeignKey('reviews.id'), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    actor = relationship("Users", foreign_keys=[actor_id])
    review = relationship("Reviews", foreign_keys=[review_id])

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

class RevokedTokens(Base):
    __tablename__ = 'revoked_tokens'
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    media_id = Column(String(36), ForeignKey('media.id'))
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=func.now())
    user = relationship("Users", back_populates="ratings")
    
class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    activity_type = Column(String(32), nullable=False)
    media_id = Column(String(36), ForeignKey('media.id'), nullable=True)
    review_id = Column(Integer, ForeignKey('reviews.id'), nullable=True)
    rating_score = Column(Float, nullable=True)
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("Users", foreign_keys=[user_id])
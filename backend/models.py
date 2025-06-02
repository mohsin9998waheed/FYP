from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Float, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
target_metadata = Base.metadata

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    password_hash = Column(String)
    phone_number = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String)  # 'user', 'admin', 'creator'
    preferences = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    audiobooks = relationship("Audiobook", back_populates="creator")
    likes = relationship("Like", back_populates="user")
    listening_history = relationship("ListeningHistory", back_populates="user")


class Audiobook(Base):
    __tablename__ = "audiobooks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")
    creator = relationship("User", back_populates="audiobooks")
    chapters = relationship("Chapter", back_populates="audiobook")
    listening_history = relationship("ListeningHistory", back_populates="book")
    likes = relationship("Like", back_populates="book")

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    audiobook_id = Column(Integer, ForeignKey("audiobooks.id"), nullable=False)
    title = Column(String, nullable=False)
    audio_url = Column(String, nullable=False)
    thumbnail_url = Column(String)
    order = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    audiobook = relationship("Audiobook", back_populates="chapters")



class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("audiobooks.id"))
    progress = Column(Float)  # 0.0 to 1.0
    last_played = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="listening_history")
    book = relationship("Audiobook", back_populates="listening_history")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("audiobooks.id"))

    user = relationship("User", back_populates="likes")
    book = relationship("Audiobook", back_populates="likes")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Banner {self.id}>"
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Float, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

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
    title = Column(String)
    description = Column(Text)
    author = Column(String)
    narrator = Column(String)
    duration = Column(String)
    file_url = Column(String)
    cover_image_url = Column(String)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_public = Column(Boolean, default=True)
    category = Column(String)
    tags = Column(String)  # Could be JSON or comma-separated
    listens = Column(Integer, default=0)

    creator = relationship("User", back_populates="audiobooks")
    likes = relationship("Like", back_populates="book")
    listening_history = relationship("ListeningHistory", back_populates="book")


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

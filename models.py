from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    user_id   = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

class Contents(Base):
    __tablename__ = "contents"
    content_id   = Column(String(255), primary_key=True)
    content_type = Column(String(50), nullable=False)
    transcript   = Column(Text)
    processed_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC))

    # Relationship to Places
    places = relationship("Places", secondary="content_places", back_populates="contents")

class Places(Base):
    __tablename__ = 'places'
    place_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    lat = Column(Float)
    lng = Column(Float)

    # Relationship to Contents
    contents = relationship("Contents", secondary="content_places", back_populates="places")

    def __repr__(self):
        return f"<Places(place_id={self.place_id}, name='{self.name}')>"

class ContentPlaces(Base):
    __tablename__ = "content_places"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    content_id   = Column(String(255), ForeignKey("contents.content_id"))
    place_id     = Column(Integer, ForeignKey("places.place_id"))
    __table_args__ = (UniqueConstraint("content_id", "place_id"),)

class UserContentHistory(Base):
    __tablename__ = "user_content_history"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(String(36), ForeignKey("users.user_id"))
    content_id   = Column(String(255), ForeignKey("contents.content_id"))
    created_at   = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    __table_args__ = (
        UniqueConstraint("user_id", "content_id"),
    )






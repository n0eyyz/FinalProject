from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Users(Base):
    """
    사용자 정보를 저장하는 데이터베이스 모델입니다.
    - user_id: 사용자 고유 ID (기본 키)
    - email: 사용자 이메일 (고유)
    - hashed_password: 해시된 비밀번호
    - created_at: 사용자 생성 시간
    """
    __tablename__ = "users"
    user_id   = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

class Contents(Base):
    """
    처리된 콘텐츠(예: YouTube 비디오) 정보를 저장하는 데이터베이스 모델입니다.
    - content_id: 콘텐츠 고유 ID (기본 키, 예: YouTube video ID)
    - content_type: 콘텐츠 유형 (예: 'youtube')
    - transcript: 콘텐츠의 텍스트 스크립트
    - processed_at: 콘텐츠 처리 시간
    - places: 이 콘텐츠와 연결된 장소들 (ContentPlaces를 통한 관계)
    """
    __tablename__ = "contents"
    content_id   = Column(String(255), primary_key=True)
    content_type = Column(String(50), nullable=False)
    transcript   = Column(Text)
    processed_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC))

    # Relationship to Places
    places = relationship("Places", secondary="content_places", back_populates="contents")

class Places(Base):
    """
    추출된 장소 정보를 저장하는 데이터베이스 모델입니다.
    - place_id: 장소 고유 ID (기본 키)
    - name: 장소 이름 (고유)
    - lat: 장소의 위도
    - lng: 장소의 경도
    - contents: 이 장소와 연결된 콘텐츠들 (ContentPlaces를 통한 관계)
    """
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
    """
    콘텐츠와 장소 간의 다대다 관계를 연결하는 데이터베이스 모델입니다.
    - id: 고유 ID (기본 키)
    - content_id: Contents 테이블의 content_id를 참조하는 외래 키
    - place_id: Places 테이블의 place_id를 참조하는 외래 키
    - UniqueConstraint: content_id와 place_id의 조합은 고유해야 합니다.
    """
    __tablename__ = "content_places"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    content_id   = Column(String(255), ForeignKey("contents.content_id"))
    place_id     = Column(Integer, ForeignKey("places.place_id"))
    __table_args__ = (UniqueConstraint("content_id", "place_id"),)

class UserContentHistory(Base):
    """
    사용자가 조회하거나 처리한 콘텐츠 기록을 저장하는 데이터베이스 모델입니다.
    - id: 고유 ID (기본 키)
    - user_id: Users 테이블의 user_id를 참조하는 외래 키
    - content_id: Contents 테이블의 content_id를 참조하는 외래 키
    - created_at: 기록 생성 시간
    - UniqueConstraint: user_id와 content_id의 조합은 고유해야 합니다.
    """
    __tablename__ = "user_content_history"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.user_id"))
    content_id   = Column(String(255), ForeignKey("contents.content_id"))
    created_at   = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    __table_args__ = (
        UniqueConstraint("user_id", "content_id"),
    )






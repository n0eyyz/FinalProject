from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

class URLRequest(BaseModel):
    """
    YouTube URL 요청을 위한 Pydantic 스키마.
    """
    url: str

class Place(BaseModel):
    """
    장소 정보를 나타내는 Pydantic 스키마.
    이름, 위도, 경도를 포함합니다.
    """
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None

    class Config:
        from_attributes = True

class PlaceResponse(BaseModel):
    """
    장소 추출 결과 응답을 위한 Pydantic 스키마.
    데이터베이스에서 가져왔는지(db) 새로 추출했는지(new)를
    나타내는 모드와 장소 목록을 포함합니다.
    장소 목록을 포함합니다.
    """
    mode: str # "db", "new", 또는 "new_processing"
    places: List[Place]

    class Config:
        from_attributes = True

class ApiVideoHistory(BaseModel):
    """
    사용자 히스토리 응답을 위한 Pydantic 스키마.
    """
    id: str
    title: Optional[str] = None
    created_at: datetime
    thumbnail_url: Optional[HttpUrl] = None
    youtube_url: Optional[HttpUrl] = None
    places: List[Place] = []

    class Config:
        from_attributes = True

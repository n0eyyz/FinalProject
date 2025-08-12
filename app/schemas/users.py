from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

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

class UserContentHistoryResponse(BaseModel):
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

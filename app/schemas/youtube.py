from pydantic import BaseModel, Field
from typing import List, Optional

class URLRequest(BaseModel):
    """프론트에서 URL을 받기 위한 요청 스키마"""
    url: str

class Place(BaseModel):
    """장소 정보 스키마"""
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None

    class Config:
        from_attributes = True

class PlaceResponse(BaseModel):
    """장소 정보를 프론트로 보내기 위한 응답 스키마"""
    mode: str # "db" 또는 "new"
    places: List[Place]

    class Config:
        from_attributes = True
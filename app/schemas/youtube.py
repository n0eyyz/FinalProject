from pydantic import BaseModel, Field
from typing import List, Optional

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
    데이터베이스에서 가져왔는지(db) 새로 추출했는지(new)를 나타내는 모드와 장소 목록을 포함합니다.
    """
    mode: str # "db" 또는 "new"
    places: List[Place]

    class Config:
        from_attributes = True
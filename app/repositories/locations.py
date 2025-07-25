from sqlalchemy.orm import Session
from models import Contents, Places, ContentPlaces, UserContentHistory
from sqlalchemy.exc import IntegrityError
from app.services.extractor import extract_locations_from_youtube
from typing import List

def get_content_by_id(db: Session, content_id: str) -> Contents | None:
    return db.query(Contents).filter(Contents.content_id == content_id).first()

def create_or_update_content(db: Session, content_id: str, content_type: str, transcript: str | None):
    content = get_content_by_id(db, content_id)
    if content:
        content.transcript = transcript
        db.commit()
        db.refresh(content)
        return content
    content = Contents(content_id=content_id, content_type=content_type, transcript=transcript)
    db.add(content)
    db.commit()
    db.refresh(content)
    return content

def upsert_place(db: Session, name: str, lat: float | None, lng: float | None) -> Places:
    place = db.query(Places).filter(Places.name == name).first()
    if place:
        if (place.lat is None or place.lng is None) and (lat is not None and lng is not None):
            place.lat, place.lng = lat, lng
            db.commit()
            db.refresh(place)
        return place
    place = Places(name=name, lat=lat, lng=lng)
    db.add(place)
    db.commit()
    db.refresh(place)
    return place

def link_content_place(db: Session, content_id: str, place_id: int):
    exists = (
        db.query(ContentPlaces)
        .filter(ContentPlaces.content_id == content_id, ContentPlaces.place_id == place_id)
        .first()
    )
    if not exists:
        db.add(ContentPlaces(content_id=content_id, place_id=place_id))
        db.commit()

def add_user_history(db: Session, user_id: str | None, content_id: str):
    if not user_id:
        return
    hist = UserContentHistory(user_id=user_id, content_id=content_id)
    db.add(hist)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # 이미 있으면 무시

def get_places_by_content_id(db: Session, content_id: str) -> list[Places]:
    """
    콘텐츠 ID와 연결된 모든 장소 정보를 조회합니다.
    """
    return (
        db.query(Places)
        .join(ContentPlaces, ContentPlaces.place_id == Places.place_id)
        .filter(ContentPlaces.content_id == content_id)
        .all()
    )

def extract_and_save_locations(db: Session, video_id: str, url: str) -> list[Places]:
    """
    (Mode 2) URL에서 장소를 새로 추출하고 DB에 저장하는 서비스 로직
    """
    # 1. 외부 서비스(Youtube, Gemini)를 통해 스크립트와 장소 정보 추출
    transcript, extracted_locs = extract_locations_from_youtube(url)

    if not transcript or not extracted_locs:
        return []

    # 2. 콘텐츠 정보 저장 (또는 업데이트)
    create_or_update_content(db, video_id, 'youtube', transcript)

    # 3. 추출된 장소들을 DB에 저장하고 콘텐츠와 연결
    saved_places = []
    for loc in extracted_locs:
        # upsert_place는 장소를 찾거나 새로 만들고, 그 객체를 반환합니다.
        place_obj = upsert_place(db, name=loc['name'], lat=loc.get('lat'), lng=loc.get('lng'))
        # 콘텐츠와 장소를 연결합니다.
        link_content_place(db, video_id, place_obj.place_id)
        saved_places.append(place_obj)
    
    # 4. 최종 저장된 장소 목록 반환
    return saved_places

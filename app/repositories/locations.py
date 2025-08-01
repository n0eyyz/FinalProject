from sqlalchemy.orm import Session, joinedload
from models import Contents, Places, ContentPlaces, UserContentHistory
from sqlalchemy.exc import IntegrityError
from app.services.extractor import extract_locations_from_youtube
from typing import List


def get_content_by_id(db: Session, content_id: str) -> Contents | None:
    """
    주어진 content_id에 해당하는 Contents 객체를 데이터베이스에서 조회합니다.
    """
    return db.query(Contents).filter(Contents.content_id == content_id).first()


# <<< 변경: create_or_update_content 함수가 메타데이터를 받도록 수정
def create_or_update_content(
    db: Session,
    content_id: str,
    content_type: str,
    url: str,
    title: str = None,
    thumbnail_url: str = None,
):
    content = get_content_by_id(db, content_id)
    if content:
        # 이미 콘텐츠가 있으면 제목, 썸네일이 비어있을 경우에만 업데이트
        if not content.title and title:
            content.title = title
        if not content.thumbnail_url and thumbnail_url:
            content.thumbnail_url = thumbnail_url
        db.commit()
        db.refresh(content)
        return content

    # 새 콘텐츠 생성
    content = Contents(
        content_id=content_id,
        content_type=content_type,
        transcript=None,
        youtube_url=url,  # URL 저장
        title=title,  # 제목 저장
        thumbnail_url=thumbnail_url,  # 썸네일 저장
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


def upsert_place(
    db: Session, name: str, lat: float | None, lng: float | None
) -> Places:
    """
    주어진 이름, 위도, 경도에 해당하는 장소를 데이터베이스에서 찾아 반환하거나, 없으면 새로 생성합니다.
    """
    # 이름, 위도, 경도를 모두 사용하여 장소를 조회
    place = db.query(Places).filter_by(name=name, lat=lat, lng=lng).first()

    if place:
        return place  # 장소가 존재하면 즉시 반환

    # 장소가 없으면 새로 생성
    new_place = Places(name=name, lat=lat, lng=lng)
    db.add(new_place)
    try:
        db.commit()
        db.refresh(new_place)
        return new_place
    except IntegrityError:
        # 동시성 문제 등으로 인해 다른 요청이 먼저 장소를 생성한 경우
        db.rollback()
        # 다시 조회하여 반환
        return db.query(Places).filter_by(name=name, lat=lat, lng=lng).first()


def link_content_place(db: Session, content_id: str, place_id: int):
    """
    콘텐츠와 장소를 연결하는 ContentPlaces 레코드를 생성합니다.
    이미 연결되어 있다면 아무것도 하지 않습니다.
    """
    exists = (
        db.query(ContentPlaces)
        .filter(
            ContentPlaces.content_id == content_id, ContentPlaces.place_id == place_id
        )
        .first()
    )
    if not exists:
        db.add(ContentPlaces(content_id=content_id, place_id=place_id))
        db.commit()


def create_user_content_history(db: Session, user_id: int, content_id: str):
    """
    사용자의 콘텐츠 조회 기록을 생성합니다. user_id와 content_id의 조합이 이미 존재하면 무시합니다.
    """
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


# <<< 변경: extract_and_save_locations 함수가 메타데이터를 저장하도록 수정
def extract_and_save_locations(db: Session, video_id: str, url: str) -> list[Places]:
    # 1. 외부 서비스에서 (스크립트, 장소, 제목, 썸네일) 추출
    transcript, extracted_locs, title, thumbnail_url = extract_locations_from_youtube(
        url
    )

    # 2. 콘텐츠 정보 저장 (메타데이터 포함)
    create_or_update_content(db, video_id, "youtube", url, title, thumbnail_url)

    if not transcript or not extracted_locs:
        return []

    # 3. 추출된 장소들을 DB에 저장하고 콘텐츠와 연결
    saved_places = []
    for loc in extracted_locs:
        place_obj = upsert_place(
            db, name=loc["name"], lat=loc.get("lat"), lng=loc.get("lng")
        )
        link_content_place(db, video_id, place_obj.place_id)
        saved_places.append(place_obj)

    return saved_places


# <<< 추가: 히스토리 상세 내역을 가져오는 새 함수
def get_user_history_details(db: Session, user_id: int) -> list[UserContentHistory]:
    """
    사용자의 전체 히스토리 내역을 content 및 places 정보와 함께 조회합니다.
    """
    history_records = (
        db.query(UserContentHistory)
        .filter(UserContentHistory.user_id == user_id)
        .options(
            joinedload(UserContentHistory.content).joinedload(  # content 정보 로드
                Contents.places
            )  # content에 연결된 places 정보 로드
        )
        .order_by(UserContentHistory.created_at.desc())
        .all()
    )

    return history_records


# def get_content_ids_by_user_id(db: Session, user_id: int) -> list[str]:
#     """
#     주어진 user_id에 해당하는 사용자가 요청했던 모든 content_id 목록을 조회합니다.
#     """
#     return [
#         history.content_id
#         for history in db.query(UserContentHistory)
#         .filter(UserContentHistory.user_id == user_id)
#         .all()
#     ]

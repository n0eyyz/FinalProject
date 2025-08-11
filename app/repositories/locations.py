from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from models import Contents, Places, ContentPlaces, UserContentHistory
from sqlalchemy.exc import IntegrityError
from app.db.database import AsyncSessionLocal
from app.services.extractor import extract_locations_from_youtube
from typing import List

async def get_content_by_id(db: AsyncSession, content_id: str) -> Contents | None:
    """
    주어진 content_id에 해당하는 Contents 객체를 데이터베이스에서 조회합니다.
    """
    result = await db.execute(select(Contents).filter(Contents.content_id == content_id))
    return result.scalars().first()

async def create_or_update_content(
    db: AsyncSession,
    content_id: str,
    content_type: str,
    url: str,
    title: str = None,
    thumbnail_url: str = None,
):
    content = await get_content_by_id(db, content_id)
    if content:
        if not content.title and title:
            content.title = title
        if not content.thumbnail_url and thumbnail_url:
            content.thumbnail_url = thumbnail_url
        await db.commit()
        await db.refresh(content)
        return content

    content = Contents(
        content_id=content_id,
        content_type=content_type,
        transcript=None,
        youtube_url=url,
        title=title,
        thumbnail_url=thumbnail_url,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content

async def upsert_place(
    db: AsyncSession, name: str, lat: float | None, lng: float | None
) -> Places:
    """
    주어진 이름, 위도, 경도에 해당하는 장소를 데이터베이스에서 찾아 반환하거나, 없으면 새로 생성합니다.
    """
    result = await db.execute(select(Places).filter_by(name=name, lat=lat, lng=lng))
    place = result.scalars().first()

    if place:
        return place

    new_place = Places(name=name, lat=lat, lng=lng)
    db.add(new_place)
    try:
        await db.commit()
        await db.refresh(new_place)
        return new_place
    except IntegrityError:
        await db.rollback()
        result = await db.execute(select(Places).filter_by(name=name, lat=lat, lng=lng))
        return result.scalars().first()

async def link_content_place(db: AsyncSession, content_id: str, place_id: int):
    """
    콘텐츠와 장소를 연결하는 ContentPlaces 레코드를 생성합니다.
    이미 연결되어 있다면 아무것도 하지 않습니다.
    """
    result = await db.execute(
        select(ContentPlaces).filter(
            ContentPlaces.content_id == content_id, ContentPlaces.place_id == place_id
        )
    )
    exists = result.scalars().first()
    
    if not exists:
        db.add(ContentPlaces(content_id=content_id, place_id=place_id))
        await db.commit()

async def create_user_content_history(db: AsyncSession, user_id: int, content_id: str):
    """
    사용자의 콘텐츠 조회 기록을 생성합니다. user_id와 content_id의 조합이 이미 존재하면 무시합니다.
    """
    if not user_id:
        return
    hist = UserContentHistory(user_id=user_id, content_id=content_id)
    db.add(hist)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()

async def get_places_by_content_id(db: AsyncSession, content_id: str) -> list[Places]:
    """
    콘텐츠 ID와 연결된 모든 장소 정보를 조회합니다.
    """
    result = await db.execute(
        select(Places)
        .join(ContentPlaces, ContentPlaces.place_id == Places.place_id)
        .filter(ContentPlaces.content_id == content_id)
    )
    return result.scalars().all()

from app.services.extractor import extract_locations_from_youtube
from typing import List

async def extract_and_save_locations(video_id: str, url: str) -> list[Places]:
    """
    백그라운드에서 동영상을 처리하고, 추출된 장소를 DB에 저장합니다.
    이 함수는 독립적인 DB 세션을 생성하고 관리합니다.
    """
    # `async with`를 사용하여 세션의 생명주기를 안전하게 관리합니다.
    # 이 블록이 끝나면 db 세션은 자동으로 닫힙니다.
    async with AsyncSessionLocal() as db:
        transcript, extracted_locs, title, thumbnail_url = extract_locations_from_youtube(
            url
        )

        await create_or_update_content(db, video_id, "youtube", url, title, thumbnail_url)

        if not transcript or not extracted_locs:
            return []

        saved_places = []
        for loc in extracted_locs:
            place_obj = await upsert_place(
                db, name=loc["name"], lat=loc.get("lat"), lng=loc.get("lng")
            )
            await link_content_place(db, video_id, place_obj.place_id)
            saved_places.append(place_obj)

        return saved_places

async def get_user_history_details(db: AsyncSession, user_id: int) -> list[UserContentHistory]:
    """
    사용자의 전체 히스토리 내역을 content 및 places 정보와 함께 조회합니다.
    """
    result = await db.execute(
        select(UserContentHistory)
        .filter(UserContentHistory.user_id == user_id)
        .options(
            joinedload(UserContentHistory.content).joinedload(
                Contents.places
            )
        )
        .order_by(UserContentHistory.created_at.desc())
    )
    return result.scalars().all()
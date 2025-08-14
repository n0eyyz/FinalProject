from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from models import Contents, Places, ContentPlaces, UserContentHistory
from sqlalchemy.exc import IntegrityError
from typing import List

async def get_content_by_id(db: AsyncSession, content_id: str) -> Contents | None:
    result = await db.execute(select(Contents).filter(Contents.content_id == content_id))
    return result.scalars().first()

async def create_or_update_content(
    db: AsyncSession,
    content_id: str,
    content_type: str,
    url: str,
    transcript: str | None,
    title: str = None,
    thumbnail_url: str = None,
):
    content = await get_content_by_id(db, content_id)
    if content:
        if not content.title and title:
            content.title = title
        if not content.thumbnail_url and thumbnail_url:
            content.thumbnail_url = thumbnail_url
        if not content.transcript and transcript:
            content.transcript = transcript
        await db.commit()
        await db.refresh(content)
        return content

    new_content = Contents(
        content_id=content_id,
        content_type=content_type,
        transcript=transcript,
        youtube_url=url,
        title=title,
        thumbnail_url=thumbnail_url,
    )
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)
    return new_content

async def upsert_place(
    db: AsyncSession, name: str, lat: float | None, lng: float | None
) -> Places:
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
    result = await db.execute(
        select(ContentPlaces).filter(
            ContentPlaces.content_id == content_id, ContentPlaces.place_id == place_id
        )
    )
    exists = result.scalars().first()
    
    if not exists:
        db.add(ContentPlaces(content_id=content_id, place_id=place_id))
        await db.commit()

async def save_extracted_data(
    db: AsyncSession,
    video_id: str,
    url: str,
    transcript: str | None,
    locations: list,
    title: str | None,
    thumbnail_url: str | None,
) -> list[Places]:
    """
    추출된 콘텐츠, 장소 및 관련 데이터를 데이터베이스에 저장하고 연결합니다.
    """
    await create_or_update_content(
        db, video_id, "youtube", url, transcript, title, thumbnail_url
    )

    if not locations:
        return []

    saved_places = []
    for loc in locations:
        if not isinstance(loc, dict):
            continue
        
        place_obj = await upsert_place(
            db, name=loc.get("name"), lat=loc.get("lat"), lng=loc.get("lng")
        )
        if place_obj:
            await link_content_place(db, video_id, place_obj.place_id)
            saved_places.append(place_obj)

    return saved_places

async def create_user_content_history(db: AsyncSession, user_id: int, content_id: str):
    print(f"[Repo] create_user_content_history 호출됨: user_id={user_id}, content_id={content_id}")
    if not user_id:
        print("[Repo] user_id가 없어 create_user_content_history 건너뜀.")
        return
    hist = UserContentHistory(user_id=user_id, content_id=content_id)
    db.add(hist)
    try:
        await db.commit()
        print(f"[Repo] UserContentHistory 성공적으로 저장됨: user_id={user_id}, content_id={content_id}")
    except IntegrityError as e:
        await db.rollback()
        print(f"[Repo] UserContentHistory 저장 중 IntegrityError 발생: {e}")
        print(f"[Repo] 롤백됨. user_id={user_id}, content_id={content_id}")

async def get_places_by_content_id(db: AsyncSession, content_id: str) -> list[Places]:
    result = await db.execute(
        select(Places)
        .join(ContentPlaces, ContentPlaces.place_id == Places.place_id)
        .filter(ContentPlaces.content_id == content_id)
    )
    return result.scalars().all()

async def get_user_history_details(db: AsyncSession, user_id: int) -> list[UserContentHistory]:
    result = await db.execute(
        select(UserContentHistory)
        .filter(UserContentHistory.user_id == user_id)
        .options(
            joinedload(UserContentHistory.content).joinedload(
                Contents.places
            )
        )
        .order_by(UserContentHistory.created_at.desc())
        .limit(50)
    )
    return result.unique().scalars().all()
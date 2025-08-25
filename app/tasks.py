from app.utils.url import extract_video_id
from app.services.extractor import ExtractorService
from app.repositories.locations import save_extracted_data
from app.db.database import AsyncSessionLocal
import asyncio

from app.repositories.locations import create_user_content_history


async def process_youtube_url_with_websocket(
    url: str, user_id: int | None = None, connection_id: str | None = None, manager=None
):
    """
    WebSocket을 통해 실시간 진행 상황을 전송하며 YouTube URL을 처리합니다.
    """
    print(
        f"[WebSocket Processing] 🚀 작업 시작! (URL: {url}, User ID: {user_id}, Connection: {connection_id})"
    )

    video_id = extract_video_id(url)
    if not video_id:
        print(f"[WebSocket Processing] ❌ 유효하지 않은 URL: {url}")
        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {
                    "status": "error",
                    "message": "invalid youtube url",
                    "progress": 0,
                },
            )
        return {"status": "Failure", "message": "Invalid YouTube URL"}

    try:
        # 캐시 확인
        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {"status": "processing", "message": "checking url ...", "progress": 10},
            )

        async with AsyncSessionLocal() as db:
            # 캐시 확인
            from app.repositories.locations import (
                get_content_by_id,
                get_places_by_content_id,
            )

            existing_content = await get_content_by_id(db, video_id)

            if existing_content:
                print(f"[WebSocket Processing] 📋 캐시된 데이터 발견: {video_id}")
                if manager and connection_id:
                    await manager.send_progress(
                        connection_id,
                        {
                            "status": "processing",
                            "message": "almost done...",
                            "progress": 90,
                        },
                    )

                if user_id:
                    await create_user_content_history(db, user_id, video_id)

                places = await get_places_by_content_id(db, video_id)
                result = {
                    "status": "Completed",
                    "source_url": url,
                    "title": existing_content.title,
                    "mode": "cached",
                    "places": [
                        {"name": p.name, "lat": p.lat, "lng": p.lng} for p in places
                    ],
                }
                return result

        # 새로운 처리 시작
        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {"status": "processing", "message": "analyzing url...", "progress": 20},
            )

        extractor_service = ExtractorService()

        # 메타데이터 및 스크립트 추출
        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {
                    "status": "processing",
                    "message": "understanding video ...",
                    "progress": 40,
                },
            )

        transcript, locations, title, thumbnail_url = (
            await extractor_service.extract_data_from_youtube(url)
        )

        # AI 위치 분석
        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {
                    "status": "processing",
                    "message": "amazing locations ...",
                    "progress": 70,
                },
            )

        # 데이터베이스 저장
        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {"status": "processing", "message": "saving ...", "progress": 90},
            )

        async with AsyncSessionLocal() as db:
            saved_places = await save_extracted_data(
                db, video_id, url, transcript, locations, title, thumbnail_url
            )

            if user_id:
                print(
                    f"[WebSocket Processing] 📝 사용자 기록 저장: user_id={user_id}, video_id={video_id}"
                )
                await create_user_content_history(db, user_id, video_id)

        print(f"[WebSocket Processing] ✅ 작업 성공!")
        return {
            "status": "Completed",
            "source_url": url,
            "title": title,
            "mode": "new",
            "places": [
                {"name": p.name, "lat": p.lat, "lng": p.lng} for p in saved_places
            ],
        }

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        error_message = f"{type(e).__name__}: {e}\n{error_traceback}"
        print(f"[WebSocket Processing] ❌ 작업 실패!, 오류: {error_message}")

        if manager and connection_id:
            await manager.send_progress(
                connection_id,
                {
                    "status": "error",
                    "message": f"there is error!: {str(e)}",
                    "progress": 0,
                },
            )
        raise


from sqlalchemy.ext.asyncio import AsyncSession

async def process_youtube_url(db: AsyncSession, url: str, user_id: int | None = None):
    """
    YouTube URL을 받아 비동기적으로 영상 정보를 추출하고, 위치 정보를 분석하여 DB에 저장합니다.
    """
    print(f"[Processing] 🚀 작업 시작! (URL: {url}, User ID: {user_id})")

    video_id = extract_video_id(url)
    if not video_id:
        print(f"[Processing] ❌ 유효하지 않은 URL: {url}")
        return {"status": "Failure", "message": "Invalid YouTube URL"}

    try:
        extractor_service = ExtractorService()
        transcript, locations, title, thumbnail_url = (
            await extractor_service.extract_data_from_youtube(url)
        )

        # 만약 추출된 장소가 없다면, DB에 저장하지 않고 바로 반환
        if not locations:
            print("[Processing] ✅ 추출된 장소가 없어 처리를 완료합니다. (DB 저장 안함)")
            return {
                'status': 'Completed',
                'source_url': url,
                'title': title,
                'places': [] # 빈 리스트 반환
            }

        # 장소가 있는 경우에만 DB에 저장
        saved_places = await save_extracted_data(
            db, video_id, url, transcript, locations, title, thumbnail_url
        )

        if user_id:
            print(
                f"[Processing] 📝 사용자 기록 저장 시도: user_id={user_id}, video_id={video_id}"
            )
            await create_user_content_history(db, user_id, video_id)

        print(f"[Processing] ✅ 작업 성공!")
        return {
            "status": "Completed",
            "source_url": url,
            "title": title,
            "places": [
                {"name": p.name, "lat": p.lat, "lng": p.lng} for p in saved_places
            ],
        }

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        error_message = f"{type(e).__name__}: {e}\n{error_traceback}"
        print(f"[Processing] ❌ 작업 실패!, 오류: {error_message}")
        # Re-raise the exception to be handled by the caller (the API route)
        raise



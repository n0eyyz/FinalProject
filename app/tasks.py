from app.utils.url import extract_video_id
from app.services.extractor import ExtractorService
from app.repositories.locations import save_extracted_data
from app.db.database import AsyncSessionLocal
import asyncio

from app.repositories.locations import create_user_content_history


async def process_youtube_url(url: str, user_id: int | None = None):
    """
    YouTube URL을 받아 비동기적으로 영상 정보를 추출하고, 위치 정보를 분석하여 DB에 저장합니다.
    """
    print(f"[Processing] 🚀 작업 시작! (URL: {url}, User ID: {user_id})")

    video_id = extract_video_id(url)
    if not video_id:
        print(f"[Processing] ❌ 유효하지 않은 URL: {url}")
        # Since this is no longer a Celery task, we can't update state.
        # We should raise an exception or return an error.
        # For now, we'll return a failure message.
        return {'status': 'Failure', 'message': 'Invalid YouTube URL'}

    try:
        # The ExtractorService might need to be refactored if it uses the task instance.
        # Looking at its previous usage, it was passed `self`. Let's assume
        # it was used for updating state, and now can be instantiated without it.
        extractor_service = ExtractorService() # Refactored: removed task instance
        transcript, locations, title, thumbnail_url = await extractor_service.extract_data_from_youtube(url)

        async with AsyncSessionLocal() as db:
            saved_places = await save_extracted_data(
                db, video_id, url, transcript, locations, title, thumbnail_url
            )

            if user_id:
                print(f"[Processing] 📝 사용자 기록 저장 시도: user_id={user_id}, video_id={video_id}")
                await create_user_content_history(db, user_id, video_id)
        
        print(f"[Processing] ✅ 작업 성공!")
        return {
            'status': 'Completed',
            'source_url': url,
            'title': title,
            'places': [{'name': p.name, 'lat': p.lat, 'lng': p.lng} for p in saved_places]
        }

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"{type(e).__name__}: {e}\n{error_traceback}"
        print(f"[Processing] ❌ 작업 실패!, 오류: {error_message}")
        # Re-raise the exception to be handled by the caller (the API route)
        raise

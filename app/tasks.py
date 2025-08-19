from .celery_config import celery_app
from app.utils.url import extract_video_id
from app.services.extractor import ExtractorService
from app.repositories.locations import save_extracted_data
from app.db.database import AsyncSessionLocal
import asyncio

from app.repositories.locations import create_user_content_history

@celery_app.task(bind=True)
def process_youtube_url(self, url: str, user_id: int | None = None):
    """
    YouTube URL을 받아 비동기적으로 영상 정보를 추출하고, 위치 정보를 분석하여 DB에 저장합니다.
    """
    job_id = self.request.id
    print(f"[Worker] 🚀 작업 시작! (Job ID: {job_id}, URL: {url}, User ID: {user_id})")

    video_id = extract_video_id(url)
    if not video_id:
        print(f"[Worker] ❌ 유효하지 않은 URL: {url}")
        self.update_state(state='FAILURE', meta={'error_message': 'Invalid YouTube URL'})
        return {'status': 'Failure', 'message': 'Invalid YouTube URL'}

    async def _run_async_processing():
        """Celery 동기 태스크 내에서 비동기 로직을 실행하기 위한 래퍼 함수"""
        try:
            # 0-20%: YouTube URL 유효성 검사, 비디오 메타데이터 추출
            self.update_state(
                state='PROGRESS',
                meta={'current_step': 'YouTube URL 유효성 검사 및 초기화 중...', 'progress': 10}
            )
            
            extractor_service = ExtractorService(self)
            transcript, locations, title, thumbnail_url = await extractor_service.extract_data_from_youtube(url)

            # 70-90%: 데이터베이스 저장 준비
            self.update_state(
                state='PROGRESS',
                meta={'current_step': '추출된 데이터 데이터베이스 저장 준비 중...', 'progress': 80}
            )
            async with AsyncSessionLocal() as db:
                saved_places = await save_extracted_data(
                    db, video_id, url, transcript, locations, title, thumbnail_url
                )

                # 사용자 기록 저장 (콘텐츠 저장이 완료된 후에만)
                # 사용자 기록 저장 (콘텐츠 저장이 완료된 후에만)
                if user_id:
                    print(f"[Worker] 📝 사용자 기록 저장 시도: user_id={user_id}, video_id={video_id}")
                    await create_user_content_history(db, user_id, video_id)
            
            # 90-100%: 데이터베이스 저장 및 최종 결과 준비
            self.update_state(
                state='PROGRESS',
                meta={'current_step': '데이터베이스 저장 완료 및 최종 결과 준비 중...', 'progress': 95}
            )
            
            print(f"[Worker] ✅ 작업 성공! (Job ID: {job_id})")
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
            print(f"[Worker] ❌ 작업 실패! (Job ID: {job_id}), 오류: {error_message}")
            
            # Celery가 예외 정보를 올바르게 저장하도록 task.result를 설정
            
            raise

    # Celery의 동기 컨텍스트에서 비동기 함수를 실행
    # try:
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop()
    #     try:
    #         return loop.run_until_complete(_run_async_processing)
    #     finally:
    #         pending = asyncio.all_tasks(loop)
    #         if pending:
    #             loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    # finally:
    #     asyncio.set_event_loop(None)
    return asyncio.run(_run_async_processing())
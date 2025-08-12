from .celery_config import celery_app
from app.utils.url import extract_video_id
from app.services.extractor import ExtractorService
from app.repositories.locations import save_extracted_data
from app.db.database import AsyncSessionLocal
import asyncio

@celery_app.task(bind=True)
def process_youtube_url(self, url: str):
    """
    YouTube URL을 받아 비동기적으로 영상 정보를 추출하고, 위치 정보를 분석하여 DB에 저장합니다.
    """
    job_id = self.request.id
    print(f"[Worker] 🚀 작업 시작! (Job ID: {job_id}, URL: {url})")

    video_id = extract_video_id(url)
    if not video_id:
        print(f"[Worker] ❌ 유효하지 않은 URL: {url}")
        self.update_state(state='FAILURE', meta={'error_message': 'Invalid YouTube URL'})
        return {'status': 'Failure', 'message': 'Invalid YouTube URL'}

    async def _run_async_processing():
        """Celery 동기 태스크 내에서 비동기 로직을 실행하기 위한 래퍼 함수"""
        try:
            # 1. 초기화 및 추출 단계
            self.update_state(
                state='PROGRESS',
                meta={'current_step': 'Extracting video data...', 'progress': 20}
            )
            extractor_service = ExtractorService()
            transcript, locations, title, thumbnail_url = await extractor_service.extract_data_from_youtube(url)

            # 2. 데이터베이스 저장 단계
            self.update_state(
                state='PROGRESS',
                meta={'current_step': 'Saving data to database...', 'progress': 70}
            )
            async with AsyncSessionLocal() as db:
                saved_places = await save_extracted_data(
                    db, video_id, url, transcript, locations, title, thumbnail_url
                )
            
            print(f"[Worker] ✅ 작업 성공! (Job ID: {job_id})")
            return {
                'status': 'Completed',
                'source_url': url,
                'title': title,
                'places': [{'name': p.name, 'lat': p.lat, 'lng': p.lng} for p in saved_places]
            }

        except Exception as e:
            print(f"[Worker] ❌ 작업 실패! (Job ID: {job_id}), 오류: {e}")
            self.update_state(
                state='FAILURE',
                meta={'current_step': 'Error', 'progress': 0, 'error_message': str(e)}
            )
            # 에러를 다시 발생시켜 Celery가 실패로 인지하도록 함
            raise

    # Celery의 동기 컨텍스트에서 비동기 함수를 실행
    return asyncio.run(_run_async_processing())
from .celery_config import celery_app
import time

@celery_app.task(bind=True)
def process_video_placeholder(self, url: str):
    """
    긴 비디오 처리 작업을 흉내 내는 기본 태스크입니다.
    `bind=True`는 self 인자를 통해 태스크의 상태를 업데이트하고 컨텍스트에 접근할 수 있게 합니다.
    """
    job_id = self.request.id
    print(f"[Worker] 🚀 작업 시작! (Job ID: {job_id}, URL: {url})")
    try:
        # 1. 초기화 단계
        print(f"[Worker] (Job ID: {job_id}) -> 1. 초기화 단계 진입")
        self.update_state(
            state='PROGRESS',
            meta={'current_step': 'Initializing', 'progress': 10, 'url': url}
        )
        time.sleep(3)

        # 2. 다운로드 및 분석 단계
        print(f"[Worker] (Job ID: {job_id}) -> 2. 분석 단계 진입")
        self.update_state(
            state='PROGRESS',
            meta={'current_step': 'Analyzing Video', 'progress': 50}
        )
        time.sleep(5)

        # 3. 후처리 단계
        print(f"[Worker] (Job ID: {job_id}) -> 3. 최종 처리 단계 진입")
        self.update_state(
            state='PROGRESS',
            meta={'current_step': 'Finalizing', 'progress': 90}
        )
        time.sleep(2)

        print(f"[Worker] ✅ 작업 성공! (Job ID: {job_id})")
        # 최종 결과 반환
        return {
            'status': 'Completed',
            'source_url': url,
            'places': [
                {'name': '서울역', 'lat': 37.5547, 'lng': 126.9704},
                {'name': 'N서울타워', 'lat': 37.5512, 'lng': 126.9882}
            ],
            'processing_time': 10.0
        }
    except Exception as e:
        print(f"[Worker] ❌ 작업 실패! (Job ID: {job_id}), 오류: {e}")
        # 실패 시 상태 업데이트
        self.update_state(
            state='FAILURE',
            meta={'current_step': 'Error', 'progress': 0, 'error_message': str(e)}
        )
        # Celery가 에러를 인지하도록 예외를 다시 발생시킵니다.
        raise

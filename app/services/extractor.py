import asyncio
from crawlers.youtube import get_transcript_from_youtube
from nlp.gemini_location import GeminiService

class ExtractorService:
    """
    YouTube 영상에서 스크립트와 위치 정보를 비동기적으로 추출하는 서비스입니다.
    - 동기적인 크롤러 함수를 논블로킹 방식으로 실행합니다.
    - 비동기적인 Gemini 서비스를 호출합니다.
    """
    def __init__(self, task_instance=None):
        self.task_instance = task_instance
        self.gemini_service = GeminiService(task_instance)

    async def extract_data_from_youtube(self, youtube_url: str) -> tuple[str | None, list, str | None, str | None]:
        """
        YouTube URL에서 (스크립트, 장소 목록, 제목, 썸네일) 정보를 비동기적으로 추출하여 반환합니다.
        """
        print(f"➡️ ExtractorService: '{youtube_url}' 처리를 시작합니다.")
        
        if self.task_instance:
            self.task_instance.update_state(
                state='PROGRESS',
                meta={'current_step': 'YouTube 비디오 메타데이터 추출 및 스크립트 다운로드 중...', 'progress': 20}
            )

        # 1. 동기적인 크롤러 함수를 별도 스레드에서 실행하여 논블로킹으로 만듭니다.
        print("➡️ YouTube 크롤러를 논블로킹으로 실행합니다...")
        transcript, title, thumbnail_url = await asyncio.to_thread(
            get_transcript_from_youtube, youtube_url
        )
        print("✅ YouTube 크롤러 작업 완료.")

        if self.task_instance:
            self.task_instance.update_state(
                state='PROGRESS',
                meta={'current_step': '비디오 내용 다운로드 및 전처리 완료.', 'progress': 40}
            )

        if not transcript:
            print("⚠️ 스크립트가 없어 위치 추출을 건너뜁니다.")
            if self.task_instance:
                self.task_instance.update_state(
                    state='PROGRESS',
                    meta={'current_step': '스크립트 없음. 위치 추출 건너뜀.', 'progress': 70}
                )
            return None, [], title, thumbnail_url

        # 2. 비동기 Gemini 서비스를 호출합니다.
        if self.task_instance:
            self.task_instance.update_state(
                state='PROGRESS',
                meta={'current_step': 'AI 모델을 통한 위치 정보 추출 및 분석 중...', 'progress': 40}
            )
        locations = await self.gemini_service.extract_locations_from_transcript(transcript)
        
        if self.task_instance:
            self.task_instance.update_state(
                state='PROGRESS',
                meta={'current_step': '위치 정보 추출 및 분석 완료.', 'progress': 70}
            )
        
        print(f"✅ ExtractorService: '{youtube_url}' 처리 완료.")
        return transcript, locations, title, thumbnail_url
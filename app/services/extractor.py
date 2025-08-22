import asyncio
from crawlers.youtube import get_youtube_metadata, get_youtube_transcript_only
from nlp.gemini_location import GeminiService

class ExtractorService:
    """
    YouTube 영상에서 스크립트와 위치 정보를 비동기적으로 추출하는 서비스입니다.
    - 동기적인 크롤러 함수를 논블로킹 방식으로 실행합니다.
    - 비동기적인 Gemini 서비스를 호출합니다.
    """
    def __init__(self):
        self.gemini_service = GeminiService()

    async def extract_data_from_youtube(self, youtube_url: str) -> tuple[str | None, list, str | None, str | None]:
        """
        YouTube URL에서 (스크립트, 장소 목록, 제목, 썸네일) 정보를 비동기적으로 추출하여 반환합니다.
        """
        print(f"➡️ ExtractorService: '{youtube_url}' 처리를 시작합니다.")
        
        # 1. 메타데이터와 스크립트 추출을 동시에 시작합니다.
        print("➡️ YouTube 메타데이터 및 스크립트 추출을 논블로킹으로 실행합니다...")
        metadata_task = asyncio.to_thread(get_youtube_metadata, youtube_url)
        transcript_task = get_youtube_transcript_only(youtube_url)

        # 두 작업을 동시에 기다립니다.
        (title, thumbnail_url), transcript = await asyncio.gather(metadata_task, transcript_task)
        
        print("✅ YouTube 메타데이터 및 스크립트 추출 작업 완료.")

        if not transcript:
            print("⚠️ 스크립트가 없어 위치 추출을 건너뜁니다.")
            return None, [], title, thumbnail_url

        # 2. 비동기 Gemini 서비스를 호출합니다.
        locations = await self.gemini_service.extract_locations_from_transcript(transcript)
        
        print(f"✅ ExtractorService: '{youtube_url}' 처리 완료.")
        return transcript, locations, title, thumbnail_url
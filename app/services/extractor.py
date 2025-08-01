from crawlers.youtube import get_transcript_from_youtube
from nlp.gemini_location import extract_locations_with_gemini


# <<< 변경: 반환 타입을 튜플로 명시
def extract_locations_from_youtube(
    youtube_url: str,
) -> tuple[str, list[dict], str, str]:
    """
    YouTube URL에서 (스크립트, 장소, 제목, 썸네일) 정보를 추출하여 반환합니다.
    """
    # <<< 변경: 제목과 썸네일을 함께 받음
    transcript, title, thumbnail_url = get_transcript_from_youtube(youtube_url)

    if not transcript:
        # 스크립트가 없어도 제목, 썸네일은 있을 수 있으므로 반환
        return None, [], title, thumbnail_url

    locs_dict = extract_locations_with_gemini(transcript)
    if isinstance(locs_dict, dict):
        locations = locs_dict.get("locations", [])
    else:
        locations = locs_dict

    return transcript, locations, title, thumbnail_url

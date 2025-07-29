from crawlers.youtube import get_transcript_from_youtube
from nlp.gemini_location import extract_locations_with_gemini

def extract_locations_from_youtube(youtube_url: str) -> tuple[str, list[dict]]:
    """
    YouTube URL에서 스크립트를 추출하고, 해당 스크립트에서 장소 정보를 추출하여 반환합니다.
    스크립트 추출에 실패하거나 장소 정보가 없으면 빈 리스트를 반환합니다.
    """
    transcript = get_transcript_from_youtube(youtube_url)
    if not transcript:
        return None, []
    locs_dict = extract_locations_with_gemini(transcript)  # {"locations": [...] } or list
    if isinstance(locs_dict, dict):
        locations = locs_dict.get("locations", [])
    else:
        locations = locs_dict
    return transcript, locations

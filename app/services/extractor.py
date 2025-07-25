from crawlers.youtube import get_transcript_from_youtube
from nlp.gemini_location import extract_locations_with_gemini

def extract_locations_from_youtube(youtube_url: str) -> tuple[str, list[dict]]:
    transcript = get_transcript_from_youtube(youtube_url)
    if not transcript:
        return None, []
    locs_dict = extract_locations_with_gemini(transcript)  # {"locations": [...] } or list
    if isinstance(locs_dict, dict):
        locations = locs_dict.get("locations", [])
    else:
        locations = locs_dict
    return transcript, locations

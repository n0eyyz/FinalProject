from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str | None:
    """
    주어진 YouTube URL에서 비디오 ID를 추출하여 반환합니다.
    유효한 비디오 ID를 찾을 수 없으면 None을 반환합니다.
    """
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/")
    qs = parse_qs(parsed.query)
    return qs.get("v", [None])[0]

from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/")
    qs = parse_qs(parsed.query)
    return qs.get("v", [None])[0]

import os
import openai
import google.generativeai as genai
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from urllib.parse import urlparse
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from nlp.gemini_location import extract_locations_with_gemini
from crawlers.youtube import get_transcript_from_youtube
from crawlers.instagram import extract_instagram_text
from crawlers.screenshot_ocr import capture_and_ocr
from sqlalchemy.orm import Session
# from database import get_db

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- 1. 설정: 환경 변수에서 API 키와 유튜브 링크를 가져옵니다. ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# API 키가 설정되지 않았을 경우 오류 메시지를 출력하고 종료
if not OPENAI_API_KEY or not GOOGLE_API_KEY:
    raise ValueError("오류: .env 파일에 OPENAI_API_KEY와 GOOGLE_API_KEY를 설정해주세요.")

# 권한 설정 (개발 중에만 전체 허용)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 클라이언트 설정
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)

# 디버깅 전용 (실패 시 로그 저장)
def _save_debug_page(driver, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"🔍 디버깅용 페이지 소스를 {filename}로 저장했습니다.")
    except Exception:
        pass


# 인스타 링크가 예외적으로 쿼리 파라미터가 붙은 채 전송되는 경우
# def clean_instagram_url(url):
#     parsed = urlparse(url)
#     return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
# -> 이후 엔드포인트에서
# insta_url = clean_instagram_url(insta_url) 추가해주세요.

@app.post("/extract-ylocations")
async def extract_ylocations(request: Request):
    data = await request.json()
    youtube_url = data.get("youtube_url")
    print(youtube_url)
    script = get_transcript_from_youtube(youtube_url)
    if not script:
        return JSONResponse({"error": "유튜브에서 텍스트 추출 실패"}, status_code=500)
    locations = extract_locations_with_gemini(script)
    if not locations:
        return JSONResponse({"error": "장소 추출 실패"}, status_code=500)
    return JSONResponse(locations)

@app.get("/extract-location-test")
async def extract_location_test():
    """
    집가고싶어요
    """
    file_path = "data.json"
    return FileResponse(path=file_path, media_type='application/json', filename="data.json")

# @app.get("/location-info")
# def location_info(db: Session = Depends(get_db)):
#     try:
#         db.execute("SELECT 1")
#         return {"status": "connected"}
#     except Exception as e:
#         return {"status": "error", "detail": str(e)}




# @app.post("/extract-ilocations/")
# async def extract_ilocations(request: Request):
#     data = await request.json()
#     insta_url = data.get("insta_url")
#     text = extract_instagram_text(insta_url)
#     if not text:
#         return JSONResponse({"error": "인스타그램에서 텍스트 추출에 실패했습니다."}, status_code=500)
#     locations = extract_locations_with_gemini(text)
#     if not locations:
#         return JSONResponse({"error": "장소 추출에 실패했습니다."}, status_code=500)
#     return JSONResponse({"insta_url": insta_url, "locations": locations})

# @app.post("/screenshot-ocr/")
# async def screenshot_ocr():
#     """
#     현재 PC 화면을 캡처해서 OCR로 텍스트를 추출, JSON으로 반환합니다.
#     """
#     texts = capture_and_ocr()
#     return JSONResponse({"ocr_texts": texts})

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=9000, reload=True, reload_dirs=["."])

import os
import json
import openai
import google.generativeai as genai
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

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

def get_transcript_from_youtube(video_url: str) -> str:
    """
    유튜브 영상에서 텍스트 스크립트를 추출합니다.
    자막이 없을 경우, 음원을 다운받아 STT를 수행하며, 파일 크기가 25MB를 넘으면 분할하여 처리합니다.
    """
    try:
        video_id = video_url.split("v=")[1].split("&")[0]
        print(f"✅ 영상 ID '{video_id}'의 자막 추출을 시도합니다.")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        full_transcript = " ".join([item['text'] for item in transcript_list])
        print("✅ 'youtube-transcript-api'를 통해 자막을 성공적으로 가져왔습니다.")
        return full_transcript
    except Exception as e:
        print(f"⚠️ 자막을 찾을 수 없습니다 ({e}). 음원 추출 및 STT를 시작합니다.")
        try:
            output_filename = "temp_audio.m4a"
            print(f"➡️ 'yt-dlp'로 음원을 다운로드합니다...")
            subprocess.run(
                ["yt-dlp", "-x", "--audio-format", "m4a", "-o", output_filename, video_url],
                check=True, capture_output=True
            )
            print("✅ 음원 다운로드 완료.")

            # --- 오디오 파일 분할 처리 로직 ---
            file_size = os.path.getsize(output_filename)
            WHISPER_API_LIMIT = 25 * 1024 * 1024  # 25MB

            if file_size < WHISPER_API_LIMIT:
                print("➡️ 파일 크기가 작아 분할 없이 처리합니다.")
                with open(output_filename, "rb") as audio_file:
                    transcription = openai.audio.transcriptions.create(model="whisper-1", file=audio_file)
                full_text = transcription.text
            else:
                print(f"⚠️ 파일 크기({file_size / 1024 / 1024:.2f}MB)가 25MB를 초과하여 분할 처리를 시작합니다.")
                audio = AudioSegment.from_file(output_filename)
                # 10분(600,000ms) 단위로 자르기
                chunk_length_ms = 10 * 60 * 1000
                chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
                
                full_text = ""
                for i, chunk in enumerate(chunks):
                    chunk_filename = f"temp_chunk_{i}.m4a"
                    print(f"➡️ {i+1}/{len(chunks)}번째 조각 처리 중...")
                    chunk.export(chunk_filename, format="mp4") # m4a는 mp4 컨테이너 사용
                    with open(chunk_filename, "rb") as chunk_file:
                        transcription = openai.audio.transcriptions.create(model="whisper-1", file=chunk_file)
                        full_text += transcription.text + " "
                    os.remove(chunk_filename)
            
            os.remove(output_filename) # 원본 오디오 파일 삭제
            print("✅ Whisper STT 변환 완료.")
            return full_text

        except subprocess.CalledProcessError as e_dlp:
            print(f"❌ yt-dlp 음원 다운로드 중 오류 발생: {e_dlp.stderr.decode()}")
            return None
        except Exception as e_whisper:
            print(f"❌ Whisper 처리 중 오류 발생: {e_whisper}")
            return None
        
def extract_locations_with_gemini(transcript: str) -> list:
    """
    Gemini API를 사용하여 텍스트에서 장소 이름과 좌표를 추출합니다.
    """
    if not transcript:
        print("⚠️ 처리할 텍스트가 없어 장소 추출을 건너뜁니다.")
        return []

    print("➡️ Gemini API로 장소 및 좌표 추출을 시작합니다.")
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # --- 여기부터가 개선된 영문 프롬프트입니다 ---
    prompt = f"""
    You are an expert AI specializing in analyzing YouTube food vlogs to extract restaurant and cafe names.
    Your task is to identify all the specific names of places like restaurants, cafes, bakeries, and food stalls that the vlogger visits or mentions in the provided script.

    **Instructions:**
    1.  Focus only on specific, proper names of establishments (e.g., "Fengmi Bunsik", "Cafe Waileddeog").
    2.  Exclude general locations like "Yaksu-dong" or "near Yaksu Station" unless they are part of a specific store name. Do not extract addresses.
    3.  Exclude names of people or general items. For example, if the text says "I met Cheolsu at the market", do not extract "Cheolsu".
    4.  Return the results as a JSON array of objects. Each object must contain "name", "lat", and "lng" keys.
    5.  If you cannot find the precise coordinates for a place on Google Maps, exclude it from the list.
    6.  The final output must be only the JSON array, with no other text or explanations.

    **Example:**
    Text: "First, I went to Gold Pâtisserie for some bread, then had lunch at a place called Daehan Gukbap. It was great."
    Correct Output:
    [
        {{"name": "Gold Pâtisserie", "lat": 37.5, "lng": 127.0}},
        {{"name": "Daehan Gukbap", "lat": 37.5, "lng": 127.0}}
    ]

    **Now, analyze the following text:**
    ---
    Text: "{transcript}"
    ---
    JSON Result:
    """
    # --- 프롬프트는 여기까지입니다 ---
    
    response = None
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip().lstrip('```json').rstrip('```')
        locations = json.loads(result_text)
        print("✅ Gemini 장소 추출 완료.")
        return locations
    except Exception as e:
        print(f"❌ Gemini API 처리 중 오류 발생: {e}")
        if response:
            print(f"받은 응답: {response.text}")
        return []



class YoutubeUrlRequest(BaseModel):
    youtube_url: str

@app.post("/extract-locations")
async def extract_locations(request: YoutubeUrlRequest):
    """
    프론트에서 { "youtube_url": "..." } 형태로 요청을 보내면
    장소명/위도/경도 json을 리턴
    """
    youtube_url = request.youtube_url
    if not youtube_url:
        return JSONResponse({"error": "youtube_url 필수"}, status_code=400)
    
    # 스크립트 추출
    script = get_transcript_from_youtube(youtube_url)
    if not script:
        return JSONResponse({"error": "유튜브에서 텍스트 추출 실패"}, status_code=500)
    
    # 장소 추출
    locations = extract_locations_with_gemini(script)
    if not locations:
        return JSONResponse({"error": "장소 추출 실패"}, status_code=500)
    
    # 최종 json 응답
    return {"youtube_url": youtube_url, "locations": locations}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)


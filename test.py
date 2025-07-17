import os
import subprocess
import requests
import json
from transformers import pipeline
from google.cloud import language_v1
import torch
from dotenv import load_dotenv


load_dotenv(override=True)
print(os.getenv('OPENAI_API_KEY'))
print(os.getenv('OPENAI_AUDIO_MODEL'))
print(os.getenv('GOOGLE_MAPS_API_KEY'))
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')


def download_youtube_audio(youtube_url, output_path="audio.mp3"):
    subprocess.run([
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", output_path,
        youtube_url
    ], check=True)

# def transcribe_audio_with_whisper(audio_path, model_name="openai/whisper-large-v3", language="ko"):
#     pipe = pipeline(
#         "automatic-speech-recognition",
#         model=model_name,
#         device="cuda" if torch.cuda.is_available() else "cpu"
#     )
#     result = pipe(audio_path, generate_kwargs={"task": "transcribe", "language": language})
#     return result["text"]

MODEL_NAME = os.getenv("OPENAI_AUDIO_MODEL", "openai/whisper-small")

def transcribe_audio_with_whisper(audio_path, model_name=MODEL_NAME, language="ko"):
    from transformers import pipeline
    import torch

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model_name,   # 환경변수에서 불러온 모델명 사용
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    result = pipe(
        audio_path,
        generate_kwargs={"task": "transcribe", "language": language},
        return_timestamps=True
    )
    return result["text"]


def extract_places_with_gcp_nlp(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    entities = client.analyze_entities(request={'document': document}).entities
    places = [entity.name for entity in entities if language_v1.Entity.Type(entity.type_).name == "LOCATION"]
    return list(set(places))

def geocode_place(place):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": place, "key": GOOGLE_MAPS_API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            loc = results[0]['geometry']['location']
            return {"place": place, "lat": loc['lat'], "lng": loc['lng']}
    return {"place": place, "lat": None, "lng": None}

def main():
    youtube_url = input("유튜브 영상 링크를 입력하세요: ")
    audio_file = "audio.mp3"

    print("1. 오디오 다운로드 중...")
    download_youtube_audio(youtube_url, audio_file)

    print("2. Whisper로 음성 텍스트 변환 중...")
    text = transcribe_audio_with_whisper(audio_file, model_name="openai/whisper-small", language="ko")
    print("\n[Whisper 텍스트 결과]\n", text)

    print("3. Google Cloud NLP로 장소명 추출 중...")
    places = extract_places_with_gcp_nlp(text)
    print("추출된 장소:", places)

    print("4. 각 장소를 Google Maps로 좌표 변환 중...")
    places_with_coords = [geocode_place(place) for place in places]

    json_data = json.dumps(places_with_coords, ensure_ascii=False, indent=2)
    print("\n[장소-좌표 매핑 JSON]\n", json_data)

    print("\n[Google Maps 쿼리 URL]")
    for item in places_with_coords:
        if item["lat"] and item["lng"]:
            url = f"https://www.google.com/maps/search/?api=1&query={item['lat']},{item['lng']}"
        else:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={item['place']}&key={GOOGLE_MAPS_API_KEY}"
        print(f"{item['place']}: {url}")

    # 필요시 오디오 파일 삭제
    os.remove(audio_file)

if __name__ == "__main__":
    main()

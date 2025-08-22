import openai
import os
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment
import json  # <<< 추가


def get_youtube_metadata(video_url: str) -> tuple[str | None, str | None]:
    """
    유튜브 영상의 제목과 썸네일 URL을 추출합니다.
    """
    video_id = video_url.split("v=")[1].split("&")[0]
    title = None
    thumbnail_url = None
    try:
        print(f"➡️ '{video_id}' 영상의 메타데이터를 가져옵니다.")
        result = subprocess.run(
            ["yt-dlp", "--dump-json", video_url],
            check=True,
            capture_output=True,
            text=True,
        )
        video_info = json.loads(result.stdout)
        title = video_info.get("title")
        thumbnail_url = video_info.get("thumbnail")
        print(f"✅ 메타데이터 로드 성공: {title}")
    except Exception as e:
        print(f"⚠️ 메타데이터 로드 실패: {e}")
    return title, thumbnail_url

from openai import AsyncOpenAI # Added import

def get_youtube_metadata(video_url: str) -> tuple[str | None, str | None]:
    """
    유튜브 영상의 제목과 썸네일 URL을 추출합니다.
    """
    video_id = video_url.split("v=")[1].split("&")[0]
    title = None
    thumbnail_url = None
    try:
        print(f"➡️ '{video_id}' 영상의 메타데이터를 가져옵니다.")
        result = subprocess.run(
            ["yt-dlp", "--dump-json", video_url],
            check=True,
            capture_output=True,
            text=True,
        )
        video_info = json.loads(result.stdout)
        title = video_info.get("title")
        thumbnail_url = video_info.get("thumbnail")
        print(f"✅ 메타데이터 로드 성공: {title}")
    except Exception as e:
        print(f"⚠️ 메타데이터 로드 실패: {e}")
    return title, thumbnail_url

async def get_youtube_transcript_only(video_url: str) -> str | None: # Changed to async def
    """
    유튜브 영상에서 스크립트만 추출합니다. 자막이 없으면 STT를 시도합니다.
    """
    video_id = video_url.split("v=")[1].split("&")[0]
    full_transcript = None

    try:
        print(f"✅ 영상 ID '{video_id}'의 자막 추출을 시도합니다.")
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ko", "en"]
        )
        full_transcript = " ".join([item["text"] for item in transcript_list])
        print("✅ 'youtube-transcript-api'를 통해 자막을 성공적으로 가져왔습니다.")
        return full_transcript

    except Exception as e:
        print(f"⚠️ 자막을 찾을 수 없습니다 ({e}). 음원 추출 및 STT를 시작합니다.")
        try:
            output_filename = f"{video_id}_audio.m4a"
            print(f"➡️ 'yt-dlp'로 음원을 다운로드합니다...")
            subprocess.run(
                [
                    "yt-dlp",
                    "-x",
                    "--audio-format",
                    "m4a",
                    "-o",
                    output_filename,
                    video_url,
                ],
                check=True,
                capture_output=True,
            )
            print("✅ 음원 다운로드 완료.")

            file_size = os.path.getsize(output_filename)
            WHISPER_API_LIMIT = 25 * 1024 * 1024

            client = AsyncOpenAI() # Initialize AsyncOpenAI client

            if file_size < WHISPER_API_LIMIT:
                print("➡️ 파일 크기가 작아 분할 없이 처리합니다.")
                with open(output_filename, "rb") as audio_file:
                    transcription = await client.audio.transcriptions.create( # Added await
                        model="whisper-1", file=audio_file
                    )
                full_transcript = transcription.text
            else:
                print(
                    f"⚠️ 파일 크기({file_size / 1024 / 1024:.2f}MB)가 25MB를 초과하여 분할 처리를 시작합니다."
                )
                audio = AudioSegment.from_file(output_filename)
                chunk_length_ms = 10 * 60 * 1000
                chunks = [
                    audio[i : i + chunk_length_ms]
                    for i in range(0, len(audio), chunk_length_ms)
                ]

                full_transcript = ""
                for i, chunk in enumerate(chunks):
                    chunk_filename = f"temp_chunk_{i}.m4a"
                    print(f"➡️ {i+1}/{len(chunks)}번째 조각 처리 중...")
                    chunk.export(chunk_filename, format="mp4")
                    with open(chunk_filename, "rb") as chunk_file:
                        transcription = await client.audio.transcriptions.create( # Added await
                            model="whisper-1", file=chunk_file
                        )
                        full_transcript += transcription.text + " "
                    os.remove(chunk_filename)

            os.remove(output_filename)
            print("✅ Whisper STT 변환 완료.")
            return full_transcript

        except Exception as e_process:
            print(f"❌ 음원 처리 중 오류 발생: {e_process}")
            return None

# 기존 get_transcript_from_youtube 함수는 이제 사용되지 않으므로 제거하거나 주석 처리합니다.
# 테스트 코드 (필요시 주석 해제 후 사용)
# if __name__ == "__main__":
#     test_url = "https://www.youtube.com/watch?v=example"  # 실제 YouTube URL로 변경
#     transcript, title, thumbnail = get_transcript_from_youtube(test_url)
#     print(f"Transcript: {transcript[:200]}...")
#     print(f"Title: {title}")
#     print(f"Thumbnail: {thumbnail}")

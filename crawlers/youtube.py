import openai
import os
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment

def get_transcript_from_youtube(video_url: str) -> str:
    """
    유튜브 영상에서 텍스트 스크립트를 추출합니다.
    자막이 없을 경우, 음원을 다운받아 STT(Speech-to-Text)를 수행하며, 파일 크기가 25MB를 넘으면 분할하여 처리합니다.
    """
    try:
        # 1. YouTube Transcript API를 사용하여 자막 추출 시도
        video_id = video_url.split("v=")[1].split("&")[0]
        print(f"✅ 영상 ID '{video_id}'의 자막 추출을 시도합니다.")
        print(f"youtube url: {video_url}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        full_transcript = " ".join([item['text'] for item in transcript_list])
        print("✅ 'youtube-transcript-api'를 통해 자막을 성공적으로 가져왔습니다.")
        return full_transcript
    except Exception as e:
        # 2. 자막 추출 실패 시, 음원 다운로드 및 STT(Whisper) 시도
        print(f"⚠️ 자막을 찾을 수 없습니다 ({e}). 음원 추출 및 STT를 시작합니다.")
        try:
            output_filename = "temp_audio.m4a"
            print(f"➡️ 'yt-dlp'로 음원을 다운로드합니다...")
            # yt-dlp를 사용하여 YouTube 영상에서 오디오만 추출하여 저장
            subprocess.run(
                ["yt-dlp", "-x", "--audio-format", "m4a", "-o", output_filename, video_url],
                check=True, capture_output=True
            )
            print("✅ 음원 다운로드 완료.")

            # --- 오디오 파일 분할 처리 로직 ---
            file_size = os.path.getsize(output_filename)
            WHISPER_API_LIMIT = 25 * 1024 * 1024  # OpenAI Whisper API의 파일 크기 제한 (25MB)

            if file_size < WHISPER_API_LIMIT:
                # 파일 크기가 제한보다 작으면 바로 STT 수행
                print("➡️ 파일 크기가 작아 분할 없이 처리합니다.")
                with open(output_filename, "rb") as audio_file:
                    transcription = openai.audio.transcriptions.create(model="whisper-1", file=audio_file)
                full_text = transcription.text
            else:
                # 파일 크기가 제한을 초과하면 오디오를 분할하여 처리
                print(f"⚠️ 파일 크기({file_size / 1024 / 1024:.2f}MB)가 25MB를 초과하여 분할 처리를 시작합니다.")
                audio = AudioSegment.from_file(output_filename)
                # 10분(600,000ms) 단위로 오디오를 자름
                chunk_length_ms = 10 * 60 * 1000
                chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
                
                full_text = ""
                for i, chunk in enumerate(chunks):
                    chunk_filename = f"temp_chunk_{i}.m4a"
                    print(f"➡️ {i+1}/{len(chunks)}번째 조각 처리 중...")
                    # 각 오디오 청크를 임시 파일로 저장
                    chunk.export(chunk_filename, format="mp4") # m4a는 mp4 컨테이너 사용
                    with open(chunk_filename, "rb") as chunk_file:
                        # 임시 파일에 대해 Whisper STT 수행
                        transcription = openai.audio.transcriptions.create(model="whisper-1", file=chunk_file)
                        full_text += transcription.text + " " # 추출된 텍스트를 전체 텍스트에 추가
                    os.remove(chunk_filename) # 임시 청크 파일 삭제
            
            os.remove(output_filename) # 원본 오디오 파일 삭제
            print("✅ Whisper STT 변환 완료.")
            print(full_text)
            return full_text

        except subprocess.CalledProcessError as e_dlp:
            # yt-dlp 실행 중 오류 발생 시
            print(f"❌ yt-dlp 음원 다운로드 중 오류 발생: {e_dlp.stderr.decode()}")
            return None
        except Exception as e_whisper:
            # Whisper STT 또는 오디오 처리 중 오류 발생 시
            print(f"❌ Whisper 처리 중 오류 발생: {e_whisper}")
            return None
 
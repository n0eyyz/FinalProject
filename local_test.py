import os
import datetime
import uuid
import sys
import io
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

# --- UnicodeEncodeError 방지를 위한 설정 ---
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- 기존 코드에서 필요한 함수와 모델들을 가져옵니다 ---
from models import Base, Users, Contents, Places, UserContentHistory

# --- .env 파일 로드 및 DB 설정 (local_server.py와 동일) ---
load_dotenv()
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("오류: .env 파일에 DB_URL을 설정해주세요.")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

# --- 데이터베이스 테이블 생성 (없을 경우에만) ---
# 이 코드는 DB 파일이 없다면 테이블을 만들어줍니다.
Base.metadata.create_all(engine)

# --- 테스트를 위한 메인 함수 ---
def run_test():
    """
    엔드포인트 없이 로컬에서 직접 유튜브 영상 처리 및 DB 저장 과정을 테스트합니다.
    """
    # ▼▼▼▼▼ 테스트하고 싶은 유튜브 URL을 여기에 입력하세요 ▼▼▼▼▼
    test_youtube_url = "https://www.youtube.com/watch?v=uQKNm2vQyME"
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    # 테스트용 임시 사용자 ID
    test_uid = f"test-user-{uuid.uuid4()}"

    db = SessionLocal()
    try:
        print("="*50)
        print(f"▶️ 테스트 시작: {test_youtube_url}")
        print(f"👤 테스트 사용자 ID: {test_uid}")
        print("="*50)

        # 1. 백엔드 서버에 GET 요청 보내기
        # 팀원 분의 엔드포인트 URL
        backend_url = "https://192.168.18.124:9000/extract-location-test"

        print(f"\n[1/4] 백엔드 서버 ({backend_url})에 GET 요청을 보냅니다...")
        response = requests.get(backend_url, verify=False) # SSL 인증서 경고 무시

        if response.status_code != 200:
            print(f"❌ 백엔드 서버 오류: {response.status_code} - {response.text}")
            return

        # 백엔드로부터 받은 JSON 데이터
        received_json_data = response.json()
        print("✅ 백엔드로부터 응답을 성공적으로 받았습니다!")
        print(f"  - 응답 데이터: {received_json_data}")

        # 받은 데이터를 data.json 파일로 저장
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(received_json_data, f, indent=4, ensure_ascii=False)
        print("✅ 응답 데이터를 data.json 파일로 저장했습니다.")

        # 응답 데이터가 장소 목록이라고 가정
        locations = []
        if isinstance(received_json_data, dict) and 'locations' in received_json_data:
            locations = received_json_data['locations']
            print("✅ 'locations' 키에서 장소 데이터를 성공적으로 추출했습니다.")
        else:
            print("❌ 백엔드 응답 형식이 예상과 다릅니다. 'locations' 키를 찾을 수 없거나 딕셔너리 형식이 아닙니다.")
            print(f"  - 받은 데이터: {received_json_data}")
            return

        if not isinstance(locations, list):
            print("❌ 'locations' 키의 값이 장소 목록(리스트) 형식이 아닙니다.")
            return

        # 2. video_id 파싱 (로컬 DB 저장을 위한 가상의 content_id)
        try:
            video_id = test_youtube_url.split("v=")[1].split("&")[0]
        except IndexError:
            print("❌ 오류: 올바른 유튜브 URL이 아닙니다. 가상의 video_id를 생성합니다.")
            video_id = f"dummy-content-{uuid.uuid4()}"

        # 3. 사용자 정보 처리 (로컬 DB에 저장)
        user = db.get(Users, test_uid)
        if not user:
            user = Users(user_id=test_uid)
            db.add(user)
            print(f"  - 새로운 사용자 '{test_uid}'를 추가합니다.")

        # 4. 영상 정보 저장 (로컬 DB에 저장 - 백엔드에서 받은 장소와 연결하기 위함)
        print("\n[2/4] 영상 정보를 데이터베이스에 저장합니다...")
        content = db.get(Contents, video_id)
        if not content:
            content = Contents(
                content_id=video_id,
                content_type='test_data', # 테스트용임을 명시
                transcript=None, # 백엔드에서 스크립트를 제공하지 않으므로 None
                processed_at=datetime.datetime.utcnow()
            )
            db.add(content)
            print(f"  - 영상 정보(ID: {video_id})를 저장합니다.")
        else:
            print(f"  - 영상 정보(ID: {video_id})가 이미 존재합니다. 업데이트를 건너뜁니다.")

        # 5. 장소 정보 저장 (백엔드에서 받은 장소 사용)
        print("\n[3/4] 장소 정보를 데이터베이스에 저장합니다...")
        if locations:
            locations_to_add = []
            for loc in locations:
                name = loc.get("name")
                lat = loc.get("lat")
                lng = loc.get("lng")

                if name is None or lat is None or lng is None:
                    print(f"  - '{loc}' 정보가 불완전하여 건너뜁니다. (name, lat, lng 필요)")
                    continue

                # Location 모델에 저장
                location_obj = Places(name=name, lat=lat, lng=lng)
                locations_to_add.append(location_obj)
                print(f"    - 새로운 장소 '{name}' 추가 (Location 테이블)")
            
            if locations_to_add:
                db.add_all(locations_to_add)
            else:
                print("  - 백엔드에서 추출된 유효한 장소 데이터가 없습니다.")
        else:
            print("  - 백엔드에서 추출된 장소가 없습니다.")

        # 6. 사용자-영상 시청 기록 연결 (로컬 DB에 저장)
        print("\n[4/4] 사용자와 영상의 시청 기록을 연결합니다...")
        existing_record = db.execute(
            select(UserContentHistory).where(
                UserContentHistory.user_id == test_uid,
                UserContentHistory.content_id == video_id
            )
        ).scalars().first()

        if not existing_record:
            db.add(UserContentHistory(user_id=test_uid, content_id=video_id))
            print(f"  - 사용자와 영상의 시청 기록을 추가합니다.")
        else:
            print(f"  - 사용자와 영상의 시청 기록이 이미 존재합니다.")

        # 7. 모든 변경사항을 한 번에 커밋
        print("\n[5/5] 모든 변경사항을 데이터베이스에 최종 저장(commit)합니다...")
        db.commit()
        print("✅ 모든 작업이 성공적으로 완료되었습니다!")

    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서버에 연결할 수 없습니다. 팀원 분의 백엔드 서버가 실행 중인지 확인해주세요.")
    except json.JSONDecodeError:
        print("❌ 백엔드 응답이 유효한 JSON 형식이 아닙니다. 서버 응답을 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 테스트 중 심각한 오류 발생: {e}")
        print("롤백을 시도합니다...")
        db.rollback() # 문제가 생기면 모든 변경사항을 취소
    finally:
        db.close() # 작업이 끝나면 항상 DB 연결을 닫아줌
        print("\n테스트가 종료되었습니다.")

if __name__ == "__main__":
    run_test()
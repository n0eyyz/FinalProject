# pind_server

`pind_server`는 YouTube 비디오에서 위치 정보를 추출하고, 사용자 인증 및 관련 데이터를 관리하는 FastAPI 기반의 백엔드 서버입니다.

## 주요 기능

- **YouTube URL 처리**: YouTube 비디오 URL을 받아 비디오 ID를 추출하고, 해당 비디오의 위치 정보를 처리합니다.
- **위치 정보 추출**: 비디오에서 언급되거나 시각적으로 나타나는 위치 정보를 추출하고 데이터베이스에 저장합니다.
- **사용자 인증**: 이메일과 비밀번호를 사용한 사용자 등록 및 로그인을 지원하며, JWT 기반의 인증 시스템을 제공합니다.
- **사용자 콘텐츠 기록**: 사용자가 조회한 비디오의 기록을 관리합니다.
- **데이터베이스 관리**: SQLAlchemy를 ORM으로 사용하여 PostgreSQL 데이터베이스와 상호작용하며, Alembic을 통해 데이터베이스 마이그레이션을 관리합니다.

## 기술 스택

- **백엔드 프레임워크**: FastAPI
- **데이터베이스**: PostgreSQL
- **ORM**: SQLAlchemy
- **데이터베이스 마이그레이션**: Alembic
- **인증**: JWT (JSON Web Tokens) 기반 OAuth2
- **비디오 처리**: `youtube-transcript-api`, `yt-dlp` (비디오 정보 및 스크립트 추출)
- **텍스트/이미지 처리**: `easyocr`, `selenium`, `torch`, `transformers`, `librosa`, `opencv-python-headless` (위치 정보 추출 및 분석에 활용)
- **AI/ML**: Google Generative AI (Gemini API)
- **ASGI 서버**: Uvicorn
- **기타**: `python-dotenv`, `fastapi-middleware-cors`

## 프로젝트 구조

```
pind_server/
├── app/
│   ├── db/                 # 데이터베이스 연결 및 세션 관리
│   ├── dependencies.py     # FastAPI 의존성 주입 (예: 현재 사용자 가져오기)
│   ├── main.py             # FastAPI 애플리케이션 진입점, 라우터 및 미들웨어 설정
│   ├── repositories/       # 데이터베이스 CRUD 작업 (Users, Locations 등)
│   ├── routers/            # API 엔드포인트 정의 (youtube, auth)
│   ├── schemas/            # Pydantic 모델 (요청/응답 데이터 유효성 검사)
│   ├── services/           # 비즈니스 로직 (예: extractor.py)
│   └── utils/              # 유틸리티 함수 (해싱, 토큰 생성, URL 처리)
├── alembic.ini             # Alembic 설정 파일
├── models.py               # SQLAlchemy ORM 모델 정의
├── migrations/             # Alembic 데이터베이스 마이그레이션 스크립트
├── crawlers/               # 웹 크롤링 로직 (예: youtube.py)
├── nlp/                    # 자연어 처리 관련 코드 (예: gemini_location.py)
├── certs/                  # SSL/TLS 인증서 (선택 사항)
├── requirements.txt        # Python 종속성 목록
└── README.md               # 프로젝트 설명 (현재 파일)
```

## 시작하기

### 1. 환경 설정

Python 3.9 이상이 설치되어 있는지 확인합니다.

```bash
# 가상 환경 생성 및 활성화 (선택 사항이지만 권장)
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 종속성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

PostgreSQL 데이터베이스를 설정하고 `alembic.ini` 파일의 `sqlalchemy.url`을 데이터베이스 연결 정보에 맞게 수정합니다.

```ini
# alembic.ini
sqlalchemy.url = postgresql://your_user:your_password@your_host:your_port/your_database
```

### 4. 데이터베이스 마이그레이션

Alembic을 사용하여 데이터베이스 스키마를 생성하고 업데이트합니다.

```bash
# 새 마이그레이션 스크립트 생성 (모델 변경 시)
alembic revision --autogenerate -m "Your migration message"

# 데이터베이스에 마이그레이션 적용
alembic upgrade head
```

### 5. 애플리케이션 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

(선택 사항) SSL/TLS를 사용하려면 `app/main.py`의 `uvicorn.run` 부분을 주석 해제하고 인증서 경로를 올바르게 설정해야 합니다.

```python
# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=1636, reload=True, ssl_keyfile = "C:/finalproject/certs/192.168.18.124+3-key.pem",
#                 ssl_certfile = "C:/finalproject/certs/192.168.18.124+3.pem",)
```

### 6. API 문서

서버가 실행되면 다음 URL에서 FastAPI 자동 생성 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 기여

기여를 환영합니다! 버그 보고, 기능 요청 또는 코드 개선을 위해 언제든지 이슈를 열거나 풀 리퀘스트를 제출해주세요.
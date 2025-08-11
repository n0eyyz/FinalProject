# pind_server

`pind_server`는 YouTube 비디오에서 위치 정보를 추출하고, 사용자 인증 및 관련 데이터를 관리하는 FastAPI 기반의 백엔드 서버입니다. 무거운 동영상 처리 작업을 위해 Celery와 Redis를 이용한 비동기 작업 큐 시스템을 도입하여 안정성과 확장성을 확보했습니다.

## 주요 기능

- **YouTube URL 처리**: YouTube 비디오 URL을 받아 비디오 ID를 추출하고, 해당 비디오의 위치 정보를 처리합니다.
- **비동기 작업 큐**: Celery와 Redis를 사용하여 동영상 처리와 같은 무거운 작업을 백그라운드에서 안정적으로 실행하고, 작업 상태를 추적합니다.
- **작업 상태 API**: 비동기 작업의 ID를 즉시 반환하고, 별도의 API를 통해 작업의 진행 상태와 최종 결과를 조회할 수 있습니다.
- **위치 정보 추출**: 비디오에서 언급되거나 시각적으로 나타나는 위치 정보를 추출하고 데이터베이스에 저장합니다.
- **사용자 인증**: 이메일과 비밀번호를 사용한 사용자 등록 및 로그인을 지원하며, JWT 기반의 인증 시스템을 제공합니다.
- **사용자 콘텐츠 기록**: 사용자가 조회한 비디오의 기록을 관리합니다.
- **데이터베이스 관리**: SQLAlchemy를 ORM으로 사용하여 PostgreSQL 데이터베이스와 상호작용하며, Alembic을 통해 데이터베이스 마이그레이션을 관리합니다.

## 기술 스택

- **백엔드 프레임워크**: FastAPI
- **메시지 큐 / 작업 분산**: Celery, Redis
- **데이터베이스**: PostgreSQL
- **ORM**: SQLAlchemy
- **데이터베이스 마이그레이션**: Alembic
- **인증**: JWT (JSON Web Tokens) 기반 OAuth2
- **비디오 처리**: `youtube-transcript-api`, `yt-dlp` (비디오 정보 및 스크립트 추출)
- **텍스트/이미지 처리**: `easyocr`, `selenium`, `torch`, `transformers`, `librosa`, `opencv-python-headless` (위치 정보 추출 및 분석에 활용)
- **AI/ML**: Google Generative AI (Gemini API)
- **ASGI 서버**: Uvicorn
- **기타**: `python-dotenv`, `fastapi-middleware-cors`

## 핵심 아키텍처

### 비동기 작업 처리 아키텍처

본 서버는 무거운 작업을 처리하기 위해 분산 작업 큐 아키텍처를 채택했습니다.

1.  **API Gateway (FastAPI)**: 사용자의 요청을 받아 즉시 `job_id`를 반환합니다.
2.  **Message Broker (Redis)**: 처리해야 할 작업들을 큐(대기열)에 저장합니다.
3.  **Celery Worker**: 별도의 프로세스에서 큐를 감시하다가 새로운 작업이 들어오면 가져가서 비동기적으로 처리합니다.
4.  **Result Backend (Redis)**: Celery 워커가 처리하는 작업의 상태, 진행률, 최종 결과를 저장합니다.
5.  **상태/결과 조회 API**: 사용자는 `job_id`를 이용해 Result Backend의 데이터를 조회하여 작업 현황을 파악합니다.

### 계층 구조

1.  **Router Layer** (`app/routers/`): API 엔드포인트 정의 및 요청 처리
2.  **Repository Layer** (`app/repositories/`): 데이터베이스 CRUD 작업
3.  **Service Layer** (`app/services/`): 비즈니스 로직 및 외부 API 통합
4.  **Schema Layer** (`app/schemas/`): Pydantic 모델로 요청/응답 검증
5.  **Task Layer** (`app/tasks.py`): Celery 워커가 실행할 실제 작업들을 정의

## 프로젝트 구조

```
pind_server/
├── app/
│   ├── celery_config.py    # Celery 앱 및 Broker/Backend 설정
│   ├── db/                 # 데이터베이스 연결 및 세션 관리
│   ├── dependencies.py     # FastAPI 의존성 주입
│   ├── main.py             # FastAPI 애플리케이션 진입점
│   ├── repositories/       # 데이터베이스 CRUD 작업
│   ├── routers/            # API 엔드포인트 정의 (youtube, auth, jobs)
│   ├── schemas/            # Pydantic 모델 (요청/응답 데이터 정의)
│   ├── services/           # 비즈니스 로직
│   ├── tasks.py            # Celery 비동기 작업 정의
│   └── utils/              # 유틸리티 함수
├── tests/
│   ├── conftest.py         # Pytest 픽스처 및 설정
│   └── test_users.py       # 사용자 관련 테스트
├── alembic.ini             # Alembic 설정 파일
├── models.py               # SQLAlchemy ORM 모델 정의
├── migrations/             # Alembic 데이터베이스 마이그레이션 스크립트
├── pytest.ini              # Pytest 설정 파일
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

### 3. 데이터베이스 설정 (PostgreSQL)

PostgreSQL 데이터베이스를 설정하고 `.env` 파일에 `DATABASE_URL`을 지정합니다.

```
# .env
DATABASE_URL="postgresql://user:password@host:port/database"
```

### 4. 메시지 브로커 설정 (Redis)

Celery를 위해 Redis 서버가 필요합니다. Docker를 사용하는 것이 가장 간편합니다.

```bash
# Docker를 이용해 백그라운드에서 Redis 서버 실행
docker run -d -p 6379:6379 --name my-redis-server redis
```

### 5. 데이터베이스 마이그레이션

Alembic을 사용하여 데이터베이스 스키마를 생성하고 업데이트합니다.

```bash
# 데이터베이스에 최신 스키마 적용
alembic upgrade head
```

### 6. 애플리케이션 실행

서버를 실행하려면 **두 개의 터미널**이 필요합니다.

**터미널 1: Celery Worker 실행**

```bash
# 프로젝트 루트 디렉토리에서 실행
celery -A app.celery_config.celery_app worker --loglevel=info
```

**터미널 2: FastAPI 서버 실행**

```bash
# 프로젝트 루트 디렉토리에서 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. API 문서

서버가 실행되면 다음 URL에서 FastAPI 자동 생성 API 문서를 확인할 수 있습니다. 비동기 작업을 관리하기 위한 `/api/v1/jobs/...` 엔드포인트들이 추가되었습니다.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
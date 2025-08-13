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

## 최근 변경 사항 및 개선 사항

이 섹션에서는 프로젝트에 적용된 주요 변경 사항 및 개선 사항을 설명합니다.

### 1. 데이터베이스 스키마 개선

*   **`models.py`**: `UserContentHistory` 모델의 `created_at` 컬럼이 데이터베이스 서버에서 직접 시간을 설정하도록 (`server_default=func.now()`) 변경되었으며, `NULL` 값을 허용하지 않도록 (`nullable=False`) 수정되었습니다. 이는 데이터 일관성을 높이고 애플리케이션의 부담을 줄입니다.
*   **마이그레이션**: 변경된 스키마를 데이터베이스에 적용하기 위해 Alembic 마이그레이션이 수행되었습니다.

### 2. API 및 비즈니스 로직 개선

*   **`app/repositories/locations.py`**: `get_user_history_details` 함수에서 컬렉션(예: `Contents.places`)을 eager loading할 때 발생할 수 있는 중복된 부모 객체 문제를 해결하기 위해 쿼리 결과에 `.unique()` 필터링이 추가되었습니다.
*   **`app/routers/jobs.py`:
    *   `/api/v1/jobs/{job_id}/result` 엔드포인트에서 `TypeError: object dict can't be used in await expression` 오류를 수정했습니다. `celery.result.AsyncResult.get()` 메소드는 이미 태스크가 완료된 상태에서 호출될 때 `await`가 필요하지 않으므로, 불필요한 `await` 키워드를 제거했습니다.
*   **`app/tasks.py`**: Celery 태스크(`process_youtube_url`)에서 예외 발생 시, Celery가 예외 정보를 올바르게 저장할 수 있도록 예외 처리 로직이 개선되었습니다. 이제 예외 타입과 전체 트레이스백을 포함한 상세한 오류 메시지가 `task.result`에 저장됩니다.

### 3. Celery 작업 진행 상황 모니터링 개선

*   **`app/routers/jobs.py`**: `/api/v1/jobs/{job_id}/status` 엔드포인트가 Celery 태스크의 `PROGRESS` 상태에서 `current_step` 및 `progress` 정보를 포함하여 반환하도록 개선되었습니다. 이를 통해 클라이언트가 작업의 상세 진행 상황을 더 명확하게 파악할 수 있습니다.

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

Docker와 Celery 실행 PC가 다를 경우 Celery Worker를 따로 열어야 합니다.
이는 scripts 디렉토리 내에 있으며 Window PowerShell에서 명령어로 열 수 있습니다.


```bash
# Window PowerShell에서 실행
C:\pind_server\scripts\run_celery.bat
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

### Celery Flower를 이용한 모니터링

Celery 작업의 실시간 상태, 워커 정보, 작업 이력 등을 웹 기반 대시보드에서 시각적으로 모니터링하려면 Celery Flower를 사용할 수 있습니다.

1.  **Flower 설치**:
    프로젝트의 가상 환경이 활성화된 상태에서 다음 명령어를 실행하여 Flower를 설치합니다.
    ```bash
    pip install flower
    ```

2.  **Flower 실행**:
    설치가 완료되면, 다음 명령어를 사용하여 Flower를 실행합니다. 이 명령어는 Celery 애플리케이션과 Redis 브로커의 위치를 Flower에 알려줍니다.
    ```bash
    # 프로젝트 루트 디렉토리에서 실행
    celery -A app.celery_config.celery_app flower --broker=redis://<your_redis_host>:6379/0
    ```
    *   `<your_redis_host>`: Redis 서버의 IP 주소 또는 호스트 이름을 입력합니다. (예: `localhost` 또는 `192.168.18.99`)
    *   Flower가 성공적으로 실행되면, 웹 브라우저에서 `http://localhost:5555` (기본 포트)로 접속하여 대시보드를 확인할 수 있습니다.

**참고**: `ModuleNotFoundError` 또는 `ConnectionRefusedError`와 같은 문제가 발생할 경우, 다음 사항을 확인하세요:
*   **`PYTHONPATH` 설정**: 프로젝트 루트 디렉토리가 Python 경로에 포함되어 있는지 확인합니다. (예: `set PYTHONPATH=%CD%` 또는 `$env:PYTHONPATH = (Get-Location).Path` for Windows)
*   **Redis 서버 상태**: Redis 서버가 실행 중이며, Flower가 접근할 수 있도록 외부 연결을 허용하는지 확인합니다.
*   **방화벽**: Redis 포트(기본 6379)가 방화벽에 의해 차단되지 않았는지 확인합니다.
```

### 7. API 문서

서버가 실행되면 다음 URL에서 FastAPI 자동 생성 API 문서를 확인할 수 있습니다. 비동기 작업을 관리하기 위한 `/api/v1/jobs/...` 엔드포인트들이 추가되었습니다.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
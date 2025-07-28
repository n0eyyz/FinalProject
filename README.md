
# Location Extractor API

## 1. 프로젝트 개요

이 프로젝트는 YouTube, Instagram 등 다양한 소셜 미디어 콘텐츠에서 장소 정보를 추출하여 데이터베이스에 저장하고, 지도 위에 시각화해주는 FastAPI 기반의 백엔드 API 서버입니다. 사용자가 콘텐츠 URL을 제공하면, 서버는 콘텐츠의 텍스트(자막, 본문 등)를 분석하여 언급된 장소(식당, 카페 등)의 이름과 좌표를 추출하고 저장합니다.

## 2. 주요 기능

- **YouTube 영상 장소 추출**: YouTube URL을 입력받아 영상의 자막 또는 음성을 텍스트로 변환하고, AI를 이용해 장소 정보를 추출합니다.
- **Instagram 게시물 장소 추출**: Instagram 게시물 URL에서 본문 텍스트를 크롤링하여 장소 정보를 추출합니다.
- **DB 기반 캐싱**: 한 번 처리된 콘텐츠의 장소 정보는 데이터베이스에 저장하여, 동일한 요청에 대해서는 DB에서 직접 결과를 반환하여 빠르게 응답합니다.
- **지도 시각화 연동**: 추출된 장소 목록을 지도 서비스(pind_web_map)에서 바로 확인할 수 있도록 리다이렉트 URL을 제공합니다.

## 3. 기술 스택

- **언어**: Python 3
- **프레임워크**: FastAPI
- **데이터베이스**: SQLAlchemy ORM (DB 종류는 .env 설정에 따름)
- **AI/NLP**: Google Gemini, OpenAI Whisper (STT)
- **크롤링**: `youtube-transcript-api`, `yt-dlp`, Selenium
- **기타**: Pydantic, Uvicorn

## 4. 프로젝트 아키텍처

```
+---------------------+      +-------------------------+      +------------------------+
|      FastAPI        |----->|   Service Layer         |----->|    Crawler Modules     |
| (Routers & Schemas) |      | (extractor.py)          |      | (youtube.py, etc.)     |
+---------------------+      +-------------------------+      +------------------------+
          |                            |                             |
          |                            |                             | (Gemini/Whisper API)
          v                            v                             v
+---------------------+      +-------------------------+      +------------------------+
|  Repository Layer   |----->|      Database           |      |   External Services    |
|  (locations.py)     |      | (models.py, database.py)|      | (Google, OpenAI)       |
+---------------------+      +-------------------------+      +------------------------+
```

1.  **Router (`app/routers/youtube.py`)**: API 엔드포인트를 정의하고 클라이언트의 요청(URL)을 받습니다.
2.  **Repository (`app/repositories/locations.py`)**: DB에 저장된 장소 정보가 있는지 확인합니다.
3.  **Service (`app/services/extractor.py`)**:
    -   DB에 정보가 없으면 **Crawler**를 호출하여 콘텐츠에서 텍스트(자막 등)를 가져옵니다.
    -   가져온 텍스트를 **NLP** 모듈에 전달하여 장소 정보를 추출합니다.
4.  **Crawler (`crawlers/`)**: `youtube-transcript-api`나 `yt-dlp` + `Whisper`를 사용해 YouTube 영상의 텍스트를 추출합니다.
5.  **NLP (`nlp/gemini_location.py`)**: Google Gemini API를 호출하여 텍스트에서 장소 이름과 좌표를 JSON 형태로 추출합니다.
6.  **Repository (`app/repositories/locations.py`)**: 추출된 장소 정보를 DB에 저장합니다.
7.  **Router (`app/routers/youtube.py`)**: 최종 결과를 클라이언트에게 응답합니다.

## 5. 파일 설명

-   **`server.py`**: FastAPI 애플리케이션의 메인 실행 파일 (Uvicorn 서버 설정 포함).
-   **`database.py`**: SQLAlchemy 엔진 및 세션 설정을 담당.
-   **`models.py`**: 데이터베이스 테이블 구조를 정의하는 SQLAlchemy ORM 모델.
-   **`requirements.txt`**: 프로젝트에 필요한 Python 라이브러리 목록.
-   **`local_test.py`**: 서버를 실행하지 않고 로컬에서 특정 기능(URL 처리, DB 저장)을 테스트하기 위한 스크립트.

-   **`app/`**: 핵심 비즈니스 로직이 담긴 디렉터리.
    -   **`main.py`**: FastAPI 앱 인스턴스를 생성하고 라우터를 포함.
    -   **`db/database.py`**: `app` 모듈용 DB 설정.
    -   **`routers/youtube.py`**: `/api/v1/youtube` 경로의 API 엔드포인트 로직.
    -   **`repositories/locations.py`**: 데이터베이스 CRUD 작업을 담당하는 함수 모음.
    -   **`schemas/youtube.py`**: API 요청/응답 데이터 형식을 정의하는 Pydantic 모델.
    -   **`services/extractor.py`**: 크롤러와 NLP 모듈을 조합하여 실제 장소 추출 로직을 수행.
    -   **`utils/url.py`**: URL에서 비디오 ID를 추출하는 등 유틸리티 함수.

-   **`crawlers/`**: 외부 웹사이트에서 데이터를 가져오는 모듈.
    -   **`youtube.py`**: YouTube 자막/음성을 추출.
    -   **`instagram.py`**: Instagram 본문을 추출.
    -   **`screenshot_ocr.py`**: 화면 캡처 및 OCR 수행.

-   **`nlp/`**: 자연어 처리를 담당하는 모듈.
    -   **`gemini_location.py`**: Gemini API를 이용해 텍스트에서 장소를 추출.

## 6. API 엔드포인트

-   `POST /api/v1/youtube/process`
    -   **설명**: YouTube URL에서 장소 정보를 추출하고 결과를 반환합니다.
    -   **요청 본문**: `{"url": "https://www.youtube.com/watch?v=..."}`
    -   **응답**:
        -   DB에 정보가 있을 경우: `{"mode": "db", "places": [{"name": ..., "lat": ..., "lng": ...}]}`
        -   새로 추출한 경우: `{"mode": "new", "places": [{"name": ..., "lat": ..., "lng": ...}]}`

-   `GET /view/{video_id}`
    -   **설명**: 주어진 `video_id`와 연관된 장소들을 `pind_web_map`에서 보여주도록 리다이렉트합니다.
    -   **경로 파라미터**: `video_id` (e.g., `uQKNm2vQyME`)

## 7. 설치 및 실행

1.  **가상환경 생성 및 활성화**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2.  **의존성 설치**
    ```bash
    pip install -r requirements.txt
    ```

3.  **.env 파일 설정**
    -   프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 채웁니다.
    ```
    DATABASE_URL="postgresql://user:password@host:port/dbname" # 또는 sqlite:///./test.db
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="..."
    ```

4.  **서버 실행**
    -   `app/main.py`의 주석 처리된 `uvicorn.run` 부분을 활성화하거나, 터미널에서 직접 실행합니다.
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
    ```
    *SSL 설정이 필요한 경우 `server.py`의 uvicorn 실행 부분을 참고하세요.*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

YouTube 비디오에서 위치 정보를 추출하는 FastAPI 기반 백엔드 서버입니다. 비디오의 음성, 텍스트, 이미지 분석을 통해 언급된 장소를 자동으로 식별하고 저장합니다.

## 개발 환경 설정 및 명령어

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 데이터베이스 마이그레이션

**중요**: 이 프로젝트는 Alembic을 사용하여 데이터베이스 스키마를 관리합니다. `Base.metadata.create_all()`은 사용하지 않습니다.

```bash
# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 이력 보기
alembic history

# 새 마이그레이션 생성 (모델 변경 후)
alembic revision --autogenerate -m "migration message"

# 마이그레이션 적용
alembic upgrade head

# 특정 버전으로 롤백
alembic downgrade <revision_id>

# 한 단계 롤백
alembic downgrade -1

# 초기 상태로 롤백 (모든 테이블 삭제)
alembic downgrade base
```

**새로운 개발 환경 설정 시**:
1. `.env` 파일에 `DATABASE_URL` 설정
2. `alembic upgrade head` 실행하여 모든 마이그레이션 적용
3. 절대 `Base.metadata.create_all()` 사용하지 않음

### 개발 서버 실행
```bash
# HTTP
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# HTTPS (SSL 인증서 사용)
uvicorn app.main:app --reload --host 0.0.0.0 --port 1636 --ssl-keyfile certs/192.168.18.124+3-key.pem --ssl-certfile certs/192.168.18.124+3.pem
```

### 데이터베이스 연결 테스트
```bash
python scripts/connection.py
```

### 데이터베이스 초기화 (새 개발 환경)
```bash
# 데이터베이스 연결 확인 및 모든 마이그레이션 적용
python scripts/init_db.py
```

## 핵심 아키텍처

### 계층 구조
1. **Router Layer** (`app/routers/`): API 엔드포인트 정의 및 요청 처리
2. **Repository Layer** (`app/repositories/`): 데이터베이스 CRUD 작업
3. **Service Layer** (`app/services/`): 비즈니스 로직 및 외부 API 통합
4. **Schema Layer** (`app/schemas/`): Pydantic 모델로 요청/응답 검증

### 인증 시스템
- JWT 토큰 기반 인증 (`app/utils/token.py`)
- 모든 YouTube API는 `get_current_user` 의존성으로 보호
- 비밀번호는 bcrypt로 해시 처리 (`app/utils/hash.py`)

### 데이터 모델 관계
```
Users (사용자)
  ↓
UserContentHistory (시청 기록)
  ↓
Contents (YouTube 비디오)
  ↓
ContentPlaces (다대다 관계)
  ↓
Places (추출된 위치 정보)
```

### 위치 추출 프로세스
1. YouTube URL에서 비디오 ID 추출 (`app/utils/url.py`)
2. 기존 처리 여부 확인 (DB 조회)
3. 신규 비디오인 경우:
   - 메타데이터 수집 (`crawlers/youtube_crawler.py`)
   - 음성→텍스트 변환 (`nlp/whisper_processing.py`)
   - 이미지 텍스트 추출 (`nlp/image_to_text.py`)
   - 통합 위치 분석 (`nlp/gemini_location.py`)
4. 추출된 위치 정보 저장 및 반환

### 주요 외부 의존성
- Google Gemini API: 고급 자연어 처리 및 위치 추출
- OpenAI Whisper: 음성 인식
- EasyOCR: 이미지에서 텍스트 추출
- PostgreSQL: 데이터 저장소

### 환경 변수
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `SECRET_KEY`: JWT 토큰 서명용 비밀키
- `GOOGLE_API_KEY`: Gemini API 키

## 개발 시 주의사항

1. 새로운 API 엔드포인트 추가 시:
   - Router → Repository → Service 계층 구조 유지
   - 인증이 필요한 경우 `Depends(get_current_user)` 추가
   - Pydantic 스키마로 입출력 검증

2. 데이터베이스 스키마 변경 시:
   - `models.py` 수정 후 반드시 Alembic 마이그레이션 생성
   - 관련 Repository 메서드 업데이트

3. 위치 추출 로직 개선 시:
   - `nlp/gemini_location.py`의 프롬프트 및 로직 수정
   - 테스트를 위해 특정 YouTube URL로 검증 필요

4. API 응답 형식:
   - 성공: 해당 데이터 반환
   - 실패: HTTPException with status_code와 detail 메시지
# app/db/database.py
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url

# 1) .env 로드 (프로젝트 루트 기준)
ROOT_DIR = Path(__file__).resolve().parents[2]  # backend/
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

# 2) URL 통일 (DATABASE_URL 사용, 없으면 DB_URL fallback)
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL (또는 DB_URL) 이 설정되지 않았습니다.")
print(f"[DB_DEBUG] Connecting to database: {DATABASE_URL}") # 이 줄을 추가하세요.

# 3) 엔진 생성: DB 종류별 옵션 처리
url_obj = make_url(DATABASE_URL)
engine_kwargs = {"pool_pre_ping": True, "future": True}

if url_obj.drivername.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

# 4) Base는 models.py에서 import
from models import Base

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

def get_db():
    """
    데이터베이스 세션을 생성하고 반환합니다. 요청 처리 후 세션을 닫습니다.
    FastAPI의 Depends를 통해 의존성 주입에 사용됩니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

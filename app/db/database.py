# app/db/database.py
import os, ssl
import uuid
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from sqlalchemy.engine.url import make_url
from models import Base

# .env 로드
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

rawdb = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")
if not rawdb:
    raise ValueError("DATABASE_URL (또는 DB_URL) 이 설정되지 않았습니다.")

if rawdb.startswith("postgres://"):
    async_db_url = rawdb.replace("postgres://", "postgresql+asyncpg://", 1)
elif rawdb.startswith("postgresql://"):
    async_db_url = rawdb.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    async_db_url = rawdb

# DB URL을 asyncpg에 맞게 변경
print(f"[DB_DEBUG] USING ASYNC_DB_URL = {async_db_url}")

# (1) 엄격 모드: 정상 경로 (가능하면 이걸 사용)
strict_ctx = ssl.create_default_context()

# (2) 느슨 모드: 검증 끔(개발/임시용)
insecure_ctx = ssl.create_default_context()
insecure_ctx.check_hostname = False
insecure_ctx.verify_mode = ssl.CERT_NONE

# 환경변수로 토글 (없으면 기본=엄격)
USE_INSECURE = os.getenv("DB_SSL_INSECURE", "").lower() in ("1","true","yes")

# 동적 prepared statement 이름 생성 함수
def prepared_statement_name_func():
    """각 prepared statement에 고유한 이름을 생성하여 중복 오류를 방지합니다."""
    return f"stmt_{uuid.uuid4().hex[:8]}"

# 비동기 엔진 생성
engine = create_async_engine(
    async_db_url,
    pool_pre_ping=True,
    poolclass=NullPool,  # 연결 풀링 비활성화로 prepared statement 충돌 방지
    execution_options={
        "prepared_cache_size": 0,  # prepared statement 캐싱 비활성화
    },
    connect_args={
        "ssl": insecure_ctx if USE_INSECURE else strict_ctx,
        "statement_cache_size": 0,  # asyncpg 레벨에서도 캐싱 비활성화
        "prepared_statement_name_func": prepared_statement_name_func,  # 동적 이름 생성
    },
)

# 비동기 세션 메이커
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    비동기 데이터베이스 세션을 생성하고 반환합니다.
    FastAPI의 Depends를 통해 의존성 주입에 사용됩니다.
    `async with`를 사용하여 세션이 자동으로 닫히도록 보장합니다.
    """
    async with AsyncSessionLocal() as session:
        yield session

# 참고: 기존의 동기 get_db 함수는 더 이상 사용되지 않습니다.
# 라우터와 리포지토리에서 이 새로운 get_db를 사용하고,
# 모든 DB 호출에 await 키워드를 붙여야 합니다. (예: await db.execute(...))
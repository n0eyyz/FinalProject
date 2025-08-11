# app/db/database.py
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.engine.url import make_url
from models import Base

# .env 로드
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL (또는 DB_URL) 이 설정되지 않았습니다.")

# DB URL을 asyncpg에 맞게 변경
async_db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
print(f"[DB_DEBUG] Connecting to async database: {async_db_url}")

# 비동기 엔진 생성
engine = create_async_engine(async_db_url, pool_pre_ping=True, echo=False)

# 비동기 세션 메이커
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    """
    비동기 데이터베이스 세션을 생성하고 반환합니다.
    FastAPI의 Depends를 통해 의존성 주입에 사용됩니다.
    """
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

# 참고: 기존의 동기 get_db 함수는 더 이상 사용되지 않습니다.
# 라우터와 리포지토리에서 이 새로운 get_db를 사용하고,
# 모든 DB 호출에 await 키워드를 붙여야 합니다. (예: await db.execute(...))
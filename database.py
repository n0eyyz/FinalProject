# SQLALchemy에서 데이터 베이스 연결을 위한 엔진 생성 함수
from sqlalchemy import create_engine 
# sessionmaker: SQLAlchemy에서 데이터베이스 세션을 만들어주는 팩토리 함수 
#/ delarative_base: ORMs에서 데이터베이스 모델 크래스의 베이스를 정의
from sqlalchemy.orm import sessionmaker, declarative_base 
# OS 환경변수와 .env 환경설정 파일을 읽기 위한 라이브러리 import
import os
from dotenv import load_dotenv

# .env 파일의 상대 경로를 정확히 지정
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'ytdb', '.env')
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
print(f"ATTEMPTING TO CONNECT TO DATABASE URL: {DB_URL}")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable not set or empty")

engine = create_engine(DB_URL, pool_pre_ping=True) # DB와 커넥션 풀을 관리하는 엔진 객체 만들고 커넥션 풀에서 죽은 연결 감지
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db(): # 데이터 베이스 세션 생성, 호출자에게 세션 객체 전달
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

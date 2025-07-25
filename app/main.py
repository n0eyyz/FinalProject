import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- 추가된 부분 ---
from app.db.database import engine
from models import Base
# --------------------

from app.routers import youtube

# --- 추가된 부분 ---
# 데이터베이스에 테이블 생성
Base.metadata.create_all(bind=engine)
# --------------------

app = FastAPI(title="Location Extractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 테스트용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(youtube.router)

# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=1636, reload=True, ssl_keyfile = "C:/finalproject/certs/192.168.18.124+3-key.pem",
#                 ssl_certfile = "C:/finalproject/certs/192.168.18.124+3.pem",)
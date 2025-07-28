import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# --- 추가된 부분 ---
from app.db.database import engine
from models import Base
# --------------------

from app.routers import youtube, auth
from app.dependencies import get_current_user # get_current_user 임포트

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

# 라우터 포함 시 의존성 추가
app.include_router(youtube.router, dependencies=[Depends(get_current_user)])
app.include_router(auth.router)

# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=1636, reload=True, ssl_keyfile = "C:/finalproject/certs/192.168.18.124+3-key.pem",
#                 ssl_certfile = "C:/finalproject/certs/192.168.18.124+3.pem",)
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

# CORS 미들웨어 설정: 모든 Origin, 자격 증명, 메서드, 헤더를 허용합니다.
# 이는 개발 및 테스트 목적으로 사용되며, 실제 배포 시에는 보안 강화를 위해 특정 Origin만 허용하도록 변경해야 합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 테스트용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함 시 의존성 추가
# youtube 라우터는 get_current_user 의존성을 통해 인증이 필요하도록 설정합니다.
# auth 라우터는 인증 없이 접근 가능합니다.
app.include_router(youtube.router, dependencies=[Depends(get_current_user)])
app.include_router(auth.router)

# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=1636, reload=True, ssl_keyfile = "C:/finalproject/certs/192.168.18.124+3-key.pem",
#                 ssl_certfile = "C:/finalproject/certs/192.168.18.124+3.pem",)
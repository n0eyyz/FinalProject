from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.repositories import users as user_repo
from app.utils import token as token_util
from models import Users # models.py에서 Users 모델 임포트

# OAuth2PasswordBearer 인스턴스 생성
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False) # auto_error=False로 설정

# 의존성 주입 함수: 토큰을 검증하고 사용자 객체를 반환
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Users:
    """
    현재 요청을 보낸 사용자의 인증 토큰을 검증하고, 해당 사용자 객체를 반환합니다.
    유효하지 않은 토큰이거나 사용자를 찾을 수 없는 경우 HTTPException을 발생시킵니다.
    FastAPI 라우터에서 Depends를 통해 의존성 주입에 사용됩니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    try:
        token_data = token_util.verify_token(token, credentials_exception)
    except Exception as e:
        raise credentials_exception from e

    user = await user_repo.get_user_by_email(db, token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_optional(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Optional[Users]:
    """
    현재 요청을 보낸 사용자의 인증 토큰을 검증하고, 해당 사용자 객체를 반환합니다.
    토큰이 없거나 유효하지 않은 경우 None을 반환합니다.
    """
    if not token:
        return None
    try:
        token_data = token_util.verify_token(token)
        user = await user_repo.get_user_by_email(db, token_data.email)
        return user
    except Exception:
        return None

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import models
from app.db.database import get_db
from app.repositories import users as user_repository
from app.schemas import auth as auth_schema
from app.utils import hash as hash_utils
from app.utils import token as token_utils
from app.utils.email import send_email

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: auth_schema.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    새로운 사용자를 등록합니다. 이메일이 이미 등록되어 있으면 400 Bad Request를 반환합니다.
    비밀번호는 해싱되어 저장됩니다.
    """
    db_user = await user_repository.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = hash_utils.get_password_hash(user.password)
    db_user = models.Users(email=user.email, hashed_password=hashed_password)
    await user_repository.create_user(db, db_user)
    
    return {"message": "User created successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    사용자 로그인을 처리하고, 유효한 자격 증명인 경우 액세스 토큰을 반환합니다.
    """
    logger.info(f"Login attempt for email: {form_data.username}")
    db_user = await user_repository.get_user_by_email(db, email=form_data.username)
    
    if not db_user:
        logger.warning(f"Login failed: User {form_data.username} not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {db_user.email}. Verifying password...")
    if not hash_utils.verify_password(form_data.password, db_user.hashed_password):
        logger.warning(f"Login failed: Incorrect password for {form_data.username}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Password verified for {form_data.username}.")
    
    access_token = token_utils.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/request-password-reset")
async def request_password_reset(
    request: auth_schema.PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    비밀번호 재설정 요청을 받아 이메일을 발송합니다.
    """
    user = await user_repository.get_user_by_email(db, email=request.email)
    if user:
        token = token_utils.create_password_reset_token(email=user.email)
        reset_link = f"http://your-frontend-url/reset-password?token={token}"
        email_body = f"<p>비밀번호를 재설정하려면 아래 링크를 클릭하세요:</p><p><a href='{reset_link}'>{reset_link}</a></p>"
        
        background_tasks.add_task(
            send_email, 
            subject="비밀번호 재설정 요청", 
            recipients=[user.email], 
            body=email_body
        )
    return {"message": "If your email is registered, you will receive a password reset link."}

@router.post("/reset-password")
async def reset_password(
    request: auth_schema.PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    토큰을 검증하고 새 비밀번호로 업데이트합니다.
    """
    email = token_utils.verify_password_reset_token(request.token)
    user = await user_repository.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token or user does not exist")
    
    hashed_password = hash_utils.get_password_hash(request.new_password)
    await user_repository.update_user_password(db, user=user, hashed_password=hashed_password)
    
    return {"message": "Password has been reset successfully."}
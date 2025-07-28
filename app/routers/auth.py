from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # 이 부분을 추가합니다.
from sqlalchemy.orm import Session
import models
from app.db.database import get_db
from app.repositories import users as user_repository
from app.schemas import auth as auth_schema
from app.utils import hash as hash_utils
from app.utils import token as token_utils

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: auth_schema.UserCreate, db: Session = Depends(get_db)):
    db_user = user_repository.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = hash_utils.get_password_hash(user.password)
    db_user = models.Users(email=user.email, hashed_password=hashed_password)
    user_repository.create_user(db, db_user)
    
    return {"message": "User created successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)): # 이 부분을 수정합니다.
    db_user = user_repository.get_user_by_email(db, email=form_data.username) # form_data.username 사용
    if not db_user or not hash_utils.verify_password(form_data.password, db_user.hashed_password): # form_data.password 사용
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = token_utils.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
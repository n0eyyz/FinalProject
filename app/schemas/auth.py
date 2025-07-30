from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """
    사용자 생성을 위한 Pydantic 스키마.
    회원가입 시 이메일과 비밀번호를 받습니다.
    """
    email: EmailStr
    password: str

class Token(BaseModel):
    """
    인증 토큰 응답을 위한 Pydantic 스키마.
    액세스 토큰과 토큰 타입을 포함합니다.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    토큰 페이로드에서 추출된 데이터를 위한 Pydantic 스키마.
    주로 이메일 정보를 포함합니다.
    """
    email: EmailStr | None = None

class User(BaseModel):
    """
    사용자 정보 응답을 위한 Pydantic 스키마.
    사용자 ID와 이메일을 포함합니다.
    """
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class PasswordResetRequest(BaseModel):
    """
    비밀번호 재설정 요청을 위한 스키마.
    """
    email: EmailStr

class PasswordReset(BaseModel):
    """
    비밀번호 재설정을 위한 스키마.
    """
    token: str
    new_password: str
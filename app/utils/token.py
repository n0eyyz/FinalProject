
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.schemas.auth import TokenData

SECRET_KEY = "your-secret-key"  # This should be loaded from environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """
    주어진 데이터를 사용하여 액세스 토큰을 생성합니다.
    토큰에는 만료 시간(ACCESS_TOKEN_EXPIRE_MINUTES)이 포함됩니다.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """
    주어진 JWT 토큰을 검증하고, 토큰에서 추출한 데이터를 TokenData 객체로 반환합니다.
    토큰이 유효하지 않거나 디코딩에 실패하면 credentials_exception을 발생시킵니다.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    return token_data

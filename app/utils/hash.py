from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """
    평문 비밀번호와 해시된 비밀번호를 비교하여 일치하는지 확인합니다.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    주어진 비밀번호를 해싱합니다.
    """
    return pwd_context.hash(password)
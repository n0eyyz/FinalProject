from sqlalchemy.orm import Session
import models
from sqlalchemy.orm import Session

def get_user_by_email(db: Session, email: str):
    """
    주어진 이메일에 해당하는 사용자(Users) 객체를 데이터베이스에서 조회합니다.
    """
    return db.query(models.Users).filter(models.Users.email == email).first()

def create_user(db: Session, user: models.Users):
    """
    새로운 사용자(Users) 객체를 데이터베이스에 추가합니다.
    """
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
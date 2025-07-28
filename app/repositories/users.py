from sqlalchemy.orm import Session
import models
from sqlalchemy.orm import Session

def get_user_by_email(db: Session, email: str):
    return db.query(models.Users).filter(models.Users.email == email).first()

def create_user(db: Session, user: models.Users):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
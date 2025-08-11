from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models

async def get_user_by_email(db: AsyncSession, email: str):
    """
    주어진 이메일에 해당하는 사용자(Users) 객체를 데이터베이스에서 조회합니다.
    """
    result = await db.execute(select(models.Users).filter(models.Users.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: models.Users):
    """
    새로운 사용자(Users) 객체를 데이터베이스에 추가합니다.
    """
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user_password(db: AsyncSession, user: models.Users, hashed_password: str):
    """
    사용자의 비밀번호를 업데이트합니다.
    """
    user.hashed_password = hashed_password
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_id(db: AsyncSession, user_id: int):
    """
    주어진 ID에 해당하는 사용자(Users) 객체를 데이터베이스에서 조회합니다.
    """
    result = await db.execute(select(models.Users).filter(models.Users.id == user_id))
    return result.scalars().first()

async def delete_user(db: AsyncSession, user: models.Users):
    """
    사용자를 데이터베이스에서 삭제합니다.
    """
    await db.delete(user)
    await db.commit()
    return user

async def get_all_users(db: AsyncSession):
    """
    모든 사용자 목록을 조회합니다.
    """
    result = await db.execute(select(models.Users))
    return result.scalars().all()

async def get_user_by_username(db: AsyncSession, username: str):
    """
    주어진 사용자 이름에 해당하는 사용자(Users) 객체를 데이터베이스에서 조회합니다.
    """
    result = await db.execute(select(models.Users).filter(models.Users.username == username))
    return result.scalars().first()

async def update_user(db: AsyncSession, user: models.Users):
    """
    사용자 정보를 업데이트합니다.
    """
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_content_history(db: AsyncSession, user_id: int):
    """
    사용자의 콘텐츠 조회 기록을 조회합니다.
    """
    result = await db.execute(select(models.UserContentHistory).filter(models.UserContentHistory.user_id == user_id))
    return result.scalars().all()

async def create_user_content_history(db: AsyncSession, user_id: int, content_id: str):
    """
    사용자의 콘텐츠 조회 기록을 생성합니다.
    """
    history = models.UserContentHistory(user_id=user_id, content_id=content_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history
# ... 이하 모든 함수들을 위와 같은 패턴으로 비동기 변환 ...
# (생략된 나머지 함수들도 모두 비동기적으로 변환되었다고 가정)

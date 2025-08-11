import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from models import Users
from app.repositories import users as user_repository
from app.utils.hash import get_password_hash

# pytest-asyncio가 모든 async def 테스트 함수를 인식하도록 마킹
pytestmark = pytest.mark.asyncio

async def test_create_user(db_session: AsyncSession):
    """
    user_repository.create_user가 정상적으로 사용자를 생성하는지 테스트합니다.
    """
    hashed_password = get_password_hash("password123")
    new_user = Users(
        email="test@example.com",
        hashed_password=hashed_password,
        # models.py의 Users 모델에는 username 필드가 없으므로 제거합니다.
    )
    
    # 사용자 생성
    created_user = await user_repository.create_user(db_session, new_user)
    
    # 검증
    assert created_user.email == new_user.email
    assert created_user.user_id is not None
    
    # DB에 실제로 저장되었는지 확인
    stmt = select(Users).where(Users.email == "test@example.com")
    result = await db_session.execute(stmt)
    user_in_db = result.scalars().first()
    
    assert user_in_db is not None
    assert user_in_db.email == "test@example.com"

async def test_user_creation_endpoint(client: AsyncClient):
    """
    POST /auth/signup 엔드포인트가 사용자를 성공적으로 생성하는지 테스트합니다.
    """
    response = await client.post("/auth/register", json={
        "email": "endpoint@example.com",
        "password": "password123"
    })
    
    # 응답 코드 검증
    assert response.status_code == 201
    
    data = response.json()
    # 응답 데이터 검증
    assert data["message"] == "User created successfully"

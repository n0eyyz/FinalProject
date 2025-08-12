from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.users import UserContentHistoryResponse, Place
from app.repositories import locations as loc_repo
from app.dependencies import get_current_user
import models
from typing import List
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)

@router.get("/history", response_model=List[UserContentHistoryResponse])
async def get_user_content_history(
    db: AsyncSession = Depends(get_db),
    current_user: models.Users = Depends(get_current_user),
):
    """
    현재 로그인한 사용자의 콘텐츠 기록을 상세 정보와 함께 비동기적으로 조회합니다.
    """
    logger.info(f"API /history 호출됨. 사용자: {current_user.email}")
    history_records = await loc_repo.get_user_history_details(db, current_user.user_id)

    response_data = []
    for record in history_records:
        if not record.content:
            continue
        places_data = [Place.from_orm(p) for p in record.content.places]
        video_history = UserContentHistoryResponse(
            id=record.content.content_id,
            title=record.content.title,
            created_at=record.created_at,
            thumbnail_url=record.content.thumbnail_url,
            youtube_url=record.content.youtube_url,
            places=places_data,
        )
        response_data.append(video_history)

    logger.info(f"사용자 {current_user.email}의 콘텐츠 상세 기록 {len(response_data)}건 조회 완료.")
    return response_data

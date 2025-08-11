from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.youtube import URLRequest, PlaceResponse, Place, ApiVideoHistory
from app.repositories import locations as loc_repo
from app.utils import url as url_util
from app.dependencies import get_current_user
import models
from typing import List, Optional
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/youtube",
    tags=["youtube"],
)

from app.schemas.jobs import JobCreationResponse
from app.tasks import process_video_placeholder

@router.post("/process", response_model=JobCreationResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_youtube_url(
    request: URLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.Users] = Depends(get_current_user), # Optional user
):
    """
    YouTube URL 처리를 위한 작업을 Celery 큐에 등록하고 즉시 job_id를 반환합니다.
    """
    user_id = current_user.user_id if current_user else None
    requester = f"user_id {user_id}" if user_id else "guest"
    logger.info(f"URL 처리 요청 접수: {request.url} (요청자: {requester})")

    video_id = url_util.extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # Celery 작업을 비동기적으로 실행하고 task 객체를 받습니다.
    task = process_video_placeholder.apply_async(args=[request.url])

    # 사용자 히스토리는 즉시 저장
    if user_id:
        await loc_repo.create_user_content_history(db, user_id, video_id)

    logger.info(f"작업이 성공적으로 큐에 등록되었습니다. Job ID: {task.id}")

    # 클라이언트에게는 job_id를 포함한 응답을 즉시 보냅니다.
    return JobCreationResponse(job_id=task.id)

@router.get("/history", response_model=List[ApiVideoHistory])
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
        video_history = ApiVideoHistory(
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

@router.get("/places/{video_id}", response_model=List[Place])
async def get_places_for_video(video_id: str, db: AsyncSession = Depends(get_db)):
    """
    특정 video_id에 해당하는 장소 목록을 비동기적으로 조회합니다. (인증 불필요)
    """
    logger.info(f"API /places/{video_id} 호출됨.")
    places = await loc_repo.get_places_by_content_id(db, video_id)
    if not places:
        logger.warning(f"video_id {video_id}에 대한 장소 정보가 없습니다.")
        raise HTTPException(
            status_code=404, detail="해당 영상에 대한 장소 정보가 없습니다."
        )
    logger.info(f"video_id {video_id}에 대한 장소 {len(places)}개 조회 완료.")
    return [Place.from_orm(p) for p in places]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.youtube import URLRequest, PlaceResponse, Place
from app.repositories import locations as loc_repo
from app.utils import url as url_util
from app.dependencies import get_current_user
from app.tasks import process_youtube_url
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

@router.post("/process", response_model=PlaceResponse, status_code=status.HTTP_200_OK)
async def process_youtube_url_and_get_places(
    request: URLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.Users] = Depends(get_current_user), # Optional user
):
    """
    YouTube URL을 받아 동기적으로 처리하고, 추출된 장소 목록을 반환합니다.
    """
    user_id = current_user.user_id if current_user else None
    requester = f"user_id {user_id}" if user_id else "guest"
    logger.info(f"URL 처리 요청 접수: {request.url} (요청자: {requester})")

    video_id = url_util.extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # 1. 캐시 확인: 이미 분석된 비디오인지 데이터베이스에서 확인
    existing_content = await loc_repo.get_content_by_id(db, video_id)
    if existing_content:
        logger.info(f"이미 분석된 비디오: {video_id}. 캐시된 결과 반환.")
        if user_id:
            await loc_repo.create_user_content_history(db, user_id, video_id)
        places = await loc_repo.get_places_by_content_id(db, video_id)
        return PlaceResponse(mode="db", places=[Place.from_orm(p) for p in places])

    # 2. Celery가 없으므로 직접 함수를 호출합니다.
    try:
        result = await process_youtube_url(db, request.url, user_id)
        if result.get('status') == 'Failure':
            raise HTTPException(status_code=400, detail=result.get('message'))
        
        # 결과에서 장소 목록을 가져와서 반환합니다.
        places_data = result.get("places", [])
        places = [Place(**p) for p in places_data]
        return PlaceResponse(mode="new", places=places)

    except Exception as e:
        logger.error(f"URL 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
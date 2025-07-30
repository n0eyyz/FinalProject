from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.youtube import URLRequest, PlaceResponse, Place
from app.repositories import locations as loc_repo
from app.utils import url as url_util
from app.dependencies import get_current_user
import models
from typing import List, Optional
import logging

# 로거 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/youtube",
    tags=["youtube"],
)

def _process_url(db: Session, url: str, user_id: Optional[int] = None):
    """URL 처리를 위한 내부 헬퍼 함수"""
    requester = f"user_id {user_id}" if user_id else "guest"
    logger.info("="*50)
    logger.info(f"URL 처리 시작: {url} (요청자: {requester})")

    try:
        # 1. URL에서 비디오 ID 추출
        video_id = url_util.extract_video_id(url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        logger.info(f"...비디오 ID 추출 성공: {video_id}")

        # 2. DB에서 기존 정보 확인
        existing_places = loc_repo.get_places_by_content_id(db, video_id)
        if existing_places:
            logger.info(f"...기존 장소 정보 {len(existing_places)}개 발견. 'db' 모드로 응답합니다.")
            if user_id:
                loc_repo.create_user_content_history(db, user_id, video_id)
                logger.info(f"...사용자 {user_id} 히스토리 저장 완료.")
            return PlaceResponse(mode="db", places=[Place.from_orm(p) for p in existing_places])

        # 3. DB에 정보가 없으면 새로 추출 및 저장
        logger.info("...기존 정보 없음. 새로운 장소 추출 및 저장 시작...")
        new_places = loc_repo.extract_and_save_locations(db, video_id, url)
        
        if not new_places:
            logger.info("...새로 추출된 장소가 없어 'new' 모드(빈 배열)로 응답합니다.")
            return PlaceResponse(mode="new", places=[])

        logger.info(f"...새로운 장소 {len(new_places)}개 추출 및 저장 완료. 'new' 모드로 응답합니다.")
        if user_id:
            loc_repo.create_user_content_history(db, user_id, video_id)
            logger.info(f"...사용자 {user_id} 히스토리 저장 완료.")
        
        return PlaceResponse(mode="new", places=[Place.from_orm(p) for p in new_places])

    except HTTPException as e:
        logger.error(f"HTTP 예외 발생: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("[CRITICAL] 처리되지 않은 심각한 예외 발생!")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

@router.post("/process", response_model=PlaceResponse)
def process_youtube_url_for_logged_in_user(
    request: URLRequest,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    (로그인 사용자 전용) YouTube URL을 받아 장소 정보를 추출하고 사용자 히스토리를 기록합니다.
    """
    return _process_url(db, request.url, current_user.user_id)

@router.post("/without-login/process", response_model=PlaceResponse)
def process_youtube_url_for_guest(
    request: URLRequest,
    db: Session = Depends(get_db)
):
    """
    (비로그인 사용자용) YouTube URL을 받아 장소 정보를 추출합니다. 히스토리는 기록하지 않습니다.
    """
    return _process_url(db, request.url, user_id=None)

@router.get("/history", response_model=List[str])
def get_user_content_history(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    현재 로그인한 사용자의 콘텐츠 기록(content_id 목록)을 조회합니다.
    """
    logger.info(f"API /history 호출됨. 사용자: {current_user.email}")
    content_ids = loc_repo.get_content_ids_by_user_id(db, current_user.user_id)
    logger.info(f"사용자 {current_user.email}의 콘텐츠 기록 조회 완료: {content_ids}")
    return content_ids

@router.get("/places/{video_id}", response_model=List[Place])
def get_places_for_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 video_id에 해당하는 장소 목록을 조회합니다. (인증 불필요)
    """
    logger.info(f"API /places/{video_id} 호출됨.")
    places = loc_repo.get_places_by_content_id(db, video_id)
    if not places:
        logger.warning(f"video_id {video_id}에 대한 장소 정보가 없습니다.")
        raise HTTPException(status_code=404, detail="해당 영상에 대한 장소 정보가 없습니다.")
    logger.info(f"video_id {video_id}에 대한 장소 {len(places)}개 조회 완료.")
    return [Place.from_orm(p) for p in places]

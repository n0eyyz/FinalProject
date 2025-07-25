from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.youtube import URLRequest, PlaceResponse, Place
from app.repositories import locations as loc_repo
from app.utils import url as url_util
from typing import List
import json
from urllib.parse import quote
import logging

# 기본 로거 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/youtube",
    tags=["youtube"],
)

@router.post("/process", response_model=PlaceResponse)
def process_youtube_url(
    request: URLRequest,
    db: Session = Depends(get_db)
):
    logger.info("="*50)
    logger.info("API /process 호출됨. 요청 URL: %s", request.url)
    try:
        # 1. URL에서 비디오 ID 추출
        logger.info("[1/5] URL에서 비디오 ID 추출 시작...")
        video_id = url_util.extract_video_id(request.url)
        if not video_id:
            logger.error("...비디오 ID 추출 실패. 잘못된 URL.")
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        logger.info("...비디오 ID 추출 성공: %s", video_id)

        # 2. (Mode 1) DB에서 기존 정보 확인
        logger.info("[2/5] DB에서 기존 장소 정보 확인 시작...")
        existing_places = loc_repo.get_places_by_content_id(db, video_id)
        logger.info("...DB 확인 완료. %d개의 장소 발견.", len(existing_places) if existing_places else 0)
        
        if existing_places:
            places_dto = [Place.from_orm(p) for p in existing_places]
            logger.info("...기존 정보가 있어 'db' 모드로 응답합니다.")
            logger.info("="*50)
            return PlaceResponse(mode="db", places=places_dto)

        # 3. (Mode 2) DB에 정보가 없으면 새로 추출 및 저장
        logger.info("[3/5] DB에 정보 없음. 새로운 장소 추출 및 저장 시작...")
        new_places = loc_repo.extract_and_save_locations(db, video_id, request.url)
        logger.info("...새로운 장소 추출 및 저장 완료. %d개의 장소 발견.", len(new_places) if new_places else 0)

        if not new_places:
            logger.info("[4/5] 새로 추출된 장소가 없어 'new' 모드(빈 배열)로 응답합니다.")
            logger.info("="*50)
            return PlaceResponse(mode="new", places=[])
        
        logger.info("[5/5] 최종 응답 준비...")
        places_dto = [Place.from_orm(p) for p in new_places]
        logger.info("...'new' 모드로 응답합니다.")
        logger.info("="*50)
        return PlaceResponse(mode="new", places=places_dto)

    except HTTPException as e:
        logger.error("HTTP 예외 발생: %s", e.detail)
        raise e
    except Exception as e:
        logger.exception("[CRITICAL] 처리되지 않은 심각한 예외 발생!")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")


@router.get("/view/{video_id}", status_code=302)
def view_locations_on_map(video_id: str, db: Session = Depends(get_db)):
    """
    video_id에 해당하는 장소들을 pind_web_map에서 보여주도록 리다이렉트합니다.
    """
    logger.info("="*50)
    logger.info("API /view/%s 호출됨", video_id)
    try:
        # 1. DB에서 해당 video_id로 저장된 장소들을 가져옵니다.
        logger.info("[1/3] DB에서 장소 정보 조회 시작...")
        places_models = loc_repo.get_places_by_content_id(db, video_id)
        logger.info("...DB 조회 완료. %d개의 장소 발견.", len(places_models) if places_models else 0)

        if not places_models:
            logger.error("...장소 정보 없음.")
            raise HTTPException(status_code=404, detail="해당 영상에 대한 장소 정보가 없습니다.")

        # 2. Pydantic 스키마를 사용해 Python dict 리스트로 변환합니다.
        logger.info("[2/3] 장소 정보 변환 및 인코딩 시작...")
        places_list = [Place.from_orm(p).dict() for p in places_models]
        locations_json_string = json.dumps(places_list)
        encoded_locations = quote(locations_json_string)
        logger.info("...인코딩 완료.")

        # 3. pind_web_map URL에 locations 파라미터로 데이터를 담아 최종 URL을 생성합니다.
        logger.info("[3/3] 리다이렉트 URL 생성 및 응답...")
        map_url = f"https://chaejoon23.github.io/pind_web_map/?locations={encoded_locations}"
        logger.info("...리다이렉트 URL: %s", map_url)
        logger.info("="*50)
        return RedirectResponse(url=map_url)
    
    except HTTPException as e:
        logger.error("HTTP 예외 발생: %s", e.detail)
        raise e
    except Exception as e:
        logger.exception("[CRITICAL] 처리되지 않은 심각한 예외 발생!")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")
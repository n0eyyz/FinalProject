from fastapi import APIRouter, HTTPException, status, Depends # Added Depends
from celery.result import AsyncResult
from app.celery_config import celery_app
from app.schemas.jobs import JobStatusResponse, JobResultResponse
from app.schemas.users import Place # Import Place from users schema
import logging
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession
from app.db.database import get_db # Added get_db
from app.repositories import locations as loc_repo # Added loc_repo

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["jobs"],
)

# Dictionary to hold active WebSocket connections
# In a real-world app, this should be more robust (e.g., Redis Pub/Sub)
# For simplicity, we'll use a dictionary for now.
active_connections: dict[str, list[WebSocket]] = {}

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for job_id: {job_id}")

    if job_id.startswith("cached_"):
        # For cached jobs, send immediate success and close
        await websocket.send_json({
            "status": "SUCCESS",
            "meta": {"current_step": "Completed (Cached)", "progress": 100}
        })
        await websocket.close()
        logger.info(f"WebSocket for cached job_id {job_id} closed after sending success.")
        return

    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)
    
    try:
        while True:
            # Get task status from Celery result backend
            task_result = AsyncResult(job_id, app=celery_app) # Use celery_app here
            status = task_result.state
            meta = task_result.info

            # Send status to client
            await websocket.send_json({"status": status, "meta": meta})

            if status in ['SUCCESS', 'FAILURE', 'REVOKED']:
                break # Task finished, close connection from server side
            
            await asyncio.sleep(1) # Poll every 1 second

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job_id: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job_id {job_id}: {e}")
    finally:
        if websocket in active_connections[job_id]:
            active_connections[job_id].remove(websocket)
        if not active_connections[job_id]:
            del active_connections[job_id]
        await websocket.close()

@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)): # Add db dependency
    """Celery 작업 ID를 사용하여 작업의 현재 상태와 진행률을 조회합니다."""
    logger.info(f"[API] Job 상태 확인 요청: {job_id}")

    if job_id.startswith("cached_"):
        video_id = job_id.replace("cached_", "")
        # Check if the content actually exists in DB for this cached_job_id
        content = await loc_repo.get_content_by_id(db, video_id) # Use loc_repo
        if content:
            response = {
                "job_id": job_id,
                "status": "SUCCESS",
                "progress": 100,
                "current_step": "Completed (Cached)"
            }
            return response
        else:
            # If it's a cached_job_id but content not found, treat as not found
            raise HTTPException(status_code=404, detail="Cached job not found or expired.")

    task_result = AsyncResult(job_id, app=celery_app)

    response = {
        "job_id": job_id,
        "status": task_result.status,
        "progress": 0,
        "current_step": "N/A"
    }

    if task_result.status == "PROGRESS":
        meta = task_result.info or {}
        response["progress"] = meta.get("progress", 0)
        response["current_step"] = meta.get("current_step", "processing")
    elif task_result.status == "SUCCESS":
        response["progress"] = 100
        response["current_step"] = "Completed"
    
    return response

@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str, db: AsyncSession = Depends(get_db)): # Add db dependency
    """Celery 작업 ID를 사용하여 작업의 최종 결과를 조회합니다."""
    logger.info(f"[API] Job 결과 확인 요청: {job_id}")

    if job_id.startswith("cached_"):
        video_id = job_id.replace("cached_", "")
        places = await loc_repo.get_places_by_content_id(db, video_id)
        if not places:
            raise HTTPException(status_code=404, detail="Cached result not found.")
        return {
            "job_id": job_id,
            "status": "SUCCESS",
            "places": [Place.from_orm(p) for p in places],
            "processing_time": 0 # Cached result, so 0 or N/A
        }

    task_result = AsyncResult(job_id, app=celery_app)

    if not task_result.ready():
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Job is not yet completed. Please check status first."
        )

    if task_result.failed():
        return {
            "job_id": job_id,
            "status": "FAILURE",
            "error_message": str(task_result.info)
        }

    result = await task_result.get()
    return {
        "job_id": job_id,
        "status": "SUCCESS",
        "places": result.get("places", []),
        "processing_time": result.get("processing_time")
    }

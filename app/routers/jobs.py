from fastapi import APIRouter, HTTPException, status
from celery.result import AsyncResult
from app.celery_config import celery_app
from app.schemas.jobs import JobStatusResponse, JobResultResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["jobs"],
)

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """Celery 작업 ID를 사용하여 작업의 현재 상태와 진행률을 조회합니다."""
    logger.info(f"[API] Job 상태 확인 요청: {job_id}")
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
def get_job_result(job_id: str):
    """Celery 작업 ID를 사용하여 작업의 최종 결과를 조회합니다."""
    logger.info(f"[API] Job 결과 확인 요청: {job_id}")
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

    result = task_result.get()
    return {
        "job_id": job_id,
        "status": "SUCCESS",
        "places": result.get("places", []),
        "processing_time": result.get("processing_time")
    }

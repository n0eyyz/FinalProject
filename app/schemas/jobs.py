from pydantic import BaseModel, Field
from typing import List, Optional, Any
from .youtube import Place

class JobCreationResponse(BaseModel):
    job_id: str = Field(..., description="생성된 작업의 고유 ID")
    status: str = Field("queued", description="작업의 현재 상태")
    estimated_time: str = Field("10-20초", description="예상 처리 시간 (테스트용)")

class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="작업의 고유 ID")
    status: str = Field(..., description="작업의 현재 상태 (e.g., PENDING, PROGRESS, SUCCESS)")
    progress: int = Field(0, description="작업 진행률 (0-100)")
    current_step: Optional[str] = Field(None, description="현재 진행 중인 단계")
    estimated_remaining: Optional[str] = Field(None, description="남은 예상 시간")

class JobResultResponse(BaseModel):
    job_id: str = Field(..., description="작업의 고유 ID")
    status: str = Field(..., description="작업의 최종 상태")
    places: Optional[List[Place]] = Field(None, description="추출된 장소 목록")
    processing_time: Optional[float] = Field(None, description="총 처리 시간(초)")
    error_message: Optional[str] = Field(None, description="실패 시 에러 메시지")

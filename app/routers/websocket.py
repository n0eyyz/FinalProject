from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.utils import url as url_util
from app.tasks import process_youtube_url_with_websocket
from typing import Dict, Set
import logging
import json
import uuid

# 로거 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()

# 활성 WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket 연결 성공: {connection_id}")

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket 연결 종료: {connection_id}")

    async def send_progress(self, connection_id: str, data: dict):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(data, ensure_ascii=False))
                logger.info(f"진행 상황 전송 완료: {connection_id} - {data}")
            except Exception as e:
                logger.error(f"WebSocket 메시지 전송 실패: {connection_id} - {e}")
                self.disconnect(connection_id)

manager = ConnectionManager()

@router.websocket("/ws/process")
async def websocket_process_endpoint(websocket: WebSocket):
    """
    YouTube URL 처리를 위한 WebSocket 엔드포인트
    실시간으로 처리 진행 상황을 클라이언트에게 전송합니다.
    """
    connection_id = str(uuid.uuid4())
    await manager.connect(websocket, connection_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "process_url":
                url = message.get("url")
                user_identifier = message.get("user_id")  # 이메일 또는 user_id일 수 있음
                
                # user_identifier가 이메일인 경우 실제 user_id로 변환
                actual_user_id = None
                if user_identifier:
                    if isinstance(user_identifier, str) and "@" in user_identifier:
                        # 이메일인 경우 데이터베이스에서 사용자 조회
                        from app.db.database import AsyncSessionLocal
                        from app.repositories.users import get_user_by_email
                        async with AsyncSessionLocal() as db:
                            user = await get_user_by_email(db, user_identifier)
                            if user:
                                actual_user_id = user.user_id
                                logger.info(f"이메일 {user_identifier}를 user_id {actual_user_id}로 변환")
                    else:
                        # 이미 정수 user_id인 경우
                        try:
                            actual_user_id = int(user_identifier)
                        except (ValueError, TypeError):
                            logger.warning(f"유효하지 않은 user_id: {user_identifier}")
                
                if not url:
                    await manager.send_progress(connection_id, {
                        "status": "error",
                        "message": "URL이 제공되지 않았습니다."
                    })
                    continue
                
                # URL 유효성 검사
                video_id = url_util.extract_video_id(url)
                if not video_id:
                    await manager.send_progress(connection_id, {
                        "status": "error", 
                        "message": "유효하지 않은 YouTube URL입니다."
                    })
                    continue
                
                # 처리 시작
                await manager.send_progress(connection_id, {
                    "status": "started",
                    "message": "처리를 시작합니다...",
                    "progress": 0
                })
                
                try:
                    # WebSocket을 통해 진행 상황을 실시간 전송하며 처리
                    result = await process_youtube_url_with_websocket(
                        url, actual_user_id, connection_id, manager
                    )
                    
                    # 최종 결과 전송
                    await manager.send_progress(connection_id, {
                        "status": "completed",
                        "message": "처리가 완료되었습니다!",
                        "progress": 100,
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"처리 중 오류 발생: {e}")
                    await manager.send_progress(connection_id, {
                        "status": "error",
                        "message": f"처리 중 오류가 발생했습니다: {str(e)}",
                        "progress": 0
                    })
                    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"클라이언트가 연결을 종료했습니다: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        manager.disconnect(connection_id)

# ConnectionManager를 다른 모듈에서 사용할 수 있도록 export
def get_connection_manager():
    return manager
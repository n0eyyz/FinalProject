from celery import Celery
import os

import os, sys
from pathlib import Path

# app/ 의 부모 = 프로젝트 루트 (C:\pind_server)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 읽어서 os.environ에 로드

# Redis 서버의 주소를 환경 변수에서 가져오거나, 없을 경우 기본값으로 설정합니다.
# 이 주소는 Celery가 작업을 받아가고(브로커), 결과를 저장하는(백엔드) 데 사용됩니다.
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Celery 애플리케이션을 생성합니다.
# - "tasks": Celery 앱의 이름입니다.
# - broker: 메시지 큐(Redis)의 주소입니다.
# - backend: 작업의 상태와 결과를 저장할 곳(Redis)의 주소입니다.
# - include: Celery 워커가 시작될 때 자동으로 찾아낼 작업 모듈의 목록입니다.
celery_app = Celery(
    "pind"
)
celery_app.conf.update(
    broker_url=broker_url,
    result_backend=backend_url,
    broker_connection_retry_on_startup=os.getenv("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP", "true").lower() in ("1","true","yes"),
    redis_socket_timeout=float(os.getenv("CELERY_REDIS_SOCKET_TIMEOUT", "5")),
    redis_retry_on_timeout=os.getenv("CELERY_REDIS_RETRY_ON_TIMEOUT", "true").lower() in ("1","true","yes"),
    task_track_started=True,
)

try:
    celery_app.autodiscover_tasks(["app"])
except Exception:
    pass

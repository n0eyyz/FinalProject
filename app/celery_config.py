from celery import Celery
import os

# Redis 서버의 주소를 환경 변수에서 가져오거나, 없을 경우 기본값으로 설정합니다.
# 이 주소는 Celery가 작업을 받아가고(브로커), 결과를 저장하는(백엔드) 데 사용됩니다.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 애플리케이션을 생성합니다.
# - "tasks": Celery 앱의 이름입니다.
# - broker: 메시지 큐(Redis)의 주소입니다.
# - backend: 작업의 상태와 결과를 저장할 곳(Redis)의 주소입니다.
# - include: Celery 워커가 시작될 때 자동으로 찾아낼 작업 모듈의 목록입니다.
celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

# Celery 추가 설정
celery_app.conf.update(
    # 작업이 시작되었을 때 상태를 'STARTED'로 보고하도록 설정합니다.
    task_track_started=True,
)

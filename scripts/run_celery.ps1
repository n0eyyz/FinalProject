# run_celery.ps1

# 프로젝트 루트로 이동
Set-Location "C:\pind_server"

# Conda 환경 활성화
conda activate finalproj

# Celery 실행
python -m celery -A app.celery_config.celery_app worker -l info --pool=solo --concurrency=1

@echo off
REM 프로젝트 루트로 이동
cd /d C:\pind_server

REM Conda 초기화 (conda-hook.ps1 대신 직접)
CALL C:\Users\user\miniforge3\Scripts\activate.bat finalproj

REM Celery 실행
python -m celery -A app.celery_config.celery_app worker -l info --pool=solo --concurrency=1

#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
새로운 개발 환경에서 데이터베이스를 설정할 때 사용합니다.
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 프로젝트 루트 디렉토리로 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
load_dotenv(project_root / '.env')


def check_database_connection():
    """데이터베이스 연결 확인"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 DATABASE_URL을 설정해주세요.")
        return False
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False


def run_alembic_migrations():
    """Alembic 마이그레이션 실행"""
    print("\n🔄 Alembic 마이그레이션 실행 중...")
    
    try:
        # 현재 마이그레이션 상태 확인
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        print(f"현재 마이그레이션 상태:\n{result.stdout}")
        
        # 마이그레이션 적용
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ 마이그레이션 성공적으로 적용됨")
            print(result.stdout)
            return True
        else:
            print("❌ 마이그레이션 실패")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ alembic 명령어를 찾을 수 없습니다. alembic이 설치되어 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류 발생: {e}")
        return False


def create_initial_data():
    """초기 데이터 생성 (선택사항)"""
    print("\n📝 초기 데이터 생성을 건너뜁니다. (필요시 이 함수를 구현하세요)")
    # 예시:
    # from app.db.database import SessionLocal
    # from app.repositories.user import UserRepository
    # 
    # db = SessionLocal()
    # try:
    #     user_repo = UserRepository(db)
    #     # 초기 사용자 생성 등
    # finally:
    #     db.close()
    pass


def main():
    """메인 실행 함수"""
    print("🚀 데이터베이스 초기화 시작\n")
    
    # 1. 데이터베이스 연결 확인
    if not check_database_connection():
        print("\n⚠️  데이터베이스 연결을 먼저 확인해주세요.")
        sys.exit(1)
    
    # 2. Alembic 마이그레이션 실행
    if not run_alembic_migrations():
        print("\n⚠️  마이그레이션 실행에 실패했습니다.")
        sys.exit(1)
    
    # 3. 초기 데이터 생성 (선택사항)
    create_initial_data()
    
    print("\n✨ 데이터베이스 초기화 완료!")
    print("   서버를 실행할 준비가 되었습니다:")
    print("   uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
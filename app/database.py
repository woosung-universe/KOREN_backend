from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# PostgreSQL 연결 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# 세션 로컬 클래스
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 의존성 (Dependency)
def get_db() -> Session:
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
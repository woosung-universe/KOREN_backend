from sqlalchemy.orm import Session
from datetime import datetime
from app.models import CommunicationSummary

# CommunicationSummary
def create_communication_summary(db: Session, summary_json: dict):
  """CommunicationSummary DB 저장"""
  db_summary = CommunicationSummary(
      summary_created_at=datetime.utcnow(),
      summary=summary_json["summary"]
  )
  db.add(db_summary)
  db.commit()
  db.refresh(db_summary)
  return db_summary

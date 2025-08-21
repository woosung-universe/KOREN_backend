from sqlalchemy.orm import Session
from datetime import datetime
from app.models import CommunicationSummary

# CommunicationSummary
def create_communication_summary(db: Session, summary_json: dict):
  """CommunicationSummary DB 저장"""
  db_summary = CommunicationSummary(
      summary_created_at=datetime.utcnow(),
      doctor_notes=summary_json["doctor_notes"],
      patient_concerns=summary_json["patient_concerns"],
      care_plans=summary_json["recommended_actions"],  # recommended_actions → DB의 care_plans
      prescription=summary_json["prescription"],
  )
  db.add(db_summary)
  db.commit()
  db.refresh(db_summary)
  return db_summary

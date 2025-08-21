from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
import os
import json

from app.database import get_db
from app import crud, models

router = APIRouter()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 입력 DTO
class ConversationInput(BaseModel):
  patient_id: str
  conversation: str  # STT된 대화 텍스트

# CommunicationSummary 출력 DTO (DB 저장용)
class CommunicationSummaryDTO(BaseModel):
  doctor_notes: str
  patient_concerns: str
  care_plans: str
  prescription: str

@router.post("/summarize", response_model=dict)
def create_summary(input_data: ConversationInput, db: Session = Depends(get_db)):
  try:
    # STT 기반 대화 요약 (CommunicationSummary)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
          {"role": "system", "content": "You are a medical assistant. Summarize the doctor-patient conversation."},
          {"role": "user", "content": f"""
대화:
\"\"\"{input_data.conversation}\"\"\"

대화 텍스트에는 화자 정보가 없습니다. 
문맥을 보고 의사와 환자 중 누가 말하는지 추론하여 JSON으로 요약하십시오:
{{
  "의사 소견": "...",
  "환자의 우려점": "...",
  "진료 계획": "...",
  "처방": "..."
}}
"""}
        ],
        response_format={"type": "json_object"}
    )

    # JSON 파싱
    summary_json_kor = response.choices[0].message.parsed

    #  ️CommunicationSummary DB 저장
    summary_text = json.dumps(summary_json_kor, ensure_ascii=False)

    # 3️total_diagnosis_summary 갱신
    patient = db.query(models.Patient).filter(models.Patient.patient_id == input_data.patient_id).first()
    if not patient:
      raise HTTPException(status_code=404, detail="Patient not found")

    # 이전 total_diagnosis_summary 불러오기
    prev_total_summary = patient.total_diagnosis_summary or ""

    # LLM에게 누적 요약 요청
    total_summary_prompt = f"""
당신은 의료 기록 요약 전문가입니다.
다음은 이전까지의 환자 총 진료 요약입니다:
\"\"\"{prev_total_summary}\"\"\"

이번 새 진료 요약 내용:
\"\"\"{summary_text}\"\"\"

이 정보를 기반으로 환자의 상태, 처방 및 진료 내용, 진료 계획을 한글 JSON으로 최신화하여 통합 요약해주세요:
{{
  "환자의 상태": "",
  "처방 및 진료 내용": "",
  "진료 계획": ""
}}
"""
    total_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
          {"role": "system", "content": "You are a medical record summarizer."},
          {"role": "user", "content": total_summary_prompt}
        ],
        response_format={"type": "json_object"}
    )

    total_summary_json = total_response.choices[0].message.parsed
    patient.total_diagnosis_summary = json.dumps(total_summary_json, ensure_ascii=False)
    db.commit()

    return summary_json_kor  # 프론트엔드에는 STT 요약 JSON 그대로 반환

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

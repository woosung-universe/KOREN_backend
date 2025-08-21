from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
import os

from app.database import get_db
from app import crud

router = APIRouter()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 입력 DTO
class ConversationInput(BaseModel):
  conversation: str  # STT된 대화 텍스트


# 출력 DTO (DB 저장용)
class CommunicationSummaryDTO(BaseModel):
  doctor_notes: str
  patient_concerns: str
  care_plans: str
  prescription: str


@router.post("/summarize", response_model=dict)  # 프론트엔드에는 한글 키 그대로 전달
def create_summary(input_data: ConversationInput, db: Session = Depends(get_db)):
  try:
    # OpenAI API 호출 (JSON mode)
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
        response_format={"type": "json_object"}  # JSON mode
    )

    # OpenAI 응답 JSON 파싱
    summary_json_kor = response.choices[0].message.parsed

    # 한글 키 → 영어 키 매핑 (DB 저장용)
    summary_json_en = {
      "doctor_notes": summary_json_kor.get("의사 소견", ""),
      "patient_concerns": summary_json_kor.get("환자의 우려점", ""),
      "care_plans": summary_json_kor.get("진료 계획", ""),
      "prescription": summary_json_kor.get("처방", "")
    }

    # DB 저장
    crud.create_communication_summary(db, summary_json_en)

    # 프론트엔드에는 한글 키 그대로 반환
    return summary_json_kor

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

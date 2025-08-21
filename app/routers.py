import Form
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
import os
import json

from app.database import get_db
from app import crud, models
from model_loader import load_model
from utils import preprocess_image

router = APIRouter()

# 모델 로드
model = load_model("../workspace/clientResults/base_model072.h5")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Post: 진단하기
@router.post("/diagnose")
async def diagnose(
    file: UploadFile = File(...),
    patient_name: str = Form(...),
    patient_age: int = Form(...),
    patient_id: str = Form(...),
    patient_sex: str = Form(...),
    anatomy_site: str = Form(...),
    db: Session = Depends(get_db)
):
  try:
    # 환자 조회 / 생성
    patient = db.query(models.Patient).filter(models.Patient.patient_id==patient_id).first()
    if not patient:
      patient = models.Patient(
          patient_id=patient_id,
          name=patient_name,
          age=patient_age,
          sex=patient_sex
      )
      db.add(patient)
      db.commit()
      db.refresh(patient)

    # 이미지 저장
    contents = await file.read()
    image = preprocess_image(contents)
    image_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = f"./uploads/{image_name}"
    os.makedirs("./uploads", exist_ok=True)
    with open(file_path, "wb") as f:
      f.write(contents)

    medical_image = models.MedicalImage(
        image_name=image_name,
        patient_id=patient.id,
        file_path=file_path,
        anatomy_site=anatomy_site
    )
    db.add(medical_image)
    db.commit()
    db.refresh(medical_image)

    # AI 모델 예측
    pred = model.predict(image)[0][0]
    confidence = float(pred)
    diagnosis_result = "malignant" if confidence > 0.5 else "benign"
    target_value = 1 if diagnosis_result=="malignant" else 0
    ai_description = f"AI predicted {diagnosis_result} with confidence {confidence:.2f}"

    # Diagnosis 생성
    diagnosis = models.Diagnosis(
        patient_id=patient.id,
        medical_image_id=medical_image.id,
        communication_summary_id=None,
        diagnosis=diagnosis_result,
        confidence_score=confidence,
        target_value=target_value,
        diagnosed_by="AI_MODEL",
        ai_description=ai_description,
        diagnosed_at=datetime.utcnow()
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    # total_diagnosis_summary 가져오기
    total_summary = patient.total_diagnosis_summary

    return JSONResponse(content={
      "total_diagnosis_summary": total_summary,
      "diagnosis": diagnosis_result,
      "medical_image_id": medical_image.id,
      "ai_description": ai_description
    })

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# GET: 진단 결과
@router.get("/diagnosis/{patient_id}")
def get_diagnosis(patient_id: str, db: Session = Depends(get_db)):
  patient = db.query(models.Patient).filter(models.Patient.patient_id==patient_id).first()
  if not patient:
    raise HTTPException(status_code=404, detail="Patient not found")

  # 최신 Diagnosis 가져오기
  diagnosis = db.query(models.Diagnosis) \
    .filter(models.Diagnosis.patient_id==patient.id) \
    .order_by(models.Diagnosis.diagnosed_at.desc()) \
    .first()
  if not diagnosis:
    raise HTTPException(status_code=404, detail="No diagnosis found for this patient")

  return {
    "total_diagnosis_summary": patient.total_diagnosis_summary,
    "diagnosis": diagnosis.diagnosis,
    "medical_image_id": diagnosis.medical_image_id,
    "ai_description": diagnosis.ai_description
  }



# Post: 대화 요약
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

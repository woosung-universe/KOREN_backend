from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# ENUM
class SexEnum(str, enum.Enum):
  male = "male"
  female = "female"

class AnatomySiteEnum(str, enum.Enum):
  head_neck = "head_neck"
  upper_extremity = "upper_extremity"
  lower_extremity = "lower_extremity"
  torso = "torso"

class DiagnosisEnum(str, enum.Enum):
  benign = "benign"
  malignant = "malignant"

# Patient
class Patient(Base):
  __tablename__ = "patients"

  id = Column(Integer, primary_key=True, index=True)
  patient_id = Column(String, unique=True, index=True)
  name = Column(String, nullable=False)
  age = Column(Integer)
  sex = Column(Enum(SexEnum))
  total_diagnosis_summary = Column(Text)  # 환자의 총 진료 기록을 요약한 현재 상태
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  medical_images = relationship("MedicalImage", back_populates="patient")
  diagnoses = relationship("Diagnosis", back_populates="patient")

# MedicalImage
class MedicalImage(Base):
  __tablename__ = "medical_images"

  id = Column(Integer, primary_key=True, index=True)
  image_name = Column(String, unique=True, index=True)
  patient_id = Column(Integer, ForeignKey("patients.id"))
  file_path = Column(String, nullable=False)
  anatomy_site = Column(Enum(AnatomySiteEnum))
  uploaded_at = Column(DateTime, default=datetime.utcnow)

  patient = relationship("Patient", back_populates="medical_images")
  diagnoses = relationship("Diagnosis", back_populates="medical_image")

# CommunicationSummary
class CommunicationSummary(Base):
  __tablename__ = "communication_summaries"

  id = Column(Integer, primary_key=True, index=True)
  summary_created_at = Column(DateTime, default=datetime.utcnow)
  summary = Column(Text)

  diagnosis = relationship("Diagnosis", back_populates="communication_summary", uselist=False)

# Diagnosis
class Diagnosis(Base):
  __tablename__ = "diagnoses"

  id = Column(Integer, primary_key=True, index=True)
  patient_id = Column(Integer, ForeignKey("patients.id"))
  medical_image_id = Column(Integer, ForeignKey("medical_images.id"))
  communication_summary_id = Column(Integer, ForeignKey("communication_summaries.id"))
  diagnosis = Column(Enum(DiagnosisEnum))
  confidence_score = Column(Float)
  target_value = Column(Integer)  # 0: benign, 1: malignant
  diagnosed_by = Column(String)  # AI_MODEL 또는 DOCTOR_NAME
  ai_description = Column(Text)
  diagnosed_at = Column(DateTime, default=datetime.utcnow)

  patient = relationship("Patient", back_populates="diagnoses")
  medical_image = relationship("MedicalImage", back_populates="diagnoses")
  communication_summary = relationship("CommunicationSummary", back_populates="diagnosis", uselist=False)

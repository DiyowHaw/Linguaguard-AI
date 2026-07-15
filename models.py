# models.py
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, JSON, Boolean, Text
from database import Base
from sqlalchemy.dialects.postgresql import JSONB
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), default='student')

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True) 
    
    exam_id = Column(Integer, ForeignKey("exams.id"))
    question_text = Column(Text)
    correct_option = Column(String(1))
    option_a = Column(String(255))
    option_b = Column(String(255))
    option_c = Column(String(255))
    option_d = Column(String(255))

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    student_name = Column(String(100))
    score = Column(Integer, default=0)
    
    # TAMBAHKAN KOLOM INI SESUAI DENGAN YANG DIKIRIM APP_UI.PY
    email = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    birth_city = Column(String(50), nullable=True)
    birth_date = Column(String(20), nullable=True)
    address = Column(String, nullable=True)

class SubmissionAnswer(Base):
    __tablename__ = "submissions_answers"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option = Column(String(1)) # Jawaban yang dipilih A/B/C/D
    is_correct = Column(Boolean) # Bisa diisi otomatis oleh sistem nanti

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    predicted_score = Column(Integer)
    shap_values = Column(JSONB) # Membutuhkan SQLAlchemy versi terbaru

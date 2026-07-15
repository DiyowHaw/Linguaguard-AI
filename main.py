from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from pydantic import BaseModel
from datetime import datetime
import models
import pytz
from typing import Optional


class AnswerRequest(BaseModel):
    submission_id: int
    question_id: int
    selected_option: str

# Membuat tabel di database
Base.metadata.create_all(bind=engine)

app = FastAPI()
WIB = pytz.timezone('Asia/Jakarta')

@app.get("/")
def read_root():
    return {"message": "Selamat datang di API LinguaGuard AI"}

@app.get("/start-exam/{exam_id}")
def start_exam(exam_id: int, db: Session = Depends(get_db)):
    # Ambil data ujian dari database
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Ujian tidak ditemukan")

    # Waktu sekarang dalam WIB
    now = datetime.now(WIB).replace(tzinfo=None)

    # Validasi Ketat
    if now < exam.start_time:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Ujian belum dimulai. Silakan tunggu hingga {exam.start_time}"
        )
    
    if now > exam.end_time:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Waktu pengerjaan ujian telah berakhir."
        )

    return {"message": "Akses diberikan. Silakan mulai mengerjakan ujian.", "exam_title": exam.title}

@app.post("/submit-answer")
def submit_answer(request: AnswerRequest, db: Session = Depends(get_db)):
    # 1. Cari soal untuk mendapatkan kunci jawaban
    question = db.query(models.Question).filter(models.Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Soal tidak ditemukan")

    # 2. Tentukan apakah jawaban benar
    is_correct = (request.selected_option.upper() == question.correct_option.upper())

    # 3. Simpan jawaban ke database (tabel submission_answers)
    new_answer = models.SubmissionAnswer(
        submission_id=request.submission_id,
        question_id=request.question_id,
        selected_option=request.selected_option.upper(),
        is_correct=is_correct
    )
    db.add(new_answer)

    # 4. TAMBAHAN: Update skor di tabel submissions
    if is_correct:
        submission = db.query(models.Submission).filter(models.Submission.id == request.submission_id).first()
        if submission:
            # Asumsi: setiap soal benar bernilai 10 poin
            submission.score = (submission.score or 0) + 10 
            db.add(submission)
    
    db.commit()
    db.refresh(new_answer)
    
    return {"message": "Jawaban berhasil disimpan", "is_correct": is_correct}

@app.get("/get-questions/{exam_id}")
def get_questions(exam_id: int, db: Session = Depends(get_db)):
    # Pastikan 'exam_id' di sisi database sama dengan yang dikirim dari aplikasi
    # Coba print dulu di terminal untuk memastikan
    print(f"Mencari soal untuk exam_id: {exam_id}")
    
    soal = db.query(models.Question).filter(models.Question.exam_id == exam_id).all()
    
    # Debug di terminal
    print(f"Ditemukan {len(soal)} soal")
    return soal

class SubmissionCreate(BaseModel):
    exam_id: int
    student_name: str
    email: Optional[str] = None
    gender: Optional[str] = None
    whatsapp: Optional[str] = None
    birth_city: Optional[str] = None
    birth_date: Optional[str] = None
    address: Optional[str] = None

@app.post("/create-submission")
def create_submission(sub: SubmissionCreate, db: Session = Depends(get_db)):
    # 2. PERBAIKAN PADA PEMETAAN: Pastikan semua field sesuai dengan models.Submission
    new_sub = models.Submission(
        exam_id=sub.exam_id,
        student_name=sub.student_name,
        email=sub.email,
        gender=sub.gender,
        whatsapp=sub.whatsapp,
        birth_city=sub.birth_city,
        birth_date=sub.birth_date,
        address=sub.address
    )
    
    try:
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub) # refresh agar ID database bisa dikembalikan
        return new_sub
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
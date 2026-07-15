# test_db.py
from database import engine, Base
from models import User, Exam, Question, Submission # Mengimpor model agar terdeteksi

def test_connection():
    try:
        # Mencoba membuat koneksi
        connection = engine.connect()
        print("✅ Koneksi ke database berhasil!")
        
        # Membuat tabel jika belum ada (opsional, tapi berguna untuk tes)
        Base.metadata.create_all(bind=engine)
        print("✅ Tabel-tabel telah diverifikasi/dibuat di database.")
        
        connection.close()
    except Exception as e:
        print(f"❌ Koneksi gagal. Error: {e}")

if __name__ == "__main__":
    test_connection()
import streamlit as st
import requests
import time
import re
import os
from datetime import date
from datetime import date, timedelta
from gtts import gTTS

# Konfigurasi Halaman
st.set_page_config(page_title="LinguaGuard AI", layout="centered")

# Inisialisasi Session State
if 'page' not in st.session_state: st.session_state['page'] = 'login'
if 'current_q_idx' not in st.session_state: st.session_state['current_q_idx'] = 0

# --- FUNGSI TIMER (Fragment) ---
@st.fragment(run_every="1s")
def display_timer():
    if 'start_time' in st.session_state:
        elapsed = time.time() - st.session_state['start_time']
        sisa_detik = (120 * 60) - elapsed
        if sisa_detik > 0:
            menit, detik = divmod(int(sisa_detik), 60)
            st.sidebar.metric("Time Remaining", f"{menit:02d}:{detik:02d}")
        else:
            st.sidebar.error("Time's up!")

# --- HALAMAN 1: Login ---
if st.session_state['page'] == 'login':
    st.title("Login Ujian")
    exam_id = st.text_input("ID Ujian:")
    
    if st.button("Next"):
        # PROTEKSI: Cek apakah ID Ujian diisi
        if not exam_id:
            st.error("Mohon masukkan ID Ujian terlebih dahulu!")
        else:
            # Opsional: Cek ke API apakah ID ujian valid
            resp = requests.get(f"http://127.0.0.1:8000/start-exam/{exam_id}")
            if resp.status_code == 200:
                st.session_state['exam_id'] = exam_id
                st.session_state['page'] = 'identitas'
                st.rerun()
            else:
                st.error("Exam ID not found!")

# --- HALAMAN 2: Identitas ---
elif st.session_state['page'] == 'identitas':
    st.title("Data Diri")
    with st.form("form_identitas"):
        nama = st.text_input("Nama Lengkap")
        email = st.text_input("Alamat Email")
        gender = st.selectbox("Gender", ["Male", "Female"])
        wa = st.text_input("No Whatsapp (Contoh: 08123456789)")
        kota = st.text_input("Kota Lahir")
        tgl = st.date_input(
            "Tgl Lahir",
            value=date(2000, 1, 1), # Tanggal default yang muncul
            min_value=date(1920, 1, 1), 
            max_value=date.today(),
            help="Pilih tanggal lahir Anda"
            )
        alamat = st.text_area("Alamat")
        
        if st.form_submit_button("Next"):
            # 1. Validasi Nama (Minimal 5 karakter)
            if len(nama) < 5:
                st.error("Nama Lengkap minimal harus 5 karakter!")
            
            # 2. Validasi Email
            elif "@" not in email or "." not in email:
                st.error("Format email tidak valid!")
            
            # 3. Validasi WhatsApp (Format nomor telepon 10-15 digit angka)
            elif not re.match(r'^[0-9]{10,15}$', wa):
                st.error("Format No WhatsApp tidak valid! Gunakan angka saja (10-15 digit).")
            
            # NEW: Validasi Tanggal Lahir (Tidak boleh masa depan)
            elif tgl > date.today():
                st.error("Tanggal lahir tidak boleh di masa depan!")
            
            # NEW: Validasi Usia Minimum (Contoh: minimal 5 tahun)
            elif (date.today().year - tgl.year) < 5:
                st.error("Usia minimal adalah 5 tahun!")

            # 4. Validasi Alamat (Wajib diisi)
            elif len(alamat.strip()) == 0:
                st.error("Alamat wajib diisi!")
            
            # 5. Jika lolos semua validasi
            else:
                st.session_state.update({
                    'nama': nama, 'email': email, 'gender': gender, 
                    'wa': wa, 'kota': kota, 'tgl': tgl, 'alamat': alamat
                })
                st.session_state['page'] = 'konfirmasi'
                st.rerun()

# --- HALAMAN 3: Konfirmasi ---
elif st.session_state['page'] == 'konfirmasi':
    st.info("Apakah Anda siap?")
    col1, col2 = st.columns(2)
    if col1.button("Ya"):
        
        # PERBAIKAN DI SINI: Pastikan semua data dikirim ke API
        sub_data = {
            "exam_id": int(st.session_state['exam_id']),
            "student_name": st.session_state['nama'],
            "email": st.session_state.get('email', ''),
            "gender": st.session_state.get('gender', ''),
            "whatsapp": st.session_state.get('wa', ''),
            "birth_city": st.session_state.get('kota', ''),
            "birth_date": str(st.session_state.get('tgl', '')), # Convert ke string agar JSON valid
            "address": st.session_state.get('alamat', '')
        }
        st.write("DEBUG DATA:", sub_data)

        resp = requests.post("http://127.0.0.1:8000/create-submission", json=sub_data)
        
        if resp.status_code == 200:
            st.session_state['submission_id'] = resp.json()['id']
            st.session_state['start_time'] = time.time()
            st.session_state['page'] = 'dashboard'
            st.rerun()
        else:
            st.error("Gagal membuat sesi ujian. Cek terminal backend!")
            
    if col2.button("Tidak"): 
        st.session_state['page'] = 'identitas'
        st.rerun()

# --- HALAMAN 4: Dashboard Soal ---
elif st.session_state['page'] == 'dashboard':
    st.title("Examination Page")
    display_timer()
    
    url = f"http://127.0.0.1:8000/get-questions/{st.session_state.get('exam_id')}"
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            soal_list = res.json()
            
            if not soal_list:
                st.warning("Soal untuk ujian ini belum tersedia.")
            else:
                if 'current_q_idx' not in st.session_state:
                    st.session_state['current_q_idx'] = 0
                
                idx = st.session_state['current_q_idx']
                soal = soal_list[idx]
                
                # Fungsi internal untuk menyimpan ke database
                def simpan_jawaban(s_id, q_id, opt):
                    payload = {"submission_id": s_id, "question_id": q_id, "selected_option": opt}
                    requests.post("http://127.0.0.1:8000/submit-answer", json=payload)

                st.markdown(f"**Soal {idx + 1} dari {len(soal_list)}**")
                st.write("---")
                st.markdown(f"### {soal['question_text']}")

                pilihan = {"A": soal['option_a'], "B": soal['option_b'], "C": soal['option_c'], "D": soal['option_d']}
                jawaban_terpilih = st.radio(
                    "Pilih jawaban Anda:", 
                    options=["A", "B", "C", "D"], 
                    format_func=lambda x: f"{x}: {pilihan[x]}", 
                    key=f"ans_{idx}"
                )
                
                # Tombol TTS
                if st.button("🔊 Dengarkan Soal (TTS)"):
                    try:
                        from gtts import gTTS
                        tts = gTTS(text=soal['question_text'], lang='en')
                        tts.save("temp_audio.mp3")
                        st.audio("temp_audio.mp3")
                    except Exception:
                        st.error("Gagal menjalankan TTS.")
                
                # Navigasi dengan simpan otomatis
                col1, col2, col3 = st.columns([1, 2, 1])
                
                if col1.button("Previous") and idx > 0:
                    simpan_jawaban(st.session_state['submission_id'], soal['id'], jawaban_terpilih)
                    st.session_state['current_q_idx'] -= 1
                    st.rerun()
                
                if col3.button("Next") and idx < len(soal_list) - 1:
                    simpan_jawaban(st.session_state['submission_id'], soal['id'], jawaban_terpilih)
                    st.session_state['current_q_idx'] += 1
                    st.rerun()
                
                if idx == len(soal_list) - 1:
                    if st.button("Finish Exam"):
                        simpan_jawaban(st.session_state['submission_id'], soal['id'], jawaban_terpilih)
                        st.session_state['page'] = 'hasil'
                        st.rerun()
        else:
            st.error("Gagal terhubung ke server soal.")
    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
        
        # --- 1. Layout Text-to-Speech ---
        # TTS diletakkan paling atas agar rapi
        if st.button("🔊 Play Audio"):
            try:
                tts = gTTS(text=soal['question_text'], lang='en')
                filename = f"temp_{soal['id']}.mp3"
                tts.save(filename)
                st.audio(filename, format="audio/mp3")
            except:
                st.error("Audio processing failed.")

        # --- 2. Layout Soal (Cukup satu saja) ---
        st.markdown("---")
        st.markdown(f"### Question {idx + 1} of {len(soal_list)}")
        st.write(f"#### {soal['question_text']}")
        st.markdown("---")
            
        # --- 3. Layout Pilihan Jawaban ---
        key_id = f"q_{soal['id']}"
        pilihan = st.radio("Select your answer:", ["A", "B", "C", "D"], key=key_id, index=None)
        
        # Tombol Simpan
        if st.button("Save Answer"):
            data = {"submission_id": st.session_state['submission_id'], "question_id": soal['id'], "selected_option": pilihan}
            requests.post("http://127.0.0.1:8000/submit-answer", json=data)
            st.toast("Answer saved!")

        # --- 4. Layout Tombol Navigasi (Sangat rapi) ---
        st.markdown("<br>", unsafe_allow_html=True) # Beri jarak
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if idx > 0:
                if st.button("Previous"):
                    st.session_state['current_q_idx'] -= 1
                    st.rerun()
                    
        with col3:
            if idx < len(soal_list) - 1:
                if st.button("Next"):
                        st.session_state['current_q_idx'] += 1
                        st.rerun()
            else:
                # Tambahkan ini di bagian atas file, di bawah st.set_page_config
                st.markdown("""
                    <style>
                    div.stButton > button:first-child[kind="primary"] {
                        background-color: #28a745;
                        color: white;
                        border: none;
                    }
                    div.stButton > button:first-child[kind="primary"]:hover {
                        background-color: #218838;
                        color: white;
                    }
                    </style>
                """, unsafe_allow_html=True)
        # Tambahkan type="primary" agar CSS di atas aktif
                # Di dalam dashboard, pastikan ini ada:
            if idx == len(soal_list) - 1:
                if st.button("Finish Examp"):
                    st.session_state['page'] = 'hasil' # Arahkan ke halaman hasil
                    st.rerun()
                    
    except Exception as e:
        st.error("Failed to load questions.")

elif st.session_state['page'] == 'hasil':
    st.title("Exam Over! 🎉")
    st.success("Thank you for completing your TOEIC exam.")
    
    # Menampilkan ringkasan singkat
    st.markdown("---")
    st.subheader("Summary")
    st.write(f"Participant Name: **{st.session_state.get('nama', '-')}**")
    st.write("Your test results are currently being processed by the system.")
    
    # Tombol untuk kembali ke awal atau keluar
    if st.button("Back to Home"):
        # Reset session state untuk mulai dari awal
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
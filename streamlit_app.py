import streamlit as st
import json
import random
import math
import re
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Fanlar bo‘yicha test", page_icon="🧠", layout="wide")

# --- Konfiguratsiya ---
DEFAULT_TEST_DURATION_MINUTES = 30

# --- Yordamchi Funksiyalar ---

def load_questions(file_name):
    """Savollarni JSON faylidan yuklaydi."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Xatolik: '{file_name}' fayli topilmadi. Iltimos, faylni yuklang.")
        return []
    except json.JSONDecodeError:
        st.error(f"Xatolik: '{file_name}' fayli JSON formatida emas.")
        return []

def evaluate_formula(formula, variables):
    """Berilgan formula va o'zgaruvchilar yordamida javobni hisoblaydi."""
    allowed_names = {
        **variables,
        "math": math,
        "random": random,
        "pi": math.pi,
        "e": math.e
    }
    try:
        result = eval(formula, {"__builtins__": None}, allowed_names)
        return result
    except Exception as e:
        st.error(f"Formula hisoblashda xatolik: {e}")
        return None

def generate_calculation_question(q_data):
    """Hisob-kitob savoli uchun tasodifiy o'zgaruvchilarni yaratadi va to'g'ri javobni hisoblaydi."""
    variables = {}
    for var, limits in q_data["variables"].items():
        variables[var] = random.randint(limits[0], limits[1])

    question_text = q_data["savol_shabloni"].format(**variables)
    correct_answer = evaluate_formula(q_data["formula"], variables)

    return {
        "id": q_data["id"],
        "type": "calculation",
        "savol": question_text,
        "to_g_ri_javob": correct_answer,
        "tolerance": q_data.get("tolerance", 0.01)
    }

def initialize_session_state(all_questions, subject, test_mode, duration_minutes):
    """Sessiya holatini (session_state) yangi test uchun sozlaydi."""
    st.session_state.current_subject = subject
    st.session_state.test_mode = test_mode
    st.session_state.test_finished = False
    
    # --- Taymerni sozlash ---
    st.session_state.start_time = datetime.now()
    st.session_state.end_time = st.session_state.start_time + timedelta(minutes=duration_minutes)

    if test_mode == "100 ta to‘liq":
        selected_questions = all_questions[:]
    else:
        num_questions = min(25, len(all_questions))
        selected_questions = random.sample(all_questions, num_questions)

    processed_questions = []
    shuffled_options = []

    for q in selected_questions:
        if q.get("type") == "multiple_choice":
            opts = q["variantlar"][:]
            random.shuffle(opts)
            shuffled_options.append(opts)
            processed_questions.append(q)
        elif q.get("type") == "calculation":
            processed_q = generate_calculation_question(q)
            processed_questions.append(processed_q)
            shuffled_options.append(None)
        else:
             # Agar type kaliti bo'lmasa, uni multiple_choice deb qabul qilamiz (eski fayllar uchun)
            q["type"] = "multiple_choice"
            opts = q["variantlar"][:]
            random.shuffle(opts)
            shuffled_options.append(opts)
            processed_questions.append(q)


    st.session_state.questions = processed_questions
    st.session_state.score = 0
    st.session_state.answered = [None] * len(processed_questions)
    st.session_state.shuffled_options = shuffled_options

def check_answer(q_index, q_data):
    """Foydalanuvchi javobini tekshiradi va natijani session_state ga saqlaydi."""
    
    if st.session_state.test_finished:
        return

    if st.session_state.answered[q_index] is not None:
        return

    user_answer = st.session_state[f"q{q_index+1}"]
    
    if q_data["type"] == "multiple_choice":
        if user_answer == q_data["javob"]:
            st.session_state.score += 1
        st.session_state.answered[q_index] = user_answer
        
    elif q_data["type"] == "calculation":
        correct_answer = q_data["to_g_ri_javob"]
        tolerance = q_data["tolerance"]
        
        try:
            user_input_float = float(user_answer)
        except (ValueError, TypeError):
            st.session_state.answered[q_index] = None
            return

        is_correct = abs(user_input_float - correct_answer) <= tolerance
        
        if is_correct:
            st.session_state.score += 1
        
        st.session_state.answered[q_index] = user_input_float
        
    st.rerun() 

# --- UI Qismi ---

st.title("📚 Fanlar bo‘yicha test ilovasi")

# Fanni tanlash
file_map = {
    "Algoritm": "Algoritm.json",
    "Dinshunoslik": "Dinshunoslik.json",
    "Ma'lumotlar Bazasi": "Ma'lumotlarBazasi.json",
    "Dasturlash": "Dasturlash.json",
    "Chiziqli Algebra": "ChiziqliAlgebra.json",
    "Hisob": "Hisob.json"
}

with st.sidebar:
    st.header("Test Sozlamalari")
    subject = st.selectbox("Fan tanlang:", list(file_map.keys()))
    test_mode = st.radio("Test turi:", ["100 ta to‘liq", "25 ta random"], horizontal=False)
    
    # --- Vaqtni tanlash ---
    st.markdown("---")
    st.subheader("Vaqt Cheklovi")
    test_duration = st.number_input("Test vaqti (daqiqa):", min_value=5, max_value=180, value=DEFAULT_TEST_DURATION_MINUTES, step=5)
    
    st.markdown("---")
    st.info("Hisob fanida dinamik, formula asosidagi savollar namoyish etilgan.")

file_name = file_map[subject]
all_questions = load_questions(file_name)

# Sessiya holatini tekshirish va sozlash
if "questions" not in st.session_state or st.session_state.get("current_subject") != subject or st.session_state.get("test_mode") != test_mode:
    initialize_session_state(all_questions, subject, test_mode, test_duration)

questions = st.session_state.questions

st.subheader(f"{subject} fanidan test")
st.markdown(f"**Savollar soni:** {len(questions)}")
st.markdown("---")

# --- Test savollarini ko'rsatish ---
for idx, q in enumerate(questions):
    q_index = idx
    
    st.markdown(f"### {q_index+1}-savol (ID: {q.get('id', '—')})")
    st.markdown(f"**Savol:** {q['savol']}")

    is_answered = st.session_state.answered[q_index] is not None
    
    input_disabled = is_answered or st.session_state.test_finished

    # --- Ko'p tanlovli savollar ---
    if q["type"] == "multiple_choice":
        options = st.session_state.shuffled_options[q_index]
        
        st.radio(
            label="Variantni tanlang:",
            options=options,
            key=f"q{q_index+1}",
            index=options.index(st.session_state.answered[q_index]) if st.session_state.answered[q_index] in options else None,
            label_visibility="collapsed",
            disabled=input_disabled,
            on_change=check_answer,
            args=(q_index, q)
        )
        
        if is_answered or st.session_state.test_finished:
            if st.session_state.answered[q_index] == q["javob"]:
                st.success(f"✅ To‘g‘ri! Javob: {q['javob']}")
            else:
                st.error(f"❌ Noto‘g‘ri. To‘g‘ri javob: {q['javob']}")

    # --- Hisob-kitob savollari ---
    elif q["type"] == "calculation":
        
        st.text_input(
            label="Javobingizni kiriting (son):",
            key=f"q{q_index+1}",
            value=str(st.session_state.answered[q_index]) if is_answered else "",
            disabled=input_disabled,
            on_change=check_answer,
            args=(q_index, q)
        )
        
        if is_answered or st.session_state.test_finished:
            correct_answer = q["to_g_ri_javob"]
            user_answer = st.session_state.answered[q_index]
            
            if user_answer is not None:
                tolerance = q["tolerance"]
                is_correct = abs(user_answer - correct_answer) <= tolerance
                
                if is_correct:
                    st.success(f"✅ To‘g‘ri! Javob: {user_answer:.2f}. To‘g‘ri javob: {correct_answer:.2f}")
                else:
                    st.error(f"❌ Noto‘g‘ri. Sizning javobingiz: {user_answer:.2f}. To‘g‘ri javob: {correct_answer:.2f}")
            else:
                st.info(f"Javob berilmagan. To‘g‘ri javob: {correct_answer:.2f}")
    
    st.markdown("---")

# --- Testni Yakunlash Qismi ---

if not st.session_state.test_finished:
    if st.button("Testni Yakunlash va Natijani Ko'rish", type="primary"):
        st.session_state.test_finished = True
        st.rerun()

if st.session_state.test_finished:
    st.balloons()
    st.header("Test Natijasi")
    st.subheader(f"Siz {len(questions)} savoldan **{st.session_state.score}** tasiga to‘g‘ri javob berdingiz!")
    
    percentage = (st.session_state.score / len(questions)) * 100 if len(questions) > 0 else 0
    st.progress(percentage / 100, text=f"Muvaffaqiyat: {percentage:.1f}%")
    
    if st.button("Yangi test boshlash"):
        st.session_state.clear()
        st.rerun()

# --- Taymerni Yangilash Qismi (Eng oxirida) ---
if not st.session_state.test_finished:
    
    time_left = st.session_state.end_time - datetime.now()
    
    if time_left.total_seconds() <= 0:
        st.session_state.test_finished = True
        st.warning("⏳ Vaqt tugadi! Test avtomatik yakunlandi.")
        st.rerun()
    
    total_seconds = int(time_left.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    # Yon panelda vaqtni ko'rsatish
    st.sidebar.markdown(f"## ⏳ Qolgan vaqt: **{minutes:02d}:{seconds:02d}**")
    
    # Har soniyada yangilash
    time.sleep(1)
    st.rerun()

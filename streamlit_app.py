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
        # eval() dan foydalanish xavfsizlik nuqtai nazaridan tavsiya etilmaydi,
        # lekin bu holatda foydalanuvchi kiritgan ma'lumot emas, balki
        # faqat savollar faylidagi formula hisoblanadi.
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
    st.session_state.test_started = False # YANGI: Test hali boshlanmadi
    st.session_state.test_duration = duration_minutes # YANGI: Vaqtni saqlash

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
    # st.session_state.answered endi foydalanuvchi kiritgan qiymatlarni saqlamaydi.
    # Qiymatlar to'g'ridan-to'g'ri st.session_state[f"q{q_index+1}"] da saqlanadi.
    # st.session_state.answered endi faqat natijani (True/False) saqlaydi.
    st.session_state.results = [None] * len(processed_questions)
    st.session_state.shuffled_options = shuffled_options

def start_test():
    """Testni boshlaydi va taymerni ishga tushiradi."""
    st.session_state.test_started = True
    st.session_state.start_time = datetime.now()
    st.session_state.end_time = st.session_state.start_time + timedelta(minutes=st.session_state.test_duration)
    st.rerun()

def evaluate_test_results():
    """Test yakunlanganda barcha javoblarni tekshiradi va natijani hisoblaydi."""
    if st.session_state.test_finished:
        return

    st.session_state.score = 0
    st.session_state.test_finished = True
    questions = st.session_state.questions
    results = [None] * len(questions)

    for q_index, q_data in enumerate(questions):
        user_answer_key = f"q{q_index+1}"
        user_input = st.session_state.get(user_answer_key)
        is_correct = False

        if user_input is None or user_input == "":
            # Javob berilmagan
            results[q_index] = {"correct": False, "user_answer": None, "correct_answer": q_data.get("javob") or q_data.get("to_g_ri_javob")}
            continue

        if q_data["type"] == "multiple_choice":
            # Ko'p tanlovli savollar
            if user_input == q_data["javob"]:
                is_correct = True
            
            results[q_index] = {"correct": is_correct, "user_answer": user_input, "correct_answer": q_data["javob"]}

        elif q_data["type"] == "calculation":
            # Hisob-kitob savollari
            correct_answer = q_data["to_g_ri_javob"]
            tolerance = q_data["tolerance"]
            
            try:
                user_input_float = float(user_input)
                is_correct = abs(user_input_float - correct_answer) <= tolerance
                user_answer_display = user_input_float
            except (ValueError, TypeError):
                # Noto'g'ri formatdagi kiritma
                user_answer_display = user_input

            results[q_index] = {"correct": is_correct, "user_answer": user_answer_display, "correct_answer": correct_answer}
        
        if is_correct:
            st.session_state.score += 1
    
    st.session_state.results = results
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
if (
    "questions" not in st.session_state 
    or st.session_state.get("current_subject") != subject 
    or st.session_state.get("test_mode") != test_mode
    or st.session_state.get("test_duration") != test_duration # Vaqt o'zgarganda ham qayta yuklash
):
    initialize_session_state(all_questions, subject, test_mode, test_duration)

questions = st.session_state.questions

st.subheader(f"{subject} fanidan test")
st.markdown(f"**Savollar soni:** {len(questions)}")
st.markdown("---")

# --- Test Boshlanmagan Holat ---
if not st.session_state.test_started and not st.session_state.test_finished:
    st.info(f"Testni boshlash uchun quyidagi tugmani bosing. Sizda **{st.session_state.test_duration} daqiqa** vaqt bo‘ladi.")
    if st.button("Testni Boshlash", type="primary", on_click=start_test):
        pass # start_test() funksiyasi st.rerun() ni chaqiradi

# --- Test Boshlangan Holat ---
elif st.session_state.test_started and not st.session_state.test_finished:
    
    # --- Test savollarini ko'rsatish ---
    for idx, q in enumerate(questions):
        q_index = idx
        
        st.markdown(f"### {q_index+1}-savol (ID: {q.get('id', '—')})")
        st.markdown(f"**Savol:** {q['savol']}")

        # Foydalanuvchi kiritgan javobni olish (agar mavjud bo'lsa)
        user_input_key = f"q{q_index+1}"
        current_value = st.session_state.get(user_input_key)

        # --- Ko'p tanlovli savollar ---
        if q["type"] == "multiple_choice":
            options = st.session_state.shuffled_options[q_index]
            
            # Agar oldin javob berilgan bo'lsa, indexni topish
            try:
                default_index = options.index(current_value) if current_value in options else None
            except ValueError:
                default_index = None

            st.radio(
                label="Variantni tanlang:",
                options=options,
                key=user_input_key,
                index=default_index,
                label_visibility="collapsed",
                # on_change va args olib tashlandi
            )

        # --- Hisob-kitob savollari ---
        elif q["type"] == "calculation":
            
            # Agar current_value son bo'lsa, uni matnga o'tkazish
            display_value = str(current_value) if current_value is not None else ""

            st.text_input(
                label="Javobingizni kiriting (son):",
                key=user_input_key,
                value=display_value,
                # on_change va args olib tashlandi
            )
        
        st.markdown("---")

    # --- Testni Yakunlash Qismi ---
    if st.button("Testni Yakunlash va Natijani Tekshirish", type="primary", on_click=evaluate_test_results):
        pass # evaluate_test_results() funksiyasi st.rerun() ni chaqiradi

# --- Test Yakunlangan Holat ---
if st.session_state.test_finished:
    st.balloons()
    st.header("Test Natijasi")
    questions = st.session_state.questions
    results = st.session_state.results
    
    st.subheader(f"Siz {len(questions)} savoldan **{st.session_state.score}** tasiga to‘g‘ri javob berdingiz!")
    
    percentage = (st.session_state.score / len(questions)) * 100 if len(questions) > 0 else 0
    st.progress(percentage / 100, text=f"Muvaffaqiyat: {percentage:.1f}%")
    
    st.markdown("---")
    st.subheader("Batafsil Natijalar")

    # Batafsil natijalarni ko'rsatish
    for idx, q in enumerate(questions):
        res = results[idx]
        
        st.markdown(f"### {idx+1}-savol (ID: {q.get('id', '—')})")
        st.markdown(f"**Savol:** {q['savol']}")

        if res["user_answer"] is None:
            st.info(f"Javob berilmagan. To‘g‘ri javob: **{res['correct_answer']}**")
        elif res["correct"]:
            if q["type"] == "multiple_choice":
                st.success(f"✅ To‘g‘ri! Sizning javobingiz: **{res['user_answer']}**")
            elif q["type"] == "calculation":
                st.success(f"✅ To‘g‘ri! Sizning javobingiz: **{res['user_answer']:.2f}**. To‘g‘ri javob: **{res['correct_answer']:.2f}**")
        else:
            if q["type"] == "multiple_choice":
                st.error(f"❌ Noto‘g‘ri. Sizning javobingiz: **{res['user_answer']}**. To‘g‘ri javob: **{res['correct_answer']}**")
            elif q["type"] == "calculation":
                # Agar kiritilgan qiymat float bo'lmasa, uni matn sifatida ko'rsatish
                user_ans_display = f"{res['user_answer']:.2f}" if isinstance(res['user_answer'], (int, float)) else res['user_answer']
                st.error(f"❌ Noto‘g‘ri. Sizning javobingiz: **{user_ans_display}**. To‘g‘ri javob: **{res['correct_answer']:.2f}**")
        
        st.markdown("---")

    if st.button("Yangi test boshlash"):
        st.session_state.clear()
        st.rerun()

# --- Taymerni Yangilash Qismi (Eng oxirida) ---
if st.session_state.test_started and not st.session_state.test_finished:
    
    time_left = st.session_state.end_time - datetime.now()
    
    if time_left.total_seconds() <= 0:
        # Vaqt tugasa, avtomatik tekshirish funksiyasini chaqirish
        evaluate_test_results() 
        st.warning("⏳ Vaqt tugadi! Test avtomatik yakunlandi va natijalar tekshirildi.")
        # st.rerun() evaluate_test_results ichida chaqiriladi
    
    total_seconds = int(time_left.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    # Yon panelda vaqtni ko'rsatish
    st.sidebar.markdown(f"## ⏳ Qolgan vaqt: **{minutes:02d}:{seconds:02d}**")
    
    # Har soniyada yangilash
    time.sleep(1)
    st.rerun()

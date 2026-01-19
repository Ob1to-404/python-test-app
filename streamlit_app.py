import streamlit as st
import json
import random
import math
import os
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Fanlar bo‘yicha test", page_icon="🧠", layout="wide")

# --- Konfiguratsiya ---
DEFAULT_TEST_DURATION_MINUTES = 30

# --- Yordamchi funksiyalar ---

def format_seconds(sec):
    sec = max(0, int(sec))
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"

def answered_count():
    cnt = 0
    if "questions" in st.session_state:
        for i in range(len(st.session_state.questions)):
            v = st.session_state.get(f"q{i+1}")
            if v is not None and v != "":
                cnt += 1
    return cnt

# --- Savol funksiyalari ---

def load_questions(file_name):
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
    st.session_state.current_subject = subject
    st.session_state.test_mode = test_mode
    st.session_state.test_finished = False
    st.session_state.test_started = False
    st.session_state.test_duration = duration_minutes

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
            q["type"] = "multiple_choice"
            opts = q["variantlar"][:]
            random.shuffle(opts)
            shuffled_options.append(opts)
            processed_questions.append(q)

    st.session_state.questions = processed_questions
    st.session_state.score = 0
    st.session_state.results = [None] * len(processed_questions)
    st.session_state.shuffled_options = shuffled_options

def start_test():
    st.session_state.test_started = True
    st.session_state.start_time = datetime.now()
    st.session_state.end_time = st.session_state.start_time + timedelta(minutes=st.session_state.test_duration)

def evaluate_test_results():
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
            results[q_index] = {
                "correct": False,
                "user_answer": None,
                "correct_answer": q_data.get("javob") or q_data.get("to_g_ri_javob")
            }
            continue

        if q_data["type"] == "multiple_choice":
            if user_input == q_data["javob"]:
                is_correct = True
            results[q_index] = {
                "correct": is_correct,
                "user_answer": user_input,
                "correct_answer": q_data["javob"]
            }

        elif q_data["type"] == "calculation":
            correct_answer = q_data["to_g_ri_javob"]
            tolerance = q_data["tolerance"]
            try:
                user_input_float = float(user_input)
                is_correct = abs(user_input_float - correct_answer) <= tolerance
                user_answer_display = user_input_float
            except (ValueError, TypeError):
                user_answer_display = user_input

            results[q_index] = {
                "correct": is_correct,
                "user_answer": user_answer_display,
                "correct_answer": correct_answer
            }

        if is_correct:
            st.session_state.score += 1

    st.session_state.results = results

# --- UI Qismi ---

st.title("📚 Fanlar bo‘yicha test ilovasi")

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

    st.markdown("---")
    st.subheader("Vaqt Cheklovi")
    test_duration = st.number_input(
        "Test vaqti (daqiqa):",
        min_value=5,
        max_value=180,
        value=DEFAULT_TEST_DURATION_MINUTES,
        step=5
    )

    st.markdown("---")
    st.info("Hisob fanida dinamik, formula asosidagi savollar namoyish etilgan.")

# Test boshlanmagan bo'lsa
if not st.session_state.get("test_started") and not st.session_state.get("test_finished"):
    st.subheader(f"Tanlangan fan: {subject}")
    st.info(f"Testni boshlash uchun tugmani bosing. Sizda **{test_duration} daqiqa** vaqt bo‘ladi.")
    
    if st.button("🚀 Testni Boshlash", type="primary", use_container_width=True):
        all_questions = load_questions(file_map[subject])
        if all_questions:
            initialize_session_state(all_questions, subject, test_mode, test_duration)
            start_test()
            st.rerun()

# Test davom etayotgan bo'lsa
elif st.session_state.get("test_started"):
    questions = st.session_state.questions
    is_finished = st.session_state.test_finished

    # Sidebar taymer va progress
    if not is_finished:
        time_left = st.session_state.end_time - datetime.now()
        if time_left.total_seconds() <= 0:
            evaluate_test_results()
            st.warning("⏳ Vaqt tugadi!")
            st.rerun()
        
        total_seconds = int(max(0, time_left.total_seconds()))
        st.sidebar.markdown(f"## ⏳ Qolgan vaqt: **{format_seconds(total_seconds)}**")
        
        ans_cnt = answered_count()
        st.sidebar.markdown(f"## ✅ Javoblar: **{ans_cnt}/{len(questions)}**")
        st.sidebar.progress(ans_cnt / len(questions) if len(questions) else 0.0)

    st.subheader(f"📝 {st.session_state.current_subject} testi")
    
    # Savollarni ko'rsatish
    for idx, q in enumerate(questions):
        st.markdown(f"### {idx+1}-savol")
        st.markdown(f"**Savol:** {q['savol']}")
        
        user_input_key = f"q{idx+1}"
        current_value = st.session_state.get(user_input_key)
        res = st.session_state.results[idx] if is_finished else None

        if q["type"] == "multiple_choice":
            options = st.session_state.shuffled_options[idx]
            try:
                default_index = options.index(current_value) if current_value in options else None
            except ValueError:
                default_index = None
            
            st.radio(
                "Variantni tanlang:",
                options,
                key=user_input_key,
                index=default_index,
                label_visibility="collapsed",
                disabled=is_finished
            )
            
            if is_finished:
                if res["user_answer"] is None:
                    st.info(f"Javob berilmagan. To‘g‘ri javob: **{res['correct_answer']}**")
                elif res["correct"]:
                    st.success(f"✅ To‘g‘ri! Sizning javobingiz: **{res['user_answer']}**")
                else:
                    st.error(f"❌ Noto‘g‘ri. Sizning javobingiz: **{res['user_answer']}**. To‘g‘ri javob: **{res['correct_answer']}**")

        elif q["type"] == "calculation":
            st.text_input(
                "Javobingizni kiriting (son):",
                key=user_input_key,
                disabled=is_finished
            )
            
            if is_finished:
                if res["user_answer"] is None:
                    st.info(f"Javob berilmagan. To‘g‘ri javob: **{res['correct_answer']:.2f}**")
                elif res["correct"]:
                    st.success(f"✅ To‘g‘ri! Sizning javobingiz: **{res['user_answer']:.2f}**. To‘g‘ri javob: **{res['correct_answer']:.2f}**")
                else:
                    user_ans_display = f"{res['user_answer']:.2f}" if isinstance(res["user_answer"], (int, float)) else res["user_answer"]
                    st.error(f"❌ Noto‘g‘ri. Sizning javobingiz: **{user_ans_display}**. To‘g‘ri javob: **{res['correct_answer']:.2f}**")
        
        st.markdown("---")

    if not is_finished:
        if st.button("✅ Testni Yakunlash", type="primary", use_container_width=True):
            evaluate_test_results()
            st.rerun()
        
        # Avtomatik yangilanish
        time.sleep(1)
        st.rerun()
    else:
        # Natija sarlavhasi
        st.header("📊 Test Natijasi")
        total = len(questions)
        score = st.session_state.score
        percentage = (score / total) * 100 if total else 0.0
        
        st.subheader(f"Siz {total} savoldan **{score}** tasiga to‘g‘ri javob berdingiz!")
        st.progress(percentage / 100, text=f"Muvaffaqiyat: {percentage:.1f}%")
        
        start_time = st.session_state.get("start_time")
        if start_time:
            spent_sec = (datetime.now() - start_time).total_seconds()
            st.write(f"⏱ **Sarflangan vaqt:** {format_seconds(spent_sec)}")

        if st.button("🔄 Yangi test boshlash", use_container_width=True):
            st.session_state.clear()
            st.rerun()

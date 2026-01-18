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
STATS_FILE = "user_stats.json"

# --- Statistika (Login) funksiyalari ---

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def ensure_user(stats, username):
    if username not in stats:
        stats[username] = {
            "created_at": datetime.now().isoformat(),
            "attempts": [],
            "summary": {
                "total_attempts": 0,
                "best_score": 0,
                "best_percent": 0.0,
                "avg_percent": 0.0
            }
        }
    return stats

def compute_summary(attempts):
    if not attempts:
        return {"total_attempts": 0, "best_score": 0, "best_percent": 0.0, "avg_percent": 0.0}

    total = len(attempts)
    best = max(attempts, key=lambda x: x.get("percent", 0.0))
    avg_percent = sum(a.get("percent", 0.0) for a in attempts) / total

    return {
        "total_attempts": total,
        "best_score": int(best.get("score", 0)),
        "best_percent": float(best.get("percent", 0.0)),
        "avg_percent": float(avg_percent)
    }

def format_seconds(sec):
    sec = max(0, int(sec))
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"

def answered_count():
    cnt = 0
    for i in range(len(st.session_state.questions)):
        v = st.session_state.get(f"q{i+1}")
        if v is not None and v != "":
            cnt += 1
    return cnt

def render_user_dashboard(stats, username):
    user = stats.get(username, {})
    attempts = user.get("attempts", [])
    summary = user.get("summary", {})

    st.sidebar.markdown("## 📊 Statistika")
    st.sidebar.write(f"**User:** `{username}`")
    st.sidebar.write(f"**Urinishlar:** {summary.get('total_attempts', 0)}")
    st.sidebar.write(f"**Best:** {summary.get('best_percent', 0.0):.1f}%  ({summary.get('best_score', 0)})")
    st.sidebar.write(f"**O‘rtacha:** {summary.get('avg_percent', 0.0):.1f}%")

    if attempts:
        st.sidebar.markdown("### 🧾 Oxirgi 5 urinish")
        for a in attempts[-5:][::-1]:
            st.sidebar.caption(
                f"• {a.get('date','—')} | {a.get('subject','—')} | {a.get('mode','—')} | "
                f"{a.get('score',0)}/{a.get('total',0)} ({a.get('percent',0.0):.1f}%) | "
                f"⏱ {a.get('time_spent','—')}"
            )
    st.sidebar.markdown("---")

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
    st.rerun()

def save_attempt_to_stats(username, subject, test_mode, score, total, time_spent_seconds):
    stats = load_stats()
    ensure_user(stats, username)

    percent = (score / total) * 100 if total else 0.0
    attempt = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "subject": subject,
        "mode": test_mode,
        "score": int(score),
        "total": int(total),
        "percent": float(percent),
        "time_spent": format_seconds(time_spent_seconds)
    }

    stats[username]["attempts"].append(attempt)
    stats[username]["summary"] = compute_summary(stats[username]["attempts"])
    save_stats(stats)

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

    # Statistikaga yozish (login bo‘lsa)
    if st.session_state.get("username"):
        spent = 0
        if st.session_state.get("start_time"):
            spent = (datetime.now() - st.session_state.start_time).total_seconds()
        save_attempt_to_stats(
            username=st.session_state.username,
            subject=st.session_state.current_subject,
            test_mode=st.session_state.test_mode,
            score=st.session_state.score,
            total=len(st.session_state.questions),
            time_spent_seconds=spent
        )

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
    st.header("Login")
    username_input = st.text_input("Username kiriting:", value=st.session_state.get("username", "")).strip()
    if username_input:
        st.session_state.username = username_input

    st.markdown("---")
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

# Login tekshirish
if not st.session_state.get("username"):
    st.warning("👤 Avval username kiriting (sidebar) so‘ng testni boshlaysiz.")
    st.stop()

# Sidebar statistika ko‘rsatish
_stats = load_stats()
ensure_user(_stats, st.session_state.username)
render_user_dashboard(_stats, st.session_state.username)

file_name = file_map[subject]
all_questions = load_questions(file_name)

# Sessiya holatini tekshirish va sozlash
if (
    "questions" not in st.session_state
    or st.session_state.get("current_subject") != subject
    or st.session_state.get("test_mode") != test_mode
    or st.session_state.get("test_duration") != test_duration
):
    initialize_session_state(all_questions, subject, test_mode, test_duration)

questions = st.session_state.questions

# Progress panel (yuqorida ham ko‘rinsin)
total_q = len(questions)
ans_cnt = answered_count()
st.subheader(f"{subject} fanidan test")
st.markdown(f"**Savollar soni:** {total_q}")
st.markdown(f"**Progress:** `{ans_cnt}/{total_q}`")
st.progress(ans_cnt / total_q if total_q else 0.0)
st.markdown("---")

# --- Test Boshlanmagan Holat ---
if not st.session_state.test_started and not st.session_state.test_finished:
    st.info(
        f"Testni boshlash uchun tugmani bosing. Sizda **{st.session_state.test_duration} daqiqa** vaqt bo‘ladi.\n\n"
        f"Login: `{st.session_state.username}`"
    )
    if st.button("Testni Boshlash", type="primary", on_click=start_test):
        pass

# --- Test Boshlangan Holat ---
elif st.session_state.test_started:

    # Savollar
    for idx, q in enumerate(questions):
        q_index = idx

        st.markdown(f"### {q_index+1}-savol (ID: {q.get('id', '—')})")
        st.markdown(f"**Savol:** {q['savol']}")

        user_input_key = f"q{q_index+1}"
        current_value = st.session_state.get(user_input_key)

        is_finished = st.session_state.test_finished
        res = st.session_state.results[idx] if is_finished else None

        if q["type"] == "multiple_choice":
            options = st.session_state.shuffled_options[q_index]

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
                disabled=is_finished
            )

            if is_finished:
                if res["user_answer"] is None:
                    st.info(f"Javob berilmagan. To‘g‘ri javob: **{res['correct_answer']}**")
                elif res["correct"]:
                    st.success(f"✅ To‘g‘ri! Sizning javobingiz: **{res['user_answer']}**")
                else:
                    st.error(
                        f"❌ Noto‘g‘ri. Sizning javobingiz: **{res['user_answer']}**. "
                        f"To‘g‘ri javob: **{res['correct_answer']}**"
                    )

        elif q["type"] == "calculation":
            display_value = str(current_value) if current_value is not None else ""

            st.text_input(
                label="Javobingizni kiriting (son):",
                key=user_input_key,
                value=display_value,
                disabled=is_finished
            )

            if is_finished:
                if res["user_answer"] is None:
                    st.info(f"Javob berilmagan. To‘g‘ri javob: **{res['correct_answer']:.2f}**")
                elif res["correct"]:
                    st.success(
                        f"✅ To‘g‘ri! Sizning javobingiz: **{res['user_answer']:.2f}**. "
                        f"To‘g‘ri javob: **{res['correct_answer']:.2f}**"
                    )
                else:
                    user_ans_display = (
                        f"{res['user_answer']:.2f}"
                        if isinstance(res["user_answer"], (int, float))
                        else res["user_answer"]
                    )
                    st.error(
                        f"❌ Noto‘g‘ri. Sizning javobingiz: **{user_ans_display}**. "
                        f"To‘g‘ri javob: **{res['correct_answer']:.2f}**"
                    )

        st.markdown("---")

    if not st.session_state.test_finished:
        if st.button("Testni Yakunlash va Natijani Tekshirish", type="primary", on_click=evaluate_test_results):
            pass

# --- Test Yakunlangan Holat ---
if st.session_state.test_finished:
    st.header("Test Natijasi")

    total = len(st.session_state.questions)
    score = st.session_state.score
    st.subheader(f"Siz {total} savoldan **{score}** tasiga to‘g‘ri javob berdingiz!")

    percentage = (score / total) * 100 if total else 0.0
    st.progress(percentage / 100, text=f"Muvaffaqiyat: {percentage:.1f}%")

    # vaqt sarfi ko‘rsatish
    start_time = st.session_state.get("start_time")
    if start_time:
        spent_sec = (datetime.now() - start_time).total_seconds()
        st.write(f"⏱ **Sarflangan vaqt:** {format_seconds(spent_sec)}")


    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yangi test boshlash"):
            # username qoladi, qolganini tozalaymiz
            username_keep = st.session_state.get("username")
            st.session_state.clear()
            if username_keep:
                st.session_state.username = username_keep
            st.rerun()

    with col2:
        if st.button("Statistikani yangilash"):
            st.rerun()

# --- Taymer (Eng oxirida) ---
if st.session_state.test_started and not st.session_state.test_finished:
    time_left = st.session_state.end_time - datetime.now()

    if time_left.total_seconds() <= 0:
        evaluate_test_results()
        st.warning("⏳ Vaqt tugadi! Test avtomatik yakunlandi va natijalar tekshirildi.")

    total_seconds = int(max(0, time_left.total_seconds()))
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    # Sidebar: qolgan vaqt + progress
    st.sidebar.markdown(f"## ⏳ Qolgan vaqt: **{minutes:02d}:{seconds:02d}**")
    ans_cnt = answered_count()
    st.sidebar.markdown(f"## ✅ Javoblar: **{ans_cnt}/{len(st.session_state.questions)}**")
    st.sidebar.progress(ans_cnt / len(st.session_state.questions) if len(st.session_state.questions) else 0.0)

    # Har soniyada yangilash
    time.sleep(1)
    st.rerun()

# ... (mavjud kodning oxiri)
    time.sleep(1)
    st.rerun()

# --- YANGI QO'SHILADIGAN QISM ---
st.markdown("---") # Ajratuvchi chiziq
all_stats = load_stats()

if all_stats:
    st.header("👥 Foydalanuvchilar Reytingi (Leaderboard)")
    st.write(f"Jami foydalanuvchilar soni: **{len(all_stats)} ta**")
    
    sorted_users = sorted(
        all_stats.items(), 
        key=lambda x: x[1]['summary'].get('best_percent', 0), 
        reverse=True
    )
    
    for i, (username, data) in enumerate(sorted_users, 1):
        summary = data.get("summary", {})
        st.markdown(f"""
        **{i}. {username}** — Eng yaxshi: `{summary.get('best_percent', 0):.1f}%` | Urinishlar: `{summary.get('total_attempts', 0)}`
        """)
else:
    st.info("Hozircha hech qanday foydalanuvchi ro'yxatdan o'tmagan.")

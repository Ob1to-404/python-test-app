import streamlit as st
import json
import random
import os
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Test Ilovasi", page_icon="🧠", layout="wide")

DEFAULT_TEST_DURATION_MINUTES = 30

# ─────────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────

def format_seconds(sec):
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


def answered_count():
    if "questions" not in st.session_state:
        return 0
    return sum(
        1 for i in range(len(st.session_state.questions))
        if st.session_state.get(f"q{i+1}") not in (None, "")
    )


def load_questions(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"'{file_name}' fayli topilmadi.")
        return []
    except json.JSONDecodeError:
        st.error(f"'{file_name}' JSON formatida emas.")
        return []


# ─────────────────────────────────────────────
# SAVOL TANLASH
# ─────────────────────────────────────────────

def get_next_25_block(all_questions, used_indices_per_subject):
    total = len(all_questions)
    used = used_indices_per_subject
    available = [i for i in range(total) if i not in used]
    count = min(25, len(available))
    if count < 10:
        return None
    return random.sample(available, count)


def prepare_block(all_questions, selected_indices):
    questions = []
    shuffled_options = []
    for idx in selected_indices:
        q = dict(all_questions[idx])
        q["original_index"] = idx
        if "variantlar" in q:
            opts = q["variantlar"][:]
            random.shuffle(opts)
            shuffled_options.append(opts)
        else:
            shuffled_options.append(None)
        questions.append(q)
    return questions, shuffled_options


# ─────────────────────────────────────────────
# NATIJALARNI SAQLASH
# ─────────────────────────────────────────────

def record_test_result(subject, questions, results, score, spent_sec, test_number):
    if "history" not in st.session_state:
        st.session_state.history = {}
    if subject not in st.session_state.history:
        st.session_state.history[subject] = []
    wrong_ids = []
    for q, r in zip(questions, results):
        if r and not r["correct"]:
            wrong_ids.append(q.get("id", q.get("original_index", "?")))
    st.session_state.history[subject].append({
        "test_number": test_number,
        "score": score,
        "total": len(questions),
        "wrong_ids": wrong_ids,
        "spent_sec": spent_sec,
    })


def get_subject_stats(subject):
    history = st.session_state.get("history", {}).get(subject, [])
    if not history:
        return None
    wrong_counter = {}
    for rec in history:
        for wid in rec["wrong_ids"]:
            wrong_counter[wid] = wrong_counter.get(wid, 0) + 1
    top10_repeated = sorted(wrong_counter.items(), key=lambda x: -x[1])[:10]
    top5_wrong = sorted(wrong_counter.items(), key=lambda x: -x[1])[:5]
    return {
        "history": history,
        "wrong_counter": wrong_counter,
        "top10_repeated": top10_repeated,
        "top5_wrong": top5_wrong,
    }


# ─────────────────────────────────────────────
# MOSLASHTIRILGAN TEST
# ─────────────────────────────────────────────

def build_adaptive_test(subject, all_questions):
    stats = get_subject_stats(subject)
    if not stats:
        return None, None
    wrong_counter = stats["wrong_counter"]
    if not wrong_counter:
        return None, None
    id_to_idx = {q.get("id", i): i for i, q in enumerate(all_questions)}
    weighted_unique = list({id_to_idx[qid] for qid in wrong_counter if qid in id_to_idx})
    random.shuffle(weighted_unique)
    hard_pick = weighted_unique[:min(18, len(weighted_unique))]
    normal_pool = [i for i in range(len(all_questions)) if i not in set(hard_pick)]
    random.shuffle(normal_pool)
    easy_pick = normal_pool[:max(0, 25 - len(hard_pick))]
    selected = (hard_pick + easy_pick)[:25]
    if len(selected) < 10:
        selected = random.sample(range(len(all_questions)), min(25, len(all_questions)))
    return selected, True


# ─────────────────────────────────────────────
# SAVOL RENDER (umumiy funksiya)
# ─────────────────────────────────────────────

def render_question(idx, q, opts, mode, is_finished, result, instant_result):
    """
    mode: "instant" — javob bosganda darhol ko'rsatadi
          "final"   — yakunlashda ko'rsatadi (hozirgidek)
    """
    st.markdown(f"**{idx+1}.** {q['savol']}")
    key = f"q{idx+1}"
    cur = st.session_state.get(key)

    try:
        default_index = opts.index(cur) if cur in opts else None
    except (ValueError, TypeError):
        default_index = None

    disabled = is_finished or (mode == "instant" and instant_result is not None)

    def on_change_instant():
        val = st.session_state.get(key)
        correct_ans = q.get("javob")
        is_correct = val == correct_ans if val not in (None, "") else False
        st.session_state.setdefault("instant_results", {})[idx] = {
            "correct": is_correct,
            "user_answer": val,
            "correct_answer": correct_ans
        }

    if mode == "instant" and not is_finished:
        st.radio(
            label="",
            options=opts,
            key=key,
            index=default_index,
            label_visibility="collapsed",
            disabled=disabled,
            on_change=on_change_instant
        )
        # Darhol natija ko'rsatish
        if instant_result is not None:
            if instant_result["correct"]:
                st.markdown(
                    f"<div style='background:#d4edda;border-left:4px solid #28a745;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"✅ To'g'ri!</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='background:#f8d7da;border-left:4px solid #dc3545;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"❌ Xato! To'g'ri javob: <b>{instant_result['correct_answer']}</b></div>",
                    unsafe_allow_html=True
                )
    else:
        # Final rejim yoki yakunlangan holat
        st.radio(
            label="",
            options=opts,
            key=key,
            index=default_index,
            label_visibility="collapsed",
            disabled=is_finished
        )
        if is_finished and result:
            if result["user_answer"] is None:
                st.markdown(
                    f"<div style='background:#fff3cd;border-left:4px solid #ffc107;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"⚠️ Javob berilmagan. To'g'ri: <b>{result['correct_answer']}</b></div>",
                    unsafe_allow_html=True
                )
            elif result["correct"]:
                st.markdown(
                    f"<div style='background:#d4edda;border-left:4px solid #28a745;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"✅ To'g'ri: <b>{result['user_answer']}</b></div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='background:#f8d7da;border-left:4px solid #dc3545;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"❌ Xato: <b>{result['user_answer']}</b> | To'g'ri: <b>{result['correct_answer']}</b></div>",
                    unsafe_allow_html=True
                )

    st.markdown("---")


# ─────────────────────────────────────────────
# BAHOLASH FUNKSIYASI
# ─────────────────────────────────────────────

def evaluate(questions):
    score = 0
    results = []
    for qi, qd in enumerate(questions):
        ui = st.session_state.get(f"q{qi+1}")
        correct = ui == qd.get("javob") if ui not in (None, "") else False
        if correct:
            score += 1
        results.append({"correct": correct, "user_answer": ui, "correct_answer": qd.get("javob")})
    return score, results


# ─────────────────────────────────────────────
# ASOSIY APP
# ─────────────────────────────────────────────

FILE_MAP = {
    "Elektronika va Sxemalar": "Elektronika_va_sxemalar.json",
    "Kiberxavfsizlik": "Kiberxavfsizlik.json",
    "Diskret Matematika": "Diskret.json",
    "Kompyuter Tarmoqlari": "Kompuyter_tarmoqlari.json",
}

QUESTION_COUNTS = {}
for name, fname in FILE_MAP.items():
    if os.path.exists(fname):
        try:
            with open(fname, "r", encoding="utf-8") as f:
                d = json.load(f)
            QUESTION_COUNTS[name] = len(d)
        except Exception:
            QUESTION_COUNTS[name] = 0
    else:
        QUESTION_COUNTS[name] = 0

# ── Sidebar ──────────────────────────────────
with st.sidebar:
    st.header("⚙️ Sozlamalar")

    subject_options = [
        f"{name} ({QUESTION_COUNTS.get(name, '?')} ta savol)"
        for name in FILE_MAP
    ]
    subject_display = st.selectbox("Fan:", subject_options)
    subject = subject_display.split(" (")[0]

    st.markdown("---")

    # ── Test turi ────────────────────────────
    test_type = st.radio(
        "Test turi:",
        ["25 ta blok (x10)", "To'liq test (barcha savollar)"],
        help="25 ta blok: 10 marta unikal 25 ta savol. To'liq: barcha savollar birdan."
    )

    st.markdown("---")

    # ── Javob ko'rsatish rejimi ───────────────
    answer_mode = st.radio(
        "Javob ko'rsatish:",
        ["Darhol (bosganda)", "Yakunlashda (hammasi birga)"],
    )
    answer_mode_key = "instant" if answer_mode.startswith("Darhol") else "final"

    st.markdown("---")
    st.subheader("⏱ Vaqt")
    test_duration = st.number_input(
        "Test vaqti (daqiqa):",
        min_value=5, max_value=180,
        value=DEFAULT_TEST_DURATION_MINUTES, step=5
    )

    if st.session_state.get("test_started") and not st.session_state.get("test_finished"):
        time_left_sb = st.session_state.get("end_time", datetime.now()) - datetime.now()
        total_sec_sb = int(max(0, time_left_sb.total_seconds()))
        ans_cnt_sb = answered_count()
        total_q_sb = len(st.session_state.get("questions", []))
        st.markdown("---")
        st.markdown(f"## ⏳ `{format_seconds(total_sec_sb)}`")
        st.markdown(f"**Javoblar:** {ans_cnt_sb}/{total_q_sb}")
        st.progress(ans_cnt_sb / total_q_sb if total_q_sb else 0.0)


# ── State ─────────────────────────────────────
state = st.session_state


def clear_test_keys():
    for k in list(state.keys()):
        if k.startswith("q") and k[1:].isdigit():
            del state[k]
    for key in ["questions", "shuffled_options", "results", "score",
                "test_started", "test_finished", "start_time", "end_time",
                "current_block_indices", "instant_results"]:
        if key in state:
            del state[key]


def reset_all():
    clear_test_keys()
    for key in ["phase", "used_indices", "current_test_number",
                "history", "adaptive_history"]:
        if key in state:
            del state[key]


# Fan yoki test_type o'zgarganda reset
combo_key = f"{subject}|{test_type}"
if state.get("_combo_key") != combo_key:
    clear_test_keys()
    if "phase" in state:
        del state["phase"]
    if "used_indices" in state:
        del state["used_indices"]
    state._combo_key = combo_key
    state.current_subject = subject

all_questions = load_questions(FILE_MAP[subject])
if not all_questions:
    st.stop()

if "phase" not in state:
    state.phase = 1
if "used_indices" not in state:
    state.used_indices = {}
if subject not in state.used_indices:
    state.used_indices[subject] = set()
if "instant_results" not in state:
    state.instant_results = {}

history = state.get("history", {}).get(subject, [])
tests_done = len(history)

st.title(f"📚 {subject}")

# ═════════════════════════════════════════════
# TO'LIQ TEST rejimi
# ═════════════════════════════════════════════
if test_type.startswith("To'liq"):

    st.markdown(f"**Umumiy savollar:** {len(all_questions)} ta")

    # Savollarni tayyorlash
    if "questions" not in state:
        all_indices = list(range(len(all_questions)))
        questions, shuffled_options = prepare_block(all_questions, all_indices)
        state.questions = questions
        state.shuffled_options = shuffled_options
        state.results = [None] * len(questions)
        state.score = 0
        state.test_started = False
        state.test_finished = False
        state.instant_results = {}

    questions = state.get("questions", [])

    # Boshlash
    if not state.get("test_started") and not state.get("test_finished"):
        st.info(f"To'liq test — {len(questions)} ta savol. Vaqt: **{test_duration} daqiqa**")
        if st.button("▶️ Testni Boshlash", type="primary"):
            state.test_started = True
            state.start_time = datetime.now()
            state.end_time = state.start_time + timedelta(minutes=test_duration)
            st.rerun()
        st.stop()

    if state.get("test_started"):
        # Taymer
        time_left = state.end_time - datetime.now()
        if time_left.total_seconds() <= 0 and not state.get("test_finished"):
            score, results = evaluate(questions)
            state.score = score
            state.results = results
            state.test_finished = True
            st.rerun()

        is_finished = state.get("test_finished", False)
        ans_cnt = answered_count()
        total_q = len(questions)

        st.markdown(f"**To'liq Test** | Progress: `{ans_cnt}/{total_q}`")
        st.progress(ans_cnt / total_q if total_q else 0.0)
        st.markdown("---")

        for idx, q in enumerate(questions):
            opts = state.shuffled_options[idx]
            res = state.results[idx] if is_finished else None
            inst = state.instant_results.get(idx) if not is_finished else None
            render_question(idx, q, opts, answer_mode_key, is_finished, res, inst)

        if not is_finished:
            if st.button("✅ Testni Yakunlash", type="primary"):
                score, results = evaluate(questions)
                state.score = score
                state.results = results
                state.test_finished = True
                st.rerun()

        if is_finished:
            total = len(questions)
            score = state.score
            pct = (score / total * 100) if total else 0
            spent = (datetime.now() - state.start_time).total_seconds() if state.get("start_time") else 0
            st.header("📊 Natija")
            st.subheader(f"{total} savoldan **{score}** to'g'ri — {pct:.1f}%")
            st.progress(pct / 100)
            st.write(f"⏱ Sarflangan vaqt: **{format_seconds(spent)}**")
            if st.button("🔄 Yangi test"):
                clear_test_keys()
                st.rerun()

    if state.get("test_started") and not state.get("test_finished"):
        time.sleep(1)
        st.rerun()

    st.stop()


# ═════════════════════════════════════════════
# PHASE 1: 25-LIK BLOK TESTLAR (x10)
# ═════════════════════════════════════════════
if state.phase == 1:

    st.markdown(f"**Bosib o'tilgan testlar:** {tests_done}/10")

    if tests_done >= 10:
        st.success("✅ 10 ta test yakunlandi! Moslashtirilgan test tayyor.")
        if st.button("🎯 Moslashtirilgan testni boshlash", type="primary"):
            clear_test_keys()
            state.phase = 2
            st.rerun()
        st.stop()

    if "questions" not in state:
        selected_indices = get_next_25_block(all_questions, state.used_indices[subject])
        if selected_indices is None:
            st.warning("Barcha savollar ishlatildi.")
            state.phase = 3
            st.rerun()
            st.stop()
        state.current_block_indices = selected_indices
        questions, shuffled_options = prepare_block(all_questions, selected_indices)
        state.questions = questions
        state.shuffled_options = shuffled_options
        state.results = [None] * len(questions)
        state.score = 0
        state.test_started = False
        state.test_finished = False
        state.instant_results = {}

    questions = state.get("questions", [])

    if not state.get("test_started") and not state.get("test_finished"):
        st.info(f"Test #{tests_done + 1} — 25 ta savol. Vaqt: **{test_duration} daqiqa**")
        if st.button("▶️ Testni Boshlash", type="primary"):
            state.test_started = True
            state.start_time = datetime.now()
            state.end_time = state.start_time + timedelta(minutes=test_duration)
            st.rerun()
        st.stop()

    if state.get("test_started"):
        time_left = state.end_time - datetime.now()
        if time_left.total_seconds() <= 0 and not state.get("test_finished"):
            score, results = evaluate(questions)
            state.score = score
            state.results = results
            state.test_finished = True
            spent = (datetime.now() - state.start_time).total_seconds()
            state.used_indices[subject].update(state.current_block_indices)
            record_test_result(subject, questions, results, score, spent, tests_done + 1)
            st.rerun()

        is_finished = state.get("test_finished", False)
        ans_cnt = answered_count()
        total_q = len(questions)

        st.markdown(f"**Test #{tests_done + 1 if not is_finished else tests_done}** | Progress: `{ans_cnt}/{total_q}`")
        st.progress(ans_cnt / total_q if total_q else 0.0)
        st.markdown("---")

        for idx, q in enumerate(questions):
            opts = state.shuffled_options[idx]
            res = state.results[idx] if is_finished else None
            inst = state.instant_results.get(idx) if not is_finished else None
            render_question(idx, q, opts, answer_mode_key, is_finished, res, inst)

        if not is_finished:
            if st.button("✅ Testni Yakunlash", type="primary"):
                score, results = evaluate(questions)
                state.score = score
                state.results = results
                state.test_finished = True
                spent = (datetime.now() - state.start_time).total_seconds()
                state.used_indices[subject].update(state.current_block_indices)
                record_test_result(subject, questions, results, score, spent, tests_done + 1)
                st.rerun()

        if is_finished:
            total = len(questions)
            score = state.score
            pct = (score / total * 100) if total else 0
            spent = (datetime.now() - state.start_time).total_seconds() if state.get("start_time") else 0
            st.header("📊 Natija")
            st.subheader(f"{total} savoldan **{score}** to'g'ri — {pct:.1f}%")
            st.progress(pct / 100)
            st.write(f"⏱ Sarflangan vaqt: **{format_seconds(spent)}**")

            new_done = len(state.get("history", {}).get(subject, []))
            remaining = 10 - new_done

            if remaining > 0:
                if st.button(f"➡️ Keyingi test ({remaining} ta qoldi)"):
                    clear_test_keys()
                    st.rerun()
            else:
                st.success("🎉 10 ta test bajarildi!")
                if st.button("🎯 Moslashtirilgan testni boshlash", type="primary"):
                    clear_test_keys()
                    state.phase = 2
                    st.rerun()

    if state.get("test_started") and not state.get("test_finished"):
        time.sleep(1)
        st.rerun()


# ═════════════════════════════════════════════
# PHASE 2: MOSLASHTIRILGAN TEST
# ═════════════════════════════════════════════
elif state.phase == 2:

    st.markdown("### 🎯 Moslashtirilgan Test")
    st.info("Bu test sizning oldingi 10 ta testdagi xatolaringiz asosida tuzilgan.")

    adaptive_history = state.get("adaptive_history", {}).get(subject, [])
    adaptive_done = len(adaptive_history)

    if adaptive_done > 0:
        last = adaptive_history[-1]
        if last["score"] == last["total"]:
            st.success("✅ Barcha javoblar to'g'ri! Statistikaga o'tishingiz mumkin.")
            if st.button("📈 Statistikani ko'rish"):
                state.phase = 3
                st.rerun()
            st.stop()

    if "questions" not in state:
        selected_indices, ok = build_adaptive_test(subject, all_questions)
        if not ok or selected_indices is None:
            st.warning("Moslashtirilgan test uchun yetarli ma'lumot yo'q.")
            st.stop()
        state.current_block_indices = selected_indices
        questions, shuffled_options = prepare_block(all_questions, selected_indices)
        state.questions = questions
        state.shuffled_options = shuffled_options
        state.results = [None] * len(questions)
        state.score = 0
        state.test_started = False
        state.test_finished = False
        state.instant_results = {}

    questions = state.get("questions", [])

    if not state.get("test_started") and not state.get("test_finished"):
        st.info(f"Moslashtirilgan test #{adaptive_done + 1} — {len(questions)} ta savol. Vaqt: **{test_duration} daqiqa**")
        if st.button("▶️ Boshlash", type="primary"):
            state.test_started = True
            state.start_time = datetime.now()
            state.end_time = state.start_time + timedelta(minutes=test_duration)
            st.rerun()
        st.stop()

    if state.get("test_started"):
        time_left = state.end_time - datetime.now()
        if time_left.total_seconds() <= 0 and not state.get("test_finished"):
            score, results = evaluate(questions)
            state.score = score
            state.results = results
            state.test_finished = True
            spent = (datetime.now() - state.start_time).total_seconds()
            if "adaptive_history" not in state:
                state.adaptive_history = {}
            if subject not in state.adaptive_history:
                state.adaptive_history[subject] = []
            wrong_ids = [q.get("id", q.get("original_index", "?")) for q, r in zip(questions, results) if not r["correct"]]
            state.adaptive_history[subject].append({
                "test_number": adaptive_done + 1,
                "score": score,
                "total": len(questions),
                "wrong_ids": wrong_ids,
                "spent_sec": spent,
            })
            st.rerun()

        is_finished = state.get("test_finished", False)
        ans_cnt = answered_count()
        total_q = len(questions)

        st.markdown(f"**Moslashtirilgan Test #{adaptive_done + 1}** | Progress: `{ans_cnt}/{total_q}`")
        st.progress(ans_cnt / total_q if total_q else 0.0)
        st.markdown("---")

        for idx, q in enumerate(questions):
            opts = state.shuffled_options[idx]
            res = state.results[idx] if is_finished else None
            inst = state.instant_results.get(idx) if not is_finished else None
            render_question(idx, q, opts, answer_mode_key, is_finished, res, inst)

        if not is_finished:
            if st.button("✅ Testni Yakunlash", type="primary"):
                score, results = evaluate(questions)
                state.score = score
                state.results = results
                state.test_finished = True
                spent = (datetime.now() - state.start_time).total_seconds()
                if "adaptive_history" not in state:
                    state.adaptive_history = {}
                if subject not in state.adaptive_history:
                    state.adaptive_history[subject] = []
                wrong_ids = [q.get("id", q.get("original_index", "?")) for q, r in zip(questions, results) if not r["correct"]]
                state.adaptive_history[subject].append({
                    "test_number": adaptive_done + 1,
                    "score": score,
                    "total": len(questions),
                    "wrong_ids": wrong_ids,
                    "spent_sec": spent,
                })
                st.rerun()

        if is_finished:
            total = len(questions)
            score = state.score
            pct = (score / total * 100) if total else 0
            st.header("📊 Natija")
            st.subheader(f"{total} savoldan **{score}** to'g'ri — {pct:.1f}%")
            st.progress(pct / 100)
            if score == total:
                st.success("🎉 Hammasi to'g'ri! Statistikaga o'tishingiz mumkin.")
                if st.button("📈 Statistikani ko'rish"):
                    state.phase = 3
                    st.rerun()
            else:
                st.info("Hali xatolar bor. Qayta urinib ko'ring.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Qayta urinish"):
                        clear_test_keys()
                        st.rerun()
                with col2:
                    if st.button("📈 Statistikani ko'rish"):
                        state.phase = 3
                        st.rerun()

    if state.get("test_started") and not state.get("test_finished"):
        time.sleep(1)
        st.rerun()


# ═════════════════════════════════════════════
# PHASE 3: STATISTIKA
# ═════════════════════════════════════════════
elif state.phase == 3:

    st.markdown("## 📈 Statistika")

    stats = get_subject_stats(subject)
    adaptive_history = state.get("adaptive_history", {}).get(subject, [])

    if not stats:
        st.info("Hali statistika yo'q.")
    else:
        st.subheader("📋 Oddiy Testlar Tarixi (1-10)")
        for rec in stats["history"]:
            pct = rec["score"] / rec["total"] * 100 if rec["total"] else 0
            color = "#d4edda" if pct >= 70 else "#f8d7da"
            st.markdown(
                f"<div style='background:{color};border-left:4px solid #666;padding:8px 14px;border-radius:6px;margin-bottom:6px;color:#111;'>"
                f"<b>Test #{rec['test_number']}</b> — {rec['score']}/{rec['total']} ({pct:.0f}%) "
                f"| Vaqt: {format_seconds(rec['spent_sec'])}"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("---")

        st.subheader("🔁 Top 10 — Ko'p Qaytarilgan Xato Savollar")
        if stats["top10_repeated"]:
            for rank, (qid, cnt) in enumerate(stats["top10_repeated"], 1):
                st.markdown(
                    f"<div style='background:#fff3cd;border-left:4px solid #ffc107;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"<b>#{rank}</b> — Savol ID: <code>{qid}</code> | Xato soni: <b>{cnt}</b></div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Xato yo'q — ajoyib!")

        st.markdown("---")

        st.subheader("❌ Top 5 — Eng Ko'p Xato Qilingan Savollar")
        if stats["top5_wrong"]:
            for rank, (qid, cnt) in enumerate(stats["top5_wrong"], 1):
                st.markdown(
                    f"<div style='background:#f8d7da;border-left:4px solid #dc3545;padding:6px 12px;border-radius:6px;margin-bottom:4px;color:#111;'>"
                    f"<b>#{rank}</b> — Savol ID: <code>{qid}</code> | Xato: <b>{cnt}</b> marta</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Xato yo'q!")

        st.markdown("---")

        if adaptive_history:
            st.subheader("🎯 Moslashtirilgan Test Tarixi")
            for rec in adaptive_history:
                pct = rec["score"] / rec["total"] * 100 if rec["total"] else 0
                color = "#d4edda" if pct >= 80 else "#f8d7da"
                st.markdown(
                    f"<div style='background:{color};border-left:4px solid #666;padding:8px 14px;border-radius:6px;margin-bottom:6px;color:#111;'>"
                    f"<b>Moslashtirilgan Test #{rec['test_number']}</b> — {rec['score']}/{rec['total']} ({pct:.0f}%) "
                    f"| Vaqt: {format_seconds(rec['spent_sec'])}"
                    f"</div>",
                    unsafe_allow_html=True
                )

    st.markdown("---")
    if st.button("🔄 Yangi sessiya boshlash"):
        state.clear()
        st.rerun()

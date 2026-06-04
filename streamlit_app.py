import streamlit as st
import json
import random
import os
import hashlib
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Test Ilovasi", page_icon="🧠", layout="wide")

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DEFAULT_TEST_DURATION_MINUTES = 30
ADMIN_USERNAME = "Obito_404"
ADMIN_PASSWORD_HASH = hashlib.sha256("qwerty1488".encode()).hexdigest()  # <-- parolni shu yerda o'zgartir
USERS_FILE = "users.json"
RESULTS_FILE = "results.json"

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}
code, .stCode { font-family: 'Space Mono', monospace !important; }

.stApp { background: #0d0d0d; color: #e8e8e8; }
.stSidebar { background: #111 !important; border-right: 1px solid #222; }
h1, h2, h3 { color: #00ff88 !important; font-family: 'Syne', sans-serif !important; font-weight: 800 !important; letter-spacing: -1px; }
h4, h5 { color: #aaa !important; }

div[data-testid="stButton"] > button {
    background: #00ff88 !important; color: #000 !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 4px !important; font-family: 'Space Mono', monospace !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stButton"] > button:hover { background: #00cc6a !important; transform: translateY(-1px); }

div[data-testid="stTextInput"] input {
    background: #1a1a1a !important; color: #e8e8e8 !important;
    border: 1px solid #333 !important; border-radius: 4px !important;
    font-family: 'Space Mono', monospace !important;
}
div[data-testid="stTextInput"] input:focus { border-color: #00ff88 !important; box-shadow: 0 0 0 1px #00ff88 !important; }

.stRadio label { color: #ccc !important; }
.stProgress > div > div { background: #00ff88 !important; }

.stat-card {
    background: #161616; border: 1px solid #2a2a2a;
    border-radius: 8px; padding: 16px 20px; margin-bottom: 10px;
    border-left: 3px solid #00ff88;
}
.leaderboard-row {
    background: #161616; border: 1px solid #2a2a2a;
    border-radius: 6px; padding: 10px 16px; margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
}
.rank-1 { border-left: 3px solid #FFD700; }
.rank-2 { border-left: 3px solid #C0C0C0; }
.rank-3 { border-left: 3px solid #CD7F32; }
.rank-other { border-left: 3px solid #333; }
.tag-green { color: #00ff88; font-weight: 700; font-family: 'Space Mono', monospace; }
.tag-red { color: #ff4444; font-weight: 700; }
.tag-yellow { color: #ffcc00; font-weight: 700; }
.admin-badge {
    background: #ff4444; color: #fff; font-size: 11px;
    padding: 2px 8px; border-radius: 3px; font-family: 'Space Mono', monospace;
    font-weight: 700; letter-spacing: 1px;
}
div[data-testid="stSelectbox"] > div { background: #1a1a1a !important; border-color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILE HELPERS
# ─────────────────────────────────────────────

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────

def get_client_ip():
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        if headers:
            return headers.get("X-Forwarded-For", headers.get("X-Real-IP", "unknown"))
    except Exception:
        pass
    try:
        import streamlit.runtime.scriptrunner as sr
        ctx = sr.get_script_run_ctx()
        if ctx:
            from streamlit.runtime.runtime import Runtime
            rt = Runtime.instance()
            session_info = rt.get_client(ctx.session_id)
            if session_info:
                return str(session_info.request.remote_ip)
    except Exception:
        pass
    return "127.0.0.1"

def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    save_json(USERS_FILE, users)

def register_or_login(username, ip):
    """Returns: (success, message, is_admin)"""
    if not username or len(username) < 2:
        return False, "Username kamida 2 ta harf bo'lishi kerak.", False
    users = load_users()
    is_admin = (username == ADMIN_USERNAME)
    if username in users:
        stored_ip = users[username].get("ip")
        if stored_ip == ip or stored_ip == "unknown":
            users[username]["ip"] = ip
            users[username]["last_seen"] = datetime.now().isoformat()
            save_users(users)
            return True, f"Xush kelibsiz, {username}!", is_admin
        else:
            return False, "Bu username boshqa qurilmada ro'yxatdan o'tgan. Boshqa username tanlang.", False
    else:
        if is_admin:
            return False, "Bu username band.", False
        users[username] = {
            "ip": ip,
            "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        save_users(users)
        return True, f"Xush kelibsiz, {username}! Ro'yxatdan o'tdingiz.", False

# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────

def save_result(username, subject, test_type, test_number, score, total, spent_sec):
    results = load_json(RESULTS_FILE, [])
    results.append({
        "username": username,
        "subject": subject,
        "test_type": test_type,
        "test_number": test_number,
        "score": score,
        "total": total,
        "percent": round(score / total * 100, 1) if total else 0,
        "spent_sec": spent_sec,
        "timestamp": datetime.now().isoformat()
    })
    save_json(RESULTS_FILE, results)

def get_leaderboard(subject, test_type="25-talik"):
    """Top 5 users for a subject/test_type by best percent."""
    results = load_json(RESULTS_FILE, [])
    filtered = [r for r in results if r["subject"] == subject and r["test_type"] == test_type]
    best = {}
    for r in filtered:
        u = r["username"]
        tests_done = sum(1 for x in filtered if x["username"] == u)
        avg = sum(x["percent"] for x in filtered if x["username"] == u) / tests_done if tests_done else 0
        if u not in best or avg > best[u]["avg_percent"]:
            best[u] = {
                "username": u,
                "best_score": r["score"],
                "best_total": r["total"],
                "best_percent": max(x["percent"] for x in filtered if x["username"] == u),
                "avg_percent": round(avg, 1),
                "tests_done": tests_done
            }
    top5 = sorted(best.values(), key=lambda x: -x["best_percent"])[:5]
    return top5

def get_user_stats(username, subject):
    results = load_json(RESULTS_FILE, [])
    return [r for r in results if r["username"] == username and r["subject"] == subject]

# ─────────────────────────────────────────────
# QUESTION HELPERS
# ─────────────────────────────────────────────

def format_seconds(sec):
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"

def answered_count():
    if "questions" not in st.session_state:
        return 0
    return sum(1 for i in range(len(st.session_state.questions))
               if st.session_state.get(f"q{i+1}") not in (None, ""))

def load_questions(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"'{file_name}' fayli topilmadi.")
        return []
    except json.JSONDecodeError:
        st.error(f"'{file_name}' JSON formatida emas.")
        return []

def get_next_25_block(all_questions, used_indices):
    available = [i for i in range(len(all_questions)) if i not in used_indices]
    count = min(25, len(available))
    if count < 10:
        return None
    return random.sample(available, count)

def prepare_block(all_questions, selected_indices):
    questions, shuffled_options = [], []
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

def evaluate(questions):
    score, results = 0, []
    for qi, qd in enumerate(questions):
        ui = st.session_state.get(f"q{qi+1}")
        correct = ui == qd.get("javob") if ui not in (None, "") else False
        if correct:
            score += 1
        results.append({"correct": correct, "user_answer": ui, "correct_answer": qd.get("javob")})
    return score, results

def render_question(idx, q, opts, mode, is_finished, result, instant_result):
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
            "correct": is_correct, "user_answer": val, "correct_answer": correct_ans
        }

    if mode == "instant" and not is_finished:
        st.radio("", opts, key=key, index=default_index, label_visibility="collapsed",
                 disabled=disabled, on_change=on_change_instant)
        if instant_result is not None:
            if instant_result["correct"]:
                st.markdown("<div class='stat-card' style='border-left-color:#00ff88'>✅ To'g'ri!</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='stat-card' style='border-left-color:#ff4444'>❌ Xato! To'g'ri javob: <b>{instant_result['correct_answer']}</b></div>", unsafe_allow_html=True)
    else:
        st.radio("", opts, key=key, index=default_index, label_visibility="collapsed", disabled=is_finished)
        if is_finished and result:
            if result["user_answer"] is None:
                st.markdown(f"<div class='stat-card' style='border-left-color:#ffcc00'>⚠️ Javob berilmagan. To'g'ri: <b>{result['correct_answer']}</b></div>", unsafe_allow_html=True)
            elif result["correct"]:
                st.markdown(f"<div class='stat-card' style='border-left-color:#00ff88'>✅ To'g'ri: <b>{result['user_answer']}</b></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='stat-card' style='border-left-color:#ff4444'>❌ Xato: <b>{result['user_answer']}</b> | To'g'ri: <b>{result['correct_answer']}</b></div>", unsafe_allow_html=True)
    st.markdown("---")

def clear_test_keys():
    for k in list(st.session_state.keys()):
        if k.startswith("q") and k[1:].isdigit():
            del st.session_state[k]
    for key in ["questions", "shuffled_options", "results", "score",
                "test_started", "test_finished", "start_time", "end_time",
                "current_block_indices", "instant_results"]:
        if key in st.session_state:
            del st.session_state[key]

# ─────────────────────────────────────────────
# FILE MAP
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
                QUESTION_COUNTS[name] = len(json.load(f))
        except Exception:
            QUESTION_COUNTS[name] = 0
    else:
        QUESTION_COUNTS[name] = 0

# ═════════════════════════════════════════════
# LOGIN SCREEN
# ═════════════════════════════════════════════
state = st.session_state

if "username" not in state:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🧠 Test Ilovasi")
        st.markdown("---")
        st.markdown("### Kirish")
        st.markdown("<p style='color:#888;font-size:14px;'>Username kiriting. Avval ro'yxatdan o'tmagan bo'lsangiz — avtomatik yaratiladi.</p>", unsafe_allow_html=True)
        username_input = st.text_input("Username:", placeholder="masalan: ali_2024", key="login_input")

        admin_mode = (username_input == ADMIN_USERNAME)
        if admin_mode:
            password_input = st.text_input("Parol:", type="password", key="login_pass")
        else:
            password_input = None

        if st.button("▶️ Kirish", type="primary"):
            if not username_input:
                st.error("Username bo'sh bo'lishi mumkin emas.")
            elif admin_mode:
                if hashlib.sha256(password_input.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
                    state.username = ADMIN_USERNAME
                    state.is_admin = True
                    st.rerun()
                else:
                    st.error("Noto'g'ri parol.")
            else:
                ip = get_client_ip()
                ok, msg, is_admin = register_or_login(username_input, ip)
                if ok:
                    state.username = username_input
                    state.is_admin = is_admin
                    st.success(msg)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(msg)
    st.stop()

# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────
if state.get("is_admin"):
    st.markdown(f"# 🔐 Admin Panel <span class='admin-badge'>ADMIN</span>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#666;font-family:Space Mono,monospace;font-size:13px;'>Kirdi: {ADMIN_USERNAME}</p>", unsafe_allow_html=True)

    users = load_users()
    results = load_json(RESULTS_FILE, [])

    tab1, tab2, tab3 = st.tabs(["👥 Foydalanuvchilar", "📊 Natijalar", "🏆 Leaderboard"])

    with tab1:
        st.markdown(f"### Jami foydalanuvchilar: `{len(users)}`")
        if users:
            for uname, udata in sorted(users.items(), key=lambda x: x[1].get("last_seen",""), reverse=True):
                user_results = [r for r in results if r["username"] == uname]
                tests_done = len(user_results)
                avg_pct = round(sum(r["percent"] for r in user_results) / tests_done, 1) if tests_done else 0
                last = udata.get("last_seen", "—")[:16].replace("T", " ")
                st.markdown(f"""
                <div class='stat-card'>
                  <b style='color:#00ff88;font-family:Space Mono,monospace;'>{uname}</b>
                  <span style='color:#555;font-size:12px;margin-left:12px;'>IP: {udata.get('ip','—')}</span><br>
                  <span style='color:#aaa;font-size:13px;'>Testlar: <b>{tests_done}</b> &nbsp;|&nbsp; O'rtacha: <b>{avg_pct}%</b> &nbsp;|&nbsp; Oxirgi: {last}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Hali hech kim ro'yxatdan o'tmagan.")

    with tab2:
        st.markdown(f"### Jami natijalar: `{len(results)}`")
        subject_filter = st.selectbox("Fan bo'yicha filtrlash:", ["Hammasi"] + list(FILE_MAP.keys()), key="admin_subj_filter")
        filtered_results = [r for r in results if subject_filter == "Hammasi" or r["subject"] == subject_filter]
        filtered_results_sorted = sorted(filtered_results, key=lambda x: x.get("timestamp",""), reverse=True)

        for r in filtered_results_sorted[:50]:
            pct = r.get("percent", 0)
            color = "#00ff88" if pct >= 70 else "#ffcc00" if pct >= 50 else "#ff4444"
            ts = r.get("timestamp","—")[:16].replace("T"," ")
            st.markdown(f"""
            <div class='stat-card' style='border-left-color:{color}'>
              <b style='color:#e8e8e8;'>{r['username']}</b>
              <span style='color:#555;font-size:12px;margin-left:8px;'>{ts}</span><br>
              <span style='color:#aaa;font-size:13px;'>
                {r['subject']} &nbsp;|&nbsp; {r['test_type']} #{r.get('test_number','')}
                &nbsp;|&nbsp; <b style='color:{color};'>{r['score']}/{r['total']} ({pct}%)</b>
                &nbsp;|&nbsp; ⏱ {format_seconds(r.get('spent_sec',0))}
              </span>
            </div>""", unsafe_allow_html=True)
        if len(filtered_results) > 50:
            st.caption(f"(Faqat oxirgi 50 ta ko'rsatilmoqda, jami: {len(filtered_results)})")

    with tab3:
        st.markdown("### Leaderboard — 25-talik testlar")
        for subj in FILE_MAP.keys():
            st.markdown(f"#### 📚 {subj}")
            top5 = get_leaderboard(subj, "25-talik")
            if not top5:
                st.caption("Hali natija yo'q.")
                continue
            rank_classes = ["rank-1","rank-2","rank-3","rank-other","rank-other"]
            rank_icons = ["🥇","🥈","🥉","4️⃣","5️⃣"]
            for i, row in enumerate(top5):
                st.markdown(f"""
                <div class='leaderboard-row {rank_classes[i]}'>
                  <span>{rank_icons[i]} <b style='color:#e8e8e8;font-family:Space Mono,monospace;'>{row['username']}</b></span>
                  <span style='color:#aaa;font-size:13px;'>
                    Eng yaxshi: <span class='tag-green'>{row['best_percent']}%</span>
                    &nbsp;|&nbsp; O'rtacha: {row['avg_percent']}%
                    &nbsp;|&nbsp; Testlar: {row['tests_done']}
                  </span>
                </div>""", unsafe_allow_html=True)
            st.markdown("")

    st.markdown("---")
    if st.button("🚪 Chiqish"):
        for k in list(state.keys()):
            del state[k]
        st.rerun()
    st.stop()

# ─────────────────────────────────────────────
# SIDEBAR (normal user)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<p style='color:#00ff88;font-family:Space Mono,monospace;font-weight:700;'>👤 {state.username}</p>", unsafe_allow_html=True)
    st.header("⚙️ Sozlamalar")

    subject_options = [f"{name} ({QUESTION_COUNTS.get(name,'?')} ta savol)" for name in FILE_MAP]
    subject_display = st.selectbox("Fan:", subject_options)
    subject = subject_display.split(" (")[0]

    st.markdown("---")
    test_type = st.radio("Test turi:", ["25 ta blok (x10)", "To'liq test (barcha savollar)"])
    st.markdown("---")
    answer_mode = st.radio("Javob ko'rsatish:", ["Darhol (bosganda)", "Yakunlashda (hammasi birga)"])
    answer_mode_key = "instant" if answer_mode.startswith("Darhol") else "final"
    st.markdown("---")
    st.subheader("⏱ Vaqt")
    test_duration = st.number_input("Test vaqti (daqiqa):", min_value=5, max_value=180,
                                     value=DEFAULT_TEST_DURATION_MINUTES, step=5)

    if state.get("test_started") and not state.get("test_finished"):
        time_left_sb = state.get("end_time", datetime.now()) - datetime.now()
        total_sec_sb = int(max(0, time_left_sb.total_seconds()))
        ans_cnt_sb = answered_count()
        total_q_sb = len(state.get("questions", []))
        st.markdown("---")
        st.markdown(f"## ⏳ `{format_seconds(total_sec_sb)}`")
        st.markdown(f"**Javoblar:** {ans_cnt_sb}/{total_q_sb}")
        st.progress(ans_cnt_sb / total_q_sb if total_q_sb else 0.0)

    st.markdown("---")
    if st.button("🚪 Chiqish"):
        for k in list(state.keys()):
            del state[k]
        st.rerun()

# ─────────────────────────────────────────────
# COMBO KEY RESET
# ─────────────────────────────────────────────
combo_key = f"{state.username}|{subject}|{test_type}"
if state.get("_combo_key") != combo_key:
    clear_test_keys()
    if "phase" in state: del state["phase"]
    if "used_indices" in state: del state["used_indices"]
    state._combo_key = combo_key
    state.current_subject = subject

all_questions = load_questions(FILE_MAP[subject])
if not all_questions:
    st.stop()

if "phase" not in state: state.phase = 1
if "used_indices" not in state: state.used_indices = {}
if subject not in state.used_indices: state.used_indices[subject] = set()
if "instant_results" not in state: state.instant_results = {}

history_results = [r for r in load_json(RESULTS_FILE, [])
                   if r["username"] == state.username and r["subject"] == subject and r["test_type"] == "25-talik"]
tests_done = len(history_results)

st.title(f"📚 {subject}")

# ═════════════════════════════════════════════
# LEADERBOARD SECTION (public, top of page)
# ═════════════════════════════════════════════
with st.expander("🏆 Leaderboard — Top 5", expanded=False):
    lb_tabs = st.tabs(list(FILE_MAP.keys()))
    rank_classes = ["rank-1","rank-2","rank-3","rank-other","rank-other"]
    rank_icons = ["🥇","🥈","🥉","4️⃣","5️⃣"]
    for ti, (subj, lb_tab) in enumerate(zip(FILE_MAP.keys(), lb_tabs)):
        with lb_tab:
            top5 = get_leaderboard(subj, "25-talik")
            if not top5:
                st.caption("Hali natija yo'q.")
                continue
            for i, row in enumerate(top5):
                st.markdown(f"""
                <div class='leaderboard-row {rank_classes[i]}'>
                  <span>{rank_icons[i]} <b style='color:#e8e8e8;font-family:Space Mono,monospace;'>{row['username']}</b></span>
                  <span style='color:#aaa;font-size:13px;'>
                    Eng yaxshi: <span class='tag-green'>{row['best_percent']}%</span>
                    &nbsp;|&nbsp; Testlar: {row['tests_done']}
                  </span>
                </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════
# TO'LIQ TEST
# ═════════════════════════════════════════════
if test_type.startswith("To'liq"):
    st.markdown(f"**Umumiy savollar:** {len(all_questions)} ta")

    if "questions" not in state:
        questions, shuffled_options = prepare_block(all_questions, list(range(len(all_questions))))
        state.questions = questions
        state.shuffled_options = shuffled_options
        state.results = [None] * len(questions)
        state.score = 0
        state.test_started = False
        state.test_finished = False
        state.instant_results = {}

    questions = state.get("questions", [])

    if not state.get("test_started") and not state.get("test_finished"):
        st.info(f"To'liq test — {len(questions)} ta savol. Vaqt: **{test_duration} daqiqa**")
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
            state.score = score; state.results = results; state.test_finished = True
            spent = (datetime.now() - state.start_time).total_seconds()
            save_result(state.username, subject, "to'liq", 1, score, len(questions), spent)
            st.rerun()

        is_finished = state.get("test_finished", False)
        ans_cnt = answered_count(); total_q = len(questions)
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
                state.score = score; state.results = results; state.test_finished = True
                spent = (datetime.now() - state.start_time).total_seconds()
                save_result(state.username, subject, "to'liq", 1, score, len(questions), spent)
                st.rerun()

        if is_finished:
            total = len(questions); score = state.score
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
        time.sleep(1); st.rerun()
    st.stop()

# ═════════════════════════════════════════════
# PHASE 1: 25-LIK BLOK TESTLAR (x10)
# ═════════════════════════════════════════════
if state.phase == 1:
    st.markdown(f"**Bosib o'tilgan testlar:** {tests_done}/10")

    if tests_done >= 10:
        st.success("✅ 10 ta test yakunlandi!")
        st.stop()

    if "questions" not in state:
        selected_indices = get_next_25_block(all_questions, state.used_indices[subject])
        if selected_indices is None:
            st.warning("Barcha savollar ishlatildi.")
            st.stop()
        state.current_block_indices = selected_indices
        questions, shuffled_options = prepare_block(all_questions, selected_indices)
        state.questions = questions; state.shuffled_options = shuffled_options
        state.results = [None] * len(questions); state.score = 0
        state.test_started = False; state.test_finished = False; state.instant_results = {}

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
            state.score = score; state.results = results; state.test_finished = True
            spent = (datetime.now() - state.start_time).total_seconds()
            state.used_indices[subject].update(state.current_block_indices)
            save_result(state.username, subject, "25-talik", tests_done + 1, score, len(questions), spent)
            st.rerun()

        is_finished = state.get("test_finished", False)
        ans_cnt = answered_count(); total_q = len(questions)
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
                state.score = score; state.results = results; state.test_finished = True
                spent = (datetime.now() - state.start_time).total_seconds()
                state.used_indices[subject].update(state.current_block_indices)
                save_result(state.username, subject, "25-talik", tests_done + 1, score, len(questions), spent)
                st.rerun()

        if is_finished:
            total = len(questions); score = state.score
            pct = (score / total * 100) if total else 0
            spent = (datetime.now() - state.start_time).total_seconds() if state.get("start_time") else 0
            st.header("📊 Natija")
            st.subheader(f"{total} savoldan **{score}** to'g'ri — {pct:.1f}%")
            st.progress(pct / 100)
            st.write(f"⏱ Sarflangan vaqt: **{format_seconds(spent)}**")

            # Shaxsiy statistika
            st.markdown("---")
            st.subheader("📈 Mening Statistikam")
            my_results = [r for r in load_json(RESULTS_FILE, [])
                          if r["username"] == state.username and r["subject"] == subject and r["test_type"] == "25-talik"]
            if my_results:
                for rec in my_results:
                    color = "#00ff88" if rec["percent"] >= 70 else "#ffcc00" if rec["percent"] >= 50 else "#ff4444"
                    st.markdown(f"""
                    <div class='stat-card' style='border-left-color:{color}'>
                      <b>Test #{rec['test_number']}</b> —
                      <span style='color:{color};'>{rec['score']}/{rec['total']} ({rec['percent']}%)</span>
                      &nbsp;|&nbsp; ⏱ {format_seconds(rec['spent_sec'])}
                    </div>""", unsafe_allow_html=True)

            new_done = len([r for r in load_json(RESULTS_FILE, [])
                            if r["username"] == state.username and r["subject"] == subject and r["test_type"] == "25-talik"])
            remaining = 10 - new_done
            if remaining > 0:
                if st.button(f"➡️ Keyingi test ({remaining} ta qoldi)"):
                    clear_test_keys()
                    st.rerun()
            else:
                st.success("🎉 10 ta test bajarildi!")

    if state.get("test_started") and not state.get("test_finished"):
        time.sleep(1); st.rerun()

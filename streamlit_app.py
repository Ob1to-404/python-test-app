import streamlit as st
import json
import random
import math
import os
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Test Ilovasi", page_icon="🧠", layout="wide")

# ══════════════════════════════════════════════
# CSS — Terminal/hacker dark aesthetic
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Rajdhani:wght@400;500;600;700&display=swap');

*, html, body { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif !important;
    background: #080c0f !important;
    color: #c9d1d9 !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1e2a35 !important;
}
section[data-testid="stSidebar"] * { color: #8b949e !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #58a6ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}

/* ── Headings ── */
h1 {
    font-family: 'JetBrains Mono', monospace !important;
    color: #58a6ff !important;
    font-size: 22px !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #1e2a35;
    padding-bottom: 12px;
    margin-bottom: 4px !important;
}
h2, h3 {
    font-family: 'Rajdhani', sans-serif !important;
    color: #e6edf3 !important;
    font-weight: 600 !important;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    color: #39d353 !important;
    border: 1px solid #39d353 !important;
    border-radius: 3px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    padding: 8px 24px !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #39d35318 !important;
    box-shadow: 0 0 12px #39d35340 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #39d35312 !important;
    border-color: #39d353 !important;
    box-shadow: 0 0 8px #39d35328 !important;
}

/* ── Radio ── */
div[data-testid="stRadio"] label {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 16px !important;
    color: #c9d1d9 !important;
    padding: 6px 10px !important;
    border-radius: 4px !important;
    transition: color 0.15s !important;
}
div[data-testid="stRadio"] label:hover { color: #58a6ff !important; }

/* ── Progress ── */
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #1f6feb, #58a6ff) !important;
}

/* ── Selectbox ── */
div[data-testid="stSelectbox"] > div > div {
    background: #0d1117 !important;
    border: 1px solid #1e2a35 !important;
    color: #c9d1d9 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── Info/success/error boxes ── */
div[data-testid="stAlert"] {
    border-radius: 4px !important;
    border-left-width: 3px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 16px !important;
}

/* ── Number input ── */
div[data-testid="stNumberInput"] input {
    background: #0d1117 !important;
    border: 1px solid #1e2a35 !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Custom cards ── */
.q-card {
    background: #0d1117;
    border: 1px solid #1e2a35;
    border-left: 3px solid #1f6feb;
    border-radius: 6px;
    padding: 20px 24px 14px 24px;
    margin-bottom: 16px;
}
.q-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #1f6feb;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.q-text {
    font-family: 'Rajdhani', sans-serif;
    font-size: 18px;
    font-weight: 600;
    color: #e6edf3;
    line-height: 1.5;
}
.result-correct {
    background: #0d1117;
    border: 1px solid #238636;
    border-left: 3px solid #39d353;
    border-radius: 4px;
    padding: 10px 16px;
    margin-top: 6px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 15px;
    color: #39d353;
}
.result-wrong {
    background: #0d1117;
    border: 1px solid #da3633;
    border-left: 3px solid #f85149;
    border-radius: 4px;
    padding: 10px 16px;
    margin-top: 6px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 15px;
    color: #f85149;
}
.result-skip {
    background: #0d1117;
    border: 1px solid #9e6a03;
    border-left: 3px solid #d29922;
    border-radius: 4px;
    padding: 10px 16px;
    margin-top: 6px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 15px;
    color: #d29922;
}
.score-box {
    background: #0d1117;
    border: 1px solid #1e2a35;
    border-radius: 8px;
    padding: 32px;
    text-align: center;
    margin: 24px 0;
}
.score-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 56px;
    font-weight: 700;
    color: #58a6ff;
    line-height: 1;
}
.score-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 14px;
    color: #8b949e;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 6px;
}
.stat-row {
    display: flex;
    justify-content: center;
    gap: 48px;
    margin-top: 20px;
}
.stat-item { text-align: center; }
.stat-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 700;
}
.stat-lbl {
    font-family: 'Rajdhani', sans-serif;
    font-size: 12px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.green { color: #39d353; }
.red   { color: #f85149; }
.blue  { color: #58a6ff; }
.timer-bar {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: #58a6ff;
    letter-spacing: 2px;
}
.fan-badge {
    display: inline-block;
    background: #1f6feb18;
    border: 1px solid #1f6feb44;
    color: #58a6ff;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 3px;
    margin-bottom: 16px;
    text-transform: uppercase;
}
.divider {
    border: none;
    border-top: 1px solid #1e2a35;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# CONSTANTS & CONFIG
# ══════════════════════════════════════════════
FILE_MAP = {
    "Kompyuter Tarmoqlari":    "Kompuyter_tarmoqlari.json",
    "Elektronika va Sxemalar": "Elektronika_va_sxemalar.json",
    "Kiberxavfsizlik":         "Kiberxavfsizlik.json",
    "Diskret Matematika":      "Diskret.json"
}
DEFAULT_DURATION = 30   # daqiqa
TEST_SIZE = 25          # bir testdagi savollar soni

# ══════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════

def load_questions(fname):
    try:
        with open(fname, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"'{fname}' fayli topilmadi.")
        return []
    except json.JSONDecodeError:
        st.error(f"'{fname}' JSON formatida emas.")
        return []


def fmt_sec(sec):
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


def answered_count():
    qs = st.session_state.get("questions", [])
    return sum(1 for i in range(len(qs)) if st.session_state.get(f"q{i}") not in (None, ""))


def pick_questions(all_q, prev_indices, n=TEST_SIZE):
    """
    Weighted random: oldingi testda chiqqan savollar 3x kamroq ehtimol.
    Bir testda qaytarilmaydi (random.sample).
    """
    total = len(all_q)
    weights = []
    for i in range(total):
        weights.append(1 if i not in prev_indices else 0.33)

    # Weighted sampling without replacement
    pool = list(range(total))
    chosen = []
    w = weights[:]
    n = min(n, total)
    for _ in range(n):
        total_w = sum(w)
        r = random.uniform(0, total_w)
        cum = 0
        for idx, wi in enumerate(w):
            cum += wi
            if r <= cum:
                chosen.append(pool[idx])
                w[idx] = 0   # o'chiramiz — bir testda qaytarilmasin
                break
    return chosen


def prepare_block(all_q, indices):
    questions, options = [], []
    for i in indices:
        q = dict(all_q[i])
        q["_orig_idx"] = i
        if "variantlar" in q:
            opts = q["variantlar"][:]
            random.shuffle(opts)
            options.append(opts)
        else:
            options.append(None)
        questions.append(q)
    return questions, options


def evaluate(questions):
    score, results = 0, []
    for i, q in enumerate(questions):
        ua = st.session_state.get(f"q{i}")
        if q.get("type") == "calculation":
            try:
                uv = float(ua) if ua not in (None, "") else None
                cv = float(q["to_g_ri_javob"])
                tol = float(q.get("tolerance", 0.01))
                ok = uv is not None and abs(uv - cv) <= tol
            except Exception:
                ok = False
                uv = None
                cv = q.get("to_g_ri_javob")
            results.append({"correct": ok, "user": ua, "answer": cv})
        else:
            ca = q.get("javob")
            ok = (ua == ca) if ua not in (None, "") else False
            results.append({"correct": ok, "user": ua, "answer": ca})
        if ok:
            score += 1
    return score, results


def clear_test():
    keys_to_del = [k for k in st.session_state.keys()
                   if k.startswith("q") and k[1:].isdigit()]
    for k in keys_to_del:
        del st.session_state[k]
    for k in ["questions", "options", "results", "score",
              "started", "finished", "t_start", "t_end", "instant"]:
        st.session_state.pop(k, None)


# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
state = st.session_state

with st.sidebar:
    st.markdown("### // SOZLAMALAR")

    q_counts = {}
    for n, f in FILE_MAP.items():
        if os.path.exists(f):
            try:
                q_counts[n] = len(json.load(open(f, encoding="utf-8")))
            except Exception:
                q_counts[n] = 0
        else:
            q_counts[n] = 0

    subject_opts = [f"{n}  [{q_counts[n]}]" for n in FILE_MAP]
    sel = st.selectbox("Fan:", subject_opts, label_visibility="collapsed")
    subject = sel.split("  [")[0]

    st.markdown("---")

    test_mode = st.radio(
        "Test turi:",
        ["25 ta savol", "To'liq test"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    answer_mode = st.radio(
        "Javob:",
        ["Darhol ko'rsat", "Oxirida ko'rsat"],
        label_visibility="collapsed"
    )
    instant = answer_mode == "Darhol ko'rsat"

    st.markdown("---")
    duration = st.slider("Vaqt (daqiqa)", 5, 120, DEFAULT_DURATION, 5)

    # Timer sidebar
    if state.get("started") and not state.get("finished"):
        left = state.get("t_end", datetime.now()) - datetime.now()
        secs = max(0, int(left.total_seconds()))
        aq = answered_count()
        tq = len(state.get("questions", []))
        st.markdown("---")
        st.markdown(f"<div class='timer-bar'>⏱ {fmt_sec(secs)}</div>", unsafe_allow_html=True)
        st.progress(aq / tq if tq else 0, text=f"{aq}/{tq} javob")

# ══════════════════════════════════════════════
# COMBO RESET — fan yoki rejim o'zgarganda
# ══════════════════════════════════════════════
combo = f"{subject}|{test_mode}"
if state.get("_combo") != combo:
    clear_test()
    state.pop("prev_indices", None)
    state["_combo"] = combo

all_q = load_questions(FILE_MAP[subject])
if not all_q:
    st.stop()

q_count = len(all_q)

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown(f"# 🧠 TEST ILOVASI")
st.markdown(f"<div class='fan-badge'>{subject} — {q_count} ta savol</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SAVOLLARNI TAYYORLASH
# ══════════════════════════════════════════════
if "questions" not in state:
    if test_mode == "25 ta savol":
        prev = state.get("prev_indices", set())
        indices = pick_questions(all_q, prev, TEST_SIZE)
    else:
        indices = list(range(q_count))
        random.shuffle(indices)

    questions, options = prepare_block(all_q, indices)
    state.questions = questions
    state.options = options
    state.results = [None] * len(questions)
    state.score = 0
    state.started = False
    state.finished = False
    state.instant = {}

questions = state.questions
opts_all  = state.options
n_q       = len(questions)

# ══════════════════════════════════════════════
# BOSHLASH EKRANI
# ══════════════════════════════════════════════
if not state.get("started") and not state.get("finished"):
    label = f"{n_q} ta savol" if test_mode == "25 ta savol" else f"To'liq test — {n_q} ta savol"
    st.info(f"📋 {label} · ⏱ {duration} daqiqa")
    if st.button("▶  TESTNI BOSHLASH", type="primary"):
        state.started = True
        state.t_start = datetime.now()
        state.t_end   = datetime.now() + timedelta(minutes=duration)
        st.rerun()
    st.stop()

# ══════════════════════════════════════════════
# TEST JARAYONI
# ══════════════════════════════════════════════
if state.get("started"):

    # Vaqt tugadimi?
    time_left = state.t_end - datetime.now()
    if time_left.total_seconds() <= 0 and not state.get("finished"):
        sc, res = evaluate(questions)
        state.score   = sc
        state.results = res
        state.finished = True
        if test_mode == "25 ta savol":
            prev = state.get("prev_indices", set())
            prev.update(q["_orig_idx"] for q in questions)
            state.prev_indices = prev
        st.rerun()

    is_done = state.get("finished", False)

    # Progress bar (faqat test davomida)
    if not is_done:
        aq = answered_count()
        col_p, col_t = st.columns([4, 1])
        with col_p:
            st.progress(aq / n_q if n_q else 0, text=f"Javoblar: {aq}/{n_q}")
        with col_t:
            secs = max(0, int(time_left.total_seconds()))
            st.markdown(f"<div class='timer-bar'>{fmt_sec(secs)}</div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Savollar ──────────────────────────────
    for i, q in enumerate(questions):
        opts   = opts_all[i]
        res    = state.results[i] if is_done else None
        inst_r = state.instant.get(i) if not is_done else None
        q_type = q.get("type", "multiple_choice")

        q_id = q.get("id", q.get("_orig_idx", "—"))
        st.markdown(
            f"<div class='q-card'>"
            f"<div class='q-num'>"
            f"{i+1} / <span style='color:#58a6ff;'>{q_id}</span>"
            f"</div>"
            f"<div class='q-text'>{q['savol']}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        key = f"q{i}"
        cur = state.get(key)

        if q_type == "multiple_choice":
            try:
                def_idx = opts.index(cur) if cur in opts else None
            except (ValueError, TypeError):
                def_idx = None

            disabled = is_done or (instant and inst_r is not None)

            def make_on_change(qi, qdata):
                def _cb():
                    val = state.get(f"q{qi}")
                    ca  = qdata.get("javob")
                    ok  = (val == ca) if val not in (None, "") else False
                    state.instant[qi] = {"correct": ok, "user": val, "answer": ca}
                return _cb

            if instant and not is_done:
                st.radio("", opts, key=key, index=def_idx,
                         label_visibility="collapsed",
                         disabled=disabled,
                         on_change=make_on_change(i, q))
                if inst_r is not None:
                    if inst_r["correct"]:
                        st.markdown("<div class='result-correct'>✓ To'g'ri!</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='result-wrong'>✗ Xato — To'g'ri javob: <b>{inst_r['answer']}</b></div>", unsafe_allow_html=True)
            else:
                st.radio("", opts, key=key, index=def_idx,
                         label_visibility="collapsed", disabled=is_done)
                if is_done and res:
                    ua = res["user"]
                    ca = res["answer"]
                    if ua is None:
                        st.markdown(f"<div class='result-skip'>— Javob berilmagan · To'g'ri: <b>{ca}</b></div>", unsafe_allow_html=True)
                    elif res["correct"]:
                        st.markdown(f"<div class='result-correct'>✓ To'g'ri: <b>{ua}</b></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='result-wrong'>✗ Xato: <b>{ua}</b> · To'g'ri: <b>{ca}</b></div>", unsafe_allow_html=True)

        elif q_type == "calculation":
            st.number_input("Javob (son):", key=key, format="%.2f", disabled=is_done)
            if is_done and res:
                ua = res["user"]
                ca = res["answer"]
                if ua is None:
                    st.markdown(f"<div class='result-skip'>— Javob berilmagan · To'g'ri: <b>{ca}</b></div>", unsafe_allow_html=True)
                elif res["correct"]:
                    st.markdown(f"<div class='result-correct'>✓ To'g'ri: <b>{ua}</b></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='result-wrong'>✗ Xato: <b>{ua}</b> · To'g'ri: <b>{ca}</b></div>", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Yakunlash tugmasi ──────────────────────
    if not is_done:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✔  TESTNI YAKUNLASH", type="primary", use_container_width=True):
                sc, res = evaluate(questions)
                state.score   = sc
                state.results = res
                state.finished = True
                if test_mode == "25 ta savol":
                    prev = state.get("prev_indices", set())
                    prev.update(q["_orig_idx"] for q in questions)
                    state.prev_indices = prev
                st.rerun()

    # ── Natija ekrani ──────────────────────────
    if is_done:
        sc    = state.score
        total = n_q
        pct   = sc / total * 100 if total else 0
        wrong = total - sc
        spent = (datetime.now() - state.t_start).total_seconds() if state.get("t_start") else 0

        grade_color = "green" if pct >= 70 else ("blue" if pct >= 50 else "red")
        grade_icon  = "✓" if pct >= 70 else ("△" if pct >= 50 else "✗")

        st.markdown(f"""
        <div class='score-box'>
            <div class='score-num {grade_color}'>{pct:.0f}%</div>
            <div class='score-label'>{grade_icon} {sc} / {total} to'g'ri javob</div>
            <div class='stat-row'>
                <div class='stat-item'>
                    <div class='stat-val green'>{sc}</div>
                    <div class='stat-lbl'>To'g'ri</div>
                </div>
                <div class='stat-item'>
                    <div class='stat-val red'>{wrong}</div>
                    <div class='stat-lbl'>Xato</div>
                </div>
                <div class='stat-item'>
                    <div class='stat-val blue'>{fmt_sec(spent)}</div>
                    <div class='stat-lbl'>Vaqt</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(pct / 100)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("↺  YANGI TEST", type="primary", use_container_width=True):
                clear_test()
                st.rerun()

# ── Auto-rerun (taymer) ────────────────────────
if state.get("started") and not state.get("finished"):
    time.sleep(1)
    st.rerun()

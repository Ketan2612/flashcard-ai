import streamlit as st
from groq import Groq
import PyPDF2
import json
import os
import re
import random
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DATA_FILE = "decks.json"

st.set_page_config(page_title="Smart Flashcard Engine", page_icon="🧠", layout="wide")

# ---------- LOAD/SAVE ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.decks, f)

# ---------- THEME ----------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

theme_toggle = st.toggle("🌙 Dark Mode", value=(st.session_state.theme == "dark"))
st.session_state.theme = "dark" if theme_toggle else "light"

if st.session_state.theme == "dark":
    bg             = "#0f1117"
    text           = "#e8eaf0"
    card_bg        = "#1a1d2e"
    card_border    = "#2e3250"
    card_front_bg  = "linear-gradient(135deg, #1f2937, #2d3748)"
    card_front_text= "#f1f5f9"
    card_back_bg   = "linear-gradient(135deg, #064e3b, #065f46)"
    card_back_text = "#ffffff"
    stat_text      = "#ffffff"
else:
    bg             = "#f8fafc"
    text           = "#1e293b"
    card_bg        = "#ffffff"
    card_border    = "#e2e8f0"
    card_front_bg  = "linear-gradient(135deg, #dbeafe, #eff6ff)"
    card_front_text= "#1e3a5f"
    card_back_bg   = "linear-gradient(135deg, #d1fae5, #ecfdf5)"
    card_back_text = "#064e3b"
    stat_text      = "#ffffff"

# ---------- CSS ----------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif !important;
    font-size: 16px !important;
}}

.stApp {{ background: {bg}; color: {text}; }}

h1 {{ font-size: 2rem !important; font-weight: 700 !important; }}
h2 {{ font-size: 1.5rem !important; }}
h3 {{ font-size: 1.2rem !important; }}
p, div, span, label {{ font-size: 1rem !important; }}

.stTabs [data-baseweb="tab"] {{
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: {text} !important;
}}

.stSelectbox label, .stTextInput label, .stFileUploader label {{
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: {text} !important;
}}

.card-front {{
    background: {card_front_bg};
    padding: 60px 40px;
    border-radius: 20px;
    font-size: 1.4rem !important;
    font-weight: 600;
    text-align: center;
    color: {card_front_text};
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    line-height: 1.6;
}}

.card-back {{
    background: {card_back_bg};
    padding: 50px 35px;
    border-radius: 20px;
    font-size: 1.2rem !important;
    text-align: center;
    margin-top: 20px;
    color: {card_back_text};
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    line-height: 1.6;
}}

.stat-card {{
    border-radius: 18px;
    padding: 24px;
    text-align: center;
    color: {stat_text};
    font-weight: bold;
    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    margin-bottom: 8px;
}}

.stat-card h2 {{
    font-size: 2.2rem !important;
    margin: 8px 0 0 0;
    color: {stat_text} !important;
}}

.stat-card p {{
    font-size: 0.9rem !important;
    margin: 0;
    opacity: 0.9;
}}

.streak-box {{
    background: linear-gradient(135deg, #ff6b35, #f7c59f);
    border-radius: 16px;
    padding: 16px 24px;
    text-align: center;
    color: white;
    font-weight: 700;
    font-size: 1.1rem !important;
    box-shadow: 0 4px 16px rgba(255,107,53,0.3);
}}

.confidence-bar-bg {{
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
    height: 10px;
    overflow: hidden;
    margin-top: 6px;
}}

.result-card {{
    background: {card_front_bg};
    padding: 48px;
    border-radius: 24px;
    text-align: center;
    max-width: 520px;
    margin: 32px auto;
    box-shadow: 0 12px 40px rgba(0,0,0,0.25);
}}

.result-score {{
    font-size: 5rem !important;
    font-weight: 700;
    color: #4f7cff;
    margin: 0;
    line-height: 1;
}}

.result-label {{
    font-size: 1rem !important;
    color: {card_front_text};
    opacity: 0.7;
    margin-top: 8px;
}}

.result-title {{
    font-size: 1.4rem !important;
    color: {card_front_text};
    font-weight: 600;
    margin-bottom: 16px;
}}

.progress-bar-bg {{
    margin-top: 20px;
    height: 12px;
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
    overflow: hidden;
}}

.stButton > button {{
    width: 100%;
    border-radius: 12px;
    padding: 14px;
    font-weight: 600;
    font-size: 1rem !important;
    border: none;
    background: #4f7cff;
    color: white;
}}

.stButton > button:hover {{ opacity: 0.88; }}

</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "decks"          not in st.session_state: st.session_state.decks = load_data()
if "current_deck"   not in st.session_state: st.session_state.current_deck = None
if "card_index"     not in st.session_state: st.session_state.card_index = 0
if "show_answer"    not in st.session_state: st.session_state.show_answer = False
if "practice_queue" not in st.session_state: st.session_state.practice_queue = []
if "prev_deck"      not in st.session_state: st.session_state.prev_deck = None
if "explanations"   not in st.session_state: st.session_state.explanations = {}
if "simple_exp"     not in st.session_state: st.session_state.simple_exp = ""
if "exam_started"   not in st.session_state: st.session_state.exam_started = False
if "exam_index"     not in st.session_state: st.session_state.exam_index = 0
if "exam_score"     not in st.session_state: st.session_state.exam_score = 0
if "exam_cards"     not in st.session_state: st.session_state.exam_cards = []
# NEW — Streak
if "streak"         not in st.session_state: st.session_state.streak = 0
if "max_streak"     not in st.session_state: st.session_state.max_streak = 0

# ---------- HELPERS ----------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:5000]

def generate_flashcards(text):
    prompt = f"""Create 15 flashcards from the text below.
Output must be a JSON array only. No explanation. No markdown. No extra text.
Each item must have exactly two keys: "question" and "answer".
Example output:
[{{"question": "What is X?", "answer": "X is Y."}}]

Text:
{text}
"""
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a flashcard generator. You only output valid JSON arrays. Never include markdown, code blocks, or explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        raw = res.choices[0].message.content.strip()

        # Aggressive cleaning
        raw = re.sub(r"```json|```", "", raw).strip()
        raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)

        # Extract JSON array
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            st.error("Could not find JSON in response")
            return []

        raw_json = match.group(0)

        # Parse
        data = json.loads(raw_json)
        return [{"question": c["question"], "answer": c["answer"],
                 "status": "new", "attempts": 0, "correct": 0} for c in data]

    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return []

def get_smart_queue(cards):
    weighted = []
    for i, c in enumerate(cards):
        priority = (c["attempts"] - c["correct"]) + (0 if c["status"] == "mastered" else 2)
        weighted.extend([i] * max(1, priority))
    random.shuffle(weighted)
    return weighted

def explain_simple(answer):
    prompt = f"Explain this in very simple terms a student can understand:\n{answer}"
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content

def get_confidence(card):
    if card["attempts"] == 0:
        return 0
    return int((card["correct"] / card["attempts"]) * 100)

def update_card(deck, idx, correct):
    c = deck["cards"][idx]
    c["attempts"] += 1
    if correct:
        c["correct"] += 1
        c["status"] = "mastered" if c["correct"] >= 2 else "learning"
        # Update streak
        st.session_state.streak += 1
        if st.session_state.streak > st.session_state.max_streak:
            st.session_state.max_streak = st.session_state.streak
    else:
        c["correct"] = 0
        c["status"] = "learning"
        st.session_state.streak = 0  # Reset streak on wrong
    save_data()

# ---------- HEADER ----------
st.title("🧠 Smart Flashcard Engine")

tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "🃏 Practice", "📊 Progress", "🎯 Exam"])

# ══════════════════════════════════════════════
# TAB 1 — UPLOAD
# ══════════════════════════════════════════════
with tab1:
    name = st.text_input("Deck Name", placeholder="e.g. Trigonometry, French Revolution...")
    file = st.file_uploader("Upload PDF", type=["pdf"])

    if st.button("⚡ Generate Flashcards"):
        if not name:
            st.warning("Please enter a deck name!")
        elif not file:
            st.warning("Please upload a PDF!")
        elif name in st.session_state.decks:
            st.warning("Deck with this name already exists!")
        else:
            with st.spinner("Reading PDF and generating flashcards..."):
                cards = generate_flashcards(extract_pdf_text(file))
                if cards:
                    st.session_state.decks[name] = {"cards": cards}
                    save_data()
                    st.success(f"✅ {len(cards)} flashcards generated for '{name}'!")
                    st.balloons()
                else:
                    st.error("Could not generate flashcards. Please try again.")

    if st.session_state.decks:
        st.markdown("---")
        st.markdown("### Your Decks")
        for dname, deck in st.session_state.decks.items():
            cards    = deck["cards"]
            mastered = sum(1 for c in cards if c["status"] == "mastered")
            avg_conf = int(sum(get_confidence(c) for c in cards) / len(cards)) if cards else 0
            st.markdown(f"""
            <div style='background:{card_bg}; border:1px solid {card_border};
                        border-radius:14px; padding:16px 20px; margin-bottom:10px;'>
                <strong style='color:{text}; font-size:1rem;'>{dname}</strong>
                <span style='color:#8b90a8; float:right; font-size:0.9rem;'>
                    {mastered}/{len(cards)} mastered · Avg Confidence: {avg_conf}%
                </span>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 2 — PRACTICE
# ══════════════════════════════════════════════
with tab2:
    if not st.session_state.decks:
        st.info("📤 Upload a PDF first to generate flashcards!")
    else:
        sel   = st.selectbox("Deck", list(st.session_state.decks.keys()))
        deck  = st.session_state.decks[sel]
        cards = deck["cards"]

        if sel != st.session_state.prev_deck:
            st.session_state.practice_queue = get_smart_queue(cards)
            st.session_state.card_index     = 0
            st.session_state.prev_deck      = sel
            st.session_state.show_answer    = False
            st.session_state.simple_exp     = ""
            st.session_state.streak         = 0

        if not st.session_state.practice_queue:
            st.session_state.practice_queue = get_smart_queue(cards)

        queue    = st.session_state.practice_queue
        i        = st.session_state.card_index % len(queue)
        card_idx = queue[i]
        card     = cards[card_idx]
        mastered = sum(1 for c in cards if c["status"] == "mastered")

        # ── TOP ROW: Progress + Streak ──
        col_prog, col_streak = st.columns([3, 1])

        with col_prog:
            st.progress(mastered / len(cards))
            st.markdown(
                f"<p style='color:#8b90a8; font-size:0.9rem;'>"
                f"Card {i+1} of {len(queue)} · {mastered}/{len(cards)} mastered</p>",
                unsafe_allow_html=True
            )

        with col_streak:
            streak_emoji = "🔥" if st.session_state.streak >= 3 else "⚡"
            st.markdown(f"""
            <div class='streak-box'>
                {streak_emoji} Streak: {st.session_state.streak}<br>
                <span style='font-size:0.8rem; opacity:0.85;'>Best: {st.session_state.max_streak}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── STATUS BADGE + CONFIDENCE ──
        status_colors = {"new": "#ffaa4f", "learning": "#4f7cff", "mastered": "#3ddc97"}
        sc         = status_colors.get(card["status"], "#8b90a8")
        confidence = get_confidence(card)

        conf_color = "#3ddc97" if confidence >= 70 else "#ffaa4f" if confidence >= 40 else "#ff4f6a"

        col_badge, col_conf = st.columns([1, 2])
        with col_badge:
            st.markdown(
                f"<span style='background:{sc}22; color:{sc}; padding:6px 16px; "
                f"border-radius:999px; font-size:0.85rem; font-weight:600;'>"
                f"{card['status'].upper()}</span>",
                unsafe_allow_html=True
            )
        with col_conf:
            st.markdown(
                f"<p style='color:{conf_color}; font-size:0.9rem; font-weight:600; margin:0;'>"
                f"Confidence: {confidence}%</p>"
                f"<div class='confidence-bar-bg'>"
                f"<div style='width:{confidence}%; height:100%; background:{conf_color}; border-radius:10px;'></div>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── QUESTION CARD ──
        st.markdown(f"<div class='card-front'>❓ {card['question']}</div>", unsafe_allow_html=True)

        if st.session_state.show_answer:
            st.markdown(f"<div class='card-back'>💡 {card['answer']}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🧠 Explain Simply", key=f"explain_{card_idx}"):
                if card_idx not in st.session_state.explanations:
                    with st.spinner("Explaining..."):
                        st.session_state.explanations[card_idx] = explain_simple(card["answer"])
                st.session_state.simple_exp = st.session_state.explanations[card_idx]

            if st.session_state.simple_exp:
                st.info(st.session_state.simple_exp)

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ I knew it!", key=f"know_{card_idx}", use_container_width=True):
                    update_card(deck, card_idx, True)
                    # Milestone celebration
                    if st.session_state.streak in [5, 10, 15, 20]:
                        st.balloons()
                    st.session_state.practice_queue = get_smart_queue(cards)
                    st.session_state.card_index    += 1
                    st.session_state.show_answer    = False
                    st.session_state.simple_exp     = ""
                    st.rerun()

            with col2:
                if st.button("🔄 Still Learning", key=f"next_{card_idx}", use_container_width=True):
                    update_card(deck, card_idx, False)
                    st.session_state.practice_queue = get_smart_queue(cards)
                    st.session_state.card_index    += 1
                    st.session_state.show_answer    = False
                    st.session_state.simple_exp     = ""
                    st.rerun()

            with col3:
                if st.button("⏭️ Skip", key=f"skip_{card_idx}", use_container_width=True):
                    st.session_state.card_index += 1
                    st.session_state.show_answer = False
                    st.session_state.simple_exp  = ""
                    st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("👁️ Show Answer", key=f"show_{card_idx}", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()

# ══════════════════════════════════════════════
# TAB 3 — PROGRESS
# ══════════════════════════════════════════════
with tab3:
    if not st.session_state.decks:
        st.info("📤 Upload a PDF first to see progress!")
    else:
        total_mastered = sum(sum(1 for c in d["cards"] if c["status"] == "mastered") for d in st.session_state.decks.values())
        total_learning = sum(sum(1 for c in d["cards"] if c["status"] == "learning") for d in st.session_state.decks.values())
        total_new      = sum(sum(1 for c in d["cards"] if c["status"] == "new")      for d in st.session_state.decks.values())

        # Top stats
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(f"<div class='stat-card' style='background:#4f7cff'><p>Decks</p><h2>{len(st.session_state.decks)}</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-card' style='background:#22c55e'><p>Mastered</p><h2>{total_mastered}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-card' style='background:#f59e0b'><p>Learning</p><h2>{total_learning}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='stat-card' style='background:#6b7280'><p>New</p><h2>{total_new}</h2></div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='stat-card' style='background:#ff6b35'><p>🔥 Best Streak</p><h2>{st.session_state.max_streak}</h2></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        for dname, deck in st.session_state.decks.items():
            cards    = deck["cards"]
            mastered = sum(1 for c in cards if c["status"] == "mastered")
            learning = sum(1 for c in cards if c["status"] == "learning")
            new_c    = sum(1 for c in cards if c["status"] == "new")
            pct      = int(mastered / len(cards) * 100) if cards else 0
            avg_conf = int(sum(get_confidence(c) for c in cards) / len(cards)) if cards else 0

            with st.expander(f"📚 {dname} — {pct}% mastered · Avg Confidence: {avg_conf}%"):
                st.progress(pct / 100)

                col1, col2, col3, col4 = st.columns(4)
                col1.markdown(f"<div class='stat-card' style='background:#22c55e'><p>Mastered</p><h2>{mastered}</h2></div>", unsafe_allow_html=True)
                col2.markdown(f"<div class='stat-card' style='background:#f59e0b'><p>Learning</p><h2>{learning}</h2></div>", unsafe_allow_html=True)
                col3.markdown(f"<div class='stat-card' style='background:#6b7280'><p>New</p><h2>{new_c}</h2></div>", unsafe_allow_html=True)
                col4.markdown(f"<div class='stat-card' style='background:#4f7cff'><p>Avg Confidence</p><h2>{avg_conf}%</h2></div>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"<strong style='color:{text};'>All Cards:</strong>", unsafe_allow_html=True)

                for card in cards:
                    sc   = {"new": "#ffaa4f", "learning": "#4f7cff", "mastered": "#3ddc97"}.get(card["status"], "#8b90a8")
                    conf = get_confidence(card)
                    conf_color = "#3ddc97" if conf >= 70 else "#ffaa4f" if conf >= 40 else "#ff4f6a"
                    st.markdown(f"""
                    <div style='background:{card_bg}; border-radius:10px; padding:14px 18px;
                                margin:6px 0; border-left:3px solid {sc};'>
                        <strong style='color:{text}; font-size:1rem;'>Q: {card['question']}</strong><br>
                        <span style='color:#8b90a8; font-size:0.9rem;'>A: {card['answer']}</span><br>
                        <div style='display:flex; align-items:center; gap:12px; margin-top:6px;'>
                            <span style='color:{sc}; font-size:0.8rem; font-weight:600;'>{card['status'].upper()}</span>
                            <span style='color:{conf_color}; font-size:0.8rem;'>Confidence: {conf}%</span>
                            <span style='color:#8b90a8; font-size:0.8rem;'>{card['correct']}/{card['attempts']} correct</span>
                        </div>
                        <div style='margin-top:6px; height:6px; background:rgba(255,255,255,0.1); border-radius:10px; overflow:hidden;'>
                            <div style='width:{conf}%; height:100%; background:{conf_color}; border-radius:10px;'></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🗑️ Delete '{dname}'", key=f"del_{dname}"):
                    del st.session_state.decks[dname]
                    save_data()
                    st.rerun()

# ══════════════════════════════════════════════
# TAB 4 — EXAM
# ══════════════════════════════════════════════
with tab4:
    if not st.session_state.decks:
        st.info("📤 Upload a PDF first!")
    else:
        sel   = st.selectbox("Deck for Exam", list(st.session_state.decks.keys()))
        deck  = st.session_state.decks[sel]
        cards = deck["cards"]

        if st.button("🎯 Start Exam"):
            st.session_state.exam_cards   = random.sample(cards, min(5, len(cards)))
            st.session_state.exam_index   = 0
            st.session_state.exam_score   = 0
            st.session_state.exam_started = True
            st.rerun()

        if st.session_state.exam_started:
            i = st.session_state.exam_index

            if i < len(st.session_state.exam_cards):
                q     = st.session_state.exam_cards[i]
                total = len(st.session_state.exam_cards)

                st.progress(i / total)
                st.markdown(f"<p style='color:#8b90a8; font-size:0.9rem;'>Question {i+1} of {total}</p>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-front'>❓ {q['question']}</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                user_ans = st.text_input("Your Answer", key=f"ans_{i}", placeholder="Type your answer here...")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Submit", key=f"submit_{i}", use_container_width=True):
                        correct = q["answer"].strip().lower()
                        user    = user_ans.strip().lower() if user_ans else ""
                        if user and (user == correct or user in correct or correct in user):
                            st.session_state.exam_score += 1
                        st.session_state.exam_index += 1
                        st.rerun()
                with col2:
                    if st.button("⏭️ Skip", key=f"skip_exam_{i}", use_container_width=True):
                        st.session_state.exam_index += 1
                        st.rerun()
            else:
                score   = st.session_state.exam_score
                total   = len(st.session_state.exam_cards)
                percent = int((score / total) * 100) if total > 0 else 0

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(f"""
                    <div class='result-card'>
                        <p class='result-title'>🎯 Exam Result</p>
                        <p class='result-score'>{score}/{total}</p>
                        <p class='result-label'>Accuracy: {percent}%</p>
                        <div class='progress-bar-bg'>
                            <div style='width:{percent}%; height:100%; background:#22c55e; border-radius:10px;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                if percent == 100:
                    st.balloons()
                    st.success("🔥 Perfect Score! Outstanding!")
                elif percent >= 70:
                    st.info("👍 Good job! Keep practicing!")
                else:
                    st.warning("📚 Keep practicing — you'll get there!")

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 Try Again", use_container_width=True):
                        st.session_state.exam_started = False
                        st.session_state.exam_index   = 0
                        st.session_state.exam_score   = 0
                        st.rerun()

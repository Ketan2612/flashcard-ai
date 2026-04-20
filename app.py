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

theme_toggle = st.toggle("🌙 Dark Mode", value=True)
st.session_state.theme = "dark" if theme_toggle else "light"

if st.session_state.theme == "dark":
    bg = "#0f1117"
    text = "#ffffff"
    card_bg = "#1a1d2e"
else:
    bg = "#ffffff"
    text = "#111111"
    card_bg = "#f5f7ff"

# ---------- CSS ----------
st.markdown(f"""
<style>
.stApp {{
    background: {bg};
    color: {text};
}}

.card-front {{
    background: {card_bg};
    padding: 50px;
    border-radius: 15px;
    font-size: 1.6rem;
    font-weight: bold;
}}

.card-back {{
    background: #d1fae5;
    padding: 40px;
    border-radius: 15px;
    font-size: 1.3rem;
}}

.stButton > button {{
    background-color: #4f7cff;
    color: white;
    font-size: 16px;
    border-radius: 8px;
}}

.stat-card {{
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    color: white;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)

# ---------- STATE ----------
if "decks" not in st.session_state:
    st.session_state.decks = load_data()

if "current_deck" not in st.session_state:
    st.session_state.current_deck = None

if "card_index" not in st.session_state:
    st.session_state.card_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ---------- PDF ----------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:5000]

# ---------- AI ----------
def generate_flashcards(text):
    prompt = f"""
Generate 15 flashcards in JSON:
[{{"question": "...", "answer": "..."}}]

{text}
"""
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = res.choices[0].message.content
        raw = re.sub(r"```|json", "", raw)

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(0))

        return [{
            "question": c["question"],
            "answer": c["answer"],
            "status": "new",
            "attempts": 0,
            "correct": 0
        } for c in data]

    except:
        return []

# ---------- SMART REVISION ----------
def get_smart_queue(cards):
    weighted = []
    for i, c in enumerate(cards):
        priority = (c["attempts"] - c["correct"]) + (0 if c["status"] == "mastered" else 2)
        weighted.extend([i] * max(1, priority))
    random.shuffle(weighted)
    return weighted

# ---------- EXPLAIN ----------
def explain_simple(answer):
    prompt = f"Explain this in very simple terms:\n{answer}"
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content

# ---------- UPDATE ----------
def update_card(deck, idx, correct):
    c = deck["cards"][idx]
    c["attempts"] += 1
    if correct:
        c["correct"] += 1
        c["status"] = "mastered" if c["correct"] >= 2 else "learning"
    else:
        c["correct"] = 0
        c["status"] = "learning"
    save_data()

# ---------- UI ----------
st.title("🧠 Smart Flashcard Engine")

tab1, tab2, tab3, tab4 = st.tabs(["Upload", "Practice", "Progress", "Exam"])

# ---------- UPLOAD ----------
with tab1:
    name = st.text_input("Deck Name")
    file = st.file_uploader("Upload PDF")

    if st.button("Generate"):
        if name and file:
            cards = generate_flashcards(extract_pdf_text(file))
            if cards:
                st.session_state.decks[name] = {"cards": cards}
                save_data()
                st.success("Done!")

# ---------- PRACTICE ----------
with tab2:
    if not st.session_state.decks:
        st.info("Upload first")
    else:
        sel = st.selectbox("Deck", list(st.session_state.decks.keys()))
        deck = st.session_state.decks[sel]
        cards = deck["cards"]

        queue = get_smart_queue(cards)

        i = st.session_state.card_index % len(queue)
        card_idx = queue[i]
        card = cards[card_idx]

        st.markdown(f"<div class='card-front'>{card['question']}</div>", unsafe_allow_html=True)

        if st.session_state.show_answer:
            st.markdown(f"<div class='card-back'>{card['answer']}</div>", unsafe_allow_html=True)

            # 🔥 EXPLAIN BUTTON
            if "simple_exp" not in st.session_state:
                st.session_state.simple_exp = ""

            if st.button("Explain Simply"):
                st.session_state.simple_exp = explain_simple(card["answer"])

            if st.session_state.simple_exp:
                st.info(st.session_state.simple_exp)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("I knew it"):
                    update_card(deck, card_idx, True)
                    st.session_state.card_index += 1
                    st.session_state.show_answer = False
                    st.session_state.simple_exp = ""
                    st.rerun()

            with c2:
                if st.button("Next"):
                    update_card(deck, card_idx, False)
                    st.session_state.card_index += 1
                    st.session_state.show_answer = False
                    st.session_state.simple_exp = ""
                    st.rerun()
        else:
            if st.button("Show Answer"):
                st.session_state.show_answer = True
                st.rerun()

# ---------- PROGRESS ----------
with tab3:
    if not st.session_state.decks:
        st.info("No data")
    else:
        total_mastered = sum(sum(1 for c in d["cards"] if c["status"] == "mastered") for d in st.session_state.decks.values())
        total_learning = sum(sum(1 for c in d["cards"] if c["status"] == "learning") for d in st.session_state.decks.values())
        total_new = sum(sum(1 for c in d["cards"] if c["status"] == "new") for d in st.session_state.decks.values())

        c1, c2, c3, c4 = st.columns(4)

        c1.markdown(f"<div class='stat-card' style='background:#4f7cff'>Decks<br><h2>{len(st.session_state.decks)}</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-card' style='background:#22c55e'>Mastered<br><h2>{total_mastered}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-card' style='background:#f59e0b'>Learning<br><h2>{total_learning}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='stat-card' style='background:#6b7280'>New<br><h2>{total_new}</h2></div>", unsafe_allow_html=True)

# ---------- EXAM ----------
with tab4:
    if not st.session_state.decks:
        st.info("Upload first")
    else:
        sel = st.selectbox("Deck for Exam", list(st.session_state.decks.keys()))
        deck = st.session_state.decks[sel]
        cards = deck["cards"]

        if "exam_started" not in st.session_state:
            st.session_state.exam_started = False

        if st.button("Start Exam"):
            st.session_state.exam_cards = random.sample(cards, min(5, len(cards)))
            st.session_state.exam_index = 0
            st.session_state.exam_score = 0
            st.session_state.exam_started = True

        if st.session_state.exam_started:
            i = st.session_state.exam_index

            if i < len(st.session_state.exam_cards):
                q = st.session_state.exam_cards[i]

                st.markdown(f"### Q{i+1}: {q['question']}")
                user_ans = st.text_input("Your Answer")

                if st.button("Submit"):
                    if user_ans.lower() in q["answer"].lower():
                        st.success("Correct!")
                        st.session_state.exam_score += 1
                    else:
                        st.error(f"Correct: {q['answer']}")

                    st.session_state.exam_index += 1
                    st.rerun()
            else:
                st.success(f"Final Score: {st.session_state.exam_score}/{len(st.session_state.exam_cards)}")
                st.session_state.exam_started = False
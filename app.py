import csv
import io
import os
import sqlite3
from datetime import datetime

import streamlit as st

# FinQuest - anonymous weekly insurance learning drop
# Stores challenge answer, correctness and timestamp only.
# Does NOT collect names, email addresses or employee IDs.

st.set_page_config(
    page_title="FinQuest | Insurance Mini-Drop",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB_PATH = "finquest_anonymous.db"
CHALLENGE_ID = "insurance_week_01"

# Replace these sample details with SME-approved content for each weekly drop.
FACT = (
    "A co-payment is the share of an admissible claim that the insured must pay, "
    "as defined in the policy. Check the exact percentage and conditions in the policy wording."
)
MYTH = "“Cashless” means the customer never pays anything."
REALITY = (
    "Not necessarily! Co-payments, deductibles, non-payable items, limits or expenses "
    "outside the policy cover may still be payable by the customer."
)
QUESTION = "A health policy has a 10% co-payment clause. What does this generally mean?"
OPTIONS = [
    "The insurer pays 10% of the admissible claim",
    "The customer pays 10% of the admissible claim",
    "The customer pays nothing",
    "Every claim is automatically rejected",
]
CORRECT_ANSWER = OPTIONS[1]
EXPLANATION = (
    "A co-payment is the portion of an admissible claim the insured pays. "
    "Always check the actual policy terms."
)

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def initialise_database():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS anonymous_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                submitted_at TEXT NOT NULL
            )
        """)
        conn.commit()

def save_submission(answer):
    correct = int(answer == CORRECT_ANSWER)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with get_db() as conn:
        conn.execute("""
            INSERT INTO anonymous_submissions
            (challenge_id, answer, is_correct, submitted_at)
            VALUES (?, ?, ?, ?)
        """, (CHALLENGE_ID, answer, correct, timestamp))
        conn.commit()
    return correct

def fetch_submissions():
    with get_db() as conn:
        return conn.execute("""
            SELECT answer,
                   CASE WHEN is_correct = 1 THEN 'Correct' ELSE 'Incorrect' END,
                   submitted_at
            FROM anonymous_submissions
            WHERE challenge_id = ?
            ORDER BY submitted_at DESC
        """, (CHALLENGE_ID,)).fetchall()

def get_admin_password():
    try:
        return st.secrets["admin_password"]
    except Exception:
        return os.getenv("FINQUEST_ADMIN_PASSWORD", "")

initialise_database()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Inter:wght@400;500;600;700&display=swap');
.stApp {
 background: radial-gradient(circle at 12% 8%,rgba(0,255,209,.13),transparent 27%),
 radial-gradient(circle at 88% 20%,rgba(174,0,255,.17),transparent 30%),
 linear-gradient(135deg,#080b18 0%,#10142b 55%,#080b18 100%);
 color:#f4f7ff;
}
[data-testid="stHeader"]{background:transparent}
h1,h2,h3{font-family:'Orbitron',sans-serif!important}
p,label,div{font-family:'Inter',sans-serif}
.hero,.card{border:1px solid rgba(0,255,209,.34);
 background:linear-gradient(125deg,rgba(0,255,209,.09),rgba(174,0,255,.13));
 border-radius:20px;padding:20px;margin:12px 0;box-shadow:0 0 24px rgba(0,255,209,.06)}
.eyebrow{color:#00ffd1;letter-spacing:2px;font-size:11px;font-weight:800}
.headline{font-family:'Orbitron',sans-serif;font-size:clamp(27px,5vw,40px);
 line-height:1.15;font-weight:800;color:#fff;margin:8px 0}
.muted{color:#b7c0d8}
.tag{display:inline-block;padding:5px 10px;border-radius:99px;background:rgba(0,255,209,.12);
 color:#00ffd1;border:1px solid rgba(0,255,209,.35);font-size:10px;font-weight:800;letter-spacing:1px}
.bigline{font-size:19px;line-height:1.45;font-weight:700;color:#fff;margin-top:10px}
.mascot{font-size:56px;line-height:1;text-align:center;padding:5px}
div.stButton>button,div.stFormSubmitButton>button{border:1px solid #00ffd1;border-radius:12px;
 background:linear-gradient(90deg,#00bfa5,#7c3aed);color:white;font-weight:800;padding:.65rem 1rem}
.footer{text-align:center;color:#78839f;font-size:11px;padding:24px 0 8px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
 <div class="eyebrow">FINQUEST // INSURANCE EDITION</div>
 <div class="headline">A tiny insurance<br>brain boost.</div>
 <p class="muted">60 seconds. One myth. One challenge. No 47-slide deck. 😌</p>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("FinQuest menu", ["Play", "Admin: engagement"])

if page == "Admin: engagement":
    st.markdown("## 📊 Mission Control")
    st.caption("Anonymous engagement overview — no employee details are collected.")
    password = get_admin_password()
    if not password:
        st.warning(
            'Admin password is not configured. Create `.streamlit/secrets.toml` '
            'with `admin_password = "choose-a-password"` and restart Streamlit.'
        )
    else:
        entered = st.text_input("Admin password", type="password")
        if entered and entered == password:
            rows = fetch_submissions()
            total = len(rows)
            correct_count = sum(row[1] == "Correct" for row in rows)
            incorrect_count = total - correct_count
            rate = (correct_count / total * 100) if total else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Challenge submissions", total)
            c2.metric("Correct answers", correct_count)
            c3.metric("Correct rate", f"{rate:.0f}%")

            st.markdown("### Answer breakdown")
            counts = {option: 0 for option in OPTIONS}
            for row in rows:
                counts[row[0]] = counts.get(row[0], 0) + 1
            for option, count in counts.items():
                st.write(f"**{count}** · {option}")

            if rows:
                st.markdown("### Anonymous submission log")
                st.dataframe(
                    [{"Answer": row[0], "Result": row[1], "Submitted at": row[2]} for row in rows],
                    use_container_width=True,
                    hide_index=True,
                )
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Answer", "Result", "Submitted at"])
                writer.writerows(rows)
                st.download_button(
                    "⬇️ Download anonymous responses (CSV)",
                    data=output.getvalue().encode("utf-8-sig"),
                    file_name="finquest_anonymous_responses.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.info("No challenge submissions yet. Cover Cub is waiting for the first player. 🦸")
            st.caption(
                "Note: this counts submitted answers, not verified unique colleagues. "
                "Without sign-in or identifiers, repeat submissions cannot be reliably prevented."
            )
        elif entered:
            st.error("That password doesn't match.")

else:
    if st.query_params.get("insurance_popup") != "1":
        st.markdown("""
        <div class="card">
          <div class="mascot">🛡️☂️</div>
          <div class="bigline" style="text-align:center">Cover Cub has a notification for you!</div>
          <p class="muted" style="text-align:center">It's short. It has a point. It might even make you smile.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔔 OPEN MY INSURANCE DROP", use_container_width=True):
            st.query_params["insurance_popup"] = "1"
            st.rerun()
        st.caption("Email link: add `?insurance_popup=1` to your deployed app URL.")
    else:
        st.markdown("""
        <div class="card">
          <span class="tag">🔔 NEW NOTIFICATION</span>
          <div class="bigline">Your insurance gossip is here. Don't leave Cover Cub on read. 👀</div>
          <div class="mascot">🛡️✨</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("LET'S GO!", use_container_width=True):
            st.session_state["show_learning"] = True

        if st.session_state.get("show_learning", False):
            st.markdown(
                f'<div class="card"><span class="tag">⏱️ 60-SECOND FACT</span>'
                f'<div class="bigline">{FACT}</div><div class="mascot">💡</div></div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="card"><span class="tag">🔍 MYTH BUSTER</span>'
                f'<div class="bigline">{MYTH}</div><p class="muted">REALITY: {REALITY}</p>'
                f'<div class="mascot">🕵️</div></div>',
                unsafe_allow_html=True
            )

            st.markdown("### ⚡ One-minute challenge")
            st.write(QUESTION)
            # Anonymous form: no name, email, employee ID or other identity field.
            with st.form("anonymous_challenge"):
                answer = st.radio("Choose one answer:", OPTIONS, index=None)
                submitted = st.form_submit_button("SUBMIT MY ANSWER 🚀", use_container_width=True)

            if submitted:
                if answer is None:
                    st.error("Choose an answer before submitting.")
                else:
                    correct = save_submission(answer)
                    st.session_state["last_submitted"] = True
                    if correct:
                        st.balloons()
                        st.success("Correct! +10 XP. Insurance genius unlocked. 🏆")
                        st.info(EXPLANATION)
                    else:
                        st.success("Answer submitted! Thanks for playing. +5 participation XP. 🕵️")
                        st.info("Not quite. " + EXPLANATION)
                    st.caption("Your response was recorded anonymously. No personal details were collected.")

st.markdown(
    '<div class="footer">FINQUEST • Learn a little. Laugh a little. Level up.<br>'
    'Anonymous challenge participation. Educational awareness only; refer to approved policy wording.</div>',
    unsafe_allow_html=True,
)

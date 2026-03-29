"""
app.py  ←  SINGLE ENTRY POINT
==============================
    streamlit run app.py

Flow:
  1. wars.csv missing or "Refresh" clicked → fetch_wars.run() scrapes Wikipedia
  2. Load wars.csv → wars_gantt.render() draws the timeline
"""

from pathlib import Path
import streamlit as st
import fetch_wars
import wars_gantt

CSV_FILE = "wars.csv"

st.set_page_config(page_title="Wars Timeline 1900–2026", page_icon="⚔️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Sans+3:wght@300;400;600&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#0d0d0f;color:#e8e0d0;}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at top left,#1a0a0a 0%,#0d0d0f 50%,#05080f 100%);}
h1{font-family:'Playfair Display',serif;font-size:3rem!important;font-weight:900;letter-spacing:-1px;color:#f0e6d0!important;text-shadow:0 0 60px rgba(180,60,30,0.4);margin-bottom:0!important;}
h2,h3{font-family:'Playfair Display',serif;color:#c8a882!important;}
p,li,label,.stMarkdown{font-family:'Source Sans 3',sans-serif;color:#b0a898!important;}
.subtitle{font-family:'Source Sans 3',sans-serif;font-weight:300;font-size:1.1rem;color:#8a8070!important;letter-spacing:3px;text-transform:uppercase;margin-top:0;}
.metric-box{background:rgba(255,255,255,0.03);border:1px solid rgba(200,168,130,0.15);border-radius:8px;padding:16px 20px;text-align:center;}
.metric-val{font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:700;color:#d4603a;}
.metric-label{font-size:0.75rem;letter-spacing:2px;text-transform:uppercase;color:#7a7060;}
[data-testid="stSidebar"]{background:#0a0a0c!important;border-right:1px solid rgba(200,168,130,0.1);}
hr{border-color:rgba(200,168,130,0.15)!important;}
div.stButton>button{background:rgba(212,96,58,0.15);border:1px solid rgba(212,96,58,0.4);color:#d4603a;border-radius:6px;font-family:'Source Sans 3',sans-serif;}
div.stButton>button:hover{background:rgba(212,96,58,0.28);border-color:#d4603a;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1>⚔ Wars of the Modern World</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Timeline 1900 – 2026 · Wikipedia Data</p>', unsafe_allow_html=True)
st.markdown("---")

col_info, col_btn = st.columns([5, 1])
with col_btn:
    force_refresh = st.button("⟳ Refresh data", help="Re-scrape Wikipedia and rebuild CSV")

if not Path(CSV_FILE).exists() or force_refresh:
    with st.status("Fetching war data from Wikipedia...", expanded=True) as status:
        count = fetch_wars.run(output_file=CSV_FILE, log=status.write)
        status.update(label=f"Done — {count} conflicts saved to {CSV_FILE}",
                      state="complete", expanded=False)
    wars_gantt.load_data.clear()
else:
    with col_info:
        st.caption(f"Using cached **{CSV_FILE}** — click ⟳ to re-scrape.")

try:
    df = wars_gantt.load_data(CSV_FILE)
    wars_gantt.render(df)
except FileNotFoundError:
    st.error(f"**{CSV_FILE}** not found. Click **⟳ Refresh data** above.")

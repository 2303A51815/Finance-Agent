import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px

from parser import parse_statement
from categorizer import categorizer_df, spending_by_category
from rag_chain import build_rag_chain, ask

# =========================
# ⚡ PAGE CONFIG
# =========================
st.set_page_config(
    page_title="💰 AI Finance Dashboard",
    layout="wide"
)

# =========================
# 🌌 ULTRA PREMIUM UI (NO LOGIC CHANGE)
# =========================
st.markdown("""
<style>

/* 🌌 Background (Fintech Premium Style) */
.main {
    background: radial-gradient(circle at 15% 15%, #0ea5e9 0%, transparent 35%),
                radial-gradient(circle at 85% 20%, #a855f7 0%, transparent 40%),
                radial-gradient(circle at 50% 80%, #22c55e 0%, transparent 40%),
                linear-gradient(135deg, #020617 0%, #0f172a 50%, #0b1220 100%);
    background-attachment: fixed;
    color: white;
}

/* ✨ Soft glow animation */
.main::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: radial-gradient(circle at 50% 50%, rgba(56,189,248,0.08), transparent 60%);
    animation: glow 6s ease-in-out infinite;
    pointer-events: none;
}

@keyframes glow {
    0% {opacity: 0.3;}
    50% {opacity: 0.7;}
    100% {opacity: 0.3;}
}

/* 🧊 Glass cards */
.stDataFrame, .stPlotlyChart, .stMetric {
    background: rgba(255,255,255,0.05);
    border-radius: 20px;
    padding: 14px;
    backdrop-filter: blur(22px);
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 15px 40px rgba(0,0,0,0.4);
}

/* 🧠 Headings */
h1 {
    font-size: 40px !important;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #a855f7, #22c55e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

h2, h3 {
    color: #7dd3fc;
}

/* 🚀 Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #06b6d4, #a855f7);
    border-radius: 14px;
    padding: 10px 18px;
    border: none;
    color: white;
    font-weight: 600;
}

.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(99,102,241,0.5);
}

/* 📂 uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03);
    border-radius: 14px;
    padding: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* 💬 chat */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.04);
    border-radius: 16px;
    padding: 14px;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.06);
}

/* hide streamlit default UI */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("# 💰 Finance AI Dashboard")
st.markdown("### 🚀 Smart insights for your spending")
st.markdown("---")

uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

# 🎨 Colors
COLORS = [
    "#4F46E5", "#22C55E", "#F59E0B",
    "#EF4444", "#3B82F6", "#8B5CF6",
    "#14B8A6"
]

# 💬 Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# 💡 INSIGHTS (UNCHANGED)
# =========================
def generate_insights(df):
    insights = []

    total = df["amount"].sum()
    cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)

    top = cat.idxmax()
    val = cat.max()

    insights.append(f"💸 Top spending: **{top} → ₹{val:.0f}**")

    for c, v in cat.items():
        pct = (v / total) * 100
        if pct > 50:
            insights.append(f"🔥 {c}: {pct:.1f}% (very high)")
        elif pct > 25:
            insights.append(f"⚠️ {c}: {pct:.1f}% (moderate)")
        else:
            insights.append(f"✅ {c}: {pct:.1f}% (controlled)")

    return insights

# =========================
# MAIN APP
# =========================
if uploaded_file is not None:

    df = parse_statement(uploaded_file)
    df = categorizer_df(df)

    # 💎 KPI CARDS
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Spend", f"₹{df['amount'].sum():,.0f}")
    col2.metric("📊 Transactions", len(df))
    col3.metric("🏷️ Categories", df['category'].nunique())

    st.subheader("📊 Data Preview")
    st.dataframe(df, use_container_width=True)

    summary = spending_by_category(df)

    # 📊 CHARTS
    st.markdown("## 📊 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(summary, x="category", y="total", color="category", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(summary, names="category", values="total", hole=0.5)
        st.plotly_chart(fig2, use_container_width=True)

    # 📈 TREND
    st.markdown("## 📈 Monthly Trend")

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month")["amount"].sum().reset_index()

    fig3 = px.line(monthly, x="month", y="amount", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    # 💡 INSIGHTS
    st.markdown("## 💡 AI Insights")

    for i in generate_insights(df):
        st.markdown(f"- {i}")

    # 🚨 BUDGET
    st.markdown("## 🚨 Budget")

    budget = st.number_input("Set budget (₹)", min_value=0)

    if budget > 0:
        total = df["amount"].sum()
        rem = budget - total

        if rem < 0:
            st.error(f"⚠️ Over by ₹{abs(rem):.0f}")
        else:
            st.success(f"₹{rem:.0f} remaining")

    # 📄 DOWNLOAD
    st.markdown("## 📄 Download")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        csv,
        file_name="report.csv",
        mime="text/csv"
    )

    # =========================
    # 💬 CHAT (UNCHANGED LOGIC)
    # =========================
    st.markdown("## 💬 Chat AI")

    chain = build_rag_chain(df)

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Ask something..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        answer = ask(chain, prompt)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()

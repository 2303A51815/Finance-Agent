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
    page_title="💰 AI Finance Assistant",
    layout="wide"
)

# =========================
# 🌌 ULTRA PREMIUM BACKGROUND (ONLY UI)
# =========================
st.markdown("""
<style>

/* 🌌 Aurora Luxury Background */
.main {
    background: radial-gradient(circle at 10% 20%, #0b1220 0%, transparent 25%),
                radial-gradient(circle at 80% 10%, #1e1b4b 0%, transparent 30%),
                radial-gradient(circle at 50% 90%, #0ea5e9 0%, transparent 35%),
                radial-gradient(circle at 90% 80%, #a855f7 0%, transparent 40%),
                linear-gradient(135deg, #020617 0%, #0f172a 40%, #0b1220 100%);
    background-attachment: fixed;
    color: white;
}

/* ✨ Soft glow overlay */
.main::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(56,189,248,0.08), transparent 60%);
    animation: glowPulse 8s ease-in-out infinite;
    pointer-events: none;
}

@keyframes glowPulse {
    0% {opacity: 0.3;}
    50% {opacity: 0.7;}
    100% {opacity: 0.3;}
}

/* 🧊 Glass cards */
div.stDataFrame, .stPlotlyChart, .stMetric {
    background: rgba(255,255,255,0.05);
    border-radius: 18px;
    padding: 14px;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 12px 35px rgba(0,0,0,0.35);
    transition: all 0.3s ease;
}

/* hover effect */
div.stDataFrame:hover, .stPlotlyChart:hover {
    transform: translateY(-4px) scale(1.01);
}

/* 🌟 headings */
h1, h2, h3 {
    color: #7dd3fc;
    text-shadow: 0 0 18px rgba(125,211,252,0.4);
}

/* 🎯 button premium */
div.stButton > button {
    background: linear-gradient(135deg, #6366f1, #06b6d4, #a855f7);
    background-size: 200% 200%;
    color: white;
    border-radius: 14px;
    padding: 10px 18px;
    border: none;
    font-weight: 600;
}

div.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(99,102,241,0.4);
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
    border-radius: 14px;
    padding: 10px;
    backdrop-filter: blur(12px);
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("# 💰 AI Finance Assistant")
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

# 💡 Insights
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

    st.subheader("📊 Data Preview")
    st.dataframe(df, use_container_width=True)

    summary = spending_by_category(df)

    # 📊 Charts
    st.markdown("## 📊 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(summary, x="category", y="total", color="category", text_auto=True)
        fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(summary, names="category", values="total", hole=0.5)
        st.plotly_chart(fig2, use_container_width=True)

    # 📈 Monthly trend
    st.markdown("## 📈 Monthly Trend")

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month")["amount"].sum().reset_index()

    fig3 = px.line(monthly, x="month", y="amount", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    # 💡 Insights
    st.markdown("## 💡 AI Insights")

    for i in generate_insights(df):
        st.markdown(f"- {i}")

    # 🚨 Budget
    st.markdown("## 🚨 Budget")

    budget = st.number_input("Set budget (₹)", min_value=0)

    if budget > 0:
        total = df["amount"].sum()
        rem = budget - total

        if rem < 0:
            st.error(f"⚠️ Over by ₹{abs(rem):.0f}")
        else:
            st.success(f"₹{rem:.0f} remaining")

    # 📄 Download
    st.markdown("## 📄 Download")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        csv,
        file_name="report.csv",
        mime="text/csv"
    )

    # 🤖 Chat
    st.markdown("## 💬 Chat AI")

    chain = build_rag_chain(df)

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Ask something..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        answer = ask(chain, prompt + "\n\nIf user asks for graph/chart/visualization, respond briefly and do NOT explain text-only alternatives.")

        st.session_state.messages.append({"role": "assistant", "content": answer})

        st.rerun()

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
# 🌈 PREMIUM UI CONFIG
# =========================
st.set_page_config(
    page_title="💰 Finance AI Pro",
    layout="wide"
)

st.markdown("""
<style>

/* 🌈 Animated Gradient Background */
.main {
    background: linear-gradient(-45deg, #0f172a, #1e1b4b, #0f766e, #1e3a8a, #7c3aed);
    background-size: 400% 400%;
    animation: gradientBG 12s ease infinite;
    color: white;
}

/* Animation */
@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* 🧊 Glass Effect Cards */
div.stDataFrame, .stPlotlyChart, .stMetric {
    background: rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 12px;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.15);
}

/* ✨ Headings Glow */
h1, h2, h3 {
    color: #00e5ff;
    text-shadow: 0px 0px 12px rgba(0,229,255,0.6);
}

/* 🎯 Buttons */
div.stButton > button {
    background: linear-gradient(90deg, #ff4ecd, #6a5cff, #00e5ff);
    color: white;
    border-radius: 12px;
    padding: 8px 18px;
    border: none;
    font-weight: bold;
}

/* 📊 Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 10px;
}

/* 📦 File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER (PREMIUM)
# =========================
st.markdown("# 💰 Finance AI Pro")
st.markdown("### 🚀 Smart insights for your money with AI")
st.markdown("---")

st.markdown("""
<div style="
    padding:18px;
    border-radius:16px;
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    text-align:center;
    font-size:16px;
    margin-bottom:20px;
">
🔥 Track expenses • 📊 Visual analytics • 🤖 AI financial assistant
</div>
""", unsafe_allow_html=True)

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

# 🎨 Color palette
COLORS = [
    "#4F46E5", "#22C55E", "#F59E0B",
    "#EF4444", "#3B82F6", "#8B5CF6",
    "#14B8A6"
]

# 💬 Chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# 💡 Insight function
def generate_insights(df):
    insights = []

    total_spend = df["amount"].sum()
    category_sum = df.groupby("category")["amount"].sum().sort_values(ascending=False)

    top_category = category_sum.idxmax()
    top_value = category_sum.max()

    insights.append(f"💸 You spent the most on **{top_category}** (₹{top_value})")

    for cat, val in category_sum.items():
        percent = (val / total_spend) * 100

        if percent > 50:
            insights.append(f"⚠️ {cat.capitalize()} takes **{percent:.1f}%** — very high!")
        elif percent > 25:
            insights.append(f"📊 {cat.capitalize()} takes **{percent:.1f}%** — moderate")
        else:
            insights.append(f"✅ {cat.capitalize()} is under control ({percent:.1f}%)")

    return insights


# =========================
# MAIN APP
# =========================
if uploaded_file is not None:

    df = parse_statement(uploaded_file)
    df = categorizer_df(df)

    st.markdown("## 📊 Transaction Overview")
    st.dataframe(df, use_container_width=True)

    summary = spending_by_category(df)

    # =========================
    # VISUAL DASHBOARD
    # =========================
    st.markdown("## 📊 Spending Analytics Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        fig_bar = px.bar(
            summary,
            x="category",
            y="total",
            color="category",
            text_auto=True,
            color_discrete_sequence=COLORS,
        )
        fig_bar.update_layout(
            template="plotly_white",
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        fig_pie = px.pie(
            summary,
            names="category",
            values="total",
            hole=0.5,
            color_discrete_sequence=COLORS,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # =========================
    # MONTHLY TREND
    # =========================
    st.markdown("## 📈 Monthly Trend")

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month")["amount"].sum().reset_index()

    fig_line = px.line(monthly, x="month", y="amount", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

    # =========================
    # INSIGHTS
    # =========================
    st.markdown("## 💡 Smart Insights")

    insights = generate_insights(df)
    for ins in insights:
        st.markdown(f"- {ins}")

    # =========================
    # BUDGET
    # =========================
    st.markdown("## 🚨 Budget Control")

    budget = st.number_input("Set your budget (₹)", min_value=0)

    if budget > 0:
        total_spend = df["amount"].sum()
        remaining = budget - total_spend

        if remaining < 0:
            st.error(f"⚠️ Over budget by ₹{abs(remaining):.0f}")
        else:
            st.success(f"✅ Remaining ₹{remaining:.0f}")

    # =========================
    # DOWNLOAD
    # =========================
    st.markdown("## 📄 Download Report")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Data",
        csv,
        file_name="finance_report.csv",
        mime="text/csv"
    )

    # =========================
    # AI CHAT
    # =========================
    st.markdown("## 💬 AI Assistant")

    chain = build_rag_chain(df)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your spending..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        answer = ask(chain, prompt)

        with st.chat_message("assistant"):
            st.markdown(f"💡 {answer}")

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )

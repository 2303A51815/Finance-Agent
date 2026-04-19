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
# 🌌 BACKGROUND (UNCHANGED)
# =========================
st.markdown("""
<style>

.main {
    background: radial-gradient(circle at 10% 20%, #0b1220 0%, transparent 25%),
                radial-gradient(circle at 80% 10%, #1e1b4b 0%, transparent 30%),
                radial-gradient(circle at 50% 90%, #0ea5e9 0%, transparent 35%),
                radial-gradient(circle at 90% 80%, #a855f7 0%, transparent 40%),
                linear-gradient(135deg, #020617 0%, #0f172a 40%, #0b1220 100%);
    background-attachment: fixed;
    color: white;
}

</style>
""", unsafe_allow_html=True)

st.markdown("# 💰 AI Finance Assistant")

uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

COLORS = ["#4F46E5", "#22C55E", "#F59E0B", "#EF4444", "#3B82F6"]

if "messages" not in st.session_state:
    st.session_state.messages = []

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

    # 📊 CHARTS
    st.markdown("## 📊 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(summary, x="category", y="total", color="category", text_auto=True)
        st.plotly_chart(fig, use_container_width=True, key="bar_chart")

    with col2:
        fig2 = px.pie(summary, names="category", values="total", hole=0.5)
        st.plotly_chart(fig2, use_container_width=True, key="pie_chart")

    # 📈 MONTHLY
    st.markdown("## 📈 Monthly Trend")

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month")["amount"].sum().reset_index()

    fig3 = px.line(monthly, x="month", y="amount", markers=True)
    st.plotly_chart(fig3, use_container_width=True, key="line_chart")

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
    s# 🤖 CHAT (CLEAN VERSION - FIXED)

st.markdown("## 💬 Chat AI")

chain = build_rag_chain(df)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask something..."):

    # store user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):

        q = prompt.lower()

        # =========================
        # 📊 GRAPH MODE (FIXED - NO AI DECISION)
        # =========================
        if "graph" in q or "chart" in q or "visual" in q:

            # default safe graph (always works)
            fig = px.bar(
                summary,
                x="category",
                y="total",
                color="category",
                text_auto=True,
                title="📊 Expense Overview"
            )

            st.markdown("📊 Here is your expense visualization:")
            st.plotly_chart(fig, use_container_width=True)

            response = "📊 Displayed your expense graph."

        # =========================
        # 💬 TEXT MODE (AI ONLY HERE)
        # =========================
        else:

            response = ask(chain, prompt)
            st.markdown(response)

    # store assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

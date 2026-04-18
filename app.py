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
# 🎨 PAGE CONFIG + UI THEME
# =========================
st.set_page_config(
    page_title="💰 AI Finance Dashboard",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: white;
    }

    h1, h2, h3 {
        color: #60a5fa;
    }

    .stMetric {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 12px;
    }

    div.stButton > button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("# 💰 AI Finance Dashboard")
st.markdown("### Smart insights for your personal spending 📊")
st.markdown("---")

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

    # -------------------------
    # DATA PREVIEW
    # -------------------------
    st.markdown("## 📊 Transaction Overview")
    st.dataframe(df, use_container_width=True)

    summary = spending_by_category(df)

    # -------------------------
    # VISUAL DASHBOARD
    # -------------------------
    st.markdown("## 📊 Spending Analytics Dashboard")
    st.caption("Interactive breakdown of your financial behavior")

    col1, col2 = st.columns(2)

    # BAR CHART
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
            title="Category Spending",
            template="plotly_white",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # PIE CHART
    with col2:
        fig_pie = px.pie(
            summary,
            names="category",
            values="total",
            hole=0.5,
            color_discrete_sequence=COLORS,
        )
        fig_pie.update_layout(
            title="Spending Distribution",
            template="plotly_white",
            height=400
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
    st.markdown("## 💡 Smart Financial Insights")
    st.caption("AI-generated spending analysis")

    insights = generate_insights(df)
    for ins in insights:
        st.markdown(f"- {ins}")

    # =========================
    # BUDGET
    # =========================
    st.markdown("## 🚨 Budget Control Center")
    st.caption("Track your spending discipline")

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
    st.markdown("## 📄 Export Financial Report")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Report",
        csv,
        file_name="finance_report.csv",
        mime="text/csv"
    )

    # =========================
    # AI CHAT
    # =========================
    st.markdown("## 💬 AI Financial Assistant")
    st.caption("Ask anything about your spending habits")

    chain = build_rag_chain(df)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your spending..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        q = prompt.lower()

        if "graph" in q or "chart" in q:

            plot_df = summary
            x = "category"
            y = "total"
            title = "Category Spending"

            for cat in df["category"].unique():
                if cat in q:
                    filtered = df[df["category"] == cat]
                    plot_df = filtered
                    x = "description"
                    y = "amount"
                    title = f"{cat.capitalize()} Expenses"
                    break

            fig = px.bar(plot_df, x=x, y=y, color=y, text_auto=True)

            fig.update_layout(title=title, template="plotly_white", height=400)

            with st.chat_message("assistant"):
                st.plotly_chart(fig, use_container_width=True)

        else:
            answer = ask(chain, prompt)

            with st.chat_message("assistant"):
                st.markdown(f"💡 {answer}")

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

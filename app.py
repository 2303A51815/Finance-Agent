import streamlit as st
import pandas as pd
import plotly.express as px

from src.parser import parse_statement
from src.categorizer import categorizer_df, spending_by_category
from src.rag_chain import build_rag_chain, ask

st.set_page_config(page_title="AI Finance Assistant", layout="wide")

st.title("💰 AI Finance Assistant")

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
            insights.append(f"⚠️ {cat.capitalize()} takes **{percent:.1f}%** of your spending — very high!")
        elif percent > 25:
            insights.append(f"📊 {cat.capitalize()} takes **{percent:.1f}%** — moderate spending")
        else:
            insights.append(f"✅ {cat.capitalize()} is under control ({percent:.1f}%)")

    return insights


if uploaded_file is not None:
    df = parse_statement(uploaded_file)
    df = categorizer_df(df)

    st.subheader("📊 Data Preview")
    st.dataframe(df, use_container_width=True)

    summary = spending_by_category(df)

    st.markdown("## 📊 Visual Insights")

    col1, col2 = st.columns(2)

    # 📊 Bar chart
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
            title="📊 Category Spending",
            template="plotly_white",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # 🍩 Donut chart
    with col2:
        fig_pie = px.pie(
            summary,
            names="category",
            values="total",
            hole=0.5,
            color_discrete_sequence=COLORS,
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(
            title="🎯 Category Distribution",
            template="plotly_white",
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # =========================
    # 📅 MONTHLY SPENDING TREND (NEW)
    # =========================
    st.markdown("## 📅 Monthly Spending Trend")

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month")["amount"].sum().reset_index()

    fig_line = px.line(
        monthly,
        x="month",
        y="amount",
        markers=True,
    )

    fig_line.update_layout(
        title="📈 Monthly Spending Trend",
        template="plotly_white",
        height=400
    )

    st.plotly_chart(fig_line, use_container_width=True)

    # 💡 AI INSIGHTS
    st.markdown("## 💡 AI Insights")

    insights = generate_insights(df)
    for ins in insights:
        st.markdown(f"- {ins}")

    # =========================
    # 🚨 BUDGET TRACKER
    # =========================
    st.markdown("## 🚨 Budget Tracker")

    budget = st.number_input("Set your budget (₹)", min_value=0)

    if budget > 0:
        total_spend = df["amount"].sum()
        remaining = budget - total_spend

        if remaining < 0:
            st.error(f"⚠️ You exceeded your budget by ₹{abs(remaining):.0f}")
        else:
            st.success(f"✅ You are within budget. Remaining ₹{remaining:.0f}")

    # =========================
    # 📄 DOWNLOAD REPORT
    # =========================
    st.markdown("## 📄 Download Report")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download your data",
        data=csv,
        file_name="finance_report.csv",
        mime="text/csv"
    )

    # 🤖 Build AI
    chain = build_rag_chain(df)

    st.markdown("## 💬 Chat with your data")

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your spending..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        q = prompt.lower()

        # 📊 Graph request
        if "graph" in q or "chart" in q:

            plot_df = summary
            x = "category"
            y = "total"
            title = "📊 Category Spending"

            for cat in df["category"].unique():
                if cat in q:
                    filtered = df[df["category"] == cat]
                    plot_df = filtered
                    x = "description"
                    y = "amount"
                    title = f"📊 {cat.capitalize()} Expenses"
                    break

            fig = px.bar(
                plot_df,
                x=x,
                y=y,
                color=y,
                text_auto=True,
                color_continuous_scale="blues",
            )

            fig.update_layout(title=title, template="plotly_white", height=400)

            with st.chat_message("assistant"):
                st.markdown("📊 Here’s your graph:")
                st.plotly_chart(fig, use_container_width=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": "📊 Generated graph"
            })

        # 🤖 AI answer
        else:
            answer = ask(chain, prompt)

            final_answer = f"💡 {answer}"

            with st.chat_message("assistant"):
                st.markdown(final_answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_answer
            })
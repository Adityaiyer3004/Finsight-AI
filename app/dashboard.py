import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import requests

load_dotenv()

# ================================
# DB CONNECTION
# ================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# ================================
# PAGE CONFIG
# ================================
st.set_page_config(page_title="FinSight Dashboard", layout="wide")
st.title("💰 FinSight: AI Financial Dashboard")

# ================================
# LOAD DATA
# ================================
@st.cache_data
def load_data():
    return pd.read_sql("SELECT * FROM transactions_clean", engine)

df = load_data()

# ================================
# SIDEBAR FILTER
# ================================
category = st.sidebar.selectbox(
    "Filter by Category",
    ["All"] + sorted(df["category"].unique())
)

if category != "All":
    df = df[df["category"] == category]

# ================================
# METRICS
# ================================
total_spent = df[df["transaction_type"] == "debit"]["amount"].sum()
total_received = df[df["transaction_type"] == "credit"]["amount"].sum()

col1, col2 = st.columns(2)

col1.metric("💸 Total Spent", f"£{abs(total_spent):.2f}")
col2.metric("💰 Total Received", f"£{total_received:.2f}")

# ================================
# CATEGORY BREAKDOWN
# ================================
st.subheader("📊 Spending by Category")

@st.cache_data
def load_category_data():
    return pd.read_sql("SELECT * FROM category_summary", engine)

category_df = load_category_data()

st.bar_chart(category_df.set_index("category")["total"])
st.dataframe(category_df)

# ================================
# 🏆 TOP 3
# ================================
st.subheader("🏆 Top Spending Categories")

top3 = category_df.head(3)

for _, row in top3.iterrows():
    st.write(f"**{row['category']}** — £{row['total']:.2f} ({row['percentage']:.1f}%)")

# ================================
# TRANSACTIONS TABLE
# ================================
st.subheader("📄 Transactions")
st.dataframe(df.sort_values(by="transaction_date", ascending=False))

# ================================
# 🤖 AI REPORT (FASTAPI + CACHE)
# ================================
st.subheader("🤖 AI Financial Report")


@st.cache_data(ttl=300)  # cache for 5 mins
def get_ai_report():
    response = requests.post("http://localhost:8000/generate-report")

    if response.status_code == 200:
        return response.json()["data"]
    else:
        return None


if "ai_report" not in st.session_state:
    st.session_state.ai_report = None


if st.button("⚡ Generate AI Insights"):
    with st.spinner("Analyzing your finances..."):
        st.session_state.ai_report = get_ai_report()


report = st.session_state.ai_report

if report:
    st.success("✅ AI Insights Generated")

    # ================================
    # SUMMARY
    # ================================
    st.markdown("### 📌 Summary")
    st.info(report["summary"])

    # ================================
    # KEY INSIGHTS
    # ================================
    st.markdown("### 📊 Key Insights")
    for insight in report["key_insights"]:
        st.markdown(f"- {insight}")

    # ================================
    # CATEGORY ANALYSIS
    # ================================
    st.markdown("### 📊 Category Analysis")

    for item in report["category_analysis"]:
        with st.expander(f"{item['category']}"):
            st.write(f"Type: **{item['type']}**")
            st.write(item["insight"])

    # ================================
    # SPENDING SPLIT
    # ================================
    st.markdown("### ⚖️ Spending Split")
    st.warning(report["spending_split"])

    # ================================
    # RISK FLAGS
    # ================================
    st.markdown("### 🚩 Risk Flags")
    for risk in report["risk_flags"]:
        st.error(risk)

    # ================================
    # RECOMMENDATIONS
    # ================================
    st.markdown("### 💡 Recommendations")
    for rec in report["recommendations"]:
        st.success(rec)

    # ================================
    # FINAL VERDICT
    # ================================
    st.markdown("### 📌 Final Verdict")
    st.markdown(f"**{report['final_verdict']}**")

else:
    st.info("Click 'Generate AI Insights' to analyze your finances.")
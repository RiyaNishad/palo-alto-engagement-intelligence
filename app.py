import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Palo Alto Engagement Intelligence",
    page_icon="📊",
    layout="wide"
)

# ---------------------------
# Theme colors
# ---------------------------
PRIMARY = "#2A9D8F"
SECONDARY = "#4C78A8"
LOW_RISK = "#7BC96F"
MED_RISK = "#F4A261"
HIGH_RISK = "#E76F51"
BG = "#0E1117"
CARD = "#161B22"
TEXT = "#E6EDF3"
MUTED = "#9BA3AF"
BORDER = "#2D333B"

# ---------------------------
# Custom styling
# ---------------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BG};
        color: {TEXT};
    }}

    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 96%;
    }}

    section[data-testid="stSidebar"] {{
        width: 320px !important;
        background-color: {CARD};
        border-right: 1px solid {BORDER};
    }}

    div[data-testid="metric-container"] {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        padding: 16px;
        border-radius: 14px;
    }}

    div[data-testid="metric-container"] label {{
        color: {MUTED} !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}

    .dashboard-note {{
        background-color: #132238;
        border: 1px solid #1f3b5c;
        color: #c8def4;
        padding: 12px 16px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 10px;
    }}

    .risk-note {{
        background-color: #3b3d12;
        border: 1px solid #5a5e1d;
        color: #eef0b5;
        padding: 12px 16px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Load data
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent

POSSIBLE_FILES = [
    BASE_DIR / "palo_alto_networks.csv",
    BASE_DIR / "Palo-Alto-Networks.csv"
]

@st.cache_data
def load_data():
    data_path = None
    for path in POSSIBLE_FILES:
        if path.exists():
            data_path = path
            break

    if data_path is None:
        st.error("CSV file not found. Make sure it is in the same folder as app.py.")
        st.stop()

    df = pd.read_csv(data_path)

    # Clean column names
    df.columns = df.columns.str.strip()

    required_columns = [
        "JobSatisfaction",
        "EnvironmentSatisfaction",
        "RelationshipSatisfaction",
        "WorkLifeBalance",
        "JobInvolvement",
        "OverTime",
        "Attrition",
        "Department",
        "JobRole",
        "YearsAtCompany",
        "MonthlyIncome"
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns in CSV: {missing_cols}")
        st.write("Available columns:", df.columns.tolist())
        st.stop()

    # Normalize OverTime values
    df["OverTime"] = df["OverTime"].astype(str).str.strip()

    # Normalize Attrition
    if df["Attrition"].dtype == object:
        df["Attrition"] = df["Attrition"].astype(str).str.strip().str.lower().map({
            "yes": 1,
            "no": 0
        })

    df["Attrition"] = pd.to_numeric(df["Attrition"], errors="coerce").fillna(0)

    # Create EngagementIndex
    df["EngagementIndex"] = (
        df["JobSatisfaction"] +
        df["EnvironmentSatisfaction"] +
        df["RelationshipSatisfaction"] +
        df["WorkLifeBalance"] +
        df["JobInvolvement"]
    ) / 5 * 20

    # Burnout score
    overtime_map = {"Yes": 5, "No": 1, "yes": 5, "no": 1}
    df["BurnoutRiskScore"] = (
        (5 - df["WorkLifeBalance"]) * 0.35 +
        df["OverTime"].map(overtime_map).fillna(1) * 0.30 +
        (5 - df["EnvironmentSatisfaction"]) * 0.20 +
        (5 - df["JobSatisfaction"]) * 0.15
    )

    def classify_burnout(score):
        if score >= 3.5:
            return "High"
        elif score >= 2.5:
            return "Medium"
        else:
            return "Low"

    df["BurnoutRiskLevel"] = df["BurnoutRiskScore"].apply(classify_burnout)
    df["AttritionLabel"] = df["Attrition"].map({1: "Yes", 0: "No"})

    return df

try:
    df = load_data()

    st.title("Palo Alto Engagement Intelligence")
    st.caption(
        "A workforce well-being dashboard tracking engagement, burnout exposure, attrition risk, and work-life balance."
    )

    st.sidebar.header("Filter Panel")

    dept_options = sorted(df["Department"].dropna().unique().tolist())
    role_options = sorted(df["JobRole"].dropna().unique().tolist())

    selected_departments = st.sidebar.multiselect(
        "Select Department",
        options=dept_options,
        default=dept_options if len(dept_options) <= 3 else dept_options[:3]
    )

    selected_job_roles = st.sidebar.multiselect(
        "Select Job Role",
        options=role_options,
        default=role_options if len(role_options) <= 4 else role_options[:4]
    )

    overtime_options = ["All"] + sorted(df["OverTime"].dropna().astype(str).unique().tolist())
    selected_overtime = st.sidebar.selectbox(
        "Select Overtime",
        options=overtime_options
    )

    min_engagement = st.sidebar.slider(
        "Minimum Engagement Index",
        min_value=int(df["EngagementIndex"].min()),
        max_value=int(df["EngagementIndex"].max()),
        value=int(df["EngagementIndex"].min())
    )

    years_range = st.sidebar.slider(
        "Years at Company",
        min_value=int(df["YearsAtCompany"].min()),
        max_value=int(df["YearsAtCompany"].max()),
        value=(int(df["YearsAtCompany"].min()), int(df["YearsAtCompany"].max()))
    )

    filtered_df = df[
        (df["Department"].isin(selected_departments)) &
        (df["JobRole"].isin(selected_job_roles)) &
        (df["EngagementIndex"] >= min_engagement) &
        (df["YearsAtCompany"] >= years_range[0]) &
        (df["YearsAtCompany"] <= years_range[1])
    ]

    if selected_overtime != "All":
        filtered_df = filtered_df[filtered_df["OverTime"] == selected_overtime]

    if filtered_df.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    # ---------------------------
    # KPI row
    # ---------------------------
    st.markdown("## Overview Metrics")
    k1, k2, k3, k4 = st.columns(4)

    employee_count = len(filtered_df)
    avg_engagement = filtered_df["EngagementIndex"].mean()
    avg_wlb = filtered_df["WorkLifeBalance"].mean()
    attrition_rate = filtered_df["Attrition"].mean() * 100

    k1.metric("Employees", f"{employee_count}")
    k2.metric("Avg Engagement Index", f"{avg_engagement:.1f}")
    k3.metric("Avg Work-Life Balance", f"{avg_wlb:.2f}")
    k4.metric("Attrition Rate", f"{attrition_rate:.1f}%")

    # ---------------------------
    # Engagement section
    # ---------------------------
    st.markdown("## Engagement Health Overview")
    c1, c2 = st.columns(2)

    with c1:
        fig_hist = px.histogram(
            filtered_df,
            x="EngagementIndex",
            nbins=15,
            title="Engagement Index Distribution",
            color_discrete_sequence=[PRIMARY]
        )
        fig_hist.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        satisfaction_cols = [
            "JobInvolvement",
            "JobSatisfaction",
            "EnvironmentSatisfaction",
            "RelationshipSatisfaction",
            "WorkLifeBalance"
        ]
        avg_scores = filtered_df[satisfaction_cols].mean().reset_index()
        avg_scores.columns = ["Metric", "AverageScore"]

        fig_sat = px.bar(
            avg_scores,
            x="Metric",
            y="AverageScore",
            title="Average Satisfaction Scores",
            color="Metric",
            color_discrete_sequence=[PRIMARY, SECONDARY, "#6BAED6", "#5DA5A4", "#76C893"]
        )
        fig_sat.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT,
            showlegend=False
        )
        st.plotly_chart(fig_sat, use_container_width=True)

    st.markdown(
        f"""
        <div class="dashboard-note">
        The filtered group has an average engagement score of <b>{avg_engagement:.1f}</b>,
        an average work-life balance score of <b>{avg_wlb:.2f}</b>,
        and an attrition rate of <b>{attrition_rate:.1f}%</b>.
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------
    # Burnout section
    # ---------------------------
    st.markdown("## Burnout Risk Dashboard")
    c3, c4 = st.columns(2)

    with c3:
        burnout_counts = filtered_df["BurnoutRiskLevel"].value_counts().reset_index()
        burnout_counts.columns = ["BurnoutRiskLevel", "Count"]

        fig_burnout = px.pie(
            burnout_counts,
            names="BurnoutRiskLevel",
            values="Count",
            title="Burnout Risk Composition",
            color="BurnoutRiskLevel",
            color_discrete_map={
                "Low": LOW_RISK,
                "Medium": MED_RISK,
                "High": HIGH_RISK
            }
        )
        fig_burnout.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT
        )
        st.plotly_chart(fig_burnout, use_container_width=True)

    with c4:
        overtime_wlb = filtered_df.groupby("OverTime", as_index=False)["WorkLifeBalance"].mean()

        fig_overtime = px.bar(
            overtime_wlb,
            x="OverTime",
            y="WorkLifeBalance",
            title="Average Work-Life Balance by Overtime",
            color="OverTime",
            color_discrete_map={
                "No": PRIMARY,
                "Yes": HIGH_RISK,
                "no": PRIMARY,
                "yes": HIGH_RISK
            }
        )
        fig_overtime.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT,
            showlegend=False
        )
        st.plotly_chart(fig_overtime, use_container_width=True)

    # ---------------------------
    # Attrition section
    # ---------------------------
    st.markdown("## Attrition Insights")
    c5, c6 = st.columns(2)

    with c5:
        attrition_by_dept = (
            filtered_df.groupby("Department", as_index=False)["Attrition"]
            .mean()
            .sort_values("Attrition", ascending=False)
        )
        attrition_by_dept["Attrition"] = attrition_by_dept["Attrition"] * 100

        fig_attrition = px.bar(
            attrition_by_dept,
            x="Department",
            y="Attrition",
            title="Attrition Rate by Department (%)",
            color="Attrition",
            color_continuous_scale=[PRIMARY, MED_RISK, HIGH_RISK]
        )
        fig_attrition.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT,
            coloraxis_colorbar_title="Attrition %"
        )
        st.plotly_chart(fig_attrition, use_container_width=True)

    with c6:
        fig_scatter = px.scatter(
            filtered_df,
            x="MonthlyIncome",
            y="EngagementIndex",
            color="BurnoutRiskLevel",
            title="Monthly Income vs Engagement Index",
            color_discrete_map={
                "Low": LOW_RISK,
                "Medium": MED_RISK,
                "High": HIGH_RISK
            },
            hover_data=["JobRole", "Department", "OverTime"]
        )
        fig_scatter.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ---------------------------
    # High-risk segment
    # ---------------------------
    st.markdown("## High-Risk Segment Snapshot")
    high_risk_df = filtered_df[filtered_df["BurnoutRiskLevel"] == "High"]

    h1, h2, h3 = st.columns(3)
    h1.metric("High-Risk Employees", f"{len(high_risk_df)}")

    if len(high_risk_df) > 0:
        high_risk_attrition = high_risk_df["Attrition"].mean() * 100
        high_risk_engagement = high_risk_df["EngagementIndex"].mean()

        h2.metric("High-Risk Attrition Rate", f"{high_risk_attrition:.1f}%")
        h3.metric("High-Risk Avg Engagement", f"{high_risk_engagement:.1f}")

        st.markdown(
            f"""
            <div class="risk-note">
            <b>{len(high_risk_df)}</b> employees fall into the high-burnout category.
            Their average engagement score is <b>{high_risk_engagement:.1f}</b>,
            and their attrition rate is <b>{high_risk_attrition:.1f}%</b>.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        h2.metric("High-Risk Attrition Rate", "0.0%")
        h3.metric("High-Risk Avg Engagement", "0.0")
        st.info("No high-risk employees are present in the current filtered segment.")

    # ---------------------------
    # Download section
    # ---------------------------
    st.markdown("## Download Filtered Data")
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered dataset as CSV",
        data=csv_data,
        file_name="filtered_palo_alto_dashboard_data.csv",
        mime="text/csv"
    )

    # ---------------------------
    # Table preview
    # ---------------------------
    st.markdown("## Filtered Dataset Preview")
    with st.expander("View filtered dataset"):
        st.dataframe(filtered_df, use_container_width=True, height=320)

except Exception as e:
    st.error(f"An error occurred: {e}")

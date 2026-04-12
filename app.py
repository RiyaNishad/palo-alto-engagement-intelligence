import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Palo Alto Engagement Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# THEME
# -----------------------------
BG = "#0B1020"
CARD = "#121A2B"
CARD_2 = "#182235"
BORDER = "#24324A"
TEXT = "#F3F6FC"
MUTED = "#98A6BD"
PRIMARY = "#2EC4B6"
SECONDARY = "#5B8DEF"
WARNING = "#F4A261"
DANGER = "#E76F51"
SUCCESS = "#7BD389"

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #0B1020 0%, #0F172A 100%);
        color: {TEXT};
    }}

    .block-container {{
        max-width: 96%;
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
    }}

    section[data-testid="stSidebar"] {{
        background: #0E1627;
        border-right: 1px solid {BORDER};
    }}

    [data-testid="stSidebar"] * {{
        color: {TEXT};
    }}

    .hero {{
        background: linear-gradient(135deg, rgba(46,196,182,0.14), rgba(91,141,239,0.10));
        border: 1px solid rgba(255,255,255,0.08);
        padding: 28px 30px;
        border-radius: 22px;
        margin-bottom: 18px;
        box-shadow: 0 10px 35px rgba(0,0,0,0.22);
    }}

    .hero-title {{
        font-size: 2.3rem;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }}

    .hero-sub {{
        font-size: 1rem;
        color: {MUTED};
        margin-bottom: 1rem;
    }}

    .badge-row {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 8px;
    }}

    .badge {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        color: {TEXT};
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 0.84rem;
    }}

    .section-title {{
        font-size: 1.2rem;
        font-weight: 700;
        color: {TEXT};
        margin-top: 0.6rem;
        margin-bottom: 0.8rem;
    }}

    .kpi-card {{
        background: linear-gradient(180deg, {CARD} 0%, {CARD_2} 100%);
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 18px 18px 16px 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
        min-height: 138px;
    }}

    .kpi-label {{
        color: {MUTED};
        font-size: 0.9rem;
        margin-bottom: 10px;
    }}

    .kpi-value {{
        color: {TEXT};
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 10px;
    }}

    .kpi-delta {{
        color: {PRIMARY};
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 8px;
    }}

    .kpi-note {{
        color: {MUTED};
        font-size: 0.83rem;
        line-height: 1.4;
    }}

    .insight-box {{
        background: rgba(46,196,182,0.08);
        border: 1px solid rgba(46,196,182,0.22);
        border-radius: 16px;
        padding: 14px 16px;
        color: #D8FFF7;
        margin-top: 8px;
        margin-bottom: 10px;
    }}

    .risk-box {{
        background: rgba(231,111,81,0.08);
        border: 1px solid rgba(231,111,81,0.24);
        border-radius: 16px;
        padding: 14px 16px;
        color: #FFE0D7;
        margin-top: 8px;
        margin-bottom: 10px;
    }}

    .action-box {{
        background: linear-gradient(180deg, rgba(91,141,239,0.10), rgba(46,196,182,0.08));
        border: 1px solid rgba(91,141,239,0.24);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 12px;
    }}

    div[data-testid="metric-container"] {{
        background: transparent;
        border: none;
        padding: 0;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 14px;
        overflow: hidden;
    }}

    .small-note {{
        color: {MUTED};
        font-size: 0.85rem;
    }}

    hr {{
        border: none;
        border-top: 1px solid {BORDER};
        margin: 1rem 0 1.2rem 0;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# HELPERS
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
POSSIBLE_FILES = [
    BASE_DIR / "palo_alto_networks.csv",
    BASE_DIR / "Palo-Alto-Networks.csv"
]

def metric_card(label, value, delta_text, note):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{delta_text}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def classify_burnout(score):
    if score >= 3.5:
        return "High"
    elif score >= 2.5:
        return "Medium"
    return "Low"

def status_text(value, low_good=True):
    if low_good:
        if value < 10:
            return "Healthy range"
        elif value < 20:
            return "Watch closely"
        return "Needs attention"
    else:
        if value >= 75:
            return "Strong"
        elif value >= 60:
            return "Stable"
        return "Needs attention"

@st.cache_data
def load_data():
    data_path = None
    for path in POSSIBLE_FILES:
        if path.exists():
            data_path = path
            break

    if data_path is None:
        st.error("CSV file not found. Keep the CSV in the same folder as app.py.")
        st.stop()

    df = pd.read_csv(data_path)
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

    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        st.write("Available columns:", df.columns.tolist())
        st.stop()

    df["OverTime"] = df["OverTime"].astype(str).str.strip()

    if df["Attrition"].dtype == object:
        df["Attrition"] = (
            df["Attrition"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"yes": 1, "no": 0})
        )

    df["Attrition"] = pd.to_numeric(df["Attrition"], errors="coerce").fillna(0)

    df["EngagementIndex"] = (
        df["JobSatisfaction"] +
        df["EnvironmentSatisfaction"] +
        df["RelationshipSatisfaction"] +
        df["WorkLifeBalance"] +
        df["JobInvolvement"]
    ) / 5 * 20

    overtime_map = {"Yes": 5, "No": 1, "yes": 5, "no": 1}
    df["BurnoutRiskScore"] = (
        (5 - df["WorkLifeBalance"]) * 0.35 +
        df["OverTime"].map(overtime_map).fillna(1) * 0.30 +
        (5 - df["EnvironmentSatisfaction"]) * 0.20 +
        (5 - df["JobSatisfaction"]) * 0.15
    )

    df["BurnoutRiskLevel"] = df["BurnoutRiskScore"].apply(classify_burnout)
    df["AttritionLabel"] = df["Attrition"].map({1: "Yes", 0: "No"})

    return df

# -----------------------------
# LOAD DATA
# -----------------------------
try:
    df = load_data()
except Exception as e:
    st.error(f"An error occurred while loading data: {e}")
    st.stop()

# -----------------------------
# HERO
# -----------------------------
st.markdown(
    """
    <div class="hero">
        <div class="hero-title">Palo Alto Engagement Intelligence</div>
        <div class="hero-sub">
            Executive workforce intelligence dashboard for engagement health, burnout exposure,
            attrition signals, and work-life balance diagnostics.
        </div>
        <div class="badge-row">
            <div class="badge">Executive View</div>
            <div class="badge">HR Analytics</div>
            <div class="badge">Burnout Monitoring</div>
            <div class="badge">Decision Support</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.markdown("## Filter Panel")

dept_options = sorted(df["Department"].dropna().unique().tolist())
role_options = sorted(df["JobRole"].dropna().unique().tolist())
overtime_options = ["All"] + sorted(df["OverTime"].dropna().astype(str).unique().tolist())

selected_departments = st.sidebar.multiselect(
    "Department",
    options=dept_options,
    default=dept_options
)

selected_roles = st.sidebar.multiselect(
    "Job Role",
    options=role_options,
    default=role_options
)

selected_overtime = st.sidebar.selectbox(
    "Overtime Status",
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
    (df["JobRole"].isin(selected_roles)) &
    (df["EngagementIndex"] >= min_engagement) &
    (df["YearsAtCompany"] >= years_range[0]) &
    (df["YearsAtCompany"] <= years_range[1])
]

if selected_overtime != "All":
    filtered_df = filtered_df[filtered_df["OverTime"] == selected_overtime]

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# -----------------------------
# KPIs
# -----------------------------
employee_count = len(filtered_df)
avg_engagement = filtered_df["EngagementIndex"].mean()
avg_wlb = filtered_df["WorkLifeBalance"].mean()
attrition_rate = filtered_df["Attrition"].mean() * 100
high_risk_df = filtered_df[filtered_df["BurnoutRiskLevel"] == "High"]
high_risk_count = len(high_risk_df)
high_risk_rate = (high_risk_count / employee_count * 100) if employee_count > 0 else 0

top_risk_department = (
    filtered_df.groupby("Department")["Attrition"]
    .mean()
    .sort_values(ascending=False)
    .index[0]
)

st.markdown('<div class="section-title">Executive Snapshot</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    metric_card(
        "Employees in Scope",
        f"{employee_count}",
        "Filtered workforce view",
        "Current records included in the dashboard selection."
    )

with c2:
    metric_card(
        "Engagement Index",
        f"{avg_engagement:.1f}",
        status_text(avg_engagement, low_good=False),
        "Composite score derived from satisfaction, involvement, and work-life balance."
    )

with c3:
    metric_card(
        "Attrition Rate",
        f"{attrition_rate:.1f}%",
        status_text(attrition_rate, low_good=True),
        "Share of employees marked with attrition under the selected filters."
    )

with c4:
    metric_card(
        "High Burnout Risk",
        f"{high_risk_rate:.1f}%",
        "Escalation segment",
        "Employees in the high-risk burnout band based on work-life and overtime factors."
    )

st.markdown(
    f"""
    <div class="insight-box">
        The current filtered workforce shows an average engagement score of <b>{avg_engagement:.1f}</b>,
        an attrition rate of <b>{attrition_rate:.1f}%</b>, and the highest attrition concentration appears in
        <b>{top_risk_department}</b>.
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Burnout Risk", "Attrition", "Action Center"])

# -----------------------------
# PLOTLY COMMON STYLE
# -----------------------------
def polish(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font_color=TEXT,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    return fig

# -----------------------------
# TAB 1 - OVERVIEW
# -----------------------------
with tab1:
    st.markdown('<div class="section-title">Engagement Health Overview</div>', unsafe_allow_html=True)
    o1, o2 = st.columns([1.15, 1])

    with o1:
        fig_hist = px.histogram(
            filtered_df,
            x="EngagementIndex",
            nbins=18,
            title="Engagement Index Distribution",
            color_discrete_sequence=[PRIMARY]
        )
        st.plotly_chart(polish(fig_hist), use_container_width=True)

    with o2:
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
            title="Average Satisfaction Drivers",
            color="Metric",
            color_discrete_sequence=[PRIMARY, SECONDARY, SUCCESS, WARNING, "#72B7B2"]
        )
        fig_sat.update_layout(showlegend=False)
        st.plotly_chart(polish(fig_sat), use_container_width=True)

    dept_engagement = (
        filtered_df.groupby("Department", as_index=False)["EngagementIndex"]
        .mean()
        .sort_values("EngagementIndex", ascending=False)
    )

    fig_dept_eng = px.bar(
        dept_engagement,
        x="Department",
        y="EngagementIndex",
        title="Engagement by Department",
        color="EngagementIndex",
        color_continuous_scale=["#1F6F78", PRIMARY, SUCCESS]
    )
    st.plotly_chart(polish(fig_dept_eng), use_container_width=True)

# -----------------------------
# TAB 2 - BURNOUT
# -----------------------------
with tab2:
    st.markdown('<div class="section-title">Burnout Exposure and Work-Life Signals</div>', unsafe_allow_html=True)
    b1, b2 = st.columns(2)

    with b1:
        burnout_counts = filtered_df["BurnoutRiskLevel"].value_counts().reset_index()
        burnout_counts.columns = ["BurnoutRiskLevel", "Count"]

        fig_burn = px.pie(
            burnout_counts,
            names="BurnoutRiskLevel",
            values="Count",
            title="Burnout Risk Composition",
            hole=0.58,
            color="BurnoutRiskLevel",
            color_discrete_map={
                "Low": SUCCESS,
                "Medium": WARNING,
                "High": DANGER
            }
        )
        st.plotly_chart(polish(fig_burn), use_container_width=True)

    with b2:
        overtime_wlb = filtered_df.groupby("OverTime", as_index=False)["WorkLifeBalance"].mean()

        fig_ot = px.bar(
            overtime_wlb,
            x="OverTime",
            y="WorkLifeBalance",
            title="Work-Life Balance by Overtime",
            color="OverTime",
            color_discrete_map={
                "Yes": DANGER,
                "No": PRIMARY,
                "yes": DANGER,
                "no": PRIMARY
            }
        )
        fig_ot.update_layout(showlegend=False)
        st.plotly_chart(polish(fig_ot), use_container_width=True)

    burnout_dept = (
        filtered_df.groupby(["Department", "BurnoutRiskLevel"])
        .size()
        .reset_index(name="Count")
    )

    fig_stack = px.bar(
        burnout_dept,
        x="Department",
        y="Count",
        color="BurnoutRiskLevel",
        title="Burnout Mix by Department",
        color_discrete_map={
            "Low": SUCCESS,
            "Medium": WARNING,
            "High": DANGER
        }
    )
    st.plotly_chart(polish(fig_stack), use_container_width=True)

    st.markdown(
        f"""
        <div class="risk-box">
            <b>{high_risk_count}</b> employees are currently in the high-burnout segment.
            This group represents <b>{high_risk_rate:.1f}%</b> of the filtered workforce and should be reviewed
            first for overtime pressure, work-life imbalance, and declining satisfaction.
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# TAB 3 - ATTRITION
# -----------------------------
with tab3:
    st.markdown('<div class="section-title">Attrition Drivers and Vulnerable Segments</div>', unsafe_allow_html=True)
    a1, a2 = st.columns([1, 1.05])

    with a1:
        attrition_by_dept = (
            filtered_df.groupby("Department", as_index=False)["Attrition"]
            .mean()
            .sort_values("Attrition", ascending=False)
        )
        attrition_by_dept["Attrition"] *= 100

        fig_attr = px.bar(
            attrition_by_dept,
            x="Department",
            y="Attrition",
            title="Attrition Rate by Department (%)",
            color="Attrition",
            color_continuous_scale=[PRIMARY, WARNING, DANGER]
        )
        st.plotly_chart(polish(fig_attr), use_container_width=True)

    with a2:
        fig_scatter = px.scatter(
            filtered_df,
            x="MonthlyIncome",
            y="EngagementIndex",
            color="BurnoutRiskLevel",
            size="YearsAtCompany",
            hover_data=["JobRole", "Department", "OverTime"],
            title="Income vs Engagement vs Burnout",
            color_discrete_map={
                "Low": SUCCESS,
                "Medium": WARNING,
                "High": DANGER
            }
        )
        st.plotly_chart(polish(fig_scatter), use_container_width=True)

    role_attrition = (
        filtered_df.groupby("JobRole", as_index=False)["Attrition"]
        .mean()
        .sort_values("Attrition", ascending=False)
        .head(10)
    )
    role_attrition["Attrition"] *= 100

    fig_role = px.bar(
        role_attrition,
        x="Attrition",
        y="JobRole",
        orientation="h",
        title="Top Job Roles by Attrition Rate",
        color="Attrition",
        color_continuous_scale=[PRIMARY, WARNING, DANGER]
    )
    st.plotly_chart(polish(fig_role), use_container_width=True)

# -----------------------------
# TAB 4 - ACTION CENTER
# -----------------------------
with tab4:
    st.markdown('<div class="section-title">Action Center</div>', unsafe_allow_html=True)

    highest_attrition = attrition_by_dept.iloc[0]
    worst_role = role_attrition.iloc[0] if len(role_attrition) > 0 else None

    cta1, cta2 = st.columns([1.2, 1])

    with cta1:
        st.markdown(
            f"""
            <div class="action-box">
                <h4 style="margin-bottom:8px; color:{TEXT};">Priority Department</h4>
                <p style="margin:0 0 8px 0; color:{TEXT}; font-size:1.25rem; font-weight:700;">
                    {highest_attrition['Department']}
                </p>
                <p class="small-note">
                    This department has the highest attrition rate in the current workforce view at
                    <b>{highest_attrition['Attrition']:.1f}%</b>. Review manager workload, overtime exposure,
                    and engagement decline here first.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if worst_role is not None:
            st.markdown(
                f"""
                <div class="action-box">
                    <h4 style="margin-bottom:8px; color:{TEXT};">Most Vulnerable Job Role</h4>
                    <p style="margin:0 0 8px 0; color:{TEXT}; font-size:1.25rem; font-weight:700;">
                        {worst_role['JobRole']}
                    </p>
                    <p class="small-note">
                        This role has the highest attrition concentration among the top roles shown,
                        with a rate of <b>{worst_role['Attrition']:.1f}%</b>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    with cta2:
        if high_risk_count > 0:
            high_risk_attrition = high_risk_df["Attrition"].mean() * 100
            high_risk_engagement = high_risk_df["EngagementIndex"].mean()

            st.markdown(
                f"""
                <div class="action-box">
                    <h4 style="margin-bottom:8px; color:{TEXT};">High-Risk Segment Summary</h4>
                    <p class="small-note" style="margin-bottom:8px;">
                        Employees in high burnout risk: <b>{high_risk_count}</b>
                    </p>
                    <p class="small-note" style="margin-bottom:8px;">
                        High-risk attrition rate: <b>{high_risk_attrition:.1f}%</b>
                    </p>
                    <p class="small-note" style="margin-bottom:0;">
                        High-risk average engagement: <b>{high_risk_engagement:.1f}</b>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("No employees are currently in the high-burnout segment for the selected filters.")

    priority_table = filtered_df.copy()
    priority_table = priority_table[
        [
            "Department", "JobRole", "YearsAtCompany", "MonthlyIncome",
            "EngagementIndex", "BurnoutRiskLevel", "AttritionLabel", "OverTime"
        ]
    ].sort_values(by=["BurnoutRiskLevel", "EngagementIndex"], ascending=[False, True])

    st.markdown("### Priority Review Table")
    st.dataframe(priority_table, use_container_width=True, height=350)

    st.download_button(
        label="Download filtered dataset as CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_palo_alto_dashboard_data.csv",
        mime="text/csv"
    )

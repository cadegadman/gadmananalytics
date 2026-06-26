import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

def format_avg(x):
    return f"{x:.3f}".replace("0.", ".")

st.set_page_config(page_title="Offensive Success Rate", layout="wide")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

TEAM_IDS = {
    "Arizona Diamondbacks": 109,
    "Atlanta Braves": 144,
    "Baltimore Orioles": 110,
    "Boston Red Sox": 111,
    "Chicago Cubs": 112,
    "Chicago White Sox": 145,
    "Cincinnati Reds": 113,
    "Cleveland Guardians": 114,
    "Colorado Rockies": 115,
    "Detroit Tigers": 116,
    "Houston Astros": 117,
    "Kansas City Royals": 118,
    "Los Angeles Angels": 108,
    "Los Angeles Dodgers": 119,
    "Miami Marlins": 146,
    "Milwaukee Brewers": 158,
    "Minnesota Twins": 142,
    "New York Mets": 121,
    "New York Yankees": 147,
    "Athletics": 133,
    "Oakland Athletics": 133,
    "Philadelphia Phillies": 143,
    "Pittsburgh Pirates": 134,
    "San Diego Padres": 135,
    "Seattle Mariners": 136,
    "San Francisco Giants": 137,
    "St. Louis Cardinals": 138,
    "Tampa Bay Rays": 139,
    "Texas Rangers": 140,
    "Toronto Blue Jays": 141,
    "Washington Nationals": 120,
}
    
def get_team_logo(team):
    team_id = TEAM_IDS.get(str(team))
    if team_id:
        return f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
    return None

seasons = ["2026", "2025", "2024"]

selected_season = st.sidebar.selectbox("Season", seasons)



SEASON_DIR = DATA_DIR / selected_season
all_plays = pd.read_csv(SEASON_DIR / "all_plays.csv")
all_plays["date"] = pd.to_datetime(all_plays["date"])

base_situation_options = {
    "All": ["empty", "1st", "2nd", "3rd", "1st_2nd", "1st_3rd", "2nd_3rd", "loaded"],
    "Bases Empty": ["empty"],
    "Runner on 1st": ["1st"],
    "Runner on 2nd": ["2nd"],
    "Runner on 3rd": ["3rd"],
    "Runners on 1st & 2nd": ["1st_2nd"],
    "Runners on 1st & 3rd": ["1st_3rd"],
    "Runners on 2nd & 3rd": ["2nd_3rd"],
    "Bases Loaded": ["loaded"],
    "RISP": ["2nd", "3rd", "1st_2nd", "1st_3rd", "2nd_3rd", "loaded"],
    "Any Runners On": ["1st", "2nd", "3rd", "1st_2nd", "1st_3rd", "2nd_3rd", "loaded"]
}

def make_player_leaderboard(df, min_opps=0):
    lb = df.groupby("batter").agg(
        team=("team", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        opportunities=("success", "count"),
        successes=("success", "sum")
    ).reset_index()

    lb["success_rate"] = lb["successes"] / lb["opportunities"]
    lb = lb[lb["opportunities"] >= min_opps]
    lb["success_rate_display"] = lb["success_rate"].apply(format_avg)
    lb["Logo"] = lb["team"].apply(get_team_logo)
    lb = lb.sort_values("success_rate", ascending=False)

    display = lb[
        [
            "Logo",
            "batter",
            "opportunities",
            "successes",
            "success_rate_display"
        ]
    ].rename(columns={
        "batter": "Player",
        "opportunities": "Opportunities",
        "successes": "Successes",
        "success_rate_display": "OSR"
    })

    display.index = range(1, len(display) + 1)
    return display

def make_team_leaderboard(df, min_opps=0):
    lb = df.groupby("team").agg(
        opportunities=("success", "count"),
        successes=("success", "sum")
    ).reset_index()

    lb["success_rate"] = lb["successes"] / lb["opportunities"]
    lb = lb[lb["opportunities"] >= min_opps]
    lb["success_rate_display"] = lb["success_rate"].apply(format_avg)
    lb["Logo"] = lb["team"].apply(get_team_logo)
    lb = lb.sort_values("success_rate", ascending=False)

    display = lb[["Logo", "team", "opportunities", "successes", "success_rate_display"]].rename(columns={
        "team": "Team",
        "opportunities": "Opportunities",
        "successes": "Successes",
        "success_rate_display": "OSR"
    })

    display.index = range(1, len(display) + 1)
    return display
page = st.segmented_control(
    "",
    ["Home", "Player Leaderboard", "Team Leaderboard"],
    default="Home"
)
col1, col2 = st.columns([1, 8])

with col1:
    st.image("logo.png", width=110)

with col2:
    st.title("Offensive Success Rate")
    st.caption("Context-Dependent Offensive Success Using MLB Play-by-Play Data")

st.markdown("---")
st.set_page_config(page_title="Offensive Success Rate", layout="wide")

st.markdown("""
<style>

/* Hide Streamlit stuff */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main background */
.stApp {
    background-color: white;
}

/* Main title */
h1 {
    color: black;
    border-bottom: 4px solid #92D050;
    padding-bottom: 10px;
}

/* Subheaders */
h3 {
    color: black;
    background-color: #92D050;
    padding: 8px 15px;
    border-radius: 8px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f8f8f8;
    border-right: 3px solid #92D050;
}

/* Metric cards */
[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #d9d9d9;
    border-top: 6px solid #92D050;
    padding: 15px;
    border-radius: 10px;
}

/* Tables */
[data-testid="stDataFrame"] {
    border: 2px solid #92D050;
    border-radius: 10px;
}

/* Buttons */
.stButton > button {
    background-color: #92D050;
    color: black;
    border-radius: 8px;
    border: none;
}

/* Divider lines */
hr {
    border: 2px solid #92D050;
}

/* Reduce top padding */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.image("logo.png", width=120)
st.sidebar.markdown("### Baseball Success Metric")

if page == "Home":
    opportunities = len(all_plays)
    successes = all_plays["success"].sum()
    success_rate = successes / opportunities if opportunities > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Opportunities", opportunities)
    col2.metric("Successes", int(successes))
    col3.metric("Success Rate", format_avg(success_rate))

    daily_success = all_plays.groupby("date").agg(
    opportunities=("success", "count"),
    successes=("success", "sum")
).reset_index()

    daily_success["success_rate"] = daily_success["successes"] / daily_success["opportunities"]

    st.subheader("League Success Rate Over Time")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Players")
        st.dataframe(
        make_player_leaderboard(all_plays, min_opps=200).head(10),
        use_container_width=True,
        height=400,
        column_config={
            "Logo": st.column_config.ImageColumn ("", width="small")
        }
)

    with col2:
        st.subheader("Top 10 Teams")
        st.dataframe(
        make_team_leaderboard(all_plays).head(10),
        use_container_width=True,
        height=400,
        column_config={
            "Logo": st.column_config.ImageColumn("Logo", width="small")
        }
    )
    QUALIFYING_OPPS = 75

    player_totals = all_plays.groupby("batter").agg(
    opportunities=("success", "count"),
    successes=("success", "sum")
).reset_index()

    player_totals["osr"] = (
    player_totals["successes"] / player_totals["opportunities"]
)

    qualified_players = player_totals[
    player_totals["opportunities"] >= QUALIFYING_OPPS
].copy()

    qualified_avg_osr = qualified_players["osr"].mean()

    top_50_avg_osr = (
    qualified_players
    .sort_values("osr", ascending=False)
    .head(50)["osr"]
    .mean()
)

    top_10_avg_osr = (
    qualified_players
    .sort_values("osr", ascending=False)
    .head(10)["osr"]
    .mean()
)

    st.subheader("League OSR Benchmarks")

    bench1, bench2, bench3 = st.columns(3)

    bench1.metric(
    "Qualified Average",
    format_avg(qualified_avg_osr)
)

    bench2.metric(
    "Top 50 Average",
    format_avg(top_50_avg_osr)
)

    bench3.metric(
    "Top 10 Average",
    format_avg(top_10_avg_osr)
)

    st.caption(
    f"Benchmarks are based on qualified players with at least {QUALIFYING_OPPS} opportunities in {selected_season}."
)
    success_rules = pd.DataFrame([
        {"Outs": "0 or 1", "Base State": "Empty", "Success Condition": "Batter reaches base"},
        {"Outs": "0 or 1", "Base State": "Runner on 1st", "Success Condition": "Runner advances, no double play"},
        {"Outs": "0 or 1", "Base State": "Runner on 2nd", "Success Condition": "Runner advances"},
        {"Outs": "0 or 1", "Base State": "Runner on 3rd", "Success Condition": "Run scores"},
        {"Outs": "0 or 1", "Base State": "Runners on 1st & 2nd", "Success Condition": "Runner advances, no double play"},
        {"Outs": "0 or 1", "Base State": "Runners on 1st & 3rd", "Success Condition": "Run scores"},
        {"Outs": "0 or 1", "Base State": "Runners on 2nd & 3rd", "Success Condition": "Run scores"},
        {"Outs": "0 or 1", "Base State": "Bases Loaded", "Success Condition": "Run scores"},
        {"Outs": "2", "Base State": "Any", "Success Condition": "Batter reaches base"},
    ])

    st.subheader("How the Success Metric Works")
    st.dataframe(success_rules, use_container_width=True, hide_index=True)


elif page == "Player Leaderboard":
    st.sidebar.header("Filters")

    min_opportunities = st.sidebar.number_input(
        "Minimum Opportunities for Leaderboards",
        min_value=0,
        value=0,
        step=1
    )

    teams = ["All"] + sorted(all_plays["team"].dropna().unique().tolist())
    selected_team = st.sidebar.selectbox("Team", teams)

    players = ["All"] + sorted(all_plays["batter"].dropna().unique().tolist())
    selected_player = st.sidebar.selectbox("Player", players)

    selected_base_situation = st.sidebar.selectbox(
        "Base Situation Filter",
        options=list(base_situation_options.keys())
    )

    outs_options = ["All"] + sorted(all_plays["outs"].dropna().unique().tolist())
    selected_outs = st.sidebar.selectbox("Outs", outs_options)

    min_date = all_plays["date"].min().date()
    max_date = all_plays["date"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    filtered = all_plays.copy()
    filtered = filtered[filtered["base_state"].isin(base_situation_options[selected_base_situation])]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered["date"].dt.date >= start_date) &
            (filtered["date"].dt.date <= end_date)
        ]

    if selected_team != "All":
        filtered = filtered[filtered["team"] == selected_team]

    if selected_player != "All":
        filtered = filtered[filtered["batter"] == selected_player]

    if selected_outs != "All":
        filtered = filtered[filtered["outs"] == selected_outs]

    QUALIFYING_OPPS = 75

    player_totals = all_plays.groupby("batter").agg(
    opportunities=("success", "count"),
    successes=("success", "sum")
).reset_index()

    player_totals["osr"] = (
    player_totals["successes"] / player_totals["opportunities"]
)

    qualified_players = player_totals[
    player_totals["opportunities"] >= QUALIFYING_OPPS
].copy()

    qualified_avg_osr = qualified_players["osr"].mean()

    top_50_avg_osr = (
    qualified_players
    .sort_values("osr", ascending=False)
    .head(50)["osr"]
    .mean()
)

    top_10_avg_osr = (
    qualified_players
    .sort_values("osr", ascending=False)
    .head(10)["osr"]
    .mean()
)

    st.subheader("League OSR Benchmarks")

    bench1, bench2, bench3 = st.columns(3)

    bench1.metric(
    "Qualified Average",
    format_avg(qualified_avg_osr)
)

    bench2.metric(
    "Top 50 Average",
    format_avg(top_50_avg_osr)
)

    bench3.metric(
    "Top 10 Average",
    format_avg(top_10_avg_osr)
)

    st.caption(
    f"Benchmarks are based on qualified players with at least {QUALIFYING_OPPS} opportunities in {selected_season}."
)
    
    st.subheader("Player Leaderboard")
    st.dataframe(
    make_player_leaderboard(filtered, min_opportunities),
        use_container_width=True,
        height=900,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small")
        }
)
    
elif page == "Team Leaderboard":
    st.sidebar.header("Filters")

    min_opportunities = st.sidebar.number_input(
        "Minimum Opportunities for Leaderboards",
        min_value=0,
        value=0,
        step=1
    )

    selected_base_situation = st.sidebar.selectbox(
        "Base Situation Filter",
        options=list(base_situation_options.keys())
    )

    outs_options = ["All"] + sorted(all_plays["outs"].dropna().unique().tolist())
    selected_outs = st.sidebar.selectbox("Outs", outs_options)

    min_date = all_plays["date"].min().date()
    max_date = all_plays["date"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    filtered = all_plays.copy()
    filtered = filtered[filtered["base_state"].isin(base_situation_options[selected_base_situation])]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered["date"].dt.date >= start_date) &
            (filtered["date"].dt.date <= end_date)
        ]

    if selected_outs != "All":
        filtered = filtered[filtered["outs"] == selected_outs]

    st.subheader("Team Leaderboard")
    st.dataframe(
    make_team_leaderboard(filtered, min_opportunities),
    use_container_width=True,
    height=1090,
    column_config={
        "Logo": st.column_config.ImageColumn("Logo", width="small")
    }
)
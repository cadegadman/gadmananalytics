import requests
import pandas as pd

def get_base_state(on_1b, on_2b, on_3b):
    if not on_1b and not on_2b and not on_3b:
        return "empty"
    elif on_1b and not on_2b and not on_3b:
        return "1st"
    elif not on_1b and on_2b and not on_3b:
        return "2nd"
    elif not on_1b and not on_2b and on_3b:
        return "3rd"
    elif on_1b and on_2b and not on_3b:
        return "1st_2nd"
    elif on_1b and not on_2b and on_3b:
        return "1st_3rd"
    elif not on_1b and on_2b and on_3b:
        return "2nd_3rd"
    elif on_1b and on_2b and on_3b:
        return "loaded"

def read_event(event):
    batter_reached = False
    double_play = False

    if event in ["Single", "Double", "Triple", "Home Run", "Walk", "Hit By Pitch"]:
        batter_reached = True

    if event == "Grounded Into DP":
        double_play = True

    return batter_reached, double_play

def read_runner_movement(play):
    runner_advanced = False
    run_scored = False

    for runner in play["runners"]:
        movement = runner["movement"]
        start = movement["start"]
        end = movement["end"]

        if end == "score":
            run_scored = True

        if start in ["1B", "2B", "3B"] and end in ["2B", "3B", "score"]:
            runner_advanced = True

    return runner_advanced, run_scored

def real_success(row):
    if row["outs"] == 2:
        return row["batter_reached"]

    if row["base_state"] == "empty":
        return row["batter_reached"]
    elif row["base_state"] == "1st":
        return row["runner_advanced"] and not row["double_play"]
    elif row["base_state"] == "1st_2nd":
        return row["runner_advanced"] and not row["double_play"]
    elif row["base_state"] == "1st_3rd":
        return row["run_scored"]
    elif row["base_state"] == "2nd":
        return row["runner_advanced"]
    elif row["base_state"] == "3rd":
        return row["run_scored"]
    elif row["base_state"] == "2nd_3rd":
        return row["run_scored"]
    elif row["base_state"] == "loaded":
        return row["run_scored"]

    return False

def build_mlb_table_with_base_tracker(plays):
    rows = []

    on_1b = None
    on_2b = None
    on_3b = None
    current_inning = None
    current_half = None

    for play in plays:
        inning = play["about"]["inning"]
        half = play["about"]["halfInning"]

        if inning != current_inning or half != current_half:
            on_1b = None
            on_2b = None
            on_3b = None
            current_inning = inning
            current_half = half

        base_state = get_base_state(on_1b is not None, on_2b is not None, on_3b is not None)
        outs = play["playEvents"][-1]["count"]["outs"]

        batter = play["matchup"]["batter"]["fullName"]
        event = play["result"]["event"]
        description = play["result"]["description"]

        batter_reached, double_play = read_event(event)
        runner_advanced, run_scored = read_runner_movement(play)

        rows.append({
            "inning": inning,
            "half": half,
            "batter": batter,
            "outs": outs,
            "base_state": base_state,
            "event": event,
            "description": description,
            "batter_reached": batter_reached,
            "runner_advanced": runner_advanced,
            "run_scored": run_scored,
            "double_play": double_play
        })

        new_1b = None
        new_2b = None
        new_3b = None

        for runner in play["runners"]:
            name = runner["details"]["runner"]["fullName"]
            movement = runner["movement"]
            end = movement["end"]
            is_out = movement["isOut"]

            if not is_out:
                if end == "1B":
                    new_1b = name
                elif end == "2B":
                    new_2b = name
                elif end == "3B":
                    new_3b = name

        on_1b = new_1b
        on_2b = new_2b
        on_3b = new_3b

    return pd.DataFrame(rows)

def run_metric_for_game(game_pk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    game_data = requests.get(url).json()

    plays = game_data["liveData"]["plays"]["allPlays"]

    df = build_mlb_table_with_base_tracker(plays)
    df["success"] = df.apply(real_success, axis=1)

    leaderboard = df.groupby("batter").agg(
        opportunities=("success", "count"),
        successes=("success", "sum")
    )

    leaderboard["success_rate"] = leaderboard["successes"] / leaderboard["opportunities"]
    leaderboard = leaderboard.sort_values("success_rate", ascending=False)

    return df, leaderboard
from datetime import datetime, timedelta, date

def get_game_pks_for_date(date_string):
    schedule_url = (
        f"https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&gameType=R&date={date_string}"
    )

    schedule = requests.get(schedule_url).json()

    game_pks = []

    for date_info in schedule.get("dates", []):
        for game in date_info.get("games", []):
            game_pks.append(game["gamePk"])

    return game_pks


def get_dates_between(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []

    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates
def build_mlb_table_with_base_tracker(plays, away_team=None, home_team=None):
    rows = []

    on_1b = None
    on_2b = None
    on_3b = None
    current_inning = None
    current_half = None

    for play in plays:
        inning = play["about"]["inning"]
        half = play["about"]["halfInning"]

        if half == "top":
            team = away_team
            opponent = home_team
        else:
            team = home_team
            opponent = away_team

        if inning != current_inning or half != current_half:
            on_1b = None
            on_2b = None
            on_3b = None
            current_inning = inning
            current_half = half

        base_state = get_base_state(on_1b is not None, on_2b is not None, on_3b is not None)
        outs = play["playEvents"][-1]["count"]["outs"]

        batter = play["matchup"]["batter"]["fullName"]
        event = play["result"]["event"]
        description = play["result"]["description"]

        batter_reached, double_play = read_event(event)
        runner_advanced, run_scored = read_runner_movement(play)

        rows.append({
            "inning": inning,
            "half": half,
            "team": team,
            "opponent": opponent,
            "batter": batter,
            "outs": outs,
            "base_state": base_state,
            "event": event,
            "description": description,
            "batter_reached": batter_reached,
            "runner_advanced": runner_advanced,
            "run_scored": run_scored,
            "double_play": double_play
        })

        new_1b = None
        new_2b = None
        new_3b = None

        for runner in play["runners"]:
            name = runner["details"]["runner"]["fullName"]
            movement = runner["movement"]
            end = movement["end"]
            is_out = movement["isOut"]

            if not is_out:
                if end == "1B":
                    new_1b = name
                elif end == "2B":
                    new_2b = name
                elif end == "3B":
                    new_3b = name

        on_1b = new_1b
        on_2b = new_2b
        on_3b = new_3b

    return pd.DataFrame(rows)


def run_metric_for_game(game_pk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    game_data = requests.get(url).json()

    plays = game_data["liveData"]["plays"]["allPlays"]

    away_team = game_data["gameData"]["teams"]["away"]["name"]
    home_team = game_data["gameData"]["teams"]["home"]["name"]

    df = build_mlb_table_with_base_tracker(
        plays,
        away_team=away_team,
        home_team=home_team
    )

    df["success"] = df.apply(real_success, axis=1)

    leaderboard = df.groupby("batter").agg(
        opportunities=("success", "count"),
        successes=("success", "sum")
    )

    leaderboard["success_rate"] = leaderboard["successes"] / leaderboard["opportunities"]

    return df, leaderboard.sort_values("success_rate", ascending=False)


def run_metric(start_date, end_date):
    dates = get_dates_between(start_date, end_date)

    all_dfs = []

    for date_string in dates:
        print(f"Running {date_string}...")

        game_pks = get_game_pks_for_date(date_string)

        for game_pk in game_pks:
            try:
                df, leaderboard = run_metric_for_game(game_pk)
                df["date"] = date_string
                df["game_pk"] = game_pk
                all_dfs.append(df)

            except Exception as e:
                print(f"Skipped game {game_pk} because of error: {e}")

    full_df = pd.concat(all_dfs, ignore_index=True)

    player_leaderboard = full_df.groupby("batter").agg(
        opportunities=("success", "count"),
        successes=("success", "sum")
    )

    player_leaderboard["success_rate"] = (
        player_leaderboard["successes"] / player_leaderboard["opportunities"]
    )

    team_leaderboard = full_df.groupby("team").agg(
        opportunities=("success", "count"),
        successes=("success", "sum")
    )

    team_leaderboard["success_rate"] = (
        team_leaderboard["successes"] / team_leaderboard["opportunities"]
    )

    return (
        full_df,
        player_leaderboard.sort_values("success_rate", ascending=False),
        team_leaderboard.sort_values("success_rate", ascending=False)
    )
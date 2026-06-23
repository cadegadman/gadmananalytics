from pathlib import Path
from datetime import date
from metric_functions import run_metric

SEASONS = {
    2026: ("2026-03-01", date.today().strftime("%Y-%m-%d")),
    2025: ("2025-03-01", "2025-09-30"),
    2024: ("2024-03-01", "2024-09-30"),
    2023: ("2023-03-01", "2023-09-30"),
    2022: ("2022-03-01", "2022-09-30"),
    2021: ("2021-03-01", "2021-09-30"),
    2020: ("2020-07-01", "2020-09-30"),
    2019: ("2019-03-01", "2019-09-30"),
    2018: ("2018-03-01", "2018-09-30"),
    2017: ("2017-03-01", "2017-09-30"),
}

YEAR_TO_UPDATE = 2025

start_date, end_date = SEASONS[YEAR_TO_UPDATE]

print(f"Updating {YEAR_TO_UPDATE}: {start_date} to {end_date}")

full_df, player_leaderboard, team_leaderboard = run_metric(start_date, end_date)

season_dir = Path("data") / str(YEAR_TO_UPDATE)
season_dir.mkdir(parents=True, exist_ok=True)

full_df.to_csv(season_dir / "all_plays.csv", index=False)
player_leaderboard.to_csv(season_dir / "player_leaderboard.csv", index=False)
team_leaderboard.to_csv(season_dir / "team_leaderboard.csv", index=False)

print(f"{YEAR_TO_UPDATE} data updated successfully.")
print(f"Rows: {len(full_df)}")
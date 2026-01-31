import pandas as pd
import numpy as np


df = pd.read_csv("lmugamelog0127.csv")
LMU = "Loyola Marymount Lions"
# 1) Parse df dates robustly (handles 11/5/2025, 11/05/25, etc.)
df["Date_dt"] = pd.to_datetime(df["Date"], errors="coerce", infer_datetime_format=True).dt.normalize()

# 2) Build map as datetimes too
jersey_color_map = {
    '11/5/2025':'white',
    '11/9/2025': 'blue',
    '11/13/2025':'red',
    '11/21/2025':'black',
    '11/23/2025': 'white',
    '11/29/2025':'red',
    '12/5/2025':'gray',
    '12/13/2025':'black',
    '12/20/2025':'red',
    '12/21/2025':'white',
    '12/28/2025':'red',
    '12/30/2025':'black',
    '01/02/2026':'white',
    '01/04/2026':'blue',
    '01/08/2026':'red',
    '01/15/2026':'white',
    '01/17/2026':'black',
    '01/22/2026':'blue',
    '01/24/2026':'red',
}
jersey_map_dt = {pd.to_datetime(k).normalize(): v for k, v in jersey_color_map.items()}

# 3) Map
df["jerseycolor"] = df["Date_dt"].map(jersey_map_dt)


print(df[["Date", "Date_dt", "jerseycolor"]].sample(5))

# We want individual reports based on jersey color - stats we care about are points, assists, rebounds, efg%
# we want a team report - total points / oppoonents points / margin / didWin / efg% / opponent_efg%

players = ['Maya Hernandez','Jess Lawson','Andjela Matic']
dfplayers = df[df['Name'].isin(players)].copy()
# --- Player-by-jersey summaries ---
player_jersey = (
    dfplayers.groupby(["jerseycolor", "Name"], dropna=False)
      .agg(
          gp=("Date_dt", "nunique"),
          pts=("PTS", "sum"),
          ast=("AST", "sum"),
          reb=("REB", "sum"),
          fgm=("FGM", "sum"),
          fga=("FGA", "sum"),
          tpm=("3PM", "sum"),
          pts_mean = ("PTS", "mean"),
          ast_mean = ("AST", "mean"),
          reb_mean = ("REB", "mean"), 
      )
      .reset_index()
)

player_jersey["eFG%"] = (player_jersey["fgm"] + 0.5 * player_jersey["tpm"]) / player_jersey["fga"]
player_jersey["eFG%"] = player_jersey["eFG%"].round(3)
player_jersey["pts_mean"] = player_jersey["pts_mean"].round(2)
player_jersey["ast_mean"] = player_jersey["ast_mean"].round(2)
player_jersey["reb_mean"] = player_jersey["reb_mean"].round(2)

output = player_jersey.sort_values(["Name", "pts_mean"], ascending=[False, False])
output.to_csv("player_jersey_report3.csv", index=False)
# --- Team-by-jersey report (needs opponent points + opponent eFG inputs if you have them) ---
# ---- 3) Flag LMU vs opponent rows ----
df["is_lmu"] = df["Team"].eq(LMU)

# ---- 4) Build GAME-LEVEL table (this prevents double counting) ----
# key = one game. If you can play multiple games same date, include Opponent too.
game_key = ["Date_dt", "Opponent"]

games = (
    df.groupby(game_key, dropna=False)
      .agg(
          jerseycolor=("jerseycolor", "first"),
          didWin=("didWin", lambda s: s[df.loc[s.index, "is_lmu"]].max()),
          pts_for=("PTS", lambda s: s[df.loc[s.index, "is_lmu"]].sum()),
          pts_against=("PTS", lambda s: s[~df.loc[s.index, "is_lmu"]].sum()),
          # Team eFG% as weighted by FGA: (sum(FGM)+0.5*sum(3PM))/sum(FGA)
          lmu_fgm=("FGM", lambda s: s[df.loc[s.index, "is_lmu"]].sum()),
          lmu_tpm=("3PM", lambda s: s[df.loc[s.index, "is_lmu"]].sum()),
          lmu_fga=("FGA", lambda s: s[df.loc[s.index, "is_lmu"]].sum()),
          opp_fgm=("FGM", lambda s: s[~df.loc[s.index, "is_lmu"]].sum()),
          opp_tpm=("3PM", lambda s: s[~df.loc[s.index, "is_lmu"]].sum()),
          opp_fga=("FGA", lambda s: s[~df.loc[s.index, "is_lmu"]].sum()),
      )
      .reset_index()
)

games["margin"] = games["pts_for"] - games["pts_against"]
games["lmu_efg"] = np.where(games["lmu_fga"] > 0, (games["lmu_fgm"] + 0.5 * games["lmu_tpm"]) / games["lmu_fga"], np.nan)
games["opp_efg"] = np.where(games["opp_fga"] > 0, (games["opp_fgm"] + 0.5 * games["opp_tpm"]) / games["opp_fga"], np.nan)

# ---- Debug: see games missing jerseycolor ----
missing_colors = games[games["jerseycolor"].isna()][["Date_dt", "Opponent"]].drop_duplicates()
print("Games missing jerseycolor:\n", missing_colors)

# ---- 5) Jerseycolor TEAM report ----
team_report = (
    games.groupby("jerseycolor", dropna=False)
         .agg(
             games=("Date_dt", "nunique"),
             wins=("didWin", "sum"),
             pts_for=("pts_for", "sum"),
             pts_against=("pts_against", "sum"),
             avg_margin=("margin", "mean"),
             lmu_efg=("lmu_efg", "mean"),
             opp_efg=("opp_efg", "mean"),
         )
         .reset_index()
)

team_report["win%"] = (team_report["wins"] / team_report["games"]).round(3)
team_report['pts_for'] = (team_report['pts_for']/team_report["games"]).round(2)
team_report['pts_against'] = (team_report['pts_against']/team_report["games"]).round(2)
team_report["avg_margin"] = team_report["avg_margin"].round(2)
team_report["lmu_efg"] = team_report["lmu_efg"].round(3)
team_report["opp_efg"] = team_report["opp_efg"].round(3)

print(team_report.sort_values(["games","avg_margin"], ascending=[False,False]))

output = team_report.sort_values("games", ascending=False)
output.to_csv("team_jersey_report2.csv", index=False)

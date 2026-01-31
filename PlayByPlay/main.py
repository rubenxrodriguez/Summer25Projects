# main.py

import time
from collections import defaultdict

import pandas as pd
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By

from helpers import (
    build_roster_set,
    initial_lookup_map,
    infer_home_away_team_names_from_trs,
    extract_pbp_row,
    row_is_pbp_start,
    row_is_period_start,
    row_is_period_end,
    events_from_row,
    apply_stat_deltas,
    apply_misc_points,
    blank_miscline,
    extract_game_date_from_trs,
)
gameids = [6428682,6428674,6428675,6428676,
           6428677,6428679,6428680,6473992,6473993,6473994,6473995,6473996,6473997,6470260,6473998,6473999,6470265]
#gameids = [6428309,6428311,6428312]
links = [f"https://stats.ncaa.org/contests/{gid}/play_by_play" for gid in gameids]
LINK = "https://stats.ncaa.org/contests/6473998/play_by_play"


# -----------------------------
# USER INPUTS
# -----------------------------

PLAYER_INFO = [
    {"name": "Jess Lawson", "initial": "JL", "height": 67},
    {"name": "Mari Somvichian", "initial": "MS", "height": 64},
    {"name": "Andjela Matic", "initial": "AM", "height": 69},
    {"name": "Ivana Krajina", "initial": "IK", "height": 71},
    {"name": "Zawadi Ogot", "initial": "ZO", "height": 71},
    {"name": "Lova Lagerlid", "initial": "LL", "height": 73},
    {"name": "Carly Heidger", "initial": "CH", "height": 75},
    {"name": "Kayla Jones", "initial": "KJ", "height": 72},
    {"name": "Maya Hernandez", "initial": "MH", "height": 72},
    {"name": "Ana Milanovic", "initial": "AM7", "height": 75},
    {"name": "Paula Reus Piza", "initial": "PR", "height": 74},
    {"name": "Allison Clarke", "initial": "AC", "height": 71},
]



# -----------------------------
# Helpers for period labeling
# -----------------------------

def period_label(period_idx: int) -> str:
    if period_idx <= 4:
        return f"Q{period_idx}"
    return f"OT{period_idx-4}"

def period_length_sec(period_idx: int) -> int:
    # NCAA overtime periods are 5:00, regulation quarters are 10:00
    return 10 * 60 if period_idx <= 4 else 5 * 60

# -----------------------------
# Storage structures
# -----------------------------
# player_stats[period][team][player] -> statline dict
player_stats = defaultdict(lambda: defaultdict(dict))
# eog_stats[team][player] -> statline dict
eog_stats = defaultdict(dict)

# team_misc[period][team] -> misc dict
team_misc = defaultdict(lambda: defaultdict(blank_miscline))
# eog_misc[team] -> misc dict
eog_misc = defaultdict(blank_miscline)

# minutes tracked in SECONDS then converted to minutes
player_mins_sec = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))   # [period][team][player] -> sec
eog_mins_sec = defaultdict(lambda: defaultdict(int))                          # [team][player] -> sec


# -----------------------------
# Lineup/minutes state
# -----------------------------

on_court = defaultdict(set)   # team -> set(players)
last_time_sec = None
current_period = 0
parsing = False
period_ended = False


def allocate_minutes(team: str, elapsed_sec: int, period: str):
    """
    Allocate elapsed time to all players currently on-court for this team.
    """
    if elapsed_sec <= 0:
        return
    if len(on_court[team]) == 0:
        return

    for p in on_court[team]:
        player_mins_sec[period][team][p] += elapsed_sec
        eog_mins_sec[team][p] += elapsed_sec


def ensure_player_in_stats(period: str, team: str, player: str):
    if player not in player_stats[period][team]:
        player_stats[period][team][player] = {}  # deltas applier will initialize missing stats keys
    if player not in eog_stats[team]:
        eog_stats[team][player] = {}


def apply_event_to_storage(ev, period: str, lmu_roster_set, lmu_initial_map):
    """
    Applies stat deltas + misc points into period + EOG dicts.
    """
    team = ev.team
    player = ev.player

    # Team misc (only comes from shot events with tags in helpers)
    if ev.misc_points:
        apply_misc_points(team_misc[period][team], ev.misc_points)
        apply_misc_points(eog_misc[team], ev.misc_points)

    # Player/team stat deltas
    if ev.stat_deltas:
        if player is None:
            return
        # store team events under special player name "team" (optional)
        pkey = player

        ensure_player_in_stats(period, team, pkey)
        apply_stat_deltas(player_stats[period][team], pkey, ev.stat_deltas)
        apply_stat_deltas(eog_stats[team], pkey, ev.stat_deltas)


def update_on_court_from_sub(ev):
    """
    Uses substitution event to update on-court set.
    """
    if ev.player is None:
        return
    team = ev.team
    p = ev.player

    # If sub out, remove
    if ev.sub_direction == "out":
        # if not present, add then remove (means we at least acknowledge they were on court)
        if p in on_court[team]:
            on_court[team].remove(p)
        else:
            # unknown earlier state: we can ignore or treat as present then remove
            pass

    # If sub in, add
    elif ev.sub_direction == "in":
        on_court[team].add(p)


def add_player_to_on_court_if_needed(ev):
    """
    For any player event (shot, foul, rebound, turnover),
    assume they were on court (helps establish starters).
    """
    if ev.player and ev.player != "team":
        on_court[ev.team].add(ev.player)

# ---------------------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------------------------------

def main():
    global parsing, current_period, last_time_sec, period_ended

    lmu_roster_set = build_roster_set(PLAYER_INFO)
    lmu_initial_map = initial_lookup_map(PLAYER_INFO)

    driver = webdriver.Chrome()
    for LINK in links: 
        player_stats.clear()
        eog_stats.clear()
        team_misc.clear()
        eog_misc.clear()
        player_mins_sec.clear()
        eog_mins_sec.clear()
        on_court.clear()
        parsing = False
        current_period = 0
        last_time_sec = None
        period_ended = False
        time.sleep(1)
        driver.get(LINK)
        time.sleep(1.5)

        trs = driver.find_elements(By.TAG_NAME, "tr")
        game_date = extract_game_date_from_trs(trs)
        # infer team names from scoreboard header area
        away_team, home_team = infer_home_away_team_names_from_trs(trs)
        print("Away:", away_team, "| Home:", home_team)
        z = 0 
        # iterate through trs extracting pbp rows
        for tr in trs[8:]:
            row = extract_pbp_row(tr)
            z+=1
            #print("Processing row:", z)
            if row is None:
                continue

            # start parsing at game start / period start
            if not parsing:
                if row_is_pbp_start(row):
                    parsing = True
                    current_period = 1
                    last_time_sec = period_length_sec(current_period)
                    period_ended = False
                elif row.time_sec is not None and (row.away_desc or row.home_desc):
                    parsing = True
                    current_period = 1
                    last_time_sec = row.time_sec
                    period_ended = False
                else:
                    continue

            # detect new period start (explicit marker)
            if row_is_period_start(row):
                # if we were already in a period, reset clock
                if current_period == 0:
                    current_period = 1
                elif period_ended:
                    current_period += 1
                last_time_sec = period_length_sec(current_period)
                period = period_label(current_period)
                period_ended = False
                continue

            # detect new period start by clock reset to 10:00 without marker
            next_period_length = period_length_sec(current_period + 1)
            if row.time_sec == next_period_length and last_time_sec is not None and last_time_sec < next_period_length:
                current_period += 1
                last_time_sec = next_period_length
                period = period_label(current_period)
                period_ended = False
                continue

            # detect period end -> increment period counter for next start
            if row_is_period_end(row):
                if not period_ended:
                    period_ended = True
                    last_time_sec = row.time_sec
                continue

            period = period_label(current_period)

            # allocate minutes on time change (shared clock)
            if row.time_sec is not None:
                if last_time_sec is None:
                    last_time_sec = row.time_sec
                else:
                    if row.time_sec != last_time_sec:
                        elapsed = last_time_sec - row.time_sec
                        # allocate for both teams
                        allocate_minutes(away_team, elapsed, period)
                        allocate_minutes(home_team, elapsed, period)
                        last_time_sec = row.time_sec

            # parse events from row (away and/or home cell)
            evs = events_from_row(row, away_team, home_team)

            for ev in evs:
                # substitutions update lineup
                if ev.kind == "sub":
                    update_on_court_from_sub(ev)
                    continue

                # for player events, assume player is on court (helps starter inference)
                add_player_to_on_court_if_needed(ev)

                # apply stats/misc
                apply_event_to_storage(ev, period, lmu_roster_set, lmu_initial_map)

        

        # build output dataframes
        player_df = build_player_box_df(
            player_stats, eog_stats, player_mins_sec, eog_mins_sec,
            lmu_roster_set, lmu_initial_map,
            away_team, home_team
        )
        misc_df = build_team_misc_df(team_misc, eog_misc, away_team, home_team)
        team_df = build_team_box_df(player_df)
        player_df["game_date"] = game_date
        team_df["game_date"] = game_date
        misc_df["game_date"] = game_date

        team_df.to_csv(f"{game_date}_team_boxscore_by_period.csv", index=False)
        print("Wrote: team_boxscore_by_period.csv")
        player_df = player_df.sort_values(by=["team","player","period"], ascending = [True,True,True])
        player_df.to_csv(f"{game_date}_player_boxscore_by_period.csv", index=False)
        misc_df.to_csv(f"{game_date}_team_misc_by_period.csv", index=False)
        print("Wrote: player_boxscore_by_period.csv")
        print("Wrote: team_misc_by_period.csv")

def build_player_box_df(player_stats, eog_stats, player_mins_sec, eog_mins_sec,
                        lmu_roster_set, lmu_initial_map,
                        away_team, home_team):

    rows = []

    # period-level
    for period, teams in player_stats.items():
        for team, players in teams.items():
            isHome = (team == home_team)
            for player, statline in players.items():
                # merge minutes
                mins = player_mins_sec[period][team].get(player, 0) / 60.0

                # initial if LMU player
                initial = None
                if player in lmu_roster_set:
                    initial = lmu_initial_map.get(player)

                # compute REB
                oreb = statline.get("OREB", 0)
                dreb = statline.get("DREB", 0)
                reb = oreb + dreb

                row = {
                    "team": team,
                    "isHome": isHome,
                    "player": player,
                    "initial": initial,
                    "period": period,
                    "MIN": round(mins, 2),
                    "FGM": statline.get("FGM", 0),
                    "FGA": statline.get("FGA", 0),
                    "3PM": statline.get("3PM", 0),
                    "3PA": statline.get("3PA", 0),
                    "FTM": statline.get("FTM", 0),
                    "FTA": statline.get("FTA", 0),
                    "PTS": statline.get("PTS", 0),
                    "OREB": oreb,
                    "DREB": dreb,
                    "REB": reb,
                    "AST": statline.get("AST", 0),
                    "STL": statline.get("STL", 0),
                    "BLK": statline.get("BLK", 0),
                    "TO": statline.get("TO", 0),
                    "PF": statline.get("PF", 0),
                }
                rows.append(row)

    # EOG
    for team, players in eog_stats.items():
        isHome = (team == home_team)
        for player, statline in players.items():
            mins = eog_mins_sec[team].get(player, 0) / 60.0
            initial = None
            if player in lmu_roster_set:
                initial = lmu_initial_map.get(player)

            oreb = statline.get("OREB", 0)
            dreb = statline.get("DREB", 0)
            reb = oreb + dreb

            rows.append({
                "team": team,
                "isHome": isHome,
                "player": player,
                "initial": initial,
                "period": "EOG",
                "MIN": round(mins, 2),
                "FGM": statline.get("FGM", 0),
                "FGA": statline.get("FGA", 0),
                "3PM": statline.get("3PM", 0),
                "3PA": statline.get("3PA", 0),
                "FTM": statline.get("FTM", 0),
                "FTA": statline.get("FTA", 0),
                "PTS": statline.get("PTS", 0),
                "OREB": oreb,
                "DREB": dreb,
                "REB": reb,
                "AST": statline.get("AST", 0),
                "STL": statline.get("STL", 0),
                "BLK": statline.get("BLK", 0),
                "TO": statline.get("TO", 0),
                "PF": statline.get("PF", 0),
            })

    df = pd.DataFrame(rows)
    # Optional: sort nicely
    df = df.sort_values(["team", "period", "player"]).reset_index(drop=True)
    return df
TEAM_BOX_COLS = [
    "team","isHome","period",
    "MIN",
    "FGM","FGA",
    "3PM","3PA",
    "FTM","FTA",
    "PTS",
    "OREB","DREB","REB",
    "AST","STL","BLK",
    "TO","PF",
]
def build_team_box_df(player_df: pd.DataFrame) -> pd.DataFrame:
    # If you included "team" events as player == "team", exclude them from team totals
    df = player_df.copy()
    df = df[df["player"].ne("team")]

    team_cols = [
        "MIN","FGM","FGA","3PM","3PA","FTM","FTA","PTS",
        "OREB","DREB","REB","AST","STL","BLK","TO","PF"
    ]

    team_df = (
        df.groupby(["team","isHome","period"], as_index=False)[team_cols]
          .sum()
          .sort_values(["team","period"])
          .reset_index(drop=True)
    )
    return team_df


def build_team_misc_df(team_misc, eog_misc, away_team, home_team):
    rows = []
    for period, teams in team_misc.items():
        for team, misc in teams.items():
            rows.append({
                "team": team,
                "isHome": (team == home_team),
                "period": period,
                "PTS_POT": misc.get("PTS_POT", 0),
                "PTS_SCP": misc.get("PTS_SCP", 0),
                "PTS_FBP": misc.get("PTS_FBP", 0),
                "PTS_PIP": misc.get("PTS_PIP", 0),
            })

    for team, misc in eog_misc.items():
        rows.append({
            "team": team,
            "isHome": (team == home_team),
            "period": "EOG",
            "PTS_POT": misc.get("PTS_POT", 0),
            "PTS_SCP": misc.get("PTS_SCP", 0),
            "PTS_FBP": misc.get("PTS_FBP", 0),
            "PTS_PIP": misc.get("PTS_PIP", 0),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(["team", "period"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    main()

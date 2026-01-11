#!/usr/bin/env python3
"""
progression_builder.py

Build interval progression from multiple per-game lineup summary CSVs.

Key idea:
- NEVER sum derived columns (ratings, percentages, rel_*).
- For each interval:
    1) stack the games
    2) sum base counting stats by lineup
    3) recompute derived metrics + team-relative metrics for that interval
- Output one row per lineup per interval with interval metadata.

Assumptions:
- All files are for the same team (no team column).
- Filenames contain YYMMDD (first 6-digit chunk), e.g. lineup_summary_241228.csv
- Your input CSVs contain at least these base columns:
    lineup, secs, ptsScored, ptsAgst, netPts, oPoss, dPoss,
    fgm, fga, fgm3, fga3, fta, tov, orb,
    fgmAgst, fgaAgst, fgm3Agst, fga3Agst, ftaAgst, tovAgst, orbAgst

If your input uses slightly different names, update BASE_SUM_MAP below.
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

DATE_RE = re.compile(r"(\d{6})")  # YYMMDD


# ---------------------------
# Config: base stats to sum
# ---------------------------
# Output column name -> (input column name, aggregation)
BASE_SUM_MAP: Dict[str, Tuple[str, str]] = {
    "secs": ("secs", "sum"),
    "pts_for": ("ptsScored", "sum"),
    "pts_against": ("ptsAgst", "sum"),
    "net_pts": ("netPts", "sum"),
    "o_poss": ("oPoss", "sum"),
    "d_poss": ("dPoss", "sum"),
    "fgm": ("fgm", "sum"),
    "fga": ("fga", "sum"),
    "fgm3": ("fgm3", "sum"),
    "fga3": ("fga3", "sum"),
    "fta": ("fta", "sum"),
    "tov": ("tov", "sum"),
    "orb": ("orb", "sum"),
    "fgm_allowed": ("fgmAgst", "sum"),
    "fga_allowed": ("fgaAgst", "sum"),
    "fgm3_allowed": ("fgm3Agst", "sum"),
    "fga3_allowed": ("fga3Agst", "sum"),
    "fta_allowed": ("ftaAgst", "sum"),
    "tov_forced": ("tovAgst", "sum"),
    "orb_allowed": ("orbAgst", "sum"),
}


@dataclass(frozen=True)
class FileInfo:
    path: str
    yymmdd: str


def _extract_yymmdd(path: str) -> Optional[str]:
    name = os.path.basename(path)
    m = DATE_RE.search(name)
    return m.group(1) if m else None


def _discover_files(input_dir: str, pattern: str) -> List[FileInfo]:
    paths = glob.glob(os.path.join(input_dir, pattern))
    infos: List[FileInfo] = []
    for p in paths:
        yymmdd = _extract_yymmdd(p)
        if yymmdd:
            infos.append(FileInfo(path=p, yymmdd=yymmdd))
    infos.sort(key=lambda x: x.yymmdd)
    return infos


def _parse_intervals(intervals_str: str) -> List[int]:
    parts = [p.strip() for p in intervals_str.split(",") if p.strip()]
    if not parts:
        raise ValueError("intervals_str is empty. Example: '3,2,3'")
    intervals = [int(p) for p in parts]
    if any(i <= 0 for i in intervals):
        raise ValueError("All interval sizes must be positive integers.")
    return intervals


def _chunk_files(files: Sequence[FileInfo], intervals: Sequence[int]) -> List[List[FileInfo]]:
    need = sum(intervals)
    if len(files) != need:
        raise ValueError(
            f"Expected exactly {need} files for intervals {list(intervals)}, "
            f"but found {len(files)}.\n"
            f"Matched files (sorted): {[os.path.basename(f.path) for f in files]}"
        )
    chunks: List[List[FileInfo]] = []
    idx = 0
    for k in intervals:
        chunks.append(list(files[idx: idx + k]))
        idx += k
    return chunks


def _safe_div(n: float, d: float) -> float:
    if d is None or d == 0 or np.isnan(d):
        return 0.0
    return float(n) / float(d)


def _require_columns(df: pd.DataFrame, cols: Sequence[str], context: str = "") -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(
            f"Missing required columns {missing} {('in ' + context) if context else ''}.\n"
            f"Columns present: {list(df.columns)}"
        )


def _sum_base_by_lineup(big: pd.DataFrame, lineup_col: str = "lineup") -> pd.DataFrame:
    _require_columns(big, [lineup_col], context="input data")
    # Ensure required input columns exist
    needed_input_cols = [v[0] for v in BASE_SUM_MAP.values()]
    _require_columns(big, needed_input_cols, context="input data (base stats)")

    agg_spec = {out_col: (in_col, func) for out_col, (in_col, func) in BASE_SUM_MAP.items()}
    agg = (
        big.groupby(lineup_col, dropna=False)
           .agg(**agg_spec)
           .reset_index()
    )
    return agg


def _recompute_metrics(agg: pd.DataFrame) -> pd.DataFrame:
    """
    Given lineup-level summed base stats for an interval, recompute all derived and team-relative metrics.
    Mirrors your snippet.
    """
    # Derived basics
    agg["minutes"] = agg["secs"] / 60.0
    agg["poss_total"] = agg["o_poss"] + agg["d_poss"]
    agg["plus_minus"] = agg["net_pts"]

    # Percents / rates
    agg["o_eFG%"] = ((agg["fgm"] + 0.5 * agg["fgm3"]) / agg["fga"].replace(0, np.nan)).fillna(0)
    agg["d_eFG%"] = (
        (agg["fgm_allowed"] + 0.5 * agg["fgm3_allowed"]) / agg["fga_allowed"].replace(0, np.nan)
    ).fillna(0)

    agg["o_TOV%"] = (agg["tov"] / agg["o_poss"].replace(0, np.nan)).fillna(0)
    agg["d_TOV%"] = (agg["tov_forced"] / agg["d_poss"].replace(0, np.nan)).fillna(0)

    agg["o_orbR"] = (agg["orb"] / agg["o_poss"].replace(0, np.nan)).fillna(0)
    agg["d_orbR"] = (agg["orb_allowed"] / agg["d_poss"].replace(0, np.nan)).fillna(0)

    agg["o_ftaR"] = (agg["fta"] / agg["fga"].replace(0, np.nan)).fillna(0)
    agg["d_ftaR"] = (agg["fta_allowed"] / agg["fga_allowed"].replace(0, np.nan)).fillna(0)

    # Ratings
    agg["off_rtg"] = (agg["pts_for"] / agg["o_poss"].replace(0, np.nan) * 100).fillna(0)
    agg["def_rtg"] = (agg["pts_against"] / agg["d_poss"].replace(0, np.nan) * 100).fillna(0)
    agg["net_rtg"] = agg["off_rtg"] - agg["def_rtg"]

    agg["PM_p40"] = (
        agg["plus_minus"] * 40 / agg["minutes"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], 0).fillna(0)

    # Team totals for this interval (from the lineup table)
    team_plus_minus = float(agg["plus_minus"].sum())
    team_minutes = float(agg["minutes"].sum())
    team_o_poss = float(agg["o_poss"].sum())
    team_d_poss = float(agg["d_poss"].sum())
    team_pts_for = float(agg["pts_for"].sum())
    team_pts_against = float(agg["pts_against"].sum())

    team_off_rtg = _safe_div(team_pts_for, team_o_poss) * 100
    team_def_rtg = _safe_div(team_pts_against, team_d_poss) * 100
    team_net_rtg = team_off_rtg - team_def_rtg
    team_PM_p40 = _safe_div(team_plus_minus * 40, team_minutes)

    # Relative metrics
    agg["rel_PM_p40"] = agg["PM_p40"] - team_PM_p40
    agg["rel_off_rtg"] = agg["off_rtg"] - team_off_rtg
    agg["rel_def_rtg"] = agg["def_rtg"] - team_def_rtg
    agg["rel_net_rtg"] = agg["net_rtg"] - team_net_rtg

    # Store team context (same value for all rows)
    agg["team_minutes"] = team_minutes
    agg["team_plus_minus"] = team_plus_minus
    agg["team_pts_for"] = team_pts_for
    agg["team_pts_against"] = team_pts_against
    agg["team_o_poss"] = team_o_poss
    agg["team_d_poss"] = team_d_poss
    agg["team_poss_total"] = team_o_poss + team_d_poss
    agg["team_off_rtg"] = team_off_rtg
    agg["team_def_rtg"] = team_def_rtg
    agg["team_net_rtg"] = team_net_rtg
    agg["team_PM_p40"] = team_PM_p40

    # Round numeric columns
    numeric_cols = agg.select_dtypes(include=["float64", "int64", "int32", "float32"]).columns
    agg[numeric_cols] = agg[numeric_cols].round(3)

    return agg


def build_progression_csv(
    input_dir: str,
    pattern: str,
    intervals_str: str = "3,2,3",
    output_path: str = "progression.csv",
    lineup_col: str = "lineup",
) -> pd.DataFrame:
    """
    Main function to build progression.csv.

    Call:
      build_progression_csv("path/to/dir", "lineup_summary_*.csv", "3,2,3")

    Returns the DataFrame (and writes to output_path).
    """
    intervals = _parse_intervals(intervals_str)
    files = _discover_files(input_dir, pattern)
    if not files:
        raise FileNotFoundError(f"No files found in '{input_dir}' matching '{pattern}'.")

    chunks = _chunk_files(files, intervals)

    out_frames: List[pd.DataFrame] = []

    for interval_num, group in enumerate(chunks, start=1):
        dfs: List[pd.DataFrame] = []
        for fi in group:
            df = pd.read_csv(fi.path)
            df["game_yymmdd"] = fi.yymmdd  # provenance if you want it later
            dfs.append(df)

        big = pd.concat(dfs, ignore_index=True)

        # 1) sum base columns by lineup across the interval
        base = _sum_base_by_lineup(big, lineup_col=lineup_col)

        # 2) recompute all derived metrics for this interval
        agg = _recompute_metrics(base)

        # 3) interval metadata
        games = [fi.yymmdd for fi in group]
        agg["interval_num"] = interval_num
        agg["interval_games"] = ",".join(games)
        agg["interval_start"] = games[0]
        agg["interval_end"] = games[-1]

        front = ["interval_num", "interval_start", "interval_end", "interval_games", lineup_col]
        ordered = front + [c for c in agg.columns if c not in front]
        agg = agg[ordered]

        out_frames.append(agg)

    progression = pd.concat(out_frames, ignore_index=True)
    progression.to_csv(output_path, index=False)
    return progression


# Optional: "double click run" support (not required)
if __name__ == "__main__":
    build_progression_csv(
        input_dir="Lineup Data/Game Lineups",
        pattern="lineup_summary_*.csv",
        intervals_str="3,2,3",
        output_path="progression.csv",
    )
    print("Wrote progression.csv")

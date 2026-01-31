# helper_functions.py
# helpers.py

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Set, List, Tuple

import unidecode
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


# -----------------------------
# Canonical columns (for reference)
# -----------------------------

PLAYER_BOX_COLS = [
    "team", "player", "initial", "period",
    "MIN",
    "FGM", "FGA",
    "3PM", "3PA",
    "FTM", "FTA",
    "PTS",
    "OREB", "DREB", "REB",
    "AST", "STL", "BLK",
    "TO", "PF",
]

TEAM_MISC_COLS = ["team", "period", "PTS_POT", "PTS_SCP", "PTS_FBP", "PTS_PIP"]

STATS_BASE = ["FGM","FGA","3PM","3PA","FTM","FTA","PTS","OREB","DREB","AST","STL","BLK","TO","PF"]
MISC_TAGS = {"POT": "PTS_POT", "SCP": "PTS_SCP", "FBP": "PTS_FBP", "PIP": "PTS_PIP"}


# -----------------------------
# Normalization / roster helpers
# -----------------------------

def norm(s: str) -> str:
    s = unidecode.unidecode(str(s or ""))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def normalize_player_name(raw: str) -> str:
    s = norm(raw)
    # strip trailing punctuation
    s = re.sub(r"[,\.;:]+$", "", s).strip()
    return s

def build_roster_set(player_info: List[Dict]) -> Set[str]:
    out = set()
    for p in player_info:
        nm = normalize_player_name(p.get("name", ""))
        if nm:
            out.add(nm)
    return out

def initial_lookup_map(player_info: List[Dict]) -> Dict[str, str]:
    """
    map normalized full name -> initial for LMU players
    """
    out = {}
    for p in player_info:
        nm = normalize_player_name(p.get("name", ""))
        if nm:
            out[nm] = p.get("initial")
    return out


# -----------------------------
# Time / score parsing
# -----------------------------

TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2}):(\d{2})\s*$")
SCORE_RE = re.compile(r"^\s*(\d{1,3})-(\d{1,3})\s*$")

def parse_time_to_sec(t: str) -> Optional[int]:
    m = TIME_RE.match(norm(t))
    if not m:
        return None
    mm, ss, _ = m.groups()
    return int(mm) * 60 + int(ss)

def parse_score(score_cell: str) -> Optional[Tuple[int, int]]:
    m = SCORE_RE.match(norm(score_cell))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


# -----------------------------
# Row extraction from <tr><td>...
# -----------------------------

@dataclass
class PBPRow:
    time_str: str
    time_sec: Optional[int]
    away_desc: str
    home_desc: str
    score_str: str
    score: Optional[Tuple[int, int]]
    raw_cells: List[str] = field(default_factory=list)

def extract_pbp_row(tr: WebElement) -> Optional[PBPRow]:
    """
    Extract a PBP row from a <tr> by reading its <td> cells.
    Returns None if it doesn't look like a PBP line.
    """
    tds = tr.find_elements(By.TAG_NAME, "td")
    if not tds or len(tds) < 3:
        return None

    cells = [norm(td.text) for td in tds]
    # Commonly 4 cols: time, away, score, home
    # Some rows may have slightly different col counts; try to map best-effort.
    time_str = cells[0] if len(cells) >= 1 else ""
    away_desc = cells[1] if len(cells) >= 2 else ""
    score_str = cells[2] if len(cells) >= 3 else ""
    home_desc = cells[3] if len(cells) >= 4 else ""

    # Heuristic: must have parsable time OR contain "period"/"game" markers
    time_sec = parse_time_to_sec(time_str)
    looks_like_marker = ("period" in away_desc) or ("period" in home_desc) or ("game start" in away_desc) or ("game start" in home_desc)
    if time_sec is None and not looks_like_marker:
        return None

    return PBPRow(
        time_str=time_str,
        time_sec=time_sec,
        away_desc=away_desc,
        home_desc=home_desc,
        score_str=score_str,
        score=parse_score(score_str),
        raw_cells=cells,
    )


def row_is_pbp_start(row: PBPRow) -> bool:
    """
    We start parsing when we hit 'game start' or 'period start' in either description cell.
    """
    a = row.away_desc
    h = row.home_desc
    return ("game start" in a) or ("game start" in h) or ("period start" in a) or ("period start" in h)


# -----------------------------
# Event parsing
# -----------------------------

PLAYER_PREFIX_RE = re.compile(r"^\s*([^,]+),\s*(.*)$")

TAG_MAP = {
    "fromturnover": "POT",
    "fastbreak": "FBP",
    "secondchance": "SCP",
    "pointsinthepaint": "PIP",
}

def extract_tags(body: str) -> Set[str]:
    b = norm(body)
    out = set()
    for raw, std in TAG_MAP.items():
        if raw in b:
            out.add(std)
    return out

def split_player_and_body(desc: str) -> Tuple[Optional[str], str]:
    d = norm(desc)
    m = PLAYER_PREFIX_RE.match(d)
    if not m:
        return None, d
    player = normalize_player_name(m.group(1))
    body = m.group(2).strip()
    return player, body

def is_sub(body: str) -> bool:
    b = norm(body)
    return "substitution in" in b or "substitution out" in b

def parse_sub(player: Optional[str], body: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Given body containing substitution in/out, return (out_player, in_player).
    Your real data matches exactly: '<name>, substitution in/out'
    """
    b = norm(body)
    if not player:
        return None, None
    if "substitution out" in b:
        return player, None
    if "substitution in" in b:
        return None, player
    return None, None

def is_turnover(body: str) -> bool:
    b = norm(body)
    return ("turnover" in b) and ("fromturnover" not in b)

def is_foul(body: str) -> bool:
    return "foul" in norm(body)

def is_rebound(body: str) -> bool:
    return "rebound" in norm(body)

def rebound_kind(body: str) -> Optional[str]:
    b = norm(body)
    if "rebound offensive" in b:
        return "OREB"
    if "rebound defensive" in b:
        return "DREB"
    return None

def is_made(body: str) -> bool:
    b = norm(body)
    return (" made" in b) or b.endswith(" made")

def is_missed(body: str) -> bool:
    b = norm(body)
    return (" missed" in b) or b.endswith(" missed")

def infer_points_if_made(body: str) -> int:
    b = norm(body)
    if not is_made(b):
        return 0
    if "freethrow" in b or "free throw" in b:
        return 1
    if "3pt" in b:
        return 3
    if "2pt" in b:
        return 2
    return 2

def classify_team_by_cell(is_away_cell: bool, away_team_label: str, home_team_label: str) -> str:
    return away_team_label if is_away_cell else home_team_label


@dataclass
class Event:
    time_sec: Optional[int]
    team: str                 # 'away'/'home' labels OR your mapped labels
    player: Optional[str]     # normalized name OR 'team' OR None
    kind: str                 # 'sub','shot','turnover','rebound','foul','other'
    stat_deltas: Dict[str, int] = field(default_factory=dict)
    misc_points: Dict[str, int] = field(default_factory=dict)   # e.g. {"PTS_POT":2}
    tags: Set[str] = field(default_factory=set)
    raw_desc: str = ""


def parse_desc_to_event(
    time_sec: Optional[int],
    desc: str,
    team_label: str,
) -> Event:
    """
    Parse a SINGLE description cell (away OR home) into an Event with stat deltas.
    Note: MIN is NOT handled here (that comes from clock deltas + lineup state).
    """
    player, body = split_player_and_body(desc)
    tags = extract_tags(body)

    # Sub
    if is_sub(body):
        # keep player and kind; main loop uses this to update on-court state
        return Event(time_sec, team_label, player, "sub", tags=tags, raw_desc=desc)

    # Turnover
    if is_turnover(body):
        deltas = {"TO": 1}
        return Event(time_sec, team_label, player or "team", "turnover", stat_deltas=deltas, tags=tags, raw_desc=desc)

    # Rebound
    if is_rebound(body):
        rk = rebound_kind(body)
        deltas = {}
        if rk == "OREB":
            deltas["OREB"] = 1
        elif rk == "DREB":
            deltas["DREB"] = 1
        return Event(time_sec, team_label, player or "team", "rebound", stat_deltas=deltas, tags=tags, raw_desc=desc)

    # Foul (simple PF counter)
    if is_foul(body):
        deltas = {"PF": 1}
        return Event(time_sec, team_label, player or "team", "foul", stat_deltas=deltas, tags=tags, raw_desc=desc)

    # Shot / FT (counts FGA/FGM/3PA/3PM/FTA/FTM/PTS)
    b = norm(body)
    if ("2pt" in b) or ("3pt" in b) or ("freethrow" in b) or ("free throw" in b):
        deltas: Dict[str, int] = {}
        misc_points: Dict[str, int] = {}

        made = is_made(b)
        pts = infer_points_if_made(b)

        # Free throws
        if "freethrow" in b or "free throw" in b:
            deltas["FTA"] = 1
            if made:
                deltas["FTM"] = 1
                deltas["PTS"] = 1

        # 3PT
        elif "3pt" in b:
            deltas["FGA"] = 1
            deltas["3PA"] = 1
            if made:
                deltas["FGM"] = 1
                deltas["3PM"] = 1
                deltas["PTS"] = pts  # 3

        # 2PT
        elif "2pt" in b:
            deltas["FGA"] = 1
            if made:
                deltas["FGM"] = 1
                deltas["PTS"] = pts  # 2

        # misc scoring tags only on made baskets
        if made and pts > 0:
            for tag in tags:
                col = MISC_TAGS.get(tag)
                if col:
                    misc_points[col] = misc_points.get(col, 0) + pts

        return Event(time_sec, team_label, player, "shot", stat_deltas=deltas, misc_points=misc_points, tags=tags, raw_desc=desc)

    return Event(time_sec, team_label, player, "other", tags=tags, raw_desc=desc)


def events_from_row(
    row: PBPRow,
    away_team_label: str,
    home_team_label: str,
) -> List[Event]:
    """
    A PBP row may contain:
      - away event only
      - home event only
      - occasionally both (rare)
    Returns list of Events.
    """
    out: List[Event] = []
    if row.away_desc:
        out.append(parse_desc_to_event(row.time_sec, row.away_desc, away_team_label))
    if row.home_desc:
        out.append(parse_desc_to_event(row.time_sec, row.home_desc, home_team_label))
    return out


# -----------------------------
# Stat dict utilities (for main loop)
# -----------------------------

def blank_statline() -> Dict[str, int]:
    d = {k: 0 for k in STATS_BASE}
    # REB is derived later, but you can store it too if you prefer
    return d

def ensure_player(stats: Dict[str, Dict[str, int]], player: str) -> None:
    if player not in stats:
        stats[player] = blank_statline()

def apply_stat_deltas(stats: Dict[str, Dict[str, int]], player: str, deltas: Dict[str, int]) -> None:
    ensure_player(stats, player)
    for k, v in deltas.items():
        stats[player][k] = stats[player].get(k, 0) + int(v)

def apply_misc_points(misc: Dict[str, int], misc_points: Dict[str, int]) -> None:
    for col, pts in misc_points.items():
        misc[col] = misc.get(col, 0) + int(pts)

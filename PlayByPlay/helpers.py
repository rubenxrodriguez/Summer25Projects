# helpers.py

from __future__ import annotations
import time
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Set, List, Tuple

import unidecode
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


# -----------------------------
# Canonical columns
# -----------------------------

PLAYER_BOX_COLS = [
    "team", "isHome", "player", "initial", "period",
    "MIN",
    "FGM", "FGA",
    "3PM", "3PA",
    "FTM", "FTA",
    "PTS",
    "OREB", "DREB", "REB",
    "AST", "STL", "BLK",
    "TO", "PF",
]

TEAM_MISC_COLS = ["team", "isHome", "period", "PTS_POT", "PTS_SCP", "PTS_FBP", "PTS_PIP"]

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
    out = {}
    for p in player_info:
        nm = normalize_player_name(p.get("name", ""))
        if nm:
            out[nm] = p.get("initial")
    return out


# -----------------------------
# Team name parsing (scoreboard header rows)
# -----------------------------


DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")

def extract_game_date_from_trs(trs) -> str:
    """
    Scans early <tr> rows for a date like MM/DD/YYYY.
    Returns date as YYYYMMDD string (safe for filenames).
    Falls back to 'unknown_date' if not found.
    """
    for tr in trs[:15]:  # header area only
        txt = tr.text.strip()
        m = DATE_RE.search(txt)
        if m:
            raw_date = m.group(1)
            try:
                dt = datetime.strptime(raw_date, "%m/%d/%Y")
                return dt.strftime("%Y%m%d")
            except ValueError:
                pass
    return "unknown_date"
def tokens_until_numeric(s: str) -> str:
    toks = norm(s).split()
    out = []
    for tok in toks:
        if tok.isdigit():
            break
        out.append(tok)
    return " ".join(out).strip()

def clean_team_name(name: str) -> str:
    """
    Best-effort cleanup:
      'lmu (ca)' -> 'LMU'
      'san diego' -> 'San Diego'
      "saint mary's" -> "Saint Mary's"
    """
    n = norm(name)
    # remove parenthetical chunks
    n = re.sub(r"\([^)]*\)", "", n).strip()
    n = re.sub(r"\s+", " ", n).strip()
    # special-case lmu
    if n.startswith("lmu"):
        return "LMU"
    # title case (keeps apostrophes reasonably)
    return " ".join([w.capitalize() if w not in {"u", "st"} else w.upper() for w in n.split()])


def infer_home_away_team_names_from_trs(trs: List[WebElement]) -> Tuple[str, str]:
    """
    Looks for the two scoreboard lines like:
      'portland 16 16 19 17 68'
      'lmu (ca) 15 16 18 28 77'
    Returns (away_team_name, home_team_name) cleaned.
    """
    candidates = []
    for tr in trs[:40]:
        txt = norm(tr.text)
        # Heuristic: contains several numbers and starts with letters
        nums = re.findall(r"\b\d{1,3}\b", txt)
        if len(nums) >= 4 and not re.search(r"\b(am|pm)\b", txt) and "/" not in txt:
            team_part = tokens_until_numeric(txt)
            if team_part and len(team_part.split()) <= 4:  # avoid weird long lines
                candidates.append(team_part)

    # pick first two distinct
    distinct = []
    for c in candidates:
        if c not in distinct:
            distinct.append(c)
        if len(distinct) >= 2:
            break

    if len(distinct) < 2:
        # fallback
        return ("Away", "Home")

    away = clean_team_name(distinct[0])
    home = clean_team_name(distinct[1])
    return away, home


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
    NCAA PBP is typically 4 tds: time | away | score | home
    """
    #time.sleep(.7)
    tds = tr.find_elements(By.TAG_NAME, "td")
    if not tds:
        return None
    #time.sleep(.7)
    cells = [norm(td.text) for td in tds]
    time_str = cells[0] if len(cells) >= 1 else ""
    away_desc = cells[1] if len(cells) >= 2 else ""
    score_str = cells[2] if len(cells) >= 3 else ""
    home_desc = cells[3] if len(cells) >= 4 else ""

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
    return ("game start" in row.away_desc) or ("game start" in row.home_desc) or ("period start" in row.away_desc) or ("period start" in row.home_desc)

def row_is_period_start(row: PBPRow) -> bool:
    return ("period start" in row.away_desc) or ("period start" in row.home_desc) or ("game start" in row.away_desc) or ("game start" in row.home_desc)

def row_is_period_end(row: PBPRow) -> bool:
    return ("period end" in row.away_desc) or ("period end" in row.home_desc)


# -----------------------------
# Event parsing
# -----------------------------

PLAYER_PREFIX_RE = re.compile(r"^\s*([^,]+),\s*(.*)$")

TAG_MAP = {
    "fromturnover": "POT",
    "fastbreak": "FBP",
    "2ndchance": "SCP",
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

def sub_dir(body: str) -> Optional[str]:
    b = norm(body)
    if "substitution out" in b:
        return "out"
    if "substitution in" in b:
        return "in"
    return None

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


@dataclass
class Event:
    time_sec: Optional[int]
    team: str                  # team name string (e.g., "LMU", "San Diego")
    isHome: bool
    player: Optional[str]      # normalized name OR 'team'
    kind: str                  # 'sub','shot','turnover','rebound','foul','other'
    stat_deltas: Dict[str, int] = field(default_factory=dict)
    misc_points: Dict[str, int] = field(default_factory=dict)   # e.g. {"PTS_POT":2}
    sub_direction: Optional[str] = None                          # 'in'/'out'
    raw_desc: str = ""


def parse_desc_to_event(
    time_sec: Optional[int],
    desc: str,
    team_name: str,
    isHome: bool,
) -> Event:
    """
    Parse a SINGLE description cell (away OR home) into an Event with deltas.
    MIN is handled by clock delta allocation, not here.
    """
    player, body = split_player_and_body(desc)
    tags = extract_tags(body)

    # Sub
    if is_sub(body):
        return Event(time_sec, team_name, isHome, player, "sub", sub_direction=sub_dir(body), raw_desc=desc)

    # Turnover
    if is_turnover(body):
        deltas = {"TO": 1}
        return Event(time_sec, team_name, isHome, player or "team", "turnover", stat_deltas=deltas, raw_desc=desc)

    # Rebound
    if is_rebound(body):
        rk = rebound_kind(body)
        deltas = {}
        if rk == "OREB":
            deltas["OREB"] = 1
        elif rk == "DREB":
            deltas["DREB"] = 1
        return Event(time_sec, team_name, isHome, player or "team", "rebound", stat_deltas=deltas, raw_desc=desc)

    # Foul
    if is_foul(body):
        deltas = {"PF": 1}
        return Event(time_sec, team_name, isHome, player or "team", "foul", stat_deltas=deltas, raw_desc=desc)

    # Shot / FT
    b = norm(body)
    if ("2pt" in b) or ("3pt" in b) or ("freethrow" in b) or ("free throw" in b):
        deltas: Dict[str, int] = {}
        misc_points: Dict[str, int] = {}

        made = is_made(b)
        pts = infer_points_if_made(b)

        if "freethrow" in b or "free throw" in b:
            deltas["FTA"] = 1
            if made:
                deltas["FTM"] = 1
                deltas["PTS"] = 1
        elif "3pt" in b:
            deltas["FGA"] = 1
            deltas["3PA"] = 1
            if made:
                deltas["FGM"] = 1
                deltas["3PM"] = 1
                deltas["PTS"] = 3
        elif "2pt" in b:
            deltas["FGA"] = 1
            if made:
                deltas["FGM"] = 1
                deltas["PTS"] = 2

        # misc scoring tags only on made baskets
        if made and pts > 0:
            for raw_tag, col in MISC_TAGS.items():
                # tags set contains POT/SCP/FBP/PIP
                pass
            for tag in tags:
                col = MISC_TAGS.get(tag)
                if col:
                    misc_points[col] = misc_points.get(col, 0) + pts

        return Event(time_sec, team_name, isHome, player, "shot", stat_deltas=deltas, misc_points=misc_points, raw_desc=desc)

    return Event(time_sec, team_name, isHome, player, "other", raw_desc=desc)


def events_from_row(row: PBPRow, away_team: str, home_team: str) -> List[Event]:
    out: List[Event] = []
    if row.away_desc:
        out.append(parse_desc_to_event(row.time_sec, row.away_desc, away_team, False))
    if row.home_desc:
        out.append(parse_desc_to_event(row.time_sec, row.home_desc, home_team, True))
    return out


# -----------------------------
# Stat dict utilities
# -----------------------------

def blank_statline() -> Dict[str, int]:
    return {k: 0 for k in STATS_BASE}

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

def blank_miscline() -> Dict[str, int]:
    return {c: 0 for c in ["PTS_POT","PTS_SCP","PTS_FBP","PTS_PIP"]}

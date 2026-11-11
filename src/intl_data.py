"""Free International Football Data Engine (Historical Results, ESPN, Open-Meteo, Budget Ledger).

Implements quantitative sports modeling data practices specifically for International Football:
1. 49,940+ historical international results (martj42/international_results, CC0) for
   time-decayed Empirical Bayes ratings, competition scoring environment drift, and true H2H.
2. ESPN public soccer API (no key required) for real Past 5 match logs, real boxscore
   corners/shots won & conceded, DraftKings open/close odds, and lineup availability.
3. Open-Meteo free weather API (no key required) for kickoff rain/wind goal-tempo modifiers.
4. Strict canonical team name normalization and persistent API credit budget ledger.
"""

import csv
import json
import math
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT_DIR / "src" / "cache"
HIST_CSV_PATH = CACHE_DIR / "intl_results.csv"
ESPN_CACHE_DIR = CACHE_DIR / "espn"
WEATHER_CACHE_PATH = CACHE_DIR / "weather_cache.json"
BUDGET_PATH = CACHE_DIR / "api_budget.json"

INTL_RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# Canonical team aliases across Odds API, ESPN, martj42/international_results, and UI
TEAM_ALIASES: Dict[str, str] = {
    "czechia": "Czech Republic",
    "czech republic": "Czech Republic",
    "turkey": "Turkey",
    "türkiye": "Turkey",
    "turkiye": "Turkey",
    "bosnia & herzegovina": "Bosnia and Herzegovina",
    "bosnia and herzegovina": "Bosnia and Herzegovina",
    "bosnia-herzegovina": "Bosnia and Herzegovina",
    "republic of ireland": "Republic of Ireland",
    "ireland": "Republic of Ireland",
    "northern ireland": "Northern Ireland",
    "n. ireland": "Northern Ireland",
    "north macedonia": "North Macedonia",
    "fyr macedonia": "North Macedonia",
    "usa": "United States",
    "united states": "United States",
    "korea republic": "South Korea",
    "south korea": "South Korea",
    "korea dpr": "North Korea",
    "côte d'ivoire": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "ivory coast": "Ivory Coast",
    "iran": "Iran",
    "ir iran": "Iran",
    "holland": "Netherlands",
    "the netherlands": "Netherlands",
    "netherlands": "Netherlands",
    "great britain": "England",
    "cabo verde": "Cape Verde",
    "cape verde": "Cape Verde",
    "dr congo": "DR Congo",
    "congo dr": "DR Congo",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "china pr": "China",
    "china": "China",
}

TEAM_CODES: Dict[str, str] = {
    "France": "FRA", "Germany": "GER", "Spain": "ESP", "England": "ENG", "Italy": "ITA",
    "Portugal": "POR", "Belgium": "BEL", "Netherlands": "NED", "Croatia": "CRO", "Denmark": "DEN",
    "Switzerland": "SUI", "Austria": "AUT", "Turkey": "TUR", "Poland": "POL", "Serbia": "SRB",
    "Romania": "ROU", "Norway": "NOR", "Sweden": "SWE", "Hungary": "HUN", "Czech Republic": "CZE",
    "Scotland": "SCO", "Wales": "WAL", "Slovakia": "SVK", "Slovenia": "SVN", "Greece": "GRE",
    "Georgia": "GEO", "Albania": "ALB", "Ukraine": "UKR", "Israel": "ISR", "Northern Ireland": "NIR",
    "Iceland": "ISL", "Bulgaria": "BUL", "Cyprus": "CYP", "Kosovo": "KOS", "Belarus": "BLR",
    "Armenia": "ARM", "Luxembourg": "LUX", "Kazakhstan": "KAZ", "Azerbaijan": "AZE", "Estonia": "EST",
    "Faroe Islands": "FRO", "Moldova": "MDA", "Gibraltar": "GIB", "San Marino": "SMR",
    "Liechtenstein": "LIE", "Andorra": "AND", "Malta": "MLT", "Finland": "FIN",
    "Bosnia and Herzegovina": "BIH", "Republic of Ireland": "IRL", "Montenegro": "MNE",
    "Latvia": "LVA", "North Macedonia": "MKD", "Lithuania": "LTU", "Brazil": "BRA",
    "Argentina": "ARG", "Uruguay": "URU", "Colombia": "COL", "Ecuador": "ECU", "Chile": "CHI",
    "Paraguay": "PAR", "Peru": "PER", "Venezuela": "VEN", "Bolivia": "BOL",
    "United States": "USA", "Mexico": "MEX", "Canada": "CAN", "Japan": "JPN",
    "South Korea": "KOR", "Australia": "AUS", "Saudi Arabia": "KSA", "Morocco": "MAR",
    "Senegal": "SEN", "Nigeria": "NGA", "Egypt": "EGY", "Ivory Coast": "CIV",
}


def normalize_team_name(name: str) -> str:
    """Normalizes international national team names across data providers."""
    if not name:
        return ""
    cleaned = " ".join(name.strip().split())
    alias = TEAM_ALIASES.get(cleaned.lower())
    return alias if alias else cleaned


def to_team_code(name: str) -> str:
    canon = normalize_team_name(name)
    if canon in TEAM_CODES:
        return TEAM_CODES[canon]
    letters = "".join(c for c in canon.upper() if c.isalpha())
    return (letters[:3] if len(letters) >= 3 else "INT")


def american_to_decimal(odds_val: Any) -> Optional[float]:
    """Converts American moneyline ('+135', '-130', 135) to European decimal odds."""
    if odds_val is None:
        return None
    if isinstance(odds_val, (int, float)):
        v = float(odds_val)
        if 1.01 <= v <= 50.0 and v != 100 and abs(v) < 95:
            # Already decimal? Only treat <95 and positive non-moneyline if decimal explicitly passed,
            # though ESPN moneylines are always <= -100 or >= +100.
            return round(v, 3)
        if v >= 100:
            return round(1.0 + (v / 100.0), 3)
        if v <= -100:
            return round(1.0 + (100.0 / abs(v)), 3)
        return None

    s = str(odds_val).strip().upper()
    if s in ("EVEN", "EV", "PK"):
        return 2.0
    try:
        v = float(s.replace("+", ""))
        if v >= 100:
            return round(1.0 + (v / 100.0), 3)
        if v <= -100:
            return round(1.0 + (100.0 / abs(v)), 3)
    except ValueError:
        return None
    return None


def _ensure_cache_dirs():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ESPN_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def update_api_budget(provider: str, used_delta: int = 1, remaining: Optional[int] = None, used_total: Optional[int] = None):
    """Tracks API usage in src/cache/api_budget.json without leaking secrets."""
    _ensure_cache_dirs()
    budget = {}
    if BUDGET_PATH.exists():
        try:
            budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
        except Exception:
            budget = {}
    entry = budget.get(provider, {"calls": 0})
    entry["calls"] = entry.get("calls", 0) + used_delta
    entry["last_call_utc"] = datetime.now(timezone.utc).isoformat()
    if remaining is not None:
        entry["remaining"] = remaining
    if used_total is not None:
        entry["used_total"] = used_total
    budget[provider] = entry
    BUDGET_PATH.write_text(json.dumps(budget, indent=2), encoding="utf-8")


def get_api_budget(provider: str) -> Dict[str, Any]:
    if not BUDGET_PATH.exists():
        return {}
    try:
        return json.loads(BUDGET_PATH.read_text(encoding="utf-8")).get(provider, {})
    except Exception:
        return {}


def ensure_historical_csv(max_age_hours: float = 24.0) -> Optional[Path]:
    """Downloads/caches martj42/international_results CSV; falls back gracefully offline."""
    _ensure_cache_dirs()
    if HIST_CSV_PATH.exists():
        age_hours = (time.time() - HIST_CSV_PATH.stat().st_mtime) / 3600.0
        if age_hours < max_age_hours and HIST_CSV_PATH.stat().st_size > 100_000:
            return HIST_CSV_PATH

    try:
        resp = requests.get(INTL_RESULTS_URL, timeout=15)
        if resp.status_code == 200 and len(resp.text) > 100_000:
            HIST_CSV_PATH.write_text(resp.text, encoding="utf-8")
            update_api_budget("github_intl_results", used_delta=1)
            return HIST_CSV_PATH
    except Exception:
        pass

    return HIST_CSV_PATH if HIST_CSV_PATH.exists() else None


def _tournament_weight(tournament: str) -> float:
    t = (tournament or "").lower()
    if "world cup" in t and "qualification" not in t:
        return 1.50
    if "uefa euro" in t or "copa américa" in t or "copa america" in t or "african cup" in t:
        return 1.40
    if "nations league" in t or "qualification" in t:
        return 1.20
    if "friendly" in t:
        return 0.65
    return 1.0


def load_historical_intel(as_of_date: Optional[str] = None, lookback_years: int = 5) -> Dict[str, Any]:
    """Builds empirical time-decayed team strengths, tournament scoring baselines, and H2H index.

    If as_of_date ('YYYY-MM-DD') is supplied, filters strictly to matches BEFORE as_of_date
    for zero-leakage walk-forward backtesting!
    """
    csv_path = ensure_historical_csv()
    if not csv_path or not csv_path.exists():
        return {"team_stats": {}, "h2h": {}, "comp_env": {}, "team_form": {}, "global_gpg": 1.32}

    ref_dt = (
        datetime.strptime(as_of_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if as_of_date
        else datetime.now(timezone.utc)
    )
    min_year = ref_dt.year - lookback_years
    half_life_days = 540.0
    decay_k = math.log(2.0) / half_life_days

    team_counts: Dict[str, int] = {}
    team_recent: Dict[str, List[Dict[str, Any]]] = {}
    comp_acc: Dict[str, Dict[str, float]] = {}
    h2h_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    parsed_matches: List[Tuple[str, str, int, int, float, bool]] = []

    global_goals = 0.0
    global_weight = 0.0
    home_g_sum = 0.0
    away_g_sum = 0.0

    with csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_str = row.get("date", "")
            if not d_str or len(d_str) < 10:
                continue
            yr = int(d_str[:4])
            if yr < min_year:
                continue
            if as_of_date and d_str >= as_of_date:
                continue

            try:
                hs = int(row["home_score"])
                as_ = int(row["away_score"])
                m_dt = datetime.strptime(d_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError, KeyError):
                continue

            days_ago = max(0.0, (ref_dt - m_dt).total_seconds() / 86400.0)
            tourn = row.get("tournament", "International")
            w = math.exp(-decay_k * days_ago) * _tournament_weight(tourn)

            h_team = normalize_team_name(row.get("home_team", ""))
            a_team = normalize_team_name(row.get("away_team", ""))
            neutral = str(row.get("neutral", "")).strip().upper() == "TRUE"

            parsed_matches.append((h_team, a_team, hs, as_, w, neutral))

            global_goals += w * (hs + as_) / 2.0
            global_weight += w
            if not neutral:
                home_g_sum += w * hs
                away_g_sum += w * as_

            # Competition environment drift
            c_rec = comp_acc.setdefault(tourn, {"goals_sum": 0.0, "w_sum": 0.0, "count": 0})
            c_rec["goals_sum"] += w * (hs + as_) / 2.0
            c_rec["w_sum"] += w
            c_rec["count"] += 1

            for tm, gf, ga in ((h_team, hs, as_), (a_team, as_, hs)):
                team_counts[tm] = team_counts.get(tm, 0) + 1
                team_recent.setdefault(tm, []).append({
                    "date": d_str[:10],
                    "opp": a_team if tm == h_team else h_team,
                    "is_home": (tm == h_team and not neutral),
                    "gf": gf,
                    "ga": ga,
                    "res": "W" if gf > ga else ("D" if gf == ga else "L"),
                    "score": f"{gf}:{ga}",
                    "btts": (gf > 0 and ga > 0),
                    "tourn": tourn,
                })

            pair = tuple(sorted([h_team, a_team]))
            h2h_map.setdefault(pair, []).append({
                "date": d_str[:10],
                "home": h_team,
                "away": a_team,
                "hs": hs,
                "as": as_,
                "tourn": tourn,
            })

    global_gpg = (global_goals / global_weight) if global_weight > 0 else 1.32
    home_ratio = math.sqrt(home_g_sum / max(1e-6, away_g_sum)) if away_g_sum > 0 else 1.12
    home_ratio = max(1.02, min(1.28, home_ratio))

    # Iterative opponent-adjusted attack & defense strengths with Empirical Bayes shrinkage
    teams = list(team_counts.keys())
    att = {tm: 1.0 for tm in teams}
    dfn = {tm: 1.0 for tm in teams}
    prior_k = 5.0

    for _ in range(6):
        num_a = {tm: prior_k * global_gpg for tm in teams}
        den_a = {tm: prior_k * global_gpg for tm in teams}
        num_d = {tm: prior_k * global_gpg for tm in teams}
        den_d = {tm: prior_k * global_gpg for tm in teams}
        for ht, at, hs, as_, w, neut in parsed_matches:
            ha_h = 1.0 if neut else home_ratio
            ha_a = 1.0 if neut else (1.0 / home_ratio)
            num_a[ht] += w * hs
            den_a[ht] += w * global_gpg * ha_h * dfn[at]
            num_d[ht] += w * as_
            den_d[ht] += w * global_gpg * ha_a * att[at]
            num_a[at] += w * as_
            den_a[at] += w * global_gpg * ha_a * dfn[ht]
            num_d[at] += w * hs
            den_d[at] += w * global_gpg * ha_h * att[ht]
        for tm in teams:
            att[tm] = max(0.25, min(2.60, num_a[tm] / den_a[tm]))
            dfn[tm] = max(0.30, min(2.60, num_d[tm] / den_d[tm]))

    team_ratings: Dict[str, Tuple[float, float, int]] = {
        tm: (round(att[tm], 4), round(dfn[tm], 4), team_counts[tm]) for tm in teams
    }

    # Recent Past 5 sorted newest first
    team_form: Dict[str, List[Dict[str, Any]]] = {}
    for tm, matches in team_recent.items():
        team_form[tm] = matches[-5:][::-1]

    comp_env: Dict[str, float] = {}
    for cname, rec in comp_acc.items():
        shrunk_gpg = (rec["goals_sum"] + 25.0 * global_gpg) / (rec["w_sum"] + 25.0)
        comp_env[cname] = round(shrunk_gpg, 4)

    return {
        "team_ratings": team_ratings,
        "h2h": h2h_map,
        "comp_env": comp_env,
        "team_form": team_form,
        "global_gpg": round(global_gpg, 4),
        "home_ratio": round(home_ratio, 4),
    }


def get_real_h2h(h2h_map: Dict[Tuple[str, str], List[Dict[str, Any]]], home: str, away: str, limit: int = 10) -> Dict[str, Any]:
    h_canon = normalize_team_name(home)
    a_canon = normalize_team_name(away)
    pair = tuple(sorted([h_canon, a_canon]))
    meetings = h2h_map.get(pair, [])[-limit:]
    h_wins, draws, a_wins = 0, 0, 0
    recent = []
    for m in meetings[::-1]:
        if m["hs"] == m["as"]:
            draws += 1
        elif (m["home"] == h_canon and m["hs"] > m["as"]) or (m["away"] == h_canon and m["as"] > m["hs"]):
            h_wins += 1
        else:
            a_wins += 1
        recent.append(m)
    return {
        "hWins": h_wins,
        "draws": draws,
        "aWins": a_wins,
        "total": len(meetings),
        "recent": recent[:5],
    }


def _cached_espn_get(url: str, cache_name: str, max_age_minutes: float = 120.0) -> Optional[Dict[str, Any]]:
    """Polite cached ESPN fetcher. Never permanently caches empty responses."""
    _ensure_cache_dirs()
    cache_file = ESPN_CACHE_DIR / f"{cache_name}.json"
    if cache_file.exists():
        age_mins = (time.time() - cache_file.stat().st_mtime) / 60.0
        if age_mins < max_age_minutes:
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                if data:
                    return data
            except Exception:
                pass

    try:
        time.sleep(0.12)
        resp = requests.get(url, timeout=12)
        update_api_budget("espn_soccer", used_delta=1)
        if resp.status_code == 200:
            data = resp.json()
            # Never cache empty event payloads forever
            if data and (data.get("events") or data.get("boxscore") or data.get("lastFiveGames") or data.get("header")):
                cache_file.write_text(json.dumps(data), encoding="utf-8")
            return data
    except Exception:
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def fetch_espn_scoreboard(league_slug: str, date_yyyymmdd: str) -> List[Dict[str, Any]]:
    url = f"{ESPN_BASE}/{league_slug}/scoreboard?dates={date_yyyymmdd}"
    data = _cached_espn_get(url, f"sb_{league_slug}_{date_yyyymmdd}", max_age_minutes=30.0)
    return data.get("events", []) if data else []


def extract_espn_odds_from_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts open and current DraftKings moneyline & totals odds from ESPN summary."""
    picks = summary.get("pickcenter") or summary.get("odds") or []
    if not picks:
        return {}
    p0 = picks[0]
    ml = p0.get("moneyline", {})
    tot = p0.get("total", {})

    def _ml_dec(side_key: str, state_key: str) -> Optional[float]:
        return american_to_decimal(ml.get(side_key, {}).get(state_key, {}).get("odds"))

    h_close = _ml_dec("home", "close")
    d_close = _ml_dec("draw", "close")
    a_close = _ml_dec("away", "close")
    h_open = _ml_dec("home", "open")
    d_open = _ml_dec("draw", "open")
    a_open = _ml_dec("away", "open")

    total_line = p0.get("overUnder")
    if total_line is None:
        raw_line = str(tot.get("over", {}).get("close", {}).get("line", "")).lstrip("oOuU")
        try:
            total_line = float(raw_line) if raw_line else None
        except ValueError:
            total_line = None

    over_close = american_to_decimal(tot.get("over", {}).get("close", {}).get("odds"))
    under_close = american_to_decimal(tot.get("under", {}).get("close", {}).get("odds"))
    over_open = american_to_decimal(tot.get("over", {}).get("open", {}).get("odds"))
    under_open = american_to_decimal(tot.get("under", {}).get("open", {}).get("odds"))

    return {
        "provider": p0.get("provider", {}).get("name", "DraftKings"),
        "h_close": h_close, "d_close": d_close, "a_close": a_close,
        "h_open": h_open, "d_open": d_open, "a_open": a_open,
        "total_line": float(total_line) if total_line is not None else None,
        "over_close": over_close, "under_close": under_close,
        "over_open": over_open, "under_open": under_open,
    }


def extract_espn_team_intelligence(summary: Dict[str, Any], home_name: str, away_name: str) -> Dict[str, Any]:
    """Extracts real Past 5 form, rolling corners won/conceded, shots, and lineup status."""
    l5_blocks = summary.get("lastFiveGames") or []
    result: Dict[str, Any] = {
        "home_matches": [],
        "away_matches": [],
        "home_corners_won": [],
        "home_corners_conc": [],
        "away_corners_won": [],
        "away_corners_conc": [],
        "home_shots": [],
        "away_shots": [],
        "starters_announced": False,
    }

    rosters = summary.get("rosters") or []
    if len(rosters) >= 2 and sum(len(r.get("roster", [])) for r in rosters) >= 22:
        result["starters_announced"] = True

    h_canon = normalize_team_name(home_name).lower()
    a_canon = normalize_team_name(away_name).lower()

    for block in l5_blocks:
        t_name = normalize_team_name(block.get("team", {}).get("displayName", "")).lower()
        side = None
        if t_name == h_canon:
            side = "home"
        elif t_name == a_canon:
            side = "away"
        elif block.get("displayOrder") == 1 and not result["home_matches"]:
            side = "home"
        elif block.get("displayOrder") == 2 and not result["away_matches"]:
            side = "away"
        if not side:
            continue

        parsed_matches = []
        for ev in (block.get("events") or [])[:5]:
            ev_id = ev.get("id")
            opp_full = normalize_team_name(ev.get("opponent", {}).get("displayName", "Opponent"))
            opp_code = to_team_code(opp_full)
            score_raw = str(ev.get("score", "0-0")).replace("-", ":")
            parts = score_raw.split(":")
            btts = False
            if len(parts) == 2:
                try:
                    btts = int(parts[0].strip()) > 0 and int(parts[1].strip()) > 0
                except ValueError:
                    btts = False

            res_ch = str(ev.get("gameResult", "D")).upper()[:1]
            if res_ch not in ("W", "D", "L"):
                res_ch = "D"

            parsed_matches.append({
                "res": res_ch,
                "isHome": ev.get("atVs", "vs") == "vs",
                "opp": opp_code,
                "oppFull": opp_full,
                "score": score_raw,
                "btts": btts,
                "date": str(ev.get("gameDate", ""))[:10],
                "comp": ev.get("leagueName", ""),
            })

            # Fetch cached completed boxscore stats for real corner/shot averages
            if ev_id:
                past_sum = _cached_espn_get(
                    f"{ESPN_BASE}/all/summary?event={ev_id}",
                    f"past_ev_{ev_id}",
                    max_age_minutes=60 * 24 * 30,  # Final completed match stats never change
                )
                if past_sum and past_sum.get("boxscore", {}).get("teams"):
                    bs_teams = past_sum["boxscore"]["teams"]
                    if len(bs_teams) == 2:
                        my_idx = 0
                        for idx, bt in enumerate(bs_teams):
                            bt_name = normalize_team_name(bt.get("team", {}).get("displayName", "")).lower()
                            if bt_name == t_name:
                                my_idx = idx
                                break
                        opp_idx = 1 - my_idx

                        def _stat_val(team_obj: Dict[str, Any], stat_name: str) -> Optional[float]:
                            for st in team_obj.get("statistics", []):
                                if st.get("name") == stat_name:
                                    try:
                                        return float(st.get("displayValue", "0").replace("%", ""))
                                    except ValueError:
                                        return None
                            return None

                        c_won = _stat_val(bs_teams[my_idx], "wonCorners")
                        c_conc = _stat_val(bs_teams[opp_idx], "wonCorners")
                        shots = _stat_val(bs_teams[my_idx], "totalShots")
                        # Ignore unrecorded 0-0 stats (typical when minor friendly lacked live opta feed)
                        if (c_won or 0) + (c_conc or 0) > 0:
                            result[f"{side}_corners_won"].append(c_won)
                            result[f"{side}_corners_conc"].append(c_conc)
                        if shots and shots > 0:
                            result[f"{side}_shots"].append(shots)

        result[f"{side}_matches"] = parsed_matches

    return result


def fetch_kickoff_weather(city: str, country: str, kickoff_iso: str) -> Dict[str, Any]:
    """Fetches kickoff precipitation & wind forecast using free Open-Meteo API (no key required)."""
    if not city or not kickoff_iso:
        return {}
    _ensure_cache_dirs()
    w_cache = {}
    if WEATHER_CACHE_PATH.exists():
        try:
            w_cache = json.loads(WEATHER_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            w_cache = {}

    cache_key = f"{city}|{country}|{kickoff_iso[:13]}"
    if cache_key in w_cache:
        return w_cache[cache_key]

    try:
        q = urllib.parse.quote(city)
        geo_resp = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json",
            timeout=8,
        )
        update_api_budget("open_meteo", used_delta=1)
        if geo_resp.status_code != 200:
            return {}
        results = geo_resp.json().get("results") or []
        if not results:
            return {}

        match_loc = results[0]
        c_low = (country or "").lower()
        for r in results:
            if c_low and c_low in str(r.get("country", "")).lower():
                match_loc = r
                break

        lat, lon = match_loc["latitude"], match_loc["longitude"]
        dt_part = kickoff_iso[:10]
        hr_part = kickoff_iso[:13] + ":00"

        fc_resp = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,precipitation,windspeed_10m&start_date={dt_part}&end_date={dt_part}&timezone=UTC",
            timeout=8,
        )
        if fc_resp.status_code != 200:
            return {}
        hourly = fc_resp.json().get("hourly", {})
        times = hourly.get("time", [])
        idx = times.index(hr_part) if hr_part in times else 0
        out = {
            "city": city,
            "temp_c": (hourly.get("temperature_2m") or [15.0])[idx],
            "precip_mm": (hourly.get("precipitation") or [0.0])[idx],
            "wind_kmh": (hourly.get("windspeed_10m") or [10.0])[idx],
        }
        w_cache[cache_key] = out
        WEATHER_CACHE_PATH.write_text(json.dumps(w_cache, indent=2), encoding="utf-8")
        return out
    except Exception:
        return {}

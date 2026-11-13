"""Sync live international soccer fixtures and generate calibrated predictions.

Applies validated quantitative modeling methods to International Football:
1. Dynamic opponent-adjusted Dixon-Coles ratings + competition scoring drift from 49k+ matches.
2. Multiplicative devigging of live sharp market consensus (The Odds API + ESPN DraftKings).
3. Market-anchored simulation: blends statistical lambdas with market-implied (lam, mu) before
   deriving coherent joint probabilities across 1X2, Exact Score, Goal Total, and BTTS.
4. Over-dispersed Negative Binomial tail model for Corners using Empirical Bayes shrunk team
   boxscore corner logs from ESPN's free API.
5. Honest zero-clamped +EV vs real bookmaker prices + pre-publish Sanity Gate.
"""

import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.calibration import (
    apply_shrinkage,
    empirical_bayes_mean,
    multiplicative_devig,
    neg_binom_over_prob,
    sanity_gate,
)
from src.intl_data import (
    CACHE_DIR,
    extract_espn_odds_from_summary,
    extract_espn_team_intelligence,
    fetch_apifootball_fixtures_by_date,
    fetch_apifootball_odds_and_lineups,
    fetch_espn_scoreboard,
    fetch_kickoff_weather,
    get_real_h2h,
    load_historical_intel,
    normalize_team_name,
    to_team_code,
    update_api_budget,
    _cached_espn_get,
    ESPN_BASE,
)
from src.v2_ledger import grade_finished_v2_matches, record_pre_kickoff_snapshots
from src.ml_engine import predict_match_lambdas_ml, train_ml_model

load_dotenv()

ODDS_CACHE_PATH = CACHE_DIR / "odds_api_cache.json"


def poisson_pmf(k: int, lam: float) -> float:
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def dixon_coles_tau(x: int, y: int, lam: float, mu: float, rho: float = -0.08) -> float:
    if x == 0 and y == 0:
        return max(0.0, 1.0 - lam * mu * rho)
    if x == 0 and y == 1:
        return max(0.0, 1.0 + lam * rho)
    if x == 1 and y == 0:
        return max(0.0, 1.0 + mu * rho)
    if x == 1 and y == 1:
        return max(0.0, 1.0 - rho)
    return 1.0


def apply_game_state_lead_decay(
    scores: Dict[Tuple[int, int], float],
    lam: float,
    mu: float,
) -> Dict[Tuple[int, int], float]:
    """Models tournament game-state lead decay.

    When a team establishes a significant expected lead (differential > 0.75 xG),
    late in the match the leading side drops pressing intensity and conserves stamina,
    while the trailing side pushes recklessly for a late consolation goal.
    This shifts probability mass from clean sheets (x, 0) to consolation scorelines (x, 1) for x >= 2
    (and symmetrically for away leads).
    Critically, 1X2 probabilities remain invariant since for x >= 2, both (x, 0) and (x, 1) are Home Wins.
    """
    adjusted = dict(scores)
    diff = lam - mu
    if diff > 0.75:
        shift_rate = min(0.18, 0.05 * (diff - 0.75))
        for x in range(2, 8):
            if (x, 0) in adjusted and (x, 1) in adjusted:
                leak = adjusted[(x, 0)] * shift_rate
                adjusted[(x, 0)] -= leak
                adjusted[(x, 1)] += leak
    elif diff < -0.75:
        shift_rate = min(0.18, 0.05 * (-diff - 0.75))
        for y in range(2, 8):
            if (0, y) in adjusted and (1, y) in adjusted:
                leak = adjusted[(0, y)] * shift_rate
                adjusted[(0, y)] -= leak
                adjusted[(1, y)] += leak

    tot = sum(adjusted.values())
    return {k: v / tot for k, v in adjusted.items()} if tot > 0 else adjusted


def evaluate_dixon_coles_grid(lam: float, mu: float, rho: float = -0.08) -> Dict[str, Any]:
    """Computes normalized joint probabilities across 1X2, O/U 2.5, BTTS, and Exact Score."""
    raw_scores: Dict[Tuple[int, int], float] = {}

    for x in range(8):
        px = poisson_pmf(x, lam)
        for y in range(8):
            py = poisson_pmf(y, mu)
            prob = dixon_coles_tau(x, y, lam, mu, rho) * px * py
            raw_scores[(x, y)] = prob

    scores = apply_game_state_lead_decay(raw_scores, lam, mu)

    p_h = p_d = p_a = p_ov = p_btts = 0.0
    for (x, y), prob in scores.items():
        if x > y:
            p_h += prob
        elif x == y:
            p_d += prob
        else:
            p_a += prob
        if x + y >= 3:
            p_ov += prob
        if x > 0 and y > 0:
            p_btts += prob

    total_mass = max(1e-9, p_h + p_d + p_a)
    p_h /= total_mass
    p_d /= total_mass
    p_a /= total_mass
    p_ov /= total_mass
    p_btts /= total_mass

    norm_scores = {k: v / total_mass for k, v in scores.items()}
    ranked_scores = sorted(norm_scores.items(), key=lambda item: item[1], reverse=True)
    top_sc, top_p = ranked_scores[0]
    sec_sc, sec_p = ranked_scores[1]

    return {
        "p_h": p_h,
        "p_d": p_d,
        "p_a": p_a,
        "p_over": p_ov,
        "p_under": 1.0 - p_ov,
        "p_btts_yes": p_btts,
        "p_btts_no": 1.0 - p_btts,
        "pred_score": f"{top_sc[0]}-{top_sc[1]}",
        "pred_score_prob": top_p,
        "sec_score": f"{sec_sc[0]}-{sec_sc[1]}",
        "sec_score_prob": sec_p,
        "scores": norm_scores,
    }


def _score_matches_constraints(
    x: int,
    y: int,
    res_sel: Optional[str] = None,
    gt_sel: Optional[str] = None,
    btts_sel: Optional[str] = None,
) -> bool:
    """Returns True if an exact scoreline (x, y) satisfies all active directional constraints."""
    if res_sel == "Home Win" and not (x > y):
        return False
    if res_sel == "Draw" and not (x == y):
        return False
    if res_sel == "Away Win" and not (x < y):
        return False
    if gt_sel:
        m_l = re.search(r"(\d+(?:\.\d+)?)", gt_sel)
        line = float(m_l.group(1)) if m_l else 2.5
        if gt_sel.startswith("Over") and (x + y <= line):
            return False
        if gt_sel.startswith("Under") and (x + y >= line):
            return False
    if btts_sel == "BTTS Yes" and not (x > 0 and y > 0):
        return False
    if btts_sel == "BTTS No" and not (x == 0 or y == 0):
        return False
    return True


def _pass_pick(pick_obj: Dict[str, Any], reason: str) -> None:
    """Converts a directional pick in-place into a clean PASS preserving diagnostic metadata."""
    sel = pick_obj.get("selection")
    if sel and "NO PICK" not in str(sel):
        pick_obj["target_selection"] = sel
    pick_obj["pick"] = "NO PICK (PASS)"
    pick_obj["selection"] = "NO PICK (PASS)"
    pick_obj["composite_score"] = 0.0
    pick_obj["is_pass"] = True
    pick_obj["reason"] = reason


def resolve_cross_market_contradictions(
    scores: Dict[Tuple[int, int], float],
    result_pick: Dict[str, Any],
    goal_pick: Dict[str, Any],
    btts_pick: Dict[str, Any],
) -> None:
    """Ensures active (1X2, Goal Total, BTTS) picks have >=1 mathematically valid exact scoreline.

    If active picks form an impossible regime (e.g. Home Win + Under 2.5 + BTTS Yes, or
    Draw + Over 2.5 + BTTS No), passes the lowest-conviction active leg until coherent.
    """
    while True:
        res_sel = None if result_pick.get("is_pass") else result_pick.get("selection")
        gt_sel = None if goal_pick.get("is_pass") else goal_pick.get("selection")
        btts_sel = None if btts_pick.get("is_pass") else btts_pick.get("selection")

        has_valid = any(
            _score_matches_constraints(x, y, res_sel, gt_sel, btts_sel)
            for (x, y) in scores
        )
        if has_valid:
            return

        # Compare excess confidence above each market's coin-flip/uniform baseline (0.50 for binary, 1/3 for 1X2)
        active_legs: List[Tuple[float, Dict[str, Any]]] = []
        if not goal_pick.get("is_pass") and goal_pick.get("prob") is not None:
            active_legs.append((float(goal_pick["prob"]) - 0.50, goal_pick))
        if not btts_pick.get("is_pass") and btts_pick.get("prob") is not None:
            active_legs.append((float(btts_pick["prob"]) - 0.50, btts_pick))
        if not result_pick.get("is_pass") and result_pick.get("prob") is not None:
            active_legs.append((float(result_pick["prob"]) - (1.0 / 3.0), result_pick))

        if not active_legs:
            return
        active_legs.sort(key=lambda item: item[0])
        _pass_pick(active_legs[0][1], "Cross-Market Coherence Pass (No Valid Exact Score)")


def select_coherent_scores(
    scores: Dict[Tuple[int, int], float],
    result_pick: Dict[str, Any],
    goal_pick: Dict[str, Any],
    btts_pick: Dict[str, Any],
) -> Tuple[Tuple[int, int], float, Tuple[int, int], float, Tuple[int, int], float]:
    """Selects top 3 predicted exact scores consistent with active model picks."""
    res_sel = None if result_pick.get("is_pass") else result_pick.get("selection")
    gt_sel = None if goal_pick.get("is_pass") else goal_pick.get("selection")
    btts_sel = None if btts_pick.get("is_pass") else btts_pick.get("selection")

    ranked_all = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    coherent = [
        (sc, p) for sc, p in ranked_all
        if _score_matches_constraints(sc[0], sc[1], res_sel, gt_sel, btts_sel)
    ]
    if not coherent:
        coherent = ranked_all

    top_sc, top_p = coherent[0]
    sec_sc, sec_p = coherent[1] if len(coherent) >= 2 else (top_sc, top_p)
    thi_sc, thi_p = coherent[2] if len(coherent) >= 3 else (sec_sc, sec_p)

    if sec_sc == top_sc and len(ranked_all) > 1:
        fallback = [s for s in ranked_all if s[0] != top_sc]
        if fallback:
            sec_sc, sec_p = fallback[0]
            thi_sc, thi_p = fallback[1] if len(fallback) > 1 else (sec_sc, sec_p)

    return top_sc, top_p, sec_sc, sec_p, thi_sc, thi_p


def _fast_1x2_ov(lam: float, mu: float, total_line: float = 2.5) -> Tuple[float, float, float, float]:
    """Lightweight evaluation on 7x7 grid used during market lambda inversion."""
    p_h = p_d = p_a = p_ov = p_push = 0.0
    for x in range(7):
        px = poisson_pmf(x, lam)
        for y in range(7):
            py = poisson_pmf(y, mu)
            prob = dixon_coles_tau(x, y, lam, mu) * px * py
            if x > y:
                p_h += prob
            elif x == y:
                p_d += prob
            else:
                p_a += prob
            tot = x + y
            if abs(total_line - round(total_line)) < 1e-6:
                line_int = int(round(total_line))
                if tot > line_int:
                    p_ov += prob
                elif tot == line_int:
                    p_push += prob
            elif tot > total_line:
                p_ov += prob
    s = max(1e-9, p_h + p_d + p_a)
    ov_den = max(1e-9, s - p_push)
    return p_h / s, p_d / s, p_a / s, p_ov / ov_den


def invert_market_lambdas(
    mkt_ph: float,
    mkt_pd: float,
    mkt_pa: float,
    mkt_pov: Optional[float] = None,
    total_line: float = 2.5,
) -> Tuple[float, float]:
    """Finds (lam, mu) whose Dixon-Coles distribution matches devigged sharp market odds."""
    best_lam, best_mu = 1.35, 1.15
    best_loss = 1e9

    # Coarse grid search over realistic goal intensities
    for i in range(4, 36):
        lam = i * 0.10
        for j in range(3, 32):
            mu = j * 0.10
            ph, pd, pa, pov = _fast_1x2_ov(lam, mu, total_line)
            loss = (ph - mkt_ph) ** 2 + (pd - mkt_pd) ** 2 + (pa - mkt_pa) ** 2
            if mkt_pov is not None:
                loss += 1.2 * (pov - mkt_pov) ** 2
            if loss < best_loss:
                best_loss = loss
                best_lam, best_mu = lam, mu

    # Fine coordinate refinement around best coarse point
    for step in (0.04, 0.015):
        improved = True
        while improved:
            improved = False
            for dl in (-step, 0.0, step):
                for dm in (-step, 0.0, step):
                    if dl == 0.0 and dm == 0.0:
                        continue
                    nl = max(0.25, best_lam + dl)
                    nm = max(0.20, best_mu + dm)
                    ph, pd, pa, pov = _fast_1x2_ov(nl, nm, total_line)
                    loss = (ph - mkt_ph) ** 2 + (pd - mkt_pd) ** 2 + (pa - mkt_pa) ** 2
                    if mkt_pov is not None:
                        loss += 1.2 * (pov - mkt_pov) ** 2
                    if loss + 1e-8 < best_loss:
                        best_loss = loss
                        best_lam, best_mu = nl, nm
                        improved = True

    return round(best_lam, 3), round(best_mu, 3)


def invert_corners_mu(mkt_p_cor_over: float, line: float = 9.5) -> float:
    """Inverts devigged market Over probability into Negative Binomial expected total corners (Var = 2*mu)."""
    lo, hi = 5.5, 16.5
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if neg_binom_over_prob(mid, 2.0 * mid, line) < mkt_p_cor_over:
            lo = mid
        else:
            hi = mid
    return round(0.5 * (lo + hi), 2)


def _fetch_odds_api_cached(odds_key: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Fetches UEFA Nations League odds with 4-hour local cache to preserve free-tier credits."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force_refresh and ODDS_CACHE_PATH.exists():
        age_hours = (time.time() - ODDS_CACHE_PATH.stat().st_mtime) / 3600.0
        if age_hours < 4.0:
            try:
                cached = json.loads(ODDS_CACHE_PATH.read_text(encoding="utf-8"))
                if cached:
                    return cached
            except Exception:
                pass

    if not odds_key:
        return json.loads(ODDS_CACHE_PATH.read_text(encoding="utf-8")) if ODDS_CACHE_PATH.exists() else []

    url = (
        f"https://api.the-odds-api.com/v4/sports/soccer_uefa_nations_league/odds/"
        f"?apiKey={odds_key}&regions=eu,us&markets=h2h,totals"
    )
    try:
        resp = requests.get(url, timeout=15)
        rem_hdr = resp.headers.get("x-requests-remaining")
        used_hdr = resp.headers.get("x-requests-used")
        update_api_budget(
            "the_odds_api",
            used_delta=1,
            remaining=int(float(rem_hdr)) if rem_hdr else None,
            used_total=int(float(used_hdr)) if used_hdr else None,
        )
        if resp.status_code == 200:
            events = resp.json()
            if events:
                ODDS_CACHE_PATH.write_text(json.dumps(events), encoding="utf-8")
            return events
    except Exception:
        pass

    return json.loads(ODDS_CACHE_PATH.read_text(encoding="utf-8")) if ODDS_CACHE_PATH.exists() else []


def _median(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


def _build_espn_index(dates: List[str]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for dt in dates:
        events = fetch_espn_scoreboard("uefa.nations", dt)
        for ev in events:
            comp = (ev.get("competitions") or [{}])[0]
            comps = comp.get("competitors") or []
            h_name = next((c["team"]["displayName"] for c in comps if c.get("homeAway") == "home"), "")
            a_name = next((c["team"]["displayName"] for c in comps if c.get("homeAway") == "away"), "")
            if h_name and a_name:
                key = (normalize_team_name(h_name), normalize_team_name(a_name))
                venue_addr = (comp.get("venue") or {}).get("address") or {}
                index[key] = {
                    "espn_id": ev.get("id"),
                    "kickoff": ev.get("date"),
                    "venue_city": venue_addr.get("city", ""),
                    "venue_country": venue_addr.get("country", ""),
                    "neutral_site": bool(comp.get("neutralSite", False)),
                }
    return index


def _has_active_window(data: Dict[str, Any]) -> Tuple[bool, bool]:
    """Returns (in_lineup_revision_window, has_due_settlements) for cheap cron runs."""
    now = datetime.now(timezone.utc)
    rev_due = False
    settle_due = False
    for m in data.get("pending", []):
        k_str = m.get("kickoff")
        if not k_str:
            continue
        try:
            k_dt = datetime.fromisoformat(k_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        mins_left = (k_dt - now).total_seconds() / 60.0
        if -3.0 <= mins_left <= 95.0:
            rev_due = True
        if mins_left <= -125.0:
            settle_due = True
    return rev_due, settle_due


def sync_live_odds(force_odds: bool = False, window_check: bool = False):
    data_path = Path(__file__).parent / "data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))

    if window_check:
        rev_due, settle_due = _has_active_window(data)
        if not rev_due and not settle_due:
            graded_now = grade_finished_v2_matches()
            print(f"Window check: no imminent lineups/kickoffs (-3..95m). Settled {graded_now} V2 matches. 0 API calls spent.")
            return

    odds_key = os.getenv("ODDS_API_KEY", "").strip()
    af_key = os.getenv("API_FOOTBALL_KEY", "").strip()
    af_prov = os.getenv("API_FOOTBALL_PROVIDER", "direct").strip()

    events = _fetch_odds_api_cached(odds_key, force_refresh=force_odds)

    # If Odds API returned empty (e.g. offline/rate limit), preserve existing pending list teams/kickoffs
    if not events:
        events = [
            {
                "id": m["id"],
                "commence_time": m["kickoff"],
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "bookmakers": [],
                "_fallback_odds": {
                    "result": m.get("result_pick", {}).get("odds"),
                    "goals": m.get("goal_total_pick", {}).get("odds"),
                },
            }
            for m in data.get("pending", [])
        ]

    # Build historical opponent-adjusted ratings + competition environment + H2H
    hist_intel = load_historical_intel()
    team_ratings = hist_intel["team_ratings"]
    comp_env = hist_intel["comp_env"]
    global_gpg = hist_intel["global_gpg"]
    home_ratio = hist_intel["home_ratio"]

    # Initialize / load Machine Learning expected goals model (GBDT Residual Poisson)
    ml_model_payload = None
    try:
        ml_model_payload = train_ml_model(force_retrain=False)
    except Exception as e:
        print(f"Warning: ML model load fallback to baseline: {e}")

    # Collect unique upcoming UTC dates for free ESPN enrichment
    dates_set = sorted({str(ev.get("commence_time", ""))[:10].replace("-", "") for ev in events if ev.get("commence_time")})
    espn_index = _build_espn_index(dates_set)

    # Collect API-Football fixture IDs only for dates within 48h (preserves 100/day free budget)
    now_utc = datetime.now(timezone.utc)
    af_index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    if af_key and af_key != "your_api_football_key_here":
        near_dates = sorted({
            str(ev.get("commence_time", ""))[:10]
            for ev in events
            if ev.get("commence_time")
            and -1.0 <= (datetime.fromisoformat(str(ev["commence_time"]).replace("Z", "+00:00")) - now_utc).total_seconds() / 3600.0 <= 48.0
        })
        for dt_iso in near_dates:
            af_index.update(fetch_apifootball_fixtures_by_date(dt_iso, af_key, af_prov))

    pending: List[Dict[str, Any]] = []

    for ev in events:
        match_id = ev.get("id")
        kickoff = ev.get("commence_time")
        raw_home = ev.get("home_team", "")
        raw_away = ev.get("away_team", "")
        home = normalize_team_name(raw_home)
        away = normalize_team_name(raw_away)
        fixture = f"{home} vs {away}"
        competition = "UEFA Nations League"

        mins_to_ko = 9999.0
        if kickoff:
            try:
                mins_to_ko = (datetime.fromisoformat(str(kickoff).replace("Z", "+00:00")) - now_utc).total_seconds() / 60.0
            except ValueError:
                pass

        espn_meta = espn_index.get((home, away), {})
        espn_summary = None
        espn_odds = {}
        espn_intel = {}
        weather = {}

        if espn_meta.get("espn_id"):
            cache_ttl = 10.0 if -3.0 <= mins_to_ko <= 95.0 else 45.0
            espn_summary = _cached_espn_get(
                f"{ESPN_BASE}/uefa.nations/summary?event={espn_meta['espn_id']}",
                f"sum_unl_{espn_meta['espn_id']}",
                max_age_minutes=cache_ttl,
            )
            if espn_summary:
                espn_odds = extract_espn_odds_from_summary(espn_summary)
                espn_intel = extract_espn_team_intelligence(espn_summary, home, away)
            if espn_meta.get("venue_city"):
                weather = fetch_kickoff_weather(
                    espn_meta["venue_city"],
                    espn_meta.get("venue_country", ""),
                    kickoff or "",
                )

        # Fetch quoted BTTS, quoted Corners O/U 9.5, and T-75m lineups/injuries via API-Football
        af_meta = af_index.get((home, away), {})
        af_data: Dict[str, Any] = {}
        if af_meta.get("fixture_id") and af_key:
            af_data = fetch_apifootball_odds_and_lineups(
                af_meta["fixture_id"],
                af_key,
                af_prov,
                include_lineups=(-3.0 <= mins_to_ko <= 75.0),
            )

        # Track whether both teams exist in our empirical 266-team database (no silent unknown drops)
        r_h = team_ratings.get(home)
        r_a = team_ratings.get(away)
        unmapped_team = (r_h is None) or (r_a is None)
        att_h, def_h, n_h = r_h if r_h else (1.0, 1.0, 0)
        att_a, def_a, n_a = r_a if r_a else (1.0, 1.0, 0)

        # Competition scoring baseline + venue home advantage + weather tempo modifier
        base_gpg = comp_env.get(competition, global_gpg)
        neutral_site = espn_meta.get("neutral_site", False)
        ha_h = 1.0 if neutral_site else home_ratio
        ha_a = 1.0 if neutral_site else (1.0 / home_ratio)

        weather_mult = 1.0
        if weather:
            if (weather.get("precip_mm") or 0.0) >= 3.0 or (weather.get("wind_kmh") or 0.0) >= 32.0:
                weather_mult = 0.94

        # Machine Learning Expected Goals (GBDT Poisson residual model with momentum & log-differential features)
        lam_ml, mu_ml, ml_meta = predict_match_lambdas_ml(
            home,
            away,
            competition,
            hist_intel,
            neutral=neutral_site,
            weather_mult=weather_mult,
            model_payload=ml_model_payload,
        )
        lam_stat = lam_ml
        mu_stat = mu_ml

        # Collect bookmaker prices with strict per-bookmaker overround sanity validation
        h_odds, d_odds, a_odds = [], [], []
        totals_by_point: Dict[float, Dict[str, List[float]]] = {}

        def _accept_1x2(oh: Optional[float], od: Optional[float], oa: Optional[float]) -> bool:
            if not (oh and od and oa) or min(oh, od, oa) <= 1.01:
                return False
            vig = (1.0 / oh) + (1.0 / od) + (1.0 / oa)
            return 0.98 <= vig <= 1.15

        def _accept_2way(o1: Optional[float], o2: Optional[float]) -> bool:
            if not (o1 and o2) or min(o1, o2) <= 1.01:
                return False
            vig = (1.0 / o1) + (1.0 / o2)
            return 0.98 <= vig <= 1.14

        for b in ev.get("bookmakers", []):
            for mkt in b.get("markets", []):
                if mkt.get("key") == "h2h":
                    bh = bd = ba = None
                    for oc in mkt.get("outcomes", []):
                        nm = normalize_team_name(oc.get("name", ""))
                        price = oc.get("price")
                        if nm == home:
                            bh = price
                        elif nm == away:
                            ba = price
                        elif nm.lower() == "draw":
                            bd = price
                    if _accept_1x2(bh, bd, ba):
                        h_odds.append(bh)
                        d_odds.append(bd)
                        a_odds.append(ba)
                elif mkt.get("key") == "totals":
                    by_pt: Dict[float, Dict[str, float]] = {}
                    for oc in mkt.get("outcomes", []):
                        pt = oc.get("point")
                        price = oc.get("price")
                        if pt is None or not price:
                            continue
                        pt_f = float(pt)
                        if oc.get("name") == "Over":
                            by_pt.setdefault(pt_f, {})["Over"] = price
                        elif oc.get("name") == "Under":
                            by_pt.setdefault(pt_f, {})["Under"] = price
                    for pt_f, pair in by_pt.items():
                        ov_p, un_p = pair.get("Over"), pair.get("Under")
                        if _accept_2way(ov_p, un_p):
                            bucket = totals_by_point.setdefault(pt_f, {"Over": [], "Under": []})
                            bucket["Over"].append(ov_p)
                            bucket["Under"].append(un_p)

        # Include free DraftKings close odds from ESPN when overround and point are valid
        if _accept_1x2(espn_odds.get("h_close"), espn_odds.get("d_close"), espn_odds.get("a_close")):
            h_odds.append(espn_odds["h_close"])
            d_odds.append(espn_odds["d_close"])
            a_odds.append(espn_odds["a_close"])

        espn_line = espn_odds.get("total_line")
        if espn_line is not None and _accept_2way(espn_odds.get("over_close"), espn_odds.get("under_close")):
            bucket = totals_by_point.setdefault(float(espn_line), {"Over": [], "Under": []})
            bucket["Over"].append(espn_odds["over_close"])
            bucket["Under"].append(espn_odds["under_close"])

        over_odds = totals_by_point.get(2.5, {}).get("Over", [])
        under_odds = totals_by_point.get(2.5, {}).get("Under", [])

        has_real_h2h = bool(h_odds and d_odds and a_odds)
        has_real_totals = bool(over_odds and under_odds)

        med_h, med_d, med_a = _median(h_odds), _median(d_odds), _median(a_odds)
        med_ov, med_un = _median(over_odds), _median(under_odds)
        best_h = max(h_odds) if h_odds else None
        best_d = max(d_odds) if d_odds else None
        best_a = max(a_odds) if a_odds else None
        best_ov = max(over_odds) if over_odds else None
        best_un = max(under_odds) if under_odds else None

        # Choose best clean totals line to anchor total goal expectation (prefer 2.5, then 3.5/1.5/etc.)
        anchor_line = 2.5
        mkt_probs_tot = None
        if has_real_totals and med_ov and med_un:
            mkt_probs_tot = multiplicative_devig([med_ov, med_un])
        elif totals_by_point:
            anchor_line = max(totals_by_point.keys(), key=lambda pt: len(totals_by_point[pt]["Over"]))
            a_ov = _median(totals_by_point[anchor_line]["Over"])
            a_un = _median(totals_by_point[anchor_line]["Under"])
            if a_ov and a_un:
                mkt_probs_tot = multiplicative_devig([a_ov, a_un])

        mkt_probs_1x2 = None
        lam_mkt, mu_mkt = lam_stat, mu_stat

        if has_real_h2h and med_h and med_d and med_a:
            mkt_probs_1x2 = multiplicative_devig([med_h, med_d, med_a])
            lam_mkt, mu_mkt = invert_market_lambdas(
                mkt_probs_1x2[0],
                mkt_probs_1x2[1],
                mkt_probs_1x2[2],
                mkt_probs_tot[0] if mkt_probs_tot else None,
                total_line=anchor_line,
            )
            # Blend sharp market expectation inside the simulation (shrinkage anchor w_mkt = 0.55)
            lam_final = 0.45 * lam_stat + 0.55 * lam_mkt
            mu_final = 0.45 * mu_stat + 0.55 * mu_mkt
        else:
            lam_final, mu_final = lam_stat, mu_stat

        model = evaluate_dixon_coles_grid(lam_final, mu_final, rho=-0.08)

        # Walk-forward validated: 1X2 already incorporates Empirical Bayes + market lambda shrinkage (0.1841 RPS);
        # binary totals/BTTS benefit from 0.92 tail shrinkage against Poisson over-confidence.
        p_h = round(min(0.98, max(0.01, model["p_h"])), 3)
        p_d = round(min(0.98, max(0.01, model["p_d"])), 3)
        p_a = round(max(0.01, 1.0 - p_h - p_d), 3)

        p_over = round(apply_shrinkage(model["p_over"], prior_mean=0.50, weight=0.92), 3)
        p_under = round(1.0 - p_over, 3)

        p_btts_yes = round(apply_shrinkage(model["p_btts_yes"], prior_mean=0.50, weight=0.92), 3)
        p_btts_no = round(1.0 - p_btts_yes, 3)

        # --- Market 1: Match Result (1X2) ---
        res_choices = [
            ("Home Win", p_h, best_h, mkt_probs_1x2[0] if mkt_probs_1x2 else None),
            ("Draw", p_d, best_d, mkt_probs_1x2[1] if mkt_probs_1x2 else None),
            ("Away Win", p_a, best_a, mkt_probs_1x2[2] if mkt_probs_1x2 else None),
        ]
        # Rank strictly by model confidence (highest probability outcome) so 1X2 pick never contradicts probabilities
        res_choices.sort(key=lambda x: x[1], reverse=True)
        top_sel, top_prob, top_odds, top_mkt_p = res_choices[0]
        sec_prob = res_choices[1][1]
        if not has_real_h2h or top_odds is None:
            top_odds = round(1.0 / max(0.05, top_prob), 2)
        min_gap = 0.045 if has_real_h2h else 0.05
        res_is_pass = (top_prob < 0.44) or ((top_prob - sec_prob) < min_gap)

        ev_res = round((top_prob * top_odds - 1.0) * 100.0, 1) if (top_odds and has_real_h2h) else 0.0
        if res_is_pass:
            result_candidate = {
                "market": "Match Result",
                "pick": "NO PICK (PASS)",
                "selection": "NO PICK (PASS)",
                "target_selection": top_sel,
                "prob": top_prob,
                "odds": top_odds,
                "edge": f"{'+' if ev_res >= 0 else ''}{ev_res}%",
                "edge_val": ev_res,
                "composite_score": 0.0,
                "is_pass": True,
                "quoted_market": has_real_h2h,
                "reason": "High Entropy / Dead-Heat Toss-up",
                "status": "PENDING",
            }
        else:
            result_candidate = {
                "market": "Match Result",
                "pick": top_sel,
                "selection": top_sel,
                "prob": top_prob,
                "odds": round(top_odds, 2),
                "edge": f"{'+' if ev_res >= 0 else ''}{ev_res}%",
                "edge_val": ev_res,
                "composite_score": round(top_prob * max(0.5, ev_res), 2),
                "is_pass": False,
                "quoted_market": has_real_h2h,
                "status": "PENDING",
            }

        # --- Market 2: Goal Total (Adaptive Dynamic Totals O/U 1.5, 2.5, 3.5, etc.) ---
        exp_xg_total = round(lam_final + mu_final, 2)

        def _evaluate_gt_candidate(target_line: float) -> Dict[str, Any]:
            p_ov_raw = sum(p for (x, y), p in model["scores"].items() if (x + y) > target_line)
            p_ov_l = round(apply_shrinkage(p_ov_raw, prior_mean=0.50, weight=0.92), 3)
            p_un_l = round(1.0 - p_ov_l, 3)

            q_ovs = totals_by_point.get(target_line, {}).get("Over", [])
            q_uns = totals_by_point.get(target_line, {}).get("Under", [])
            has_q = bool(q_ovs and q_uns)
            b_ov = max(q_ovs) if q_ovs else None
            b_un = max(q_uns) if q_uns else None

            if p_ov_l >= 0.50:
                p_cand = p_ov_l
                s_cand = f"Over {target_line}"
                o_cand = b_ov
            else:
                p_cand = p_un_l
                s_cand = f"Under {target_line}"
                o_cand = b_un

            mean_conflict = (s_cand.startswith("Over") and exp_xg_total < target_line) or (
                s_cand.startswith("Under") and exp_xg_total > target_line
            )
            coin_flip = (0.48 <= p_ov_l <= 0.52)
            is_pass = coin_flip or mean_conflict
            pass_reason = "Poisson Mean/Line Skew Parity" if mean_conflict else "Spread Coin-Flip (48%-52%)"

            if not has_q or o_cand is None:
                o_cand = round(1.0 / max(0.05, p_cand), 2)
                ev = 0.0
                edge_s = "Fair Price"
                comp = 0.0
            else:
                ev = round((p_cand * o_cand - 1.0) * 100.0, 1)
                edge_s = f"{'+' if ev >= 0 else ''}{ev}%"
                comp = round(p_cand * ev, 2) if (not is_pass and ev > 0) else 0.0

            return {
                "market": "Goal Total",
                "line": target_line,
                "pick": "NO PICK (PASS)" if is_pass else s_cand,
                "selection": "NO PICK (PASS)" if is_pass else s_cand,
                "target_selection": s_cand if is_pass else None,
                "prob": p_cand,
                "odds": round(o_cand, 2),
                "edge": "0.0%" if (is_pass and not has_q) else edge_s,
                "edge_val": ev,
                "composite_score": comp,
                "is_pass": is_pass,
                "quoted_market": has_q,
                "reason": pass_reason if is_pass else None,
                "status": "PENDING",
            }

        # Evaluate 2.5 anchor line first
        gt_candidate = _evaluate_gt_candidate(2.5)

        # Explore candidate totals lines (bounded to standard match totals 1.5 to 4.5)
        candidate_gt_lines = sorted(set([1.5, 2.5, 3.5] + [pt for pt in totals_by_point.keys() if 1.5 <= pt <= 4.5]))
        qualifying_alts = []

        for alt_line in candidate_gt_lines:
            if abs(alt_line - 2.5) < 1e-4:
                continue
            alt_cand = _evaluate_gt_candidate(alt_line)
            if alt_cand["is_pass"]:
                continue

            sel_s = alt_cand["selection"]
            is_over = sel_s.startswith("Over")
            fits_projection = False
            if is_over:
                if alt_line > 2.5:
                    fits_projection = (exp_xg_total >= alt_line - 0.20)
                else:  # e.g. Over 1.5 / Over 2.0
                    fits_projection = (exp_xg_total >= 2.05 and alt_cand["prob"] >= 0.65)
            else:
                if alt_line < 2.5:
                    fits_projection = (exp_xg_total <= alt_line + 0.20)
                else:  # e.g. Under 3.0 / Under 3.5
                    fits_projection = (exp_xg_total <= 3.10 and alt_cand["prob"] >= 0.60)

            if not fits_projection:
                continue

            # "If and only if you project a much better total, that still has good value"
            # Require genuine quoted market with backable odds (>= 1.45) and real edge (>= +1.5%)
            if not alt_cand["quoted_market"] or alt_cand["odds"] < 1.45 or alt_cand["edge_val"] < 1.5:
                continue

            if gt_candidate["is_pass"]:
                qualifying_alts.append((alt_cand["composite_score"], alt_cand["prob"], alt_cand))
            else:
                anchor_comp = gt_candidate["composite_score"]
                if anchor_comp <= 0.0 or alt_cand["composite_score"] >= anchor_comp * 1.10:
                    qualifying_alts.append((alt_cand["composite_score"], alt_cand["prob"], alt_cand))

        if qualifying_alts:
            qualifying_alts.sort(key=lambda x: (x[0], x[1]), reverse=True)
            gt_candidate = qualifying_alts[0][2]

        # --- Market 3: BTTS Yes/No (Anchored Dixon-Coles + Real API-Football Bet365/Multi-Book Quotes) ---
        btts_yes_list = af_data.get("btts_yes_odds") or []
        btts_no_list = af_data.get("btts_no_odds") or []
        has_real_btts = bool(btts_yes_list and btts_no_list)
        if has_real_btts:
            med_by, med_bn = _median(btts_yes_list), _median(btts_no_list)
            mkt_btts_yes = multiplicative_devig([med_by, med_bn])[0]
            p_btts_yes = round(0.70 * p_btts_yes + 0.30 * mkt_btts_yes, 3)
            p_btts_no = round(1.0 - p_btts_yes, 3)

        btts_is_pass = (0.48 <= p_btts_yes <= 0.52)
        btts_prob = p_btts_yes if p_btts_yes >= 0.50 else p_btts_no
        btts_sel = "BTTS Yes" if p_btts_yes >= 0.50 else "BTTS No"
        btts_pass_reason = "Binary Coin-Flip Parity (48%-52%)" if btts_is_pass else None

        # Game-State Lead Decay Risk Gate for BTTS No:
        # When spread is wide (|Spread| >= 1.05), a heavy favorite often leads 2-0+ and concedes late consolation goals.
        # Pass BTTS No unless confidence P(No) is at least 60%.
        spread_abs = abs(lam_final - mu_final)
        if btts_sel == "BTTS No" and spread_abs >= 1.05 and btts_prob < 0.60:
            btts_is_pass = True
            btts_pass_reason = "Game-State Lead Decay Risk (|Spread| >= 1.05 & P(No) < 60%)"

        if has_real_btts:
            btts_odds = max(btts_yes_list) if p_btts_yes >= 0.50 else max(btts_no_list)
            ev_btts = round((btts_prob * btts_odds - 1.0) * 100.0, 1)
            btts_edge_str = f"{'+' if ev_btts >= 0 else ''}{ev_btts}%"
            btts_comp = round(btts_prob * max(0.5, ev_btts), 2)
        else:
            btts_odds = round(1.0 / max(0.05, btts_prob), 2)
            ev_btts = 0.0
            btts_edge_str = "Fair Price"
            btts_comp = 0.0

        btts_candidate = {
            "market": "BTTS",
            "pick": "NO PICK (PASS)" if btts_is_pass else btts_sel,
            "selection": "NO PICK (PASS)" if btts_is_pass else btts_sel,
            "target_selection": btts_sel if btts_is_pass else None,
            "prob": btts_prob,
            "odds": round(btts_odds, 2),
            "edge": "0.0%" if btts_is_pass and not has_real_btts else btts_edge_str,
            "edge_val": ev_btts,
            "composite_score": 0.0 if btts_is_pass else btts_comp,
            "is_pass": btts_is_pass,
            "quoted_market": has_real_btts,
            "reason": btts_pass_reason if btts_is_pass else None,
            "status": "PENDING",
        }

        # --- Market 4: Corners O/U 9.5 (Empirical Bayes ESPN Corners + Market Anchor + Negative Binomial) ---
        h_cw = espn_intel.get("home_corners_won") or []
        h_cc = espn_intel.get("home_corners_conc") or []
        a_cw = espn_intel.get("away_corners_won") or []
        a_cc = espn_intel.get("away_corners_conc") or []

        prior_c = 4.75
        avg_cw_h = empirical_bayes_mean(sum(h_cw), len(h_cw), prior_c, 4.0)
        avg_cc_h = empirical_bayes_mean(sum(h_cc), len(h_cc), prior_c, 4.0)
        avg_cw_a = empirical_bayes_mean(sum(a_cw), len(a_cw), prior_c, 4.0)
        avg_cc_a = empirical_bayes_mean(sum(a_cc), len(a_cc), prior_c, 4.0)

        exp_h_corners = 0.5 * (avg_cw_h + avg_cc_a) * (0.90 + 0.075 * lam_final)
        exp_a_corners = 0.5 * (avg_cw_a + avg_cc_h) * (0.90 + 0.075 * mu_final)

        # Possession-Skewed Corner Deflection Modeling:
        # High territorial imbalance causes low-block pin-ins and frequent deflections over the endline
        tot_lam = max(0.5, lam_final + mu_final)
        poss_skew = abs(lam_final - mu_final) / tot_lam
        deflection_mult = 1.0 + 0.12 * max(0.0, poss_skew - 0.30)
        mu_stat_corners = max(6.0, min(15.5, (exp_h_corners + exp_a_corners) * deflection_mult))

        cor_by_line: Dict[float, Dict[str, List[float]]] = dict(af_data.get("corners_by_line") or {})
        cor_ov_list = af_data.get("corners_over95_odds") or []
        cor_un_list = af_data.get("corners_under95_odds") or []
        if cor_ov_list and cor_un_list and 9.5 not in cor_by_line:
            cor_by_line[9.5] = {"Over": cor_ov_list, "Under": cor_un_list}

        # Market-anchor expected total corners (prefer 9.5 if quoted)
        has_real_corners = False
        anchor_cor_line = 9.5
        if 9.5 in cor_by_line and cor_by_line[9.5].get("Over") and cor_by_line[9.5].get("Under"):
            med_cov = _median(cor_by_line[9.5]["Over"])
            med_cun = _median(cor_by_line[9.5]["Under"])
            mkt_cor_over_p = multiplicative_devig([med_cov, med_cun])[0]
            mu_mkt_corners = invert_corners_mu(mkt_cor_over_p, line=9.5)
            exp_total_corners = round(0.50 * mu_stat_corners + 0.50 * mu_mkt_corners, 2)
            has_real_corners = True
        elif cor_by_line:
            best_cor_anchor = max(cor_by_line.keys(), key=lambda pt: len(cor_by_line[pt].get("Over", [])))
            ovs = cor_by_line[best_cor_anchor].get("Over", [])
            uns = cor_by_line[best_cor_anchor].get("Under", [])
            if ovs and uns:
                anchor_cor_line = best_cor_anchor
                med_cov, med_cun = _median(ovs), _median(uns)
                mkt_cor_over_p = multiplicative_devig([med_cov, med_cun])[0]
                mu_mkt_corners = invert_corners_mu(mkt_cor_over_p, line=anchor_cor_line)
                exp_total_corners = round(0.50 * mu_stat_corners + 0.50 * mu_mkt_corners, 2)
                has_real_corners = True
            else:
                exp_total_corners = round(mu_stat_corners, 2)
        else:
            exp_total_corners = round(mu_stat_corners, 2)

        def _evaluate_cor_candidate(target_line: float) -> Dict[str, Any]:
            cor_var_mult = 2.0 + 0.80 * max(0.0, poss_skew - 0.30)
            cor_variance = cor_var_mult * exp_total_corners
            p_cor_over_raw = neg_binom_over_prob(exp_total_corners, variance=cor_variance, line=target_line)
            p_cor_over = round(apply_shrinkage(p_cor_over_raw, prior_mean=0.50, weight=0.92), 3)
            p_cor_under = round(1.0 - p_cor_over, 3)

            q_ovs = cor_by_line.get(target_line, {}).get("Over", [])
            q_uns = cor_by_line.get(target_line, {}).get("Under", [])
            has_q = bool(q_ovs and q_uns)
            b_ov = max(q_ovs) if q_ovs else None
            b_un = max(q_uns) if q_uns else None

            if p_cor_over >= 0.50:
                p_cand = p_cor_over
                s_cand = f"Corners Over {target_line}"
                o_cand = b_ov
            else:
                p_cand = p_cor_under
                s_cand = f"Corners Under {target_line}"
                o_cand = b_un

            exp_cor_disp = round(exp_total_corners, 1)
            mean_conflict = (s_cand == f"Corners Over {target_line}" and exp_cor_disp < target_line) or (
                s_cand == f"Corners Under {target_line}" and exp_cor_disp > target_line
            )
            coin_flip = (0.48 <= p_cor_over <= 0.52)

            # Territorial Block Deflection Risk Gate:
            # Under high possession skew (>= 38%), pinned underdogs generate repeated deflection corners.
            # Avoid picking Corners Under unless confidence is at least 62%.
            skew_under_risk = (s_cand.startswith("Corners Under") and poss_skew >= 0.38 and p_cand < 0.62)

            is_pass = coin_flip or mean_conflict or skew_under_risk
            if skew_under_risk:
                pass_reason = f"Territorial Block Deflection Risk (Possession Skew {round(poss_skew * 100)}% >= 38%)"
            elif mean_conflict:
                pass_reason = "NegBin Mean/Line Skew Parity"
            else:
                pass_reason = "Handicap Center Line (48%-52%)"

            if not has_q or o_cand is None:
                o_cand = round(1.0 / max(0.05, p_cand), 2)
                ev = 0.0
                edge_s = "Fair Price"
                comp = 0.0
            else:
                ev = round((p_cand * o_cand - 1.0) * 100.0, 1)
                edge_s = f"{'+' if ev >= 0 else ''}{ev}%"
                comp = round(p_cand * ev, 2) if (not is_pass and ev > 0) else 0.0

            return {
                "market": "Corners",
                "line": target_line,
                "pick": "NO PICK (PASS)" if is_pass else s_cand,
                "selection": "NO PICK (PASS)" if is_pass else s_cand,
                "target_selection": s_cand if is_pass else None,
                "prob": p_cand,
                "odds": round(o_cand, 2),
                "edge": "0.0%" if (is_pass and not has_q) else edge_s,
                "edge_val": ev,
                "composite_score": comp,
                "is_pass": is_pass,
                "quoted_market": has_q,
                "reason": pass_reason if is_pass else None,
                "status": "PENDING",
            }

        # Evaluate 9.5 anchor line first
        cor_candidate = _evaluate_cor_candidate(9.5)

        # Explore candidate corner lines (bounded to standard match corners 7.0 to 13.0)
        candidate_cor_lines = sorted(set([8.5, 9.5, 10.5] + [pt for pt in cor_by_line.keys() if 7.0 <= pt <= 13.0]))
        qualifying_cor_alts = []

        for alt_line in candidate_cor_lines:
            if abs(alt_line - 9.5) < 1e-4:
                continue
            alt_cand = _evaluate_cor_candidate(alt_line)
            if alt_cand["is_pass"]:
                continue

            sel_s = alt_cand["selection"]
            is_over = "Over" in sel_s
            fits_projection = False
            if is_over:
                if alt_line > 9.5:
                    fits_projection = (exp_total_corners >= alt_line - 0.30)
                else:  # e.g. Over 8.5
                    fits_projection = (exp_total_corners >= 9.60 and alt_cand["prob"] >= 0.64)
            else:
                if alt_line < 9.5:
                    fits_projection = (exp_total_corners <= alt_line + 0.30)
                else:  # e.g. Under 10.5
                    fits_projection = (exp_total_corners <= 9.40 and alt_cand["prob"] >= 0.64)

            if not fits_projection:
                continue

            # "If and only if you project a much better total, that still has good value"
            # Require genuine quoted market with backable odds (>= 1.45) and real edge (>= +1.5%)
            if not alt_cand["quoted_market"] or alt_cand["odds"] < 1.45 or alt_cand["edge_val"] < 1.5:
                continue

            if cor_candidate["is_pass"]:
                qualifying_cor_alts.append((alt_cand["composite_score"], alt_cand["prob"], alt_cand))
            else:
                anchor_comp = cor_candidate["composite_score"]
                if anchor_comp <= 0.0 or alt_cand["composite_score"] >= anchor_comp * 1.10:
                    qualifying_cor_alts.append((alt_cand["composite_score"], alt_cand["prob"], alt_cand))

        if qualifying_cor_alts:
            qualifying_cor_alts.sort(key=lambda x: (x[0], x[1]), reverse=True)
            cor_candidate = qualifying_cor_alts[0][2]

        # --- Cross-Market Coherence & Coherent Exact Score Selection ---
        # Guarantees (Result, Goal Total, BTTS) never form a mutually impossible trio and
        # locks pred_score / sec_score to the highest-density scorelines inside the active regime.
        resolve_cross_market_contradictions(model["scores"], result_candidate, gt_candidate, btts_candidate)
        top_sc, top_sc_p, sec_sc, sec_sc_p, thi_sc, thi_sc_p = select_coherent_scores(
            model["scores"], result_candidate, gt_candidate, btts_candidate
        )

        # --- Best Pick Alpha Selection ---
        # Evaluates all quoted markets clearing confidence >= 48% & genuine +EV >= +1.5%
        # OR high-conviction >= 62% with EV >= -1.0%.
        # Safeguards: Disqualify BTTS No under wide spreads (|Spread| >= 1.05) unless confidence >= 64%.
        # Disqualify Corners Under under high possession skew (poss_skew >= 0.35) unless confidence >= 64%.
        quoted_candidates = [result_candidate, gt_candidate, btts_candidate, cor_candidate]
        qualifying = []
        for c in quoted_candidates:
            if c.get("is_pass") or not c.get("quoted_market"):
                continue
            sel_str = str(c.get("selection", ""))
            if sel_str == "BTTS No" and spread_abs >= 1.05 and c["prob"] < 0.64:
                continue
            if sel_str.startswith("Corners Under") and poss_skew >= 0.35 and c["prob"] < 0.64:
                continue
            if (c["prob"] >= 0.48 and c["edge_val"] >= 1.5) or (c["prob"] >= 0.62 and c["edge_val"] >= -1.0):
                qualifying.append(c)
        qualifying.sort(key=lambda x: (x["edge_val"], x["prob"]), reverse=True)

        if qualifying:
            best_pick_choice = qualifying[0]
            is_best = True
        else:
            all_active = []
            for c in quoted_candidates:
                if c.get("is_pass"):
                    continue
                sel_str = str(c.get("selection", ""))
                if sel_str == "BTTS No" and spread_abs >= 1.05 and c["prob"] < 0.64:
                    continue
                if sel_str.startswith("Corners Under") and poss_skew >= 0.35 and c["prob"] < 0.64:
                    continue
                all_active.append(c)
            all_active.sort(key=lambda x: x["prob"], reverse=True)
            if all_active and all_active[0]["prob"] >= 0.58:
                best_pick_choice = all_active[0]
                is_best = True
            else:
                is_best = False
                best_pick_choice = {
                    "market": "None",
                    "pick": "NO PICK (PASS)",
                    "selection": "NO PICK (PASS)",
                    "prob": None,
                    "odds": None,
                    "edge": "0.0%",
                    "composite_score": 0.0,
                    "is_pass": True,
                    "reason": "No market cleared real +EV (>=+1.5%) or high-conviction (>=58%) hurdle",
                    "status": "PENDING",
                }

        # Build authentic analytics payload for UI consumption (replacing synthetic RNG!)
        real_h2h = get_real_h2h(hist_intel["h2h"], home, away)

        def _format_form_matches(espn_list: List[Dict[str, Any]], csv_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if espn_list and len(espn_list) >= 3:
                return espn_list[:5]
            formatted = []
            for m_hist in csv_list[:5]:
                opp_f = m_hist["opp"]
                formatted.append({
                    "res": m_hist["res"],
                    "isHome": m_hist["is_home"],
                    "opp": to_team_code(opp_f),
                    "oppFull": opp_f,
                    "score": m_hist["score"],
                    "btts": m_hist["btts"],
                    "date": m_hist["date"],
                })
            return formatted

        home_matches = _format_form_matches(
            espn_intel.get("home_matches", []),
            hist_intel["team_form"].get(home, []),
        )
        away_matches = _format_form_matches(
            espn_intel.get("away_matches", []),
            hist_intel["team_form"].get(away, []),
        )

        # Rolling empirical goals per game from real past-5 matches
        def _real_goal_avgs(matches_list: List[Dict[str, Any]], stat_lam: float) -> Tuple[float, float]:
            gf_vals, ga_vals = [], []
            for m_item in matches_list:
                parts = str(m_item.get("score", "")).split(":")
                if len(parts) == 2:
                    try:
                        gf_vals.append(int(parts[0]))
                        ga_vals.append(int(parts[1]))
                    except ValueError:
                        pass
            if gf_vals:
                return round(empirical_bayes_mean(sum(gf_vals), len(gf_vals), stat_lam, 3.0), 2), round(
                    empirical_bayes_mean(sum(ga_vals), len(ga_vals), base_gpg, 3.0), 2
                )
            return round(stat_lam, 2), round(base_gpg, 2)

        avg_gf_h, avg_ga_h = _real_goal_avgs(home_matches, lam_stat)
        avg_gf_a, avg_ga_a = _real_goal_avgs(away_matches, mu_stat)

        starters_ready = bool(espn_intel.get("starters_announced") or af_data.get("starters_announced"))

        pending_match = {
            "id": match_id,
            "kickoff": kickoff,
            "competition": competition,
            "fixture": fixture,
            "selection": best_pick_choice["selection"],
            "model_prob": best_pick_choice["prob"] if best_pick_choice["prob"] is not None else max(p_h, p_d, p_a),
            "closing_odds": best_pick_choice["odds"] if best_pick_choice["odds"] is not None else round(1.0 / max(0.05, max(p_h, p_a)), 2),
            "implied_prob": round(mkt_probs_1x2[0], 3) if mkt_probs_1x2 else round(1.0 / max(1.01, best_pick_choice["odds"] or 2.0), 3),
            "edge": best_pick_choice["edge"],
            "status": "PENDING",
            "home_team": home,
            "away_team": away,
            "p_h": p_h,
            "p_d": p_d,
            "p_a": p_a,
            "pred_score": f"{top_sc[0]}-{top_sc[1]}",
            "pred_score_prob": round(top_sc_p, 3),
            "pred_score_pct": round(top_sc_p * 100.0, 1),
            "sec_score": f"{sec_sc[0]}-{sec_sc[1]}",
            "sec_score_prob": round(sec_sc_p, 3),
            "sec_score_pct": round(sec_sc_p * 100.0, 1),
            "thi_score": f"{thi_sc[0]}-{thi_sc[1]}",
            "thi_score_prob": round(thi_sc_p, 3),
            "thi_score_pct": round(thi_sc_p * 100.0, 1),
            "result_pick": result_candidate,
            "goal_total_pick": gt_candidate,
            "btts_pick": btts_candidate,
            "corner_pick": cor_candidate,
            "is_best": is_best,
            "best_pick": best_pick_choice,
            "unmapped_team": unmapped_team,
            "real_h2h": real_h2h,
            "real_home_form": home_matches,
            "real_away_form": away_matches,
            "real_goal_stats": {
                "avgScoredH": avg_gf_h,
                "avgConcededH": avg_ga_h,
                "avgScoredA": avg_gf_a,
                "avgConcededA": avg_ga_a,
                "expectedXg": round(lam_final + mu_final, 2),
            },
            "real_corner_stats": {
                "avgCornersH": round(avg_cw_h, 1),
                "avgCornersConcededH": round(avg_cc_h, 1),
                "avgCornersA": round(avg_cw_a, 1),
                "avgCornersConcededA": round(avg_cc_a, 1),
                "expectedCorners": round(exp_total_corners, 1),
                "sampleH": len(h_cw),
                "sampleA": len(a_cw),
                "quotedCorners": has_real_corners,
            },
            "market_anchor": {
                "espn_id": espn_meta.get("espn_id"),
                "af_fixture_id": af_meta.get("fixture_id"),
                "ml_engine": ml_meta,
                "lam_stat": round(lam_stat, 2),
                "mu_stat": round(mu_stat, 2),
                "lam_mkt": round(lam_mkt, 2),
                "mu_mkt": round(mu_mkt, 2),
                "lam_final": round(lam_final, 2),
                "mu_final": round(mu_final, 2),
                "mkt_p_h": round(mkt_probs_1x2[0], 3) if mkt_probs_1x2 else None,
                "mkt_p_d": round(mkt_probs_1x2[1], 3) if mkt_probs_1x2 else None,
                "mkt_p_a": round(mkt_probs_1x2[2], 3) if mkt_probs_1x2 else None,
                "open_odds_h": espn_odds.get("h_open"),
                "close_odds_h": espn_odds.get("h_close"),
                "starters_announced": starters_ready,
                "injuries": af_data.get("injuries", []),
                "weather": weather,
            },
        }
        pending.append(pending_match)

    # Pre-publish Sanity Gate (blocks flat/corrupt predictions from going live!)
    gate_failures = sanity_gate(pending, strict_teams=False)
    if gate_failures:
        print("SANITY GATE WARNINGS/FAILURES:")
        for reason in gate_failures:
            print(f" - {reason}")
        if any("flat/constant" in r or "sum to" in r or "out of [0.01, 0.99]" in r for r in gate_failures):
            raise RuntimeError(f"Sanity gate blocked publish: {gate_failures}")

    data["pending"] = pending
    data["summary"]["pending"] = len(pending)
    if events:
        data["summary"]["generated_at"] = events[0].get("commence_time")

    data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Lock pre-kickoff immutable V2 snapshot & auto-settle finished fixtures
    snap_cnt = record_pre_kickoff_snapshots(
        pending,
        revision_reason="window_revision" if window_check else "sync",
    )
    graded_v2_cnt = grade_finished_v2_matches()

    best_count = sum(1 for m in pending if m["is_best"])
    pass_count = sum(1 for m in pending if not m["is_best"])
    print(
        f"Saved calibrated {data_path} ({len(pending)} pending: {best_count} Best/Qualified, {pass_count} Pass). "
        f"V2 snapshots updated: {snap_cnt} | Newly settled: {graded_v2_cnt} | Sanity Gate PASSED."
    )


if __name__ == "__main__":
    force = "--force-odds" in sys.argv
    win_chk = "--window-check" in sys.argv
    sync_live_odds(force_odds=force, window_check=win_chk)

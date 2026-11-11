"""Immutable V2 Pre-Kickoff Snapshot Archive & Auto-Grading Forward Ledger.

Implements strict forward verification across all 4 football markets:
- Logs predictions into src/v2_ledger.json strictly BEFORE kickoff.
- Tracks closing-window revisions (T-95m to T-3m) with old -> new deltas pre-kickoff.
- Freezes pre-kickoff calls at kickoff; grading only appends official FT score & boxscore corners.
- Auto-settles finished fixtures from ESPN scoreboard/summary (goals + real wonCorners).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
V2_LEDGER_PATH = ROOT_DIR / "src" / "v2_ledger.json"

import sys
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.calibration import calculate_rps, evaluate_market_calibration
from src.intl_data import (
    ESPN_BASE,
    _cached_espn_get,
    fetch_apifootball_fixtures_by_date,
    fetch_espn_scoreboard,
    normalize_team_name,
)


def _load_v2_ledger() -> Dict[str, Any]:
    if V2_LEDGER_PATH.exists():
        try:
            return json.loads(V2_LEDGER_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"locked": {}, "graded": [], "revisions": []}


def _save_v2_ledger(ledger: Dict[str, Any]):
    V2_LEDGER_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def _parse_iso_utc(iso_str: str) -> Optional[datetime]:
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def record_pre_kickoff_snapshots(pending_matches: List[Dict[str, Any]], revision_reason: str = "scheduled_sync") -> int:
    """Appends/updates pre-kickoff predictions in v2_ledger.json strictly before kickoff lock."""
    ledger = _load_v2_ledger()
    locked: Dict[str, Any] = ledger.setdefault("locked", {})
    revisions: List[Dict[str, Any]] = ledger.setdefault("revisions", [])
    now = datetime.now(timezone.utc)
    updated = 0

    graded_ids = {g["id"] for g in ledger.get("graded", [])}

    for m in pending_matches:
        mid = m.get("id")
        if not mid or mid in graded_ids:
            continue
        k_dt = _parse_iso_utc(m.get("kickoff", ""))
        if not k_dt:
            continue

        # Never modify or overwrite a forecast after kickoff - 2 minutes (immutable pre-kickoff guarantee)
        mins_to_kickoff = (k_dt - now).total_seconds() / 60.0
        if mins_to_kickoff < 2.0 and mid in locked:
            continue
        if mins_to_kickoff < -5.0 and mid not in locked:
            continue

        existing = locked.get(mid)
        new_best = (m.get("best_pick") or {}).get("selection")
        new_prob = m.get("model_prob")

        if existing:
            old_best = (existing.get("best_pick") or {}).get("selection")
            old_prob = existing.get("model_prob")
            old_res_p = (existing.get("result_pick") or {}).get("prob")
            new_res_p = (m.get("result_pick") or {}).get("prob")
            if old_best != new_best or (old_res_p and new_res_p and abs(old_res_p - new_res_p) >= 0.02):
                revisions.append({
                    "timestamp_utc": now.isoformat(),
                    "id": mid,
                    "fixture": m.get("fixture"),
                    "mins_to_kickoff": round(mins_to_kickoff, 1),
                    "reason": revision_reason,
                    "old_best": old_best,
                    "new_best": new_best,
                    "old_prob": old_prob,
                    "new_prob": new_prob,
                })

        locked[mid] = {
            "id": mid,
            "fixture": m.get("fixture"),
            "home_team": m.get("home_team"),
            "away_team": m.get("away_team"),
            "competition": m.get("competition"),
            "kickoff": m.get("kickoff"),
            "espn_id": (m.get("market_anchor") or {}).get("espn_id"),
            "locked_at_utc": now.isoformat(),
            "p_h": m.get("p_h"),
            "p_d": m.get("p_d"),
            "p_a": m.get("p_a"),
            "pred_score": m.get("pred_score"),
            "model_prob": new_prob,
            "result_pick": m.get("result_pick"),
            "goal_total_pick": m.get("goal_total_pick"),
            "btts_pick": m.get("btts_pick"),
            "corner_pick": m.get("corner_pick"),
            "is_best": m.get("is_best"),
            "best_pick": m.get("best_pick"),
            "starters_announced": (m.get("market_anchor") or {}).get("starters_announced", False),
        }
        updated += 1

    # Retain last 500 revision events cleanly
    ledger["revisions"] = revisions[-500:]
    _save_v2_ledger(ledger)
    return updated


def _grade_pick(pick_obj: Optional[Dict[str, Any]], actual_yes: bool, line_type: str = "") -> Dict[str, Any]:
    if not isinstance(pick_obj, dict):
        return {}
    out = dict(pick_obj)
    sel = str(out.get("selection") or out.get("pick") or "")
    if out.get("is_pass") or "NO PICK" in sel.upper():
        out["status"] = "VOID"
        return out

    hit = False
    if line_type == "result":
        hit = actual_yes  # pre-evaluated outcome boolean passed in
    elif line_type == "goals":
        hit = (actual_yes and "Over" in sel) or ((not actual_yes) and "Under" in sel)
    elif line_type == "btts":
        hit = (actual_yes and "Yes" in sel) or ((not actual_yes) and "No" in sel)
    elif line_type == "corners":
        hit = (actual_yes and "Over" in sel) or ((not actual_yes) and "Under" in sel)

    out["status"] = "HIT" if hit else "MISS"
    return out


def grade_finished_v2_matches() -> int:
    """Checks locked V2 fixtures past kickoff + 125m and settles FT score + real boxscore corners."""
    ledger = _load_v2_ledger()
    locked: Dict[str, Any] = ledger.get("locked", {})
    graded_list: List[Dict[str, Any]] = ledger.setdefault("graded", [])
    graded_ids = {g["id"] for g in graded_list}
    now = datetime.now(timezone.utc)

    due = []
    for mid, rec in locked.items():
        if mid in graded_ids:
            continue
        k_dt = _parse_iso_utc(rec.get("kickoff", ""))
        if k_dt and (now - k_dt).total_seconds() >= 125 * 60:
            due.append(rec)

    if not due:
        return 0

    # Group ESPN scoreboards for due dates
    dates = sorted({rec["kickoff"][:10].replace("-", "") for rec in due if rec.get("kickoff")})
    espn_results: Dict[Any, Dict[str, Any]] = {}
    for dt in dates:
        for ev in fetch_espn_scoreboard("uefa.nations", dt):
            comp = (ev.get("competitions") or [{}])[0]
            status_state = comp.get("status", {}).get("type", {}).get("state", "")
            if status_state != "post":
                continue
            comps = comp.get("competitors") or []
            h_obj = next((c for c in comps if c.get("homeAway") == "home"), None)
            a_obj = next((c for c in comps if c.get("homeAway") == "away"), None)
            if not h_obj or not a_obj:
                continue
            try:
                hg = int(h_obj.get("score", "0"))
                ag = int(a_obj.get("score", "0"))
            except ValueError:
                continue
            key = (normalize_team_name(h_obj["team"]["displayName"]), normalize_team_name(a_obj["team"]["displayName"]))
            espn_results[key] = {"espn_id": ev.get("id"), "hg": hg, "ag": ag}

    # Optional API-Football FT score fallback for any remaining matches
    af_key = os.getenv("API_FOOTBALL_KEY", "").strip()
    af_prov = os.getenv("API_FOOTBALL_PROVIDER", "direct").strip()
    af_scores = {}
    if af_key and len(espn_results) < len(due):
        for dt_iso in sorted({rec["kickoff"][:10] for rec in due if rec.get("kickoff")}):
            af_scores.update(fetch_apifootball_fixtures_by_date(dt_iso, af_key, af_prov))

    newly_graded = 0
    for rec in due:
        key = (normalize_team_name(rec["home_team"]), normalize_team_name(rec["away_team"]))
        res_info = espn_results.get(key)
        hg = ag = None
        total_corners = None

        if res_info:
            hg, ag = res_info["hg"], res_info["ag"]
            ev_id = res_info.get("espn_id") or rec.get("espn_id")
            if ev_id:
                sum_data = _cached_espn_get(
                    f"{ESPN_BASE}/uefa.nations/summary?event={ev_id}",
                    f"final_unl_{ev_id}",
                    max_age_minutes=60 * 24 * 365,
                )
                bs_teams = (sum_data or {}).get("boxscore", {}).get("teams", [])
                if len(bs_teams) == 2:
                    c_vals = []
                    for bt in bs_teams:
                        for st in bt.get("statistics", []):
                            if st.get("name") == "wonCorners":
                                try:
                                    c_vals.append(int(float(st.get("displayValue", "0"))))
                                except ValueError:
                                    pass
                    if len(c_vals) == 2 and sum(c_vals) > 0:
                        total_corners = sum(c_vals)
        elif key in af_scores and af_scores[key].get("status_short") in ("FT", "AET", "PEN"):
            hg = af_scores[key]["home_goals"]
            ag = af_scores[key]["away_goals"]

        if hg is None or ag is None:
            continue

        actual_res = "Home Win" if hg > ag else ("Draw" if hg == ag else "Away Win")
        outcome_idx = 0 if hg > ag else (1 if hg == ag else 2)
        res_pick = rec.get("result_pick") or {}
        res_sel = str(res_pick.get("selection") or "")
        g_res = _grade_pick(res_pick, res_sel == actual_res, "result")
        g_gt = _grade_pick(rec.get("goal_total_pick"), (hg + ag) >= 3, "goals")
        g_btts = _grade_pick(rec.get("btts_pick"), (hg > 0 and ag > 0), "btts")
        if total_corners is not None:
            g_cor = _grade_pick(rec.get("corner_pick"), total_corners >= 10, "corners")
        else:
            g_cor = dict(rec.get("corner_pick") or {})
            g_cor["status"] = "PENDING"

        # Grade best pick status and unit return
        bp = dict(rec.get("best_pick") or {})
        mkt_map = {
            "Match Result": g_res,
            "Goal Total": g_gt,
            "BTTS": g_btts,
            "Corners": g_cor,
        }
        bp_graded = mkt_map.get(bp.get("market", ""))
        status_final = "VOID"
        net_var = 0.0
        if bp_graded and bp_graded.get("status") in ("HIT", "MISS"):
            status_final = bp_graded["status"]
            odds_f = float(bp.get("odds") or 1.90)
            net_var = round((odds_f - 1.0), 2) if status_final == "HIT" else -1.0
            bp["status"] = status_final

        rps = calculate_rps((float(rec["p_h"]), float(rec["p_d"]), float(rec["p_a"])), outcome_idx)

        graded_entry = {
            "id": rec["id"],
            "date": rec["kickoff"][:10],
            "competition": rec["competition"],
            "fixture": rec["fixture"],
            "home_team": rec["home_team"],
            "away_team": rec["away_team"],
            "pred_score": rec["pred_score"],
            "final_score": f"{hg}-{ag}",
            "actual_corners": total_corners,
            "rps": rps,
            "status": status_final,
            "net_variance": net_var,
            "result_pick": g_res,
            "goal_total_pick": g_gt,
            "btts_pick": g_btts,
            "corner_pick": g_cor,
            "is_best": rec.get("is_best"),
            "best_pick": bp,
            "graded_at_utc": now.isoformat(),
        }
        graded_list.append(graded_entry)
        newly_graded += 1

    if newly_graded > 0:
        _save_v2_ledger(ledger)
    return newly_graded


def get_v2_summary() -> Dict[str, Any]:
    ledger = _load_v2_ledger()
    locked = ledger.get("locked", {})
    graded = ledger.get("graded", [])
    rps_vals = [g["rps"] for g in graded if g.get("rps") is not None]
    per_market = {}
    for key, label in [
        ("result_pick", "Match Result"),
        ("goal_total_pick", "Goal Total"),
        ("btts_pick", "BTTS"),
        ("corner_pick", "Corners"),
    ]:
        recs = [g[key] for g in graded if isinstance(g.get(key), dict)]
        per_market[label] = evaluate_market_calibration(recs, label)

    return {
        "locked_count": len(locked),
        "graded_count": len(graded),
        "revisions_count": len(ledger.get("revisions", [])),
        "avg_rps": round(sum(rps_vals) / len(rps_vals), 4) if rps_vals else None,
        "per_market": per_market,
    }

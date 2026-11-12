"""Mathematical & Theoretical Calibration Engine for Calico Football Tracker.

Applies quantitative validation principles to international football:
- Ranked Probability Score (RPS) for ordered 1X2 match outcomes
- Multiplicative vig removal (devigging) for consensus bookmaker baselines
- Negative Binomial over-dispersed discrete count tails (Corners)
- Per-market Brier Score, Forecast SD, Calibration Bins & Paired t-tests
- Empirical Bayes shrinkage and walk-forward sample-size guards (N >= 100)
- Pre-publish Sanity Gate blocking flat templates or silent fallback bugs
"""

import math
import statistics
from typing import List, Dict, Any, Optional, Tuple


def calculate_expected_hits(probabilities: List[float]) -> float:
    """Calculates Expected Hits: E = sum(p_i)."""
    return round(sum(probabilities), 2)


def calculate_brier_score(forecasts: List[float], outcomes: List[int]) -> float:
    """Calculates Brier Score: BS = (1/N) * sum((f_t - o_t)^2).

    o_t is 1 for win, 0 for loss. Pushes are excluded from calculation.
    """
    if not forecasts or not outcomes or len(forecasts) != len(outcomes):
        return 0.0
    n = len(forecasts)
    total_sq_err = sum((f - o) ** 2 for f, o in zip(forecasts, outcomes))
    return round(total_sq_err / n, 4)


def calculate_rps(probs_3way: Tuple[float, float, float], outcome_idx: int) -> float:
    """Calculates Ranked Probability Score (RPS) for ordered [Home, Draw, Away] outcomes.

    outcome_idx: 0 (Home Win), 1 (Draw), 2 (Away Win).
    Lower is better (sharp international benchmark ~ 0.190 - 0.205).
    """
    p_sum = 0.0
    o_sum = 0.0
    rps_sum = 0.0
    for k in range(2):
        p_sum += probs_3way[k]
        if outcome_idx == k:
            o_sum += 1.0
        rps_sum += (p_sum - o_sum) ** 2
    return round(rps_sum / 2.0, 5)


def calculate_expected_value(model_prob: float, odds: float) -> float:
    """Calculates EV: EV = (P_model * Odds) - 1."""
    return round((model_prob * odds) - 1.0, 4)


def multiplicative_devig(odds_list: List[float]) -> List[float]:
    """Converts raw decimal bookmaker odds into true vig-free implied probabilities."""
    inv = [1.0 / o if o and o > 1.0 else 0.0 for o in odds_list]
    total = sum(inv)
    if total <= 0:
        n = max(1, len(odds_list))
        return [1.0 / n] * len(odds_list)
    return [x / total for x in inv]


def apply_shrinkage(prob: float, prior_mean: float = 0.50, weight: float = 0.85) -> float:
    """Shrinks an extreme probability toward the prior/base rate: p' = m + w * (p - m)."""
    shrunk = prior_mean + weight * (prob - prior_mean)
    return round(min(0.99, max(0.01, shrunk)), 4)


def empirical_bayes_mean(observed_sum: float, count: int, prior_mean: float, prior_strength: float = 4.0) -> float:
    """Applies Empirical Bayes shrinkage toward a stable prior mean for small-sample international teams."""
    return (observed_sum + prior_strength * prior_mean) / (count + prior_strength)


def neg_binom_cdf(k_max: int, mu: float, variance: float) -> float:
    """Computes P(X <= k_max) for a Negative Binomial with given mean mu and variance > mu."""
    mu = max(0.1, mu)
    var = max(variance, mu * 1.02)
    p = mu / var
    r = (mu * p) / (1.0 - p)
    log_p = math.log(p)
    log_q = math.log(1.0 - p)
    lg_r = math.lgamma(r)

    cdf = 0.0
    for k in range(k_max + 1):
        log_pmf = math.lgamma(k + r) - lg_r - math.lgamma(k + 1) + r * log_p + k * log_q
        cdf += math.exp(log_pmf)
    return min(1.0, max(0.0, cdf))


def neg_binom_over_prob(mu: float, variance: float, line: float = 9.5) -> float:
    """Computes P(X > line) using over-dispersed Negative Binomial tail (e.g. Corners Over 9.5)."""
    k_max = int(math.floor(line))
    return round(min(0.99, max(0.01, 1.0 - neg_binom_cdf(k_max, mu, variance))), 4)


def _paired_t_stat(model_briers: List[float], ref_briers: List[float]) -> Optional[float]:
    """Paired t-statistic of (model_brier - ref_brier). Negative values indicate model beats baseline."""
    if len(model_briers) < 5 or len(model_briers) != len(ref_briers):
        return None
    diffs = [m - r for m, r in zip(model_briers, ref_briers)]
    mean_d = statistics.mean(diffs)
    stdev_d = statistics.stdev(diffs)
    if stdev_d == 0:
        return 0.0
    return round(mean_d / (stdev_d / math.sqrt(len(diffs))), 2)


def evaluate_market_calibration(records: List[Dict[str, Any]], market_label: str = "All") -> Dict[str, Any]:
    """Computes comprehensive walk-forward/forward-test calibration diagnostics for a market slice."""
    forecasts: List[float] = []
    outcomes: List[int] = []
    market_probs: List[float] = []

    for r in records:
        status = str(r.get("status", "")).upper()
        p = r.get("prob") if r.get("prob") is not None else r.get("model_prob")
        if p is None or r.get("is_pass"):
            continue
        if "HIT" in status:
            forecasts.append(float(p))
            outcomes.append(1)
        elif "MISS" in status:
            forecasts.append(float(p))
            outcomes.append(0)
        else:
            continue

        odds = r.get("odds") or r.get("closing_odds")
        if odds and float(odds) > 1.0:
            # Estimate conservative devigged implied baseline (~5% vig haircut for single-side display odds)
            market_probs.append(min(0.95, max(0.05, (1.0 / float(odds)) * 0.955)))
        else:
            market_probs.append(0.50)

    n = len(forecasts)
    if n == 0:
        return {
            "market": market_label,
            "n": 0,
            "min_sample_ok": False,
            "brier": 0.0,
            "base_brier": 0.0,
            "market_brier": 0.0,
            "forecast_mean": 0.0,
            "actual_rate": 0.0,
            "forecast_sd": 0.0,
            "t_vs_base": None,
            "t_vs_market": None,
            "bins": []
        }

    actual_rate = sum(outcomes) / n
    model_briers = [(f - o) ** 2 for f, o in zip(forecasts, outcomes)]
    base_briers = [(actual_rate - o) ** 2 for o in outcomes]
    mkt_briers = [(mp - o) ** 2 for mp, o in zip(market_probs, outcomes)]

    bins_def = [
        ("40-55%", 0.0, 0.55),
        ("55-65%", 0.55, 0.65),
        ("65-75%", 0.65, 0.75),
        ("75%+", 0.75, 1.01),
    ]
    bins = []
    for label, lo, hi in bins_def:
        idxs = [i for i, f in enumerate(forecasts) if lo <= f < hi]
        if idxs:
            pred_avg = sum(forecasts[i] for i in idxs) / len(idxs)
            hit_avg = sum(outcomes[i] for i in idxs) / len(idxs)
            bins.append({
                "bin": label,
                "count": len(idxs),
                "pred_pct": round(pred_avg * 100, 1),
                "actual_pct": round(hit_avg * 100, 1),
            })

    return {
        "market": market_label,
        "n": n,
        "min_sample_ok": n >= 100,
        "brier": round(sum(model_briers) / n, 4),
        "base_brier": round(sum(base_briers) / n, 4),
        "market_brier": round(sum(mkt_briers) / n, 4),
        "forecast_mean": round(statistics.mean(forecasts) * 100, 1),
        "actual_rate": round(actual_rate * 100, 1),
        "forecast_sd": round(statistics.pstdev(forecasts) * 100, 2) if n >= 2 else 0.0,
        "t_vs_base": _paired_t_stat(model_briers, base_briers),
        "t_vs_market": _paired_t_stat(model_briers, mkt_briers),
        "bins": bins,
    }


def sanity_gate(pending_matches: List[Dict[str, Any]], strict_teams: bool = False) -> List[str]:
    """Blocks publishing flat templates, corrupted probabilities, or silent lookup fallbacks.

    Returns a list of failure reasons (empty list means safe to publish).
    """
    reasons: List[str] = []
    if not pending_matches:
        return reasons

    by_market: Dict[str, List[float]] = {
        "Match Result": [],
        "Goal Total": [],
        "BTTS": [],
        "Corners": [],
    }
    unmapped = []

    for m in pending_matches:
        if m.get("unmapped_team"):
            unmapped.append(m.get("fixture", m.get("id", "unknown")))

        p_h = m.get("p_h")
        p_d = m.get("p_d")
        p_a = m.get("p_a")
        if p_h is not None and p_d is not None and p_a is not None:
            total_1x2 = p_h + p_d + p_a
            if not (0.98 <= total_1x2 <= 1.02):
                reasons.append(f"{m.get('fixture')}: 1X2 probabilities sum to {total_1x2:.3f}")

        for key, label in [
            ("result_pick", "Match Result"),
            ("goal_total_pick", "Goal Total"),
            ("btts_pick", "BTTS"),
            ("corner_pick", "Corners"),
        ]:
            pick = m.get(key)
            if isinstance(pick, dict) and pick.get("prob") is not None:
                prob = float(pick["prob"])
                if not (0.01 <= prob <= 0.99):
                    reasons.append(f"{m.get('fixture')} [{label}]: probability {prob} out of [0.01, 0.99]")
                if not pick.get("is_pass"):
                    by_market[label].append(prob)

        res_pick = m.get("result_pick") or {}
        gt_pick = m.get("goal_total_pick") or {}
        btts_pick = m.get("btts_pick") or {}
        cor_pick = m.get("corner_pick") or {}

        # Verify 1X2 active pick matches highest probability outcome
        if (
            not res_pick.get("is_pass")
            and res_pick.get("selection") in ("Home Win", "Draw", "Away Win")
            and p_h is not None and p_d is not None and p_a is not None
        ):
            top_1x2 = max([("Home Win", p_h), ("Draw", p_d), ("Away Win", p_a)], key=lambda x: x[1])[0]
            if res_pick["selection"] != top_1x2:
                reasons.append(f"{m.get('fixture')}: Result pick {res_pick['selection']} contradicts top 1X2 outcome {top_1x2}")

        # Verify predicted exact score aligns with all active directional picks
        pred_score = m.get("pred_score")
        if pred_score and "-" in str(pred_score):
            try:
                hg, ag = map(int, str(pred_score).split("-", 1))
                tot_g = hg + ag
                sc_res = "Home Win" if hg > ag else ("Away Win" if ag > hg else "Draw")
                sc_gt = "Over 2.5" if tot_g >= 3 else "Under 2.5"
                sc_btts = "BTTS Yes" if (hg > 0 and ag > 0) else "BTTS No"

                if not res_pick.get("is_pass") and res_pick.get("selection") in ("Home Win", "Draw", "Away Win"):
                    if res_pick["selection"] != sc_res:
                        reasons.append(f"{m.get('fixture')}: pred_score {pred_score} contradicts {res_pick['selection']}")
                if not gt_pick.get("is_pass") and gt_pick.get("selection") in ("Over 2.5", "Under 2.5"):
                    if gt_pick["selection"] != sc_gt:
                        reasons.append(f"{m.get('fixture')}: pred_score {pred_score} contradicts {gt_pick['selection']}")
                if not btts_pick.get("is_pass") and btts_pick.get("selection") in ("BTTS Yes", "BTTS No"):
                    if btts_pick["selection"] != sc_btts:
                        reasons.append(f"{m.get('fixture')}: pred_score {pred_score} contradicts {btts_pick['selection']}")
            except ValueError:
                reasons.append(f"{m.get('fixture')}: invalid pred_score '{pred_score}'")

        # Verify expected mean sits on the same side of the line as active O/U picks
        xg_tot = (m.get("real_goal_stats") or {}).get("expectedXg")
        if xg_tot is not None and not gt_pick.get("is_pass") and gt_pick.get("selection"):
            if (gt_pick["selection"] == "Over 2.5" and xg_tot < 2.5) or (gt_pick["selection"] == "Under 2.5" and xg_tot > 2.5):
                reasons.append(f"{m.get('fixture')}: expectedXg {xg_tot} contradicts {gt_pick['selection']}")

        exp_cor = (m.get("real_corner_stats") or {}).get("expectedCorners")
        if exp_cor is not None and not cor_pick.get("is_pass") and cor_pick.get("selection"):
            if (cor_pick["selection"] == "Corners Over 9.5" and exp_cor < 9.5) or (cor_pick["selection"] == "Corners Under 9.5" and exp_cor > 9.5):
                reasons.append(f"{m.get('fixture')}: expectedCorners {exp_cor} contradicts {cor_pick['selection']}")

    for label, ps in by_market.items():
        if len(ps) >= 3:
            sd = statistics.pstdev(ps)
            if sd < 0.015:
                reasons.append(f"{label}: flat/constant forecasts across slate (SD {sd*100:.2f}pp < 1.50pp)")

    if strict_teams and unmapped:
        reasons.append(f"Unmapped international teams detected: {', '.join(unmapped[:5])}")

    return reasons


def evaluate_summary_metrics(graded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes the full dashboard matrix from a list of graded fixture records.

    Expected keys per record:
    - 'model_prob': float (e.g. 0.65)
    - 'closing_odds': float (e.g. 1.60)
    - 'status': 'HIT' | 'MISS' | 'PUSH'
    - 'net_variance': float
    - 'beat_clv': bool (optional)
    """
    total_selections = len(graded_rows)
    actual_hits = 0
    actual_misses = 0
    pushes = 0
    total_net_units = 0.0

    forecasts: List[float] = []
    outcomes: List[int] = []
    clv_beats = 0
    clv_total = 0

    all_model_probs = [r['model_prob'] for r in graded_rows]
    expected_hits = calculate_expected_hits(all_model_probs)

    for r in graded_rows:
        status = r['status'].upper()
        units = r.get('net_variance', 0.0)
        total_net_units += units

        if 'HIT' in status:
            actual_hits += 1
            forecasts.append(r['model_prob'])
            outcomes.append(1)
        elif 'MISS' in status:
            actual_misses += 1
            forecasts.append(r['model_prob'])
            outcomes.append(0)
        elif 'PUSH' in status:
            pushes += 1

        if 'beat_clv' in r:
            clv_total += 1
            if r['beat_clv']:
                clv_beats += 1

    decided_bets = actual_hits + actual_misses
    hit_rate = (actual_hits / decided_bets * 100) if decided_bets > 0 else 0.0
    roi = (total_net_units / total_selections * 100) if total_selections > 0 else 0.0
    brier = calculate_brier_score(forecasts, outcomes)
    clv_pct = (clv_beats / clv_total * 100) if clv_total > 0 else 0.0

    return {
        'total_selections': total_selections,
        'actual_hits': actual_hits,
        'actual_misses': actual_misses,
        'pushes': pushes,
        'expected_hits': expected_hits,
        'brier_score': brier,
        'hit_rate_pct': round(hit_rate, 2),
        'net_units': round(total_net_units, 2),
        'roi_pct': round(roi, 2),
        'clv_beat_pct': round(clv_pct, 1)
    }

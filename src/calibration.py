"""Mathematical & Theoretical Calibration Engine for Forward Ledger.

Formulas:
- Expected Hits: E = sum(p_i)
- Brier Score: BS = (1/N) * sum((f_t - o_t)^2)
- Expected Value: EV = (P_model * Odds) - 1
- CLV Beat %: sum(1 if P_fair > P_open else 0) / N
"""

from typing import List, Dict, Any, Tuple


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


def calculate_expected_value(model_prob: float, odds: float) -> float:
    """Calculates EV: EV = (P_model * Odds) - 1."""
    return round((model_prob * odds) - 1.0, 4)


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

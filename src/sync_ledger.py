"""Local Calico Football Tracker Sync & Per-Market Calibration Evaluator.

Parses LEDGER.md and src/data.json, recalculates summary and per-market metrics
(Brier Score, Forecast SD, Calibration Bins, Paired t-stats vs baseline, Sanity Gate),
and verifies data integrity.
"""

import json
import sys
import re
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.calibration import (
        evaluate_market_calibration,
        evaluate_summary_metrics,
        sanity_gate,
    )
except ModuleNotFoundError:
    from calibration import (
        evaluate_market_calibration,
        evaluate_summary_metrics,
        sanity_gate,
    )

if sys.stdout and getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def parse_and_evaluate_ledger(ledger_path: Path):
    if not ledger_path.exists():
        print(f"File not found: {ledger_path}")
        return

    content = ledger_path.read_text(encoding='utf-8')

    section3_match = re.search(r"## 3\. Historical Repository & Grading Log.*?(?=## 4|$)", content, re.DOTALL)
    if not section3_match:
        print("Could not locate Section 3 in LEDGER.md")
        return

    section3_text = section3_match.group(0)
    lines = section3_text.splitlines()

    graded_rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or ":---" in line or "Match ID" in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 11:
            try:
                match_id = parts[0]
                fixture = parts[3]
                selection = parts[4]
                model_prob = float(parts[5].replace("%", "").strip()) / 100.0
                closing_odds = float(parts[6].strip())
                result_status = parts[9]
                net_var = float(parts[10].replace("u", "").replace("+", "").strip())

                graded_rows.append({
                    'match_id': match_id,
                    'fixture': fixture,
                    'selection': selection,
                    'model_prob': model_prob,
                    'closing_odds': closing_odds,
                    'status': result_status,
                    'net_variance': net_var
                })
            except Exception:
                continue

    print(f"Parsed {len(graded_rows)} historical graded matches from LEDGER.md")
    if graded_rows:
        metrics = evaluate_summary_metrics(graded_rows)
        print("\n" + "=" * 62)
        print(" RECALCULATED CALIBRATION & PERFORMANCE DASHBOARD")
        print("=" * 62)
        print(f" Total Selections:     {metrics['total_selections']}")
        print(f" Actual Hits:          {metrics['actual_hits']}")
        print(f" Expected Hits:        {metrics['expected_hits']} (Sum of model probs)")
        print(f" Brier Score:          {metrics['brier_score']} (Benchmark: <0.2000)")
        print(f" Hit Rate:             {metrics['hit_rate_pct']}%")
        print(f" Net P/L:              {'+' if metrics['net_units'] > 0 else ''}{metrics['net_units']}u")
        print(f" ROI / Yield:          {metrics['roi_pct']}%")
        print("=" * 62)

    data_path = ledger_path.parent / "src" / "data.json"
    if data_path.exists():
        try:
            data = json.loads(data_path.read_text(encoding='utf-8'))
            graded_json = data.get("graded", [])
            pending_json = data.get("pending", [])

            if graded_json:
                print("\n PER-MARKET CALIBRATION & VARIANCE DIAGNOSTICS (Graded N={})".format(len(graded_json)))
                print("-" * 62)
                for key, label in [
                    ("result_pick", "Match Result (1X2)"),
                    ("goal_total_pick", "Goal Total (O/U 2.5)"),
                    ("btts_pick", "BTTS"),
                    ("corner_pick", "Corners (O/U 9.5)"),
                ]:
                    recs = [m[key] for m in graded_json if isinstance(m.get(key), dict)]
                    cal = evaluate_market_calibration(recs, label)
                    sample_tag = "OK" if cal["min_sample_ok"] else f"LOW N<{100}"
                    t_base = f"{cal['t_vs_base']:+.2f}" if cal["t_vs_base"] is not None else "n/a"
                    print(
                        f" {label:<22} N={cal['n']:<3} ({sample_tag}) | Brier {cal['brier']:.4f} "
                        f"(Base {cal['base_brier']:.4f}, t={t_base}) | SD {cal['forecast_sd']:.1f}pp | "
                        f"Pred {cal['forecast_mean']:.1f}% vs Hit {cal['actual_rate']:.1f}%"
                    )

            if pending_json:
                gate_issues = sanity_gate(pending_json, strict_teams=False)
                print("-" * 62)
                if gate_issues:
                    print(f" SANITY GATE ALERTS ({len(gate_issues)}):")
                    for issue in gate_issues:
                        print(f"  - {issue}")
                else:
                    print(f" SANITY GATE: PASSED ({len(pending_json)} active pending fixtures validated)")
            print("=" * 62)
        except Exception as exc:
            print(f"Could not evaluate extended data.json diagnostics: {exc}")


if __name__ == '__main__':
    ledger_file = root_dir / 'LEDGER.md'
    parse_and_evaluate_ledger(ledger_file)

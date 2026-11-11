"""Local Forward Ledger Sync & Calibration Evaluator.

Parses LEDGER.md, recalculates summary metrics using closed-form calibration
formulas, and verifies data integrity.
"""

import sys
import re
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.calibration import evaluate_summary_metrics
except ModuleNotFoundError:
    from calibration import evaluate_summary_metrics

if sys.stdout and getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def parse_and_evaluate_ledger(ledger_path: Path):
    if not ledger_path.exists():
        print(f"❌ File not found: {ledger_path}")
        return

    content = ledger_path.read_text(encoding='utf-8')

    # Find Section 3: Historical Repository & Grading Log
    section3_match = re.search(r"## 3\. Historical Repository & Grading Log.*?(?=## 4|$)", content, re.DOTALL)
    if not section3_match:
        print("❌ Could not locate Section 3 in LEDGER.md")
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

    print(f"📊 Parsed {len(graded_rows)} historical graded matches from LEDGER.md")
    if not graded_rows:
        return

    metrics = evaluate_summary_metrics(graded_rows)

    print("\n" + "=" * 55)
    print(" 📈 RECALCULATED CALIBRATION & PERFORMANCE DASHBOARD")
    print("=" * 55)
    print(f" Total Selections:     {metrics['total_selections']}")
    print(f" Actual Hits:          {metrics['actual_hits']}")
    print(f" Expected Hits:        {metrics['expected_hits']} (Sum of model probs)")
    print(f" Brier Score:          {metrics['brier_score']} (Threshold: <0.2000 is elite)")
    print(f" Hit Rate:             {metrics['hit_rate_pct']}%")
    print(f" Net P/L:              {'+' if metrics['net_units'] > 0 else ''}{metrics['net_units']}u")
    print(f" ROI / Yield:          {metrics['roi_pct']}%")
    print("=" * 55)

    if metrics['actual_hits'] > metrics['expected_hits']:
        print(" 🎯 Calibration State: Actual > Expected (Positive Variance / Model Under-confidence)")
    elif metrics['actual_hits'] < metrics['expected_hits']:
        print(" ⚠️ Calibration State: Actual < Expected (Negative Variance / Model Over-confidence)")
    else:
        print(" 🎯 Calibration State: Exact calibration match!")
    print("=" * 55)


if __name__ == '__main__':
    root_dir = Path(__file__).parent.parent
    ledger_file = root_dir / 'LEDGER.md'
    parse_and_evaluate_ledger(ledger_file)

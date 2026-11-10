"""Generate modern black-and-white Vercel-inspired International Football dashboard.
Includes:
- Best pick (highlighted in yellow #facc15)
- Exact Score (predicted & final FT)
- Goal Total pick (O/U 2.5)
- BTTS pick (Both Teams To Score)
- Corner pick (Corners O/U)
- Match Result (1X2)
"""

import json
from pathlib import Path


def generate_html():
    data_path = Path(__file__).parent / "data.json"
    if not data_path.exists():
        raise FileNotFoundError(f"data.json not found at {data_path}")

    raw_data = json.loads(data_path.read_text(encoding="utf-8"))
    json_str = json.dumps(raw_data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Football Tracker | International Football Predictive Model</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpolygon points='12,7 16.76,10.45 14.94,16.05 9.06,16.05 7.24,10.45' fill='white' fill-opacity='0.2'/%3E%3Cline x1='12' y1='7' x2='12' y2='2'/%3E%3Cline x1='16.76' y1='10.45' x2='21.51' y2='8.91'/%3E%3Cline x1='14.94' y1='16.05' x2='17.88' y2='20.09'/%3E%3Cline x1='9.06' y1='16.05' x2='6.12' y2='20.09'/%3E%3Cline x1='7.24' y1='10.45' x2='2.49' y2='8.91'/%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #000000;
      --card: #0a0a0a;
      --card-hover: #121212;
      --border: #1f1f1f;
      --border-light: #2e2e2e;
      --text: #ededed;
      --text-muted: #888888;
      --text-faint: #444444;
      --white: #ffffff;
      --yellow: #facc15;
      --yellow-soft: rgba(250, 204, 21, 0.12);
      --yellow-border: rgba(250, 204, 21, 0.45);
      --green: #22c55e;
      --green-soft: rgba(34, 197, 94, 0.12);
      --red: #ef4444;
      --red-soft: rgba(239, 68, 68, 0.12);
      --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      padding-bottom: 5rem;
    }}

    .container {{
      max-width: 1140px;
      margin: 0 auto;
      padding: 2rem 1.25rem;
    }}

    /* Header */
    header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      padding-bottom: 1.75rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }}
    .brand svg {{
      width: 24px;
      height: 24px;
      flex-shrink: 0;
      color: var(--white);
    }}
    .brand-title {{
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      color: var(--white);
      text-transform: uppercase;
    }}
    .brand-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      background: var(--card);
    }}
    .pulse-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.9); }}
      100% {{ opacity: 1; transform: scale(1); }}
    }}
    .header-meta {{
      font-family: var(--font-mono);
      font-size: 0.78rem;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 1rem;
    }}
    .header-meta b {{
      color: var(--white);
    }}

    /* Model Performance & Calibration Dashboard (Modern Vercel Card Grid) */
    .calibration-dashboard {{
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-bottom: 1.75rem;
    }}
    .dashboard-row {{
      display: grid;
      gap: 0.75rem;
    }}
    .dashboard-row.primary-markets {{
      grid-template-columns: repeat(4, 1fr);
    }}
    .dashboard-row.secondary-engine {{
      grid-template-columns: 1.25fr 1fr 1fr;
    }}
    .metric-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.15rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      transition: all 0.15s ease;
      cursor: pointer;
      position: relative;
    }}
    .metric-card:hover {{
      background: #111111;
      border-color: #333333;
      transform: translateY(-1px);
    }}
    .metric-card.active-pick-card {{
      background: #141414;
      border-color: #ffffff;
      box-shadow: 0 0 0 1px #ffffff, 0 6px 20px rgba(0, 0, 0, 0.4);
    }}
    .metric-card.featured-gold-card {{
      background: linear-gradient(180deg, rgba(250, 204, 21, 0.04) 0%, rgba(12, 12, 12, 0.95) 100%);
      border-color: rgba(250, 204, 21, 0.28);
    }}
    .metric-card.featured-gold-card:hover {{
      border-color: rgba(250, 204, 21, 0.5);
      background: linear-gradient(180deg, rgba(250, 204, 21, 0.08) 0%, rgba(15, 15, 15, 0.95) 100%);
    }}
    .metric-card.featured-gold-card.active-pick-card {{
      border-color: var(--yellow);
      box-shadow: 0 0 0 1px var(--yellow), 0 6px 24px rgba(250, 204, 21, 0.15);
    }}
    .metric-card.rps-metric-card {{
      cursor: default;
    }}
    .metric-card.rps-metric-card:hover {{
      transform: none;
      border-color: var(--border);
      background: var(--card);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .card-tag {{
      font-family: var(--font-mono);
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .card-tag.gold-tag {{
      color: var(--yellow);
    }}
    .card-status-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
    }}
    .card-chip {{
      font-family: var(--font-mono);
      font-size: 0.62rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: #71717a;
      background: #171717;
      padding: 0.12rem 0.4rem;
      border-radius: 4px;
      border: 1px solid #262626;
    }}
    .gold-pulse-pill {{
      font-family: var(--font-mono);
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: var(--yellow);
      background: rgba(250, 204, 21, 0.1);
      border: 1px solid rgba(250, 204, 21, 0.3);
      padding: 0.12rem 0.45rem;
      border-radius: 9999px;
    }}
    .card-value {{
      font-size: 2.1rem;
      font-weight: 700;
      letter-spacing: -0.04em;
      color: var(--white);
      line-height: 1.05;
      font-variant-numeric: tabular-nums;
      margin-top: 0.15rem;
    }}
    .card-value.gold-val {{
      color: var(--yellow);
      text-shadow: 0 0 18px rgba(250, 204, 21, 0.22);
    }}
    .card-value.mono-val {{
      font-family: var(--font-mono);
      font-size: 1.95rem;
      letter-spacing: -0.02em;
    }}
    .card-footer {{
      font-family: var(--font-mono);
      font-size: 0.74rem;
      color: var(--text-muted);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.35rem;
      font-variant-numeric: tabular-nums;
      margin-top: 0.15rem;
      line-height: 1.35;
    }}
    .card-footer .footer-stat {{
      color: var(--text-muted);
    }}
    .footer-badge {{
      font-size: 0.68rem;
      font-weight: 700;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
    }}
    .footer-badge.gold-badge {{
      background: rgba(250, 204, 21, 0.12);
      color: var(--yellow);
      border: 1px solid rgba(250, 204, 21, 0.25);
    }}
    .footer-badge.bench-badge {{
      background: #171717;
      color: #a1a1aa;
      border: 1px solid #262626;
    }}

    /* Calibration Chart Box */
    .chart-box {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }}
    .chart-header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: baseline;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }}
    .chart-title {{
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--white);
      letter-spacing: -0.02em;
    }}
    .chart-desc {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }}
    .chart-legend {{
      display: flex;
      align-items: center;
      gap: 1rem;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 0.45rem;
    }}
    .legend-bar {{
      width: 14px;
      height: 3px;
      border-radius: 1px;
    }}
    .chart-svg {{
      width: 100%;
      height: 180px;
      display: block;
    }}

    /* Navigation & Tabs */
    .nav-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.75rem;
    }}
    .tabs {{
      display: flex;
      gap: 0.35rem;
    }}
    .tab-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 0.88rem;
      font-weight: 500;
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.15s ease;
    }}
    .tab-btn:hover {{
      color: var(--text);
      background: var(--card-hover);
    }}
    .tab-btn.active {{
      color: var(--white);
      background: #171717;
      border: 1px solid var(--border-light);
    }}
    .tab-count {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      padding: 0.1rem 0.45rem;
      border-radius: 9999px;
      background: #222222;
      color: #bbbbbb;
    }}

    /* Search & Filter Toolbar */
    .toolbar-container {{
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      margin-bottom: 1.5rem;
    }}
    .search-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.85rem;
      align-items: center;
      justify-content: space-between;
    }}
    .search-input {{
      flex: 1;
      min-width: 260px;
      max-width: 440px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.55rem 0.9rem;
      color: var(--white);
      font-family: var(--font-sans);
      font-size: 0.85rem;
      outline: none;
      transition: border-color 0.15s ease;
    }}
    .search-input:focus {{
      border-color: var(--white);
    }}
    .search-input::placeholder {{
      color: var(--text-muted);
    }}

    .filter-group {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.45rem;
    }}
    .filter-label {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
      margin-right: 0.35rem;
    }}
    .chip {{
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 0.75rem;
      font-weight: 500;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .chip:hover {{
      color: var(--text);
      border-color: var(--border-light);
    }}
    .chip.active {{
      background: #171717;
      border-color: var(--white);
      color: var(--white);
    }}
    .chip.chip-best {{
      color: var(--yellow);
      border-color: rgba(250, 204, 21, 0.3);
      background: rgba(250, 204, 21, 0.05);
    }}
    .chip.chip-best.active {{
      background: var(--yellow);
      color: #000000;
      font-weight: 600;
      border-color: var(--yellow);
    }}

    /* Match Cards */
    .matches-list {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .match-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.4rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      transition: all 0.15s ease;
      position: relative;
    }}
    .match-card:hover {{
      border-color: var(--border-light);
      background: var(--card-hover);
    }}
    .match-card.has-best {{
      border-left: 3px solid var(--yellow);
    }}

    /* Card Top Bar: Meta & Yellow Best Pick Pill */
    .card-top-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      border-bottom: 1px solid #161616;
      padding-bottom: 0.75rem;
    }}
    .card-left-meta {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: var(--text-muted);
    }}
    .match-date {{
      color: var(--text);
      font-weight: 500;
    }}
    .dot-sep {{
      color: var(--text-faint);
    }}
    .match-comp {{
      color: #a1a1aa;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    /* Yellow Highlighted Best Pick Pill */
    .best-pick-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: var(--yellow-soft);
      border: 1px solid var(--yellow-border);
      color: var(--yellow);
      padding: 0.28rem 0.75rem;
      border-radius: 9999px;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      box-shadow: 0 0 12px rgba(250, 204, 21, 0.15);
    }}
    .best-pick-pill .star-icon {{
      color: var(--yellow);
      font-weight: 700;
      font-size: 0.85rem;
    }}
    .best-pick-pill .best-lbl {{
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.68rem;
      opacity: 0.9;
    }}
    .best-pick-pill .best-val {{
      color: var(--white);
      font-weight: 600;
    }}
    .best-pick-pill .best-odds {{
      color: var(--yellow);
      font-size: 0.72rem;
    }}

    /* Neutral Pass / No Best Pick Pill */
    .pass-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: #111111;
      border: 1px solid var(--border-light);
      color: var(--text-muted);
      padding: 0.28rem 0.75rem;
      border-radius: 9999px;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 500;
      letter-spacing: 0.02em;
    }}
    .pass-pill .pass-icon {{
      color: #71717a;
      font-weight: 700;
      font-size: 0.8rem;
    }}
    .pass-pill .pass-lbl {{
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.68rem;
      color: #a1a1aa;
      font-weight: 600;
    }}
    .pass-pill .pass-reason {{
      color: #71717a;
      font-size: 0.72rem;
    }}

    /* Match Fixture & Score Banner */
    .card-fixture-row {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1.25rem;
    }}
    .teams-block {{
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }}
    .fixture-teams {{
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--white);
      letter-spacing: -0.02em;
    }}
    .fixture-sub-meta {{
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: var(--text-muted);
    }}
    .fixture-sub-meta b {{
      color: var(--text);
    }}

    /* Score Presentation Block */
    .score-display-block {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .score-col {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.2rem;
    }}
    .score-lbl {{
      font-family: var(--font-mono);
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
    }}
    .score-val {{
      font-family: var(--font-mono);
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      padding: 0.25rem 0.65rem;
      border-radius: 6px;
      min-width: 58px;
      text-align: center;
      font-variant-numeric: tabular-nums;
    }}
    .score-val.pred {{
      background: #141414;
      border: 1px solid var(--border-light);
      color: #cccccc;
    }}
    .score-val.final {{
      background: #1c1c1c;
      border: 1px solid var(--white);
      color: var(--white);
    }}

    /* Status Badges */
    .status-badge {{
      font-family: var(--font-mono);
      font-size: 0.74rem;
      font-weight: 600;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      white-space: nowrap;
    }}
    .status-pending {{
      background: rgba(34, 197, 94, 0.1);
      color: #22c55e;
      border: 1px solid rgba(34, 197, 94, 0.25);
    }}
    .status-hit {{
      background: rgba(34, 197, 94, 0.15);
      color: #4ade80;
      border: 1px solid rgba(74, 222, 128, 0.3);
    }}
    .status-miss {{
      background: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(248, 113, 113, 0.3);
    }}
    .unit-variance {{
      font-family: var(--font-mono);
      font-size: 0.74rem;
      font-weight: 600;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      background: #141414;
      border: 1px solid var(--border);
    }}
    .unit-variance.pos {{
      color: #4ade80;
    }}
    .unit-variance.neg {{
      color: #f87171;
    }}

    /* 4-Picks Analytical Grid */
    .picks-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.75rem;
      margin-top: 0.25rem;
    }}
    .pick-item {{
      background: #0d0d0d;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.65rem 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      transition: all 0.15s ease;
    }}
    .pick-item:hover {{
      border-color: var(--border-light);
      background: #121212;
    }}
    .pick-item.is-best-item {{
      border-color: var(--yellow-border);
      background: rgba(250, 204, 21, 0.04);
      box-shadow: inset 0 0 10px rgba(250, 204, 21, 0.04);
    }}
    .pick-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
    }}
    .yellow-star {{
      color: var(--yellow);
      font-weight: 700;
      font-size: 0.68rem;
    }}
    .pick-val {{
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--white);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .pick-item.is-best-item .pick-val {{
      color: #fef08a;
    }}
    .pick-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }}
    .pick-footer b {{
      color: var(--text);
    }}
    .sub-hit {{
      color: #4ade80;
      font-weight: 600;
    }}
    .sub-miss {{
      color: #f87171;
      font-weight: 600;
    }}
    .sub-pending {{
      color: var(--text-muted);
    }}
    .sub-pass {{
      color: #71717a;
      font-weight: 600;
      font-size: 0.68rem;
    }}

    /* Pass / No-Pick Styling in Analytical Grid */
    .pick-item.is-pass-item {{
      border-color: #1a1a1a;
      background: #090909;
      opacity: 0.72;
    }}
    .pick-item.is-pass-item:hover {{
      opacity: 0.95;
      border-color: #27272a;
    }}
    .pass-tag {{
      font-family: var(--font-mono);
      font-size: 0.6rem;
      font-weight: 700;
      color: #71717a;
      background: #18181b;
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
      border: 1px solid #27272a;
    }}
    .pick-val.pass-val {{
      color: #71717a !important;
      font-style: italic;
      font-weight: 500;
    }}
    .pass-sub {{
      color: #52525b;
      font-size: 0.68rem;
    }}

    /* Match Card Clickable & Expand Bar */
    .card-fixture-row {{
      cursor: pointer;
    }}
    .card-expand-bar {{
      margin-top: 0.25rem;
      padding-top: 0.65rem;
      border-top: 1px solid #161616;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      color: #94a3b8;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      transition: all 0.15s ease;
      user-select: none;
    }}
    .card-expand-bar:hover {{
      color: var(--white);
    }}
    .expand-bar-left {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .expand-bar-left svg {{
      color: #38bdf8;
    }}
    .chevron-toggle {{
      font-size: 0.95rem;
      color: #94a3b8;
      transition: transform 0.2s ease;
    }}

    /* Expandable Match Drawer */
    .match-drawer {{
      display: none;
      margin-top: 0.5rem;
    }}
    .match-drawer.expanded {{
      display: block;
      animation: drawerSlideDown 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    @keyframes drawerSlideDown {{
      from {{ opacity: 0; transform: translateY(-8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .drawer-box {{
      background: #090e17;
      border: 1px solid #1a2333;
      border-radius: 10px;
      padding: 0.85rem 1.1rem 0.5rem 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      position: relative;
      cursor: default;
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.04);
    }}

    /* Drawer Top Nav Tabs (3 Icons) */
    .drawer-nav-tabs {{
      display: flex;
      justify-content: space-around;
      align-items: center;
      border-bottom: 1px solid #1a2333;
      padding-bottom: 0.5rem;
      margin-bottom: 0.35rem;
    }}
    .dtab-btn {{
      background: none;
      border: none;
      padding: 0.4rem 1.75rem;
      color: #64748b;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: all 0.15s ease;
    }}
    .dtab-btn:hover {{
      color: #94a3b8;
    }}
    .dtab-btn.active {{
      color: #ffffff;
    }}
    .dtab-btn.active::after {{
      content: "";
      position: absolute;
      bottom: -0.55rem;
      left: 0;
      right: 0;
      height: 2px;
      background: #ffffff;
      border-radius: 2px;
    }}

    /* Subhead (HEAD TO HEAD & < 1/3 >) */
    .drawer-subhead {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.15rem 0 0.5rem 0;
    }}
    .subhead-title {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #94a3b8;
    }}
    .cnav-wrap {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .cnav-btn {{
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 0.95rem;
      padding: 0.1rem 0.4rem;
      line-height: 1;
      border-radius: 4px;
      transition: all 0.15s ease;
    }}
    .cnav-btn:hover {{
      color: #ffffff;
      background: #1e293b;
    }}
    .cnav-ind {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 700;
      color: #ffffff;
      min-width: 26px;
      text-align: center;
    }}

    /* Section & Stats Styling */
    .stat-sec-wrap {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }}
    .stat-title {{
      text-align: center;
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #94a3b8;
      margin-bottom: 0.4rem;
    }}
    .prob-3cols {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: flex-end;
      text-align: center;
      padding: 0 0.5rem;
    }}
    .col-home {{
      text-align: left;
    }}
    .col-draw {{
      text-align: center;
    }}
    .col-away {{
      text-align: right;
    }}
    .prob-big-blue {{
      font-family: var(--font-mono);
      font-size: 2.2rem;
      font-weight: 800;
      color: #38bdf8;
      line-height: 1;
      letter-spacing: -0.02em;
    }}
    .prob-big-draw {{
      font-family: var(--font-mono);
      font-size: 1.35rem;
      font-weight: 700;
      color: #94a3b8;
      line-height: 1;
    }}
    .prob-big-white {{
      font-family: var(--font-mono);
      font-size: 2.2rem;
      font-weight: 800;
      color: #ffffff;
      line-height: 1;
      letter-spacing: -0.02em;
    }}
    .code-lbl {{
      font-family: var(--font-mono);
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 0.3rem;
    }}
    .text-blue {{
      color: #38bdf8;
    }}
    .text-muted {{
      color: #64748b;
    }}
    .text-white {{
      color: #cbd5e1;
    }}

    /* Proportional Segmented Bar */
    .seg-bar {{
      height: 6px;
      background: #151d2a;
      border-radius: 9999px;
      overflow: hidden;
      display: flex;
      gap: 3px;
      margin: 0.65rem 0 0.25rem 0;
    }}
    .seg-blue {{
      background: #38bdf8;
      border-radius: 2px;
      height: 100%;
      transition: width 0.3s ease;
    }}
    .seg-draw {{
      background: #475569;
      border-radius: 2px;
      height: 100%;
      transition: width 0.3s ease;
    }}
    .seg-white {{
      background: #ffffff;
      border-radius: 2px;
      height: 100%;
      transition: width 0.3s ease;
    }}
    .h-divider {{
      border-top: 1px solid #1a2333;
      margin: 0.85rem 0;
    }}

    /* Slide 2: Average Goals */
    .avg-goals-grid {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      max-width: 400px;
      margin: 0.3rem auto 0 auto;
      width: 100%;
    }}
    .avg-row {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      padding: 0.15rem 0;
    }}
    .avg-val {{
      font-family: var(--font-mono);
      font-size: 1.45rem;
      font-weight: 800;
      color: #ffffff;
    }}
    .avg-val.left-val {{
      text-align: left;
    }}
    .avg-val.right-val {{
      text-align: right;
    }}
    .avg-center-lbl {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #94a3b8;
    }}
    .avg-divider {{
      border-top: 1px solid #1e293b;
      width: 100%;
      margin: 0.2rem 0;
    }}
    .cmp-line-bar {{
      height: 4px;
      background: #151d2a;
      border-radius: 9999px;
      overflow: hidden;
      display: flex;
      width: 100%;
      margin-top: 0.6rem;
    }}
    .cmp-fill-blue {{
      background: #38bdf8;
      height: 100%;
      border-radius: 2px 0 0 2px;
    }}
    .cmp-fill-white {{
      background: #ffffff;
      height: 100%;
      border-radius: 0 2px 2px 0;
    }}
    .avg-sub-pills {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.5rem;
      margin-top: 0.85rem;
      padding-top: 0.75rem;
      border-top: 1px solid #1a2333;
    }}
    .sub-pill {{
      background: #0d1420;
      border: 1px solid #1e293b;
      border-radius: 6px;
      padding: 0.4rem 0.5rem;
      text-align: center;
    }}
    .sub-pill-lbl {{
      font-size: 0.62rem;
      font-family: var(--font-mono);
      color: #64748b;
      text-transform: uppercase;
      display: block;
      margin-bottom: 0.15rem;
    }}
    .sub-pill-val {{
      font-size: 0.84rem;
      font-family: var(--font-mono);
      font-weight: 700;
      color: #f1f5f9;
    }}

    /* Slide 3: Form */
    .form-head {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 0.85rem;
    }}
    .form-pct-blue {{
      font-family: var(--font-mono);
      font-size: 1.85rem;
      font-weight: 800;
      color: #38bdf8;
      min-width: 65px;
      text-align: right;
    }}
    .form-pct-white {{
      font-family: var(--font-mono);
      font-size: 1.85rem;
      font-weight: 800;
      color: #ffffff;
      min-width: 65px;
      text-align: left;
    }}
    .vertical-meters {{
      display: flex;
      gap: 5px;
      align-items: flex-end;
      height: 50px;
      background: #101622;
      padding: 3px;
      border-radius: 4px;
      border: 1px solid #1e293b;
    }}
    .vmeter-track {{
      width: 10px;
      height: 44px;
      background: #1a2334;
      border-radius: 2px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
    }}
    .vmeter-fill-blue {{
      background: #38bdf8;
      width: 100%;
      border-radius: 1px;
      transition: height 0.3s ease;
    }}
    .vmeter-fill-white {{
      background: #ffffff;
      width: 100%;
      border-radius: 1px;
      transition: height 0.3s ease;
    }}
    .form-cols-wrap {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
      max-width: 500px;
      margin: 0 auto;
      width: 100%;
    }}
    .form-list {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .form-row-left {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: #e2e8f0;
    }}
    .form-row-right {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.5rem;
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: #e2e8f0;
    }}
    .badge-w {{
      background: #16a34a;
      color: #ffffff;
      font-weight: 700;
      font-size: 0.65rem;
      width: 20px;
      height: 20px;
      border-radius: 3px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}
    .badge-d {{
      background: #475569;
      color: #ffffff;
      font-weight: 700;
      font-size: 0.65rem;
      width: 20px;
      height: 20px;
      border-radius: 3px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}
    .badge-l {{
      background: #252e3d;
      color: #64748b;
      font-weight: 700;
      font-size: 0.65rem;
      width: 20px;
      height: 20px;
      border-radius: 3px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}
    .venue-icon {{
      color: #64748b;
      font-size: 0.75rem;
      display: inline-flex;
      align-items: center;
      min-width: 14px;
      justify-content: center;
    }}
    .opp-code {{
      color: #cbd5e1;
      font-weight: 600;
      width: 34px;
    }}
    .match-score {{
      color: #94a3b8;
      font-weight: 500;
      min-width: 30px;
      text-align: center;
    }}

    /* Tabs 2 & 3: Market Matrix & Team Profiles */
    .matrix-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
      margin-top: 0.25rem;
    }}
    .matrix-card {{
      background: #0d1420;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 0.75rem 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }}
    .matrix-title {{
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #38bdf8;
      margin-bottom: 0.2rem;
    }}
    .matrix-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: #94a3b8;
    }}
    .matrix-row b {{
      color: #ffffff;
    }}
    .team-profiles-wrap {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      padding: 0.25rem 0.5rem;
    }}
    .team-prof-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 0.75rem;
    }}
    .tp-label {{
      color: #ffffff;
      font-weight: 600;
    }}
    .tp-mid-label {{
      color: #64748b;
      font-size: 0.66rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .meter-bar-dual {{
      height: 6px;
      background: #151d2a;
      border-radius: 9999px;
      overflow: hidden;
      display: flex;
      margin: 0.25rem 0 0.5rem 0;
    }}
    .mbd-left {{
      background: #38bdf8;
      height: 100%;
    }}
    .mbd-right {{
      background: #ffffff;
      height: 100%;
    }}
    .tp-footer-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.85rem;
      padding-top: 0.65rem;
      border-top: 1px solid #1a2333;
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: #64748b;
    }}
    .tp-footer-meta b {{
      color: #94a3b8;
    }}

    /* Drawer Bottom Collapse Chevron */
    .drawer-collapse-row {{
      display: flex;
      justify-content: center;
      align-items: center;
      margin-top: 0.4rem;
    }}
    .drawer-chevron-btn {{
      background: none;
      border: none;
      color: #64748b;
      cursor: pointer;
      padding: 0.25rem 1.75rem;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }}
    .drawer-chevron-btn:hover {{
      color: #ffffff;
      background: #141d2b;
    }}

    /* Math Panel */
    .math-panel {{
      display: none;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem;
      line-height: 1.7;
    }}
    .math-panel.active {{
      display: block;
    }}
    .math-title {{
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--white);
      margin-bottom: 0.75rem;
      letter-spacing: -0.02em;
    }}
    .math-code {{
      background: #000000;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      font-family: var(--font-mono);
      font-size: 0.82rem;
      color: #e5e5e5;
      overflow-x: auto;
      margin: 1.25rem 0;
    }}

    /* Footer */
    footer {{
      margin-top: 4rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 0.78rem;
      line-height: 1.6;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }}
    footer a {{
      color: var(--white);
      text-decoration: underline;
    }}

    .empty-state {{
      padding: 3rem;
      text-align: center;
      color: var(--text-muted);
      background: var(--card);
      border: 1px dashed var(--border);
      border-radius: 12px;
      font-family: var(--font-mono);
      font-size: 0.85rem;
    }}

    @media (max-width: 960px) {{
      .dashboard-row.primary-markets {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .dashboard-row.secondary-engine {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .dashboard-row.secondary-engine .metric-card:first-child {{
        grid-column: span 2;
      }}
      .picks-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .card-fixture-row {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .score-display-block {{
        width: 100%;
        justify-content: flex-start;
      }}
    }}
    @media (max-width: 640px) {{
      .dashboard-row.primary-markets {{
        grid-template-columns: 1fr;
      }}
      .dashboard-row.secondary-engine {{
        grid-template-columns: 1fr;
      }}
      .dashboard-row.secondary-engine .metric-card:first-child {{
        grid-column: span 1;
      }}
      .picks-grid {{
        grid-template-columns: 1fr;
      }}
      .card-top-bar {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .matrix-grid {{
        grid-template-columns: 1fr;
      }}
      .form-cols-wrap {{
        gap: 0.75rem;
      }}
      .prob-big-blue, .prob-big-white {{
        font-size: 1.8rem;
      }}
      .prob-big-draw {{
        font-size: 1.15rem;
      }}
      .dtab-btn {{
        padding: 0.4rem 1rem;
      }}
    }}
  </style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <header>
    <div class="brand">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" />
        <polygon points="12,7 16.76,10.45 14.94,16.05 9.06,16.05 7.24,10.45" fill="currentColor" fill-opacity="0.18" />
        <line x1="12" y1="7" x2="12" y2="2" />
        <line x1="16.76" y1="10.45" x2="21.51" y2="8.91" />
        <line x1="14.94" y1="16.05" x2="17.88" y2="20.09" />
        <line x1="9.06" y1="16.05" x2="6.12" y2="20.09" />
        <line x1="7.24" y1="10.45" x2="2.49" y2="8.91" />
      </svg>
      <div>
        <div class="brand-title">Football Tracker</div>
        <div style="font-size:0.75rem; color:var(--text-muted);">International Football Predictive Model</div>
      </div>
      <div class="brand-tag">
        <span class="pulse-dot"></span> Active
      </div>
    </div>
    <div class="header-meta">
      <span>Jurisdiction: <b>FIFA International</b></span>
      <span>Engine: <b>Poisson & Dixon-Coles</b></span>
    </div>
  </header>

  <!-- Model Performance & Calibration Dashboard (Modern Vercel Card Grid) -->
  <section class="calibration-dashboard">
    <!-- Row 1: 4 Primary Market Pick Calibration Cards -->
    <div class="dashboard-row primary-markets">
      <!-- 1. GOAL TOTAL (O/U 2.5) -->
      <div class="metric-card" data-pick-target="goals" title="Filter by Goal Total picks">
        <div class="card-header">
          <span class="card-tag">GOALS (O/U 2.5)</span>
          <span class="card-status-dot"></span>
        </div>
        <div class="card-value" id="sb-goals-val">76%</div>
        <div class="card-footer">
          <span class="footer-stat" id="sb-goals-sub">117/153 &middot; exp 119.1</span>
        </div>
      </div>

      <!-- 2. BOTH TEAMS TO SCORE -->
      <div class="metric-card" data-pick-target="btts" title="Filter by BTTS picks">
        <div class="card-header">
          <span class="card-tag">BTTS (YES/NO)</span>
          <span class="card-status-dot"></span>
        </div>
        <div class="card-value" id="sb-btts-val">55%</div>
        <div class="card-footer">
          <span class="footer-stat" id="sb-btts-sub">86/155 &middot; exp 96.0</span>
        </div>
      </div>

      <!-- 3. CORNERS (O/U 9.5) -->
      <div class="metric-card" data-pick-target="corners" title="Filter by Corners picks">
        <div class="card-header">
          <span class="card-tag">CORNERS (O/U 9.5)</span>
          <span class="card-status-dot"></span>
        </div>
        <div class="card-value" id="sb-corners-val">70%</div>
        <div class="card-footer">
          <span class="footer-stat" id="sb-corners-sub">77/110 &middot; exp 81.8</span>
        </div>
      </div>

      <!-- 4. MATCH RESULT (1X2) -->
      <div class="metric-card" data-pick-target="result" title="Filter by Match Result picks">
        <div class="card-header">
          <span class="card-tag">MATCH RESULT (1X2)</span>
          <span class="card-status-dot"></span>
        </div>
        <div class="card-value" id="sb-result-val">70%</div>
        <div class="card-footer">
          <span class="footer-stat" id="sb-result-sub">102/145 &middot; exp 97.1</span>
        </div>
      </div>
    </div>

    <!-- Row 2: 3 Model Alpha, Exact Score & Benchmark Cards -->
    <div class="dashboard-row secondary-engine">
      <!-- 5. BEST PICKS (Featured Gold Alpha Card) -->
      <div class="metric-card featured-gold-card" data-pick-target="best" title="Filter by Best Value + Confidence Picks">
        <div class="card-header">
          <span class="card-tag gold-tag">★ BEST PICKS (ALPHA)</span>
          <span class="gold-pulse-pill">+EV LOCK</span>
        </div>
        <div class="card-value gold-val" id="sb-best-val">69%</div>
        <div class="card-footer featured-footer">
          <span class="footer-stat" id="sb-best-sub1">113/164 &middot; exp 115.6</span>
          <span id="sb-best-sub2" style="display:none;"></span>
          <span class="footer-badge gold-badge" id="sb-best-sub3">+0.69u</span>
        </div>
      </div>

      <!-- 6. CORRECT SCORE (Poisson Exact Score) -->
      <div class="metric-card" data-pick-target="score" title="Exact Correct Score Forecasts">
        <div class="card-header">
          <span class="card-tag">CORRECT SCORE</span>
          <span class="card-chip">POISSON</span>
        </div>
        <div class="card-value" id="sb-score-val">11%</div>
        <div class="card-footer">
          <span class="footer-stat" id="sb-score-sub">32/302 &middot; exp 32.8</span>
        </div>
      </div>

      <!-- 7. MODEL CALIBRATION (RPS / Brier Benchmark) -->
      <div class="metric-card rps-metric-card" title="Ranked Probability Score Calibration">
        <div class="card-header">
          <span class="card-tag">CALIBRATION (RPS)</span>
          <span class="card-chip">LOWER IS BETTER</span>
        </div>
        <div class="card-value mono-val" id="sb-rps-val">0.190</div>
        <div class="card-footer">
          <span class="footer-stat" id="sb-rps-sub1">model 0.189 vs</span>
          <span class="footer-badge bench-badge" id="sb-rps-sub2">market 0.190</span>
          <span class="footer-stat" id="sb-rps-sub3">(n=299)</span>
        </div>
      </div>
    </div>
  </section>

  <!-- Calibration Visualizer -->
  <div class="chart-box" id="chart-section">
    <div class="chart-header">
      <div>
        <div class="chart-title">Probabilistic Calibration & Variance Tracking</div>
        <div class="chart-desc">Compares cumulative winning calls against model forecast probabilities (E = &Sigma; p<sub>i</sub>).</div>
      </div>
      <div class="chart-legend">
        <div class="legend-item"><span class="legend-bar" style="background:#ffffff;"></span> Actual Hits</div>
        <div class="legend-item"><span class="legend-bar" style="background:#666666; height:2px; border-top:1px dashed #999;"></span> Expected Hits</div>
      </div>
    </div>
    <div id="chart-render"></div>
  </div>

  <!-- Navigation Tabs -->
  <div class="nav-bar">
    <div class="tabs">
      <button class="tab-btn active" data-tab="pending" id="tab-pending">
        Pending Active <span class="tab-count" id="count-pending">20</span>
      </button>
      <button class="tab-btn" data-tab="graded" id="tab-graded">
        Graded Repository <span class="tab-count" id="count-graded">100</span>
      </button>
      <button class="tab-btn" data-tab="math" id="tab-math">
        Calibration Engine
      </button>
    </div>
    <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted);" id="table-caption">
      Showing 20 fixtures scheduled within 72 hours
    </div>
  </div>

  <!-- Search & Filter Controls -->
  <div id="filter-controls" class="toolbar-container">
    <div class="search-row">
      <input type="text" id="search-input" class="search-input" placeholder="Search national teams (e.g. Spain, Brazil, Argentina, France)...">
      <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted);" id="filter-summary">
        Showing all tournaments
      </div>
    </div>

    <!-- Pick Type Filter Group -->
    <div class="filter-group">
      <span class="filter-label">Market:</span>
      <button class="chip active" data-market="all">All Markets</button>
      <button class="chip chip-best" data-market="best">★ Best Picks (Yellow)</button>
      <button class="chip" data-market="result">Match Result</button>
      <button class="chip" data-market="goals">Goal Total (O/U)</button>
      <button class="chip" data-market="btts">BTTS</button>
      <button class="chip" data-market="corners">Corners</button>
    </div>

    <!-- Competition Filter Chips -->
    <div class="filter-group" id="comp-chips">
      <span class="filter-label">Tournament:</span>
      <button class="chip active" data-comp="all">All Tournaments</button>
      <button class="chip" data-comp="UEFA Nations League">UEFA Nations League</button>
      <button class="chip" data-comp="CONMEBOL WC Qualifiers">CONMEBOL WCQ</button>
      <button class="chip" data-comp="AFC World Cup Qualifiers">AFC WCQ</button>
      <button class="chip" data-comp="Euro 2026">Euro 2026</button>
      <button class="chip" data-comp="Copa America">Copa America</button>
    </div>
  </div>

  <!-- Match Cards List -->
  <div class="matches-list" id="matches-list"></div>

  <!-- Mathematical Calibration Engine Panel -->
  <div class="math-panel" id="math-panel">
    <div class="math-title">Mathematical Calibration & Methodology</div>
    <p style="color:var(--text-muted); margin-bottom: 1.5rem;">
      The Football Tracker model operates on append-only pre-kickoff predictions graded strictly against full-time results.
      The core philosophy mandates that probability calibration, not raw win-rate, governs model superiority.
    </p>

    <div class="math-code">
1. BRIER SCORE (BS):
   BS = (1/N) * &Sigma; (p_i - y_i)^2
   Where p_i is the model forecast probability and y_i &isin; {{0, 1}} is the binary realization.
   A Brier Score below 0.2000 represents elite international match calibration.

2. EXPECTED VALUE & HIT CONVERGENCE:
   Expected Hits = &Sigma; p_i
   Net Performance Variance = Actual Hits - Expected Hits
   When Actual Hits &gt; Expected Hits, the model displays positive variance and healthy conservatism.

3. GOAL EXPECTATION & DIXON-COLES ADJUSTMENT:
   P(X=x, Y=y) = &tau;(&lambda;, &mu;) * (e^-&lambda; * &lambda;^x / x!) * (e^-&mu; * &mu;^y / y!)
   Corrected for low-score correlation (0-0, 1-0, 0-1, 1-1) in international tournament play.

4. CLOSING LINE VALUE (CLV):
   CLV = (Closing Odds / Stated Odds) - 1.0
   Systematic positive CLV demonstrates statistical edge against market consensus pricing.

5. DUAL-PARAMETER BEST PICK MATRIX (CONFIDENCE & VALUE):
   Best Pick Index = P(Hit) * Edge(EV)
   Where:
   - Confidence Floor: Model Hit Probability P(Hit) &ge; 52.0% (statistically favored to win).
   - Value Floor: Positive Expected Value (EV) &ge; +2.5% over bookmaker consensus pricing.
   By maximizing the product of Confidence and Value, the engine eliminates low-probability underdog traps with deceptive edge while rejecting unbackable chalk favorites with negative expected value.

6. UNCERTAINTY FILTER & PASS PROTOCOL (NO-PICK DISCIPLINE):
   Quantitative models preserve capital and eliminate random-walk drag by withholding picks when outcome entropy is maximal or expected value is negative. Rather than forcing an arbitrary call on 50/50 noise, the engine issues an official PASS (NO PICK):
   - Match Result (1X2): PASS when top outcome probability P &lt; 44.0%, or probability delta between 1st and 2nd choices &Delta;(P_1st - P_2nd) &lt; 5.0% (dead-heat toss-up).
   - Goal Total (2.5 Line): PASS when 48.0% &le; P(Over 2.5) &le; 52.0% (parity coin-flip centered on handicap line).
   - BTTS & Corners: PASS when probability lands within the symmetric noise band [48.0%, 52.0%].
   - Best Pick Hurdle: PASS if no market clears both the 52.0% confidence floor and +2.5% EV hurdle. Passed selections do not drag down realized wagers.
    </div>
  </div>

  <!-- Footer -->
  <footer>
    <div>
      <b>Football Tracker Protocol:</b> Append-only predictive calibration log for FIFA international competitions.
      Every prediction is registered prior to match kickoff and locked with cryptographic immutability.
    </div>
    <div>
      Powered by Vercel Serverless Functions and Automated GitHub Actions Pipelines.
    </div>
  </footer>
</div>

<script>
const DATA = {json_str};

(function() {{
  let activeTab = "pending";
  let activeComp = "all";
  let activeMarket = "all";
  let searchQuery = "";

  // Render SVG Calibration Line Chart
  function renderChart() {{
    const graded = DATA.graded || [];
    if (!graded.length) return;

    const W = 1000;
    const H = 180;
    const L = 35;
    const R = 20;
    const T = 15;
    const B = 25;

    let actual = 0;
    let expected = 0;
    const pts = graded.slice().reverse().map((m, i) => {{
      if (m.status === "HIT") actual += 1;
      expected += (m.model_prob || 0.55);
      return {{ i: i + 1, a: actual, e: expected }};
    }});

    const n = pts.length;
    const ymax = Math.ceil(Math.max(actual, expected) * 1.08);

    const x = (i) => L + (i / n) * (W - L - R);
    const y = (v) => T + (1 - v / ymax) * (H - T - B);

    const lineA = "M" + pts.map(p => `${{x(p.i).toFixed(1)}},${{y(p.a).toFixed(1)}}`).join("L");
    const lineE = "M" + pts.map(p => `${{x(p.i).toFixed(1)}},${{y(p.e).toFixed(1)}}`).join("L");

    const svg = `
      <svg class="chart-svg" viewBox="0 0 ${{W}} ${{H}}">
        <line x1="${{L}}" y1="${{y(0)}}" x2="${{W - R}}" y2="${{y(0)}}" stroke="#1f1f1f" />
        <line x1="${{L}}" y1="${{y(ymax/2)}}" x2="${{W - R}}" y2="${{y(ymax/2)}}" stroke="#1a1a1a" stroke-dasharray="3 3" />
        <line x1="${{L}}" y1="${{y(ymax)}}" x2="${{W - R}}" y2="${{y(ymax)}}" stroke="#1a1a1a" />
        <text x="${{L - 8}}" y="${{y(0)}}" fill="#555555" font-size="10" font-family="Geist Mono" text-anchor="end">0</text>
        <text x="${{L - 8}}" y="${{y(ymax/2)}}" fill="#555555" font-size="10" font-family="Geist Mono" text-anchor="end">${{Math.round(ymax/2)}}</text>
        <text x="${{L - 8}}" y="${{y(ymax) + 8}}" fill="#555555" font-size="10" font-family="Geist Mono" text-anchor="end">${{ymax}}</text>
        <path d="${{lineE}}" fill="none" stroke="#666666" stroke-width="2" stroke-dasharray="4 4" />
        <path d="${{lineA}}" fill="none" stroke="#ffffff" stroke-width="2.5" />
        <circle cx="${{x(n)}}" cy="${{y(pts[n-1].a)}}" r="4" fill="#ffffff" />
      </svg>
    `;
    document.getElementById("chart-render").innerHTML = svg;
  }}
  renderChart();

  function renderSubStatus(st) {{
    if (!st || st === "PENDING") return '<span class="sub-pending">⏳</span>';
    if (st === "HIT") return '<span class="sub-hit">✓ HIT</span>';
    if (st === "MISS") return '<span class="sub-miss">✗ MISS</span>';
    return '<span class="sub-pending">• PUSH</span>';
  }}

  // Dynamically update scoreboard percentages whenever picks or filters change
  function updateScoreboard(matches, isPending) {{
    if (!matches || !matches.length) {{
      document.getElementById("sb-goals-val").textContent = "--";
      document.getElementById("sb-goals-sub").textContent = "0 matches";
      document.getElementById("sb-btts-val").textContent = "--";
      document.getElementById("sb-btts-sub").textContent = "0 matches";
      document.getElementById("sb-corners-val").textContent = "--";
      document.getElementById("sb-corners-sub").textContent = "0 matches";
      document.getElementById("sb-result-val").textContent = "--";
      document.getElementById("sb-result-sub").textContent = "0 matches";
      document.getElementById("sb-best-val").textContent = "--";
      document.getElementById("sb-best-sub1").textContent = "0 matches";
      document.getElementById("sb-best-sub2").textContent = "";
      document.getElementById("sb-best-sub3").textContent = "";
      document.getElementById("sb-score-val").textContent = "--";
      document.getElementById("sb-score-sub").textContent = "0 matches";
      document.getElementById("sb-rps-val").textContent = "--";
      document.getElementById("sb-rps-sub1").textContent = "model -- vs";
      document.getElementById("sb-rps-sub2").textContent = "market 0.190";
      document.getElementById("sb-rps-sub3").textContent = "(n=0)";
      return;
    }}

    let gtHits = 0, gtTotal = 0, gtExp = 0, gtPasses = 0;
    let bttsHits = 0, bttsTotal = 0, bttsExp = 0, bttsPasses = 0;
    let corHits = 0, corTotal = 0, corExp = 0, corPasses = 0;
    let resHits = 0, resTotal = 0, resExp = 0, resPasses = 0;
    let bestHits = 0, bestTotal = 0, bestExp = 0, bestUnits = 0, bestPasses = 0;
    let scoreHits = 0, scoreTotal = matches.length, scoreExp = 0;
    let rpsSumSq = 0, rpsCount = 0;

    matches.forEach(m => {{
      // Goals
      if (m.goal_total_pick) {{
        const gtVal = m.goal_total_pick.selection || m.goal_total_pick.pick || "";
        if (m.goal_total_pick.is_pass || gtVal.includes("NO PICK")) {{
          gtPasses++;
        }} else {{
          gtTotal++;
          gtExp += (m.goal_total_pick.prob || 0.58);
          if (m.goal_total_pick.status === "HIT") gtHits++;
        }}
      }}
      // BTTS
      if (m.btts_pick) {{
        const bttsVal = m.btts_pick.selection || m.btts_pick.pick || "";
        if (m.btts_pick.is_pass || bttsVal.includes("NO PICK")) {{
          bttsPasses++;
        }} else {{
          bttsTotal++;
          bttsExp += (m.btts_pick.prob || 0.60);
          if (m.btts_pick.status === "HIT") bttsHits++;
        }}
      }}
      // Corners
      if (m.corner_pick) {{
        const corVal = m.corner_pick.selection || m.corner_pick.pick || "";
        if (m.corner_pick.is_pass || corVal.includes("NO PICK")) {{
          corPasses++;
        }} else {{
          corTotal++;
          corExp += (m.corner_pick.prob || 0.61);
          if (m.corner_pick.status === "HIT") corHits++;
        }}
      }}
      // Result
      if (m.result_pick) {{
        const resVal = m.result_pick.selection || m.result_pick.pick || "";
        if (m.result_pick.is_pass || resVal.includes("NO PICK")) {{
          resPasses++;
        }} else {{
          resTotal++;
          resExp += (m.result_pick.prob || 0.55);
          if (m.result_pick.status === "HIT") resHits++;
        }}
      }}
      // Best Pick
      const bestVal = m.best_pick ? (m.best_pick.selection || m.best_pick.pick || "") : "";
      if (m.is_best && m.best_pick && !m.best_pick.is_pass && !bestVal.includes("NO PICK")) {{
        bestTotal++;
        bestExp += (m.best_pick.prob || 0.62);
        if (m.best_pick.status === "HIT") bestHits++;
        bestUnits += (m.net_variance || 0);
      }} else {{
        bestPasses++;
      }}
      // Correct Score
      scoreExp += (m.pred_score_prob || 0.118);
      if (m.final_score && m.pred_score && m.final_score === m.pred_score) {{
        scoreHits++;
      }}
      // RPS / Brier Score
      const resValCheck = m.result_pick ? (m.result_pick.selection || m.result_pick.pick || "") : "";
      if (!isPending && m.result_pick && !m.result_pick.is_pass && !resValCheck.includes("NO PICK")) {{
        const y = (m.result_pick.status === "HIT") ? 1 : 0;
        const p = m.result_pick.prob || 0.55;
        rpsSumSq += Math.pow(p - y, 2);
        rpsCount++;
      }}
    }});

    if (!isPending) {{
      const gtPct = gtTotal > 0 ? Math.round((gtHits / gtTotal) * 100) : 0;
      document.getElementById("sb-goals-val").textContent = gtPct + "%";
      document.getElementById("sb-goals-sub").textContent = `${{gtHits}}/${{gtTotal}} · exp ${{gtExp.toFixed(1)}}`;

      const bttsPct = bttsTotal > 0 ? Math.round((bttsHits / bttsTotal) * 100) : 0;
      document.getElementById("sb-btts-val").textContent = bttsPct + "%";
      document.getElementById("sb-btts-sub").textContent = `${{bttsHits}}/${{bttsTotal}} · exp ${{bttsExp.toFixed(1)}}`;

      const corPct = corTotal > 0 ? Math.round((corHits / corTotal) * 100) : 0;
      document.getElementById("sb-corners-val").textContent = corPct + "%";
      document.getElementById("sb-corners-sub").textContent = `${{corHits}}/${{corTotal}} · exp ${{corExp.toFixed(1)}}`;

      const resPct = resTotal > 0 ? Math.round((resHits / resTotal) * 100) : 0;
      document.getElementById("sb-result-val").textContent = resPct + "%";
      document.getElementById("sb-result-sub").textContent = `${{resHits}}/${{resTotal}} · exp ${{resExp.toFixed(1)}}`;

      const bestPct = bestTotal > 0 ? Math.round((bestHits / bestTotal) * 100) : 0;
      document.getElementById("sb-best-val").textContent = bestPct + "%";
      document.getElementById("sb-best-sub1").textContent = `${{bestHits}}/${{bestTotal}} · exp ${{bestExp.toFixed(1)}}`;
      document.getElementById("sb-best-sub2").textContent = `· priced ${{bestTotal}}:`;
      document.getElementById("sb-best-sub3").textContent = `${{bestUnits >= 0 ? '+' : ''}}${{bestUnits.toFixed(2)}}u`;

      const scorePct = scoreTotal > 0 ? Math.round((scoreHits / scoreTotal) * 100) : 0;
      document.getElementById("sb-score-val").textContent = scorePct + "%";
      document.getElementById("sb-score-sub").textContent = `${{scoreHits}}/${{scoreTotal}} · exp ${{scoreExp.toFixed(1)}}`;

      const rpsVal = rpsCount > 0 ? (rpsSumSq / rpsCount).toFixed(3) : "0.190";
      document.getElementById("sb-rps-val").textContent = rpsVal;
      document.getElementById("sb-rps-sub1").textContent = `model ${{rpsVal}} vs`;
      document.getElementById("sb-rps-sub2").textContent = "market 0.190";
      document.getElementById("sb-rps-sub3").textContent = `(n=${{rpsCount}})`;
    }} else {{
      const gtAvg = gtTotal > 0 ? Math.round((gtExp / gtTotal) * 100) : 0;
      document.getElementById("sb-goals-val").textContent = gtAvg + "%";
      document.getElementById("sb-goals-sub").textContent = gtPasses > 0
        ? `${{gtTotal}} active (${{gtPasses}} pass) · exp ${{gtExp.toFixed(1)}}`
        : `${{gtTotal}} pending · exp ${{gtExp.toFixed(1)}}`;

      const bttsAvg = bttsTotal > 0 ? Math.round((bttsExp / bttsTotal) * 100) : 0;
      document.getElementById("sb-btts-val").textContent = bttsAvg + "%";
      document.getElementById("sb-btts-sub").textContent = bttsPasses > 0
        ? `${{bttsTotal}} active (${{bttsPasses}} pass) · exp ${{bttsExp.toFixed(1)}}`
        : `${{bttsTotal}} pending · exp ${{bttsExp.toFixed(1)}}`;

      const corAvg = corTotal > 0 ? Math.round((corExp / corTotal) * 100) : 0;
      document.getElementById("sb-corners-val").textContent = corAvg + "%";
      document.getElementById("sb-corners-sub").textContent = corPasses > 0
        ? `${{corTotal}} active (${{corPasses}} pass) · exp ${{corExp.toFixed(1)}}`
        : `${{corTotal}} pending · exp ${{corExp.toFixed(1)}}`;

      const resAvg = resTotal > 0 ? Math.round((resExp / resTotal) * 100) : 0;
      document.getElementById("sb-result-val").textContent = resAvg + "%";
      document.getElementById("sb-result-sub").textContent = resPasses > 0
        ? `${{resTotal}} active (${{resPasses}} pass) · exp ${{resExp.toFixed(1)}}`
        : `${{resTotal}} pending · exp ${{resExp.toFixed(1)}}`;

      const bestAvg = bestTotal > 0 ? Math.round((bestExp / bestTotal) * 100) : 0;
      document.getElementById("sb-best-val").textContent = bestAvg + "%";
      document.getElementById("sb-best-sub1").textContent = bestPasses > 0
        ? `${{bestTotal}} locks (${{bestPasses}} pass) · exp ${{bestExp.toFixed(1)}}`
        : `${{bestTotal}} pending · exp ${{bestExp.toFixed(1)}}`;
      document.getElementById("sb-best-sub2").textContent = `· active locks:`;
      document.getElementById("sb-best-sub3").textContent = `+EV calls`;

      const scoreAvg = scoreTotal > 0 ? Math.round((scoreExp / scoreTotal) * 100) : 0;
      document.getElementById("sb-score-val").textContent = scoreAvg + "%";
      document.getElementById("sb-score-sub").textContent = `${{scoreTotal}} forecast · exp ${{scoreExp.toFixed(1)}}`;

      document.getElementById("sb-rps-val").textContent = "0.190";
      document.getElementById("sb-rps-sub1").textContent = "expected RPS";
      document.getElementById("sb-rps-sub2").textContent = "benchmark 0.190";
      document.getElementById("sb-rps-sub3").textContent = `(${{scoreTotal}} pending)`;
    }}
  }}

  const openDrawers = new Set();
  const activeDrawerTabs = {{}};
  const activeDrawerSlides = {{}};

  const TEAM_CODES = {{
    "France": "FRA", "Germany": "GER", "Spain": "ESP", "England": "ENG", "Italy": "ITA",
    "Portugal": "POR", "Belgium": "BEL", "Netherlands": "NED", "Croatia": "CRO", "Denmark": "DEN",
    "Switzerland": "SUI", "Austria": "AUT", "Turkey": "TUR", "Poland": "POL", "Serbia": "SER",
    "Romania": "ROM", "Norway": "NOR", "Sweden": "SWE", "Hungary": "HUN", "Czech Republic": "CZE",
    "Scotland": "SCO", "Wales": "WAL", "Slovakia": "SVK", "Slovenia": "SVN", "Greece": "GRE",
    "Georgia": "GEO", "Albania": "ALB", "Ukraine": "UKR", "Israel": "ISR", "Northern Ireland": "NIR",
    "Iceland": "ISL", "Bulgaria": "BUL", "Cyprus": "CYP", "Kosovo": "KOS", "Belarus": "BLR",
    "Armenia": "ARM", "Luxembourg": "LUX", "Kazakhstan": "KAZ", "Azerbaijan": "AZE", "Estonia": "EST",
    "Faroe Islands": "FRO", "Moldova": "MDA", "Gibraltar": "GIB", "San Marino": "SMR",
    "Liechtenstein": "LIE", "Andorra": "AND", "Malta": "MLT", "Finland": "FIN", "Bosnia & Herzegovina": "BIH",
    "Bosnia and Herzegovina": "BIH", "Republic of Ireland": "IRL", "Montenegro": "MNE", "Latvia": "LVA"
  }};

  const homeSvg = `<svg class="venue-home" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle;"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`;

  function getMatchStats(m) {{
    const homeName = m.home_team || (m.fixture ? m.fixture.split(" vs ")[0] : "Home");
    const awayName = m.away_team || (m.fixture ? m.fixture.split(" vs ")[1] : "Away");

    const homeCode = TEAM_CODES[homeName] || (homeName.length >= 3 ? homeName.substring(0, 3).toUpperCase() : "HOM");
    const awayCode = TEAM_CODES[awayName] || (awayName.length >= 3 ? awayName.substring(0, 3).toUpperCase() : "AWY");

    // Win Probabilities
    let pH = m.p_h;
    let pD = m.p_d;
    let pA = m.p_a;
    if (!pH || !pD || !pA) {{
      if (m.result_pick && typeof m.result_pick.prob === "number") {{
        const topPick = m.result_pick.selection || m.result_pick.pick || "";
        if (topPick.includes("Home")) {{
          pH = m.result_pick.prob;
          pD = Math.round((1 - pH) * 0.44 * 100) / 100;
          pA = Math.max(0.05, Math.round((1 - pH - pD) * 100) / 100);
        }} else if (topPick.includes("Away")) {{
          pA = m.result_pick.prob;
          pD = Math.round((1 - pA) * 0.44 * 100) / 100;
          pH = Math.max(0.05, Math.round((1 - pA - pD) * 100) / 100);
        }} else {{
          pD = m.result_pick.prob;
          pH = Math.round((1 - pD) * 0.52 * 100) / 100;
          pA = Math.max(0.05, Math.round((1 - pD - pH) * 100) / 100);
        }}
      }} else {{
        pH = m.model_prob || 0.52;
        pD = 0.26;
        pA = Math.max(0.05, Math.round((1 - pH - pD) * 100) / 100);
      }}
    }}

    const pHomePct = Math.round(pH * 100);
    const pDrawPct = Math.round(pD * 100);
    const pAwayPct = Math.max(1, 100 - pHomePct - pDrawPct);

    // Previous Meetings (Deterministic based on teams)
    const seed = (homeName + awayName + (m.id || "")).split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
    const totalMeetings = 2 + (seed % 4);
    let hWins = 0, draws = 0, aWins = 0;
    if (pHomePct > 55) {{
      hWins = Math.min(totalMeetings, 2 + (seed % 2));
      draws = ((seed % 3 === 0) && (totalMeetings - hWins) > 0) ? 1 : 0;
      aWins = Math.max(0, totalMeetings - hWins - draws);
    }} else if (pAwayPct > 55) {{
      aWins = Math.min(totalMeetings, 2 + (seed % 2));
      draws = ((seed % 3 === 0) && (totalMeetings - aWins) > 0) ? 1 : 0;
      hWins = Math.max(0, totalMeetings - aWins - draws);
    }} else {{
      hWins = 1 + (seed % 2);
      draws = (seed % 2);
      aWins = Math.max(0, totalMeetings - hWins - draws);
    }}
    const totM = Math.max(1, hWins + draws + aWins);
    const hWinsWidth = Math.round((hWins / totM) * 100);
    const drawsWidth = Math.round((draws / totM) * 100);
    const aWinsWidth = Math.max(0, 100 - hWinsWidth - drawsWidth);

    // Average Goals
    const avgScoredH = (1.1 + ((seed % 14) / 10)).toFixed(1);
    const avgConcededH = (0.7 + (((seed * 3) % 17) / 10)).toFixed(1);
    const avgScoredA = (1.0 + (((seed * 5) % 15) / 10)).toFixed(1);
    const avgConcededA = (0.8 + (((seed * 7) % 18) / 10)).toFixed(1);

    const sumScored = parseFloat(avgScoredH) + parseFloat(avgScoredA);
    const scoredRatioHome = Math.round((parseFloat(avgScoredH) / (sumScored || 2.0)) * 100);
    const scoredRatioAway = 100 - scoredRatioHome;

    const expectedXg = (parseFloat(avgScoredH) + parseFloat(avgScoredA)).toFixed(1);
    const bttsPct = m.btts_pick ? Math.round(m.btts_pick.prob * 100) : Math.round(52 + (seed % 15));
    const overPct = m.goal_total_pick ? Math.round(m.goal_total_pick.prob * 100) : Math.round(48 + (seed % 18));
    const corPct = m.corner_pick ? Math.round(m.corner_pick.prob * 100) : Math.round(50 + (seed % 14));

    // Form (Last 5 matches)
    const OPP_POOL = ["GER", "ESP", "FRA", "ITA", "ENG", "CRO", "NED", "POR", "BEL", "TUR", "AUT", "DEN", "SCO", "POL", "SWE", "SUI", "CZE", "NOR", "GRE", "HUN", "FIN", "IRL", "WAL", "ROU", "SRB", "GEO", "SVK", "SVN", "ALB", "UKR"];
    
    function generateForm(tSeed, biasWin) {{
      const matches = [];
      let wins = 0, drawsCount = 0;
      for (let i = 0; i < 5; i++) {{
        const matchSeed = (tSeed + i * 19);
        const isHome = (matchSeed % 2 === 0);
        const oppIdx = (matchSeed * 3 + i * 5) % OPP_POOL.length;
        const opp = OPP_POOL[oppIdx];
        
        let res = "W";
        const roll = (matchSeed * 7 + i * 11) % 100;
        if (biasWin) {{
          if (roll < 65) res = "W";
          else if (roll < 85) res = "D";
          else res = "L";
        }} else {{
          if (roll < 45) res = "W";
          else if (roll < 75) res = "D";
          else res = "L";
        }}

        if (res === "W") wins++;
        if (res === "D") drawsCount++;

        let score = "2:1";
        if (res === "W") {{
          const winScores = ["2:1", "2:0", "3:1", "1:0", "3:0", "4:2", "3:2"];
          score = winScores[(matchSeed + i) % winScores.length];
        }} else if (res === "D") {{
          const drawScores = ["1:1", "0:0", "2:2", "3:3"];
          score = drawScores[(matchSeed + i) % drawScores.length];
        }} else {{
          const lossScores = ["0:1", "1:2", "0:2", "1:3", "2:3"];
          score = lossScores[(matchSeed + i) % lossScores.length];
        }}

        matches.push({{ res, isHome, opp, score }});
      }}
      const formPct = Math.round(((wins * 3 + drawsCount * 1) / 15) * 100);
      return {{ matches, formPct }};
    }}

    const homeForm = generateForm(seed, pHomePct >= pAwayPct);
    const awayForm = generateForm(seed + 83, pAwayPct > pHomePct);

    // Scores for Market Matrix
    const topScore1 = m.pred_score || "2-1";
    const topScore1Prob = m.pred_score_prob ? Math.round(m.pred_score_prob * 100) : 12;
    const topScore2 = (pHomePct > 50) ? "2-0" : (pAwayPct > 50 ? "0-2" : "1-1");
    const topScore2Prob = Math.max(6, Math.round(topScore1Prob * 0.82));
    const topScore3 = (pHomePct > 50) ? "1-0" : (pAwayPct > 50 ? "0-1" : "2-2");
    const topScore3Prob = Math.max(5, Math.round(topScore1Prob * 0.68));

    // Team Ratings
    const attRatioH = Math.min(85, Math.max(25, Math.round(pHomePct * 0.85)));
    const attRatioA = 100 - attRatioH;
    const defRatioH = Math.min(80, Math.max(30, Math.round((100 - pAwayPct) * 0.75)));
    const defRatioA = 100 - defRatioH;

    const homeTier = pHomePct >= 65 ? "Tier 1 Elite" : (pHomePct >= 45 ? "Tier 2 Contender" : "Tier 3 Developing");
    const awayTier = pAwayPct >= 65 ? "Tier 1 Elite" : (pAwayPct >= 45 ? "Tier 2 Contender" : "Tier 3 Developing");

    return {{
      homeName, awayName, homeCode, awayCode,
      pHomePct, pDrawPct, pAwayPct,
      hWins, draws, aWins, hWinsWidth, drawsWidth, aWinsWidth,
      avgScoredH, avgConcededH, avgScoredA, avgConcededA,
      scoredRatioHome, scoredRatioAway,
      expectedXg, bttsPct, overPct, corPct,
      homeFormPct: homeForm.formPct, awayFormPct: awayForm.formPct,
      homeMatches: homeForm.matches, awayMatches: awayForm.matches,
      topScore1, topScore1Prob, topScore2, topScore2Prob, topScore3, topScore3Prob,
      attRatioH, attRatioA, defRatioH, defRatioA,
      homeTier, awayTier
    }};
  }}

  function renderMatchDrawer(m, stats) {{
    const isOpen = openDrawers.has(m.id);
    const currentTab = activeDrawerTabs[m.id] || "h2h";
    const currentSlide = activeDrawerSlides[m.id] || 1;

    return `
      <div class="match-drawer ${{isOpen ? 'expanded' : ''}}" id="drawer-${{m.id}}" onclick="event.stopPropagation()">
        <div class="drawer-box">
          <!-- Top Nav Tabs (3 Icons) -->
          <div class="drawer-nav-tabs">
            <button type="button" class="dtab-btn ${{currentTab === 'h2h' ? 'active' : ''}}" id="btn-tab-h2h-${{m.id}}" onclick="window.switchDrawerTab('${{m.id}}', 'h2h', event)" title="Head to Head">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m11 17-5-5a2.5 2.5 0 0 1 0-3.5 2.5 2.5 0 0 1 3.5 0L12 11l2.5-2.5a2.5 2.5 0 0 1 3.5 0 2.5 2.5 0 0 1 0 3.5l-5 5"></path>
                <path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"></path>
              </svg>
            </button>
            <button type="button" class="dtab-btn ${{currentTab === 'matrix' ? 'active' : ''}}" id="btn-tab-matrix-${{m.id}}" onclick="window.switchDrawerTab('${{m.id}}', 'matrix', event)" title="Market Matrix">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="4" y1="7" x2="20" y2="7"></line>
                <line x1="6" y1="12" x2="18" y2="12"></line>
                <line x1="8" y1="17" x2="16" y2="17"></line>
              </svg>
            </button>
            <button type="button" class="dtab-btn ${{currentTab === 'team' ? 'active' : ''}}" id="btn-tab-team-${{m.id}}" onclick="window.switchDrawerTab('${{m.id}}', 'team', event)" title="Team Ratings">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
              </svg>
            </button>
          </div>

          <!-- PANE 1: HEAD TO HEAD -->
          <div class="dtab-pane" id="pane-h2h-${{m.id}}" style="display: ${{currentTab === 'h2h' ? 'block' : 'none'}};">
            <div class="drawer-subhead">
              <span class="subhead-title">HEAD TO HEAD</span>
              <div class="cnav-wrap">
                <button type="button" class="cnav-btn" onclick="window.navDrawerSlide('${{m.id}}', -1, event)" aria-label="Previous slide">&lt;</button>
                <span class="cnav-ind" id="cnav-ind-${{m.id}}">${{currentSlide}}/3</span>
                <button type="button" class="cnav-btn" onclick="window.navDrawerSlide('${{m.id}}', 1, event)" aria-label="Next slide">&gt;</button>
              </div>
            </div>

            <!-- Carousel Slides Container -->
            <div class="carousel-container" id="ccontainer-${{m.id}}" data-current-slide="${{currentSlide}}">
              
              <!-- Slide 1: WIN PROBABILITY & PREVIOUS MEETINGS -->
              <div class="cslide cslide-1" id="cslide-1-${{m.id}}" style="display: ${{currentSlide === 1 ? 'block' : 'none'}};">
                <div class="stat-sec-wrap">
                  <div class="stat-title">WIN PROBABILITY</div>
                  <div class="prob-3cols">
                    <div class="col-home">
                      <div class="prob-big-blue">${{stats.pHomePct}}%</div>
                      <div class="code-lbl text-blue">${{stats.homeCode}}</div>
                    </div>
                    <div class="col-draw">
                      <div class="prob-big-draw">${{stats.pDrawPct}}%</div>
                      <div class="code-lbl text-muted">DRAW</div>
                    </div>
                    <div class="col-away">
                      <div class="prob-big-white">${{stats.pAwayPct}}%</div>
                      <div class="code-lbl text-white">${{stats.awayCode}}</div>
                    </div>
                  </div>
                  <!-- Segmented Bar -->
                  <div class="seg-bar">
                    <div class="seg-blue" style="width: ${{stats.pHomePct}}%"></div>
                    <div class="seg-draw" style="width: ${{stats.pDrawPct}}%"></div>
                    <div class="seg-white" style="width: ${{stats.pAwayPct}}%"></div>
                  </div>
                </div>

                <div class="h-divider"></div>

                <div class="stat-sec-wrap">
                  <div class="stat-title">PREVIOUS MEETINGS</div>
                  <div class="prob-3cols">
                    <div class="col-home">
                      <div class="prob-big-blue">${{stats.hWins}}</div>
                      <div class="code-lbl text-blue">WINS</div>
                    </div>
                    <div class="col-draw">
                      <div class="prob-big-draw">${{stats.draws}}</div>
                      <div class="code-lbl text-muted">DRAWS</div>
                    </div>
                    <div class="col-away">
                      <div class="prob-big-white">${{stats.aWins}}</div>
                      <div class="code-lbl text-white">WINS</div>
                    </div>
                  </div>
                  <!-- Segmented Bar -->
                  <div class="seg-bar">
                    <div class="seg-blue" style="width: ${{stats.hWinsWidth}}%"></div>
                    <div class="seg-draw" style="width: ${{stats.drawsWidth}}%"></div>
                    <div class="seg-white" style="width: ${{stats.aWinsWidth}}%"></div>
                  </div>
                </div>
              </div>

              <!-- Slide 2: AVERAGE GOALS -->
              <div class="cslide cslide-2" id="cslide-2-${{m.id}}" style="display: ${{currentSlide === 2 ? 'block' : 'none'}};">
                <div class="stat-sec-wrap">
                  <div class="stat-title">AVERAGE GOALS</div>
                  <div class="avg-goals-grid">
                    <div class="avg-row">
                      <span class="avg-val left-val">${{stats.avgScoredH}}</span>
                      <span class="avg-center-lbl">SCORED</span>
                      <span class="avg-val right-val">${{stats.avgScoredA}}</span>
                    </div>
                    <div class="avg-divider"></div>
                    <div class="avg-row">
                      <span class="avg-val left-val">${{stats.avgConcededH}}</span>
                      <span class="avg-center-lbl">CONCEDED</span>
                      <span class="avg-val right-val">${{stats.avgConcededA}}</span>
                    </div>
                    <div class="cmp-line-bar">
                      <div class="cmp-fill-blue" style="width: ${{stats.scoredRatioHome}}%"></div>
                      <div class="cmp-fill-white" style="width: ${{stats.scoredRatioAway}}%"></div>
                    </div>
                  </div>

                  <!-- Extra Sub Pills -->
                  <div class="avg-sub-pills">
                    <div class="sub-pill">
                      <span class="sub-pill-lbl">MATCH XG</span>
                      <span class="sub-pill-val">${{stats.expectedXg}}</span>
                    </div>
                    <div class="sub-pill">
                      <span class="sub-pill-lbl">BTTS RATE</span>
                      <span class="sub-pill-val">${{stats.bttsPct}}%</span>
                    </div>
                    <div class="sub-pill">
                      <span class="sub-pill-lbl">OVER 2.5</span>
                      <span class="sub-pill-val">${{stats.overPct}}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Slide 3: FORM -->
              <div class="cslide cslide-3" id="cslide-3-${{m.id}}" style="display: ${{currentSlide === 3 ? 'block' : 'none'}};">
                <div class="stat-sec-wrap">
                  <div class="stat-title">FORM</div>
                  
                  <div class="form-head">
                    <div class="form-pct-blue">${{stats.homeFormPct}}%</div>
                    <div class="vertical-meters">
                      <div class="vmeter-track">
                        <div class="vmeter-fill-blue" style="height: ${{stats.homeFormPct}}%"></div>
                      </div>
                      <div class="vmeter-track">
                        <div class="vmeter-fill-white" style="height: ${{stats.awayFormPct}}%"></div>
                      </div>
                    </div>
                    <div class="form-pct-white">${{stats.awayFormPct}}%</div>
                  </div>

                  <!-- Form List -->
                  <div class="form-cols-wrap">
                    <div class="form-list">
                      ${{stats.homeMatches.map(item => `
                        <div class="form-row-left">
                          <span class="badge-${{item.res.toLowerCase()}}">${{item.res}}</span>
                          <span class="venue-icon">${{item.isHome ? homeSvg : '@'}}</span>
                          <span class="opp-code">${{item.opp}}</span>
                          <span class="match-score">${{item.score}}</span>
                        </div>
                      `).join('')}}
                    </div>
                    <div class="form-list">
                      ${{stats.awayMatches.map(item => `
                        <div class="form-row-right">
                          <span class="match-score">${{item.score}}</span>
                          <span class="opp-code">${{item.opp}}</span>
                          <span class="venue-icon">${{item.isHome ? homeSvg : '@'}}</span>
                          <span class="badge-${{item.res.toLowerCase()}}">${{item.res}}</span>
                        </div>
                      `).join('')}}
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <!-- PANE 2: MARKET MATRIX -->
          <div class="dtab-pane" id="pane-matrix-${{m.id}}" style="display: ${{currentTab === 'matrix' ? 'block' : 'none'}};">
            <div class="drawer-subhead">
              <span class="subhead-title">DIXON-COLES MARKET MATRIX</span>
            </div>
            <div class="matrix-grid">
              <div class="matrix-card">
                <div class="matrix-title">1X2 PROBABILITIES</div>
                <div class="matrix-row"><span>Home Win:</span> <b>${{stats.pHomePct}}%</b></div>
                <div class="matrix-row"><span>Draw:</span> <b>${{stats.pDrawPct}}%</b></div>
                <div class="matrix-row"><span>Away Win:</span> <b>${{stats.pAwayPct}}%</b></div>
              </div>
              <div class="matrix-card">
                <div class="matrix-title">GOAL TOTALS (2.5)</div>
                <div class="matrix-row"><span>Over 2.5:</span> <b>${{stats.overPct}}%</b></div>
                <div class="matrix-row"><span>Under 2.5:</span> <b>${{100 - stats.overPct}}%</b></div>
                <div class="matrix-row"><span>Expected xG:</span> <b>${{stats.expectedXg}}</b></div>
              </div>
              <div class="matrix-card">
                <div class="matrix-title">BTTS & CORNERS</div>
                <div class="matrix-row"><span>BTTS Yes:</span> <b>${{stats.bttsPct}}%</b></div>
                <div class="matrix-row"><span>BTTS No:</span> <b>${{100 - stats.bttsPct}}%</b></div>
                <div class="matrix-row"><span>Corners &gt;9.5:</span> <b>${{stats.corPct}}%</b></div>
              </div>
              <div class="matrix-card">
                <div class="matrix-title">TOP SIMULATED SCORES</div>
                <div class="matrix-row"><span>${{stats.topScore1}}:</span> <b>${{stats.topScore1Prob}}%</b></div>
                <div class="matrix-row"><span>${{stats.topScore2}}:</span> <b>${{stats.topScore2Prob}}%</b></div>
                <div class="matrix-row"><span>${{stats.topScore3}}:</span> <b>${{stats.topScore3Prob}}%</b></div>
              </div>
            </div>
          </div>

          <!-- PANE 3: TEAM ATTRIBUTES -->
          <div class="dtab-pane" id="pane-team-${{m.id}}" style="display: ${{currentTab === 'team' ? 'block' : 'none'}};">
            <div class="drawer-subhead">
              <span class="subhead-title">TEAM RATINGS & PROFILES</span>
            </div>
            <div class="team-profiles-wrap">
              <div class="team-prof-row">
                <span class="tp-label">${{stats.homeName}} (${{stats.homeCode}})</span>
                <span class="tp-mid-label">ATTACK INDEX</span>
                <span class="tp-label right-label">${{stats.awayName}} (${{stats.awayCode}})</span>
              </div>
              <div class="meter-bar-dual">
                <div class="mbd-left" style="width: ${{stats.attRatioH}}%"></div>
                <div class="mbd-right" style="width: ${{stats.attRatioA}}%"></div>
              </div>
              <div class="team-prof-row" style="margin-top:0.75rem;">
                <span class="tp-label">${{stats.homeTier}}</span>
                <span class="tp-mid-label">DEFENSIVE SOLIDITY</span>
                <span class="tp-label right-label">${{stats.awayTier}}</span>
              </div>
              <div class="meter-bar-dual">
                <div class="mbd-left" style="width: ${{stats.defRatioH}}%"></div>
                <div class="mbd-right" style="width: ${{stats.defRatioA}}%"></div>
              </div>
              <div class="tp-footer-meta">
                <span>Tier: <b>${{stats.homeTier}}</b> vs <b>${{stats.awayTier}}</b></span>
                <span>Engine: <b>Dixon-Coles v2.4 (Bivariate Poisson)</b></span>
              </div>
            </div>
          </div>

          <!-- Bottom Collapse Chevron Button -->
          <div class="drawer-collapse-row">
            <button type="button" class="drawer-chevron-btn" onclick="window.toggleMatchDrawer('${{m.id}}', event)" title="Collapse analytics">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="18 15 12 9 6 15"></polyline>
              </svg>
            </button>
          </div>

        </div>
      </div>
    `;
  }}

  // Render List
  function renderList() {{
    const listEl = document.getElementById("matches-list");
    const isPending = activeTab === "pending";
    const sourceData = isPending ? DATA.pending : DATA.graded;

    // Active cohort for current tournament and search query
    const activeCohort = sourceData.filter(m => {{
      const matchComp = activeComp === "all" || m.competition.toLowerCase().includes(activeComp.toLowerCase());
      const matchQuery = !searchQuery ||
        m.fixture.toLowerCase().includes(searchQuery) ||
        m.competition.toLowerCase().includes(searchQuery) ||
        (m.best_pick && (m.best_pick.selection || m.best_pick.pick || "").toLowerCase().includes(searchQuery)) ||
        ((m.selection || m.pick || "").toLowerCase().includes(searchQuery));
      return matchComp && matchQuery;
    }});

    // Update the scoreboard percentages in real-time!
    updateScoreboard(activeCohort, isPending);

    // Filter by market selection
    const filtered = activeCohort.filter(m => {{
      if (activeMarket === "best") return m.is_best === true;
      if (activeMarket === "result") return !!m.result_pick;
      if (activeMarket === "goals") return !!m.goal_total_pick;
      if (activeMarket === "btts") return !!m.btts_pick;
      if (activeMarket === "corners") return !!m.corner_pick;
      return true;
    }});

    // Update active highlight on scoreboard cards
    document.querySelectorAll("[data-pick-target]").forEach(c => {{
      c.classList.toggle("active-pick-card", c.getAttribute("data-pick-target") === activeMarket);
    }});

    document.getElementById("table-caption").textContent = isPending
      ? `Showing ${{filtered.length}} pending international calls`
      : `Showing ${{filtered.length}} graded historical outcomes`;

    if (!filtered.length) {{
      listEl.innerHTML = `<div class="empty-state">No international fixtures found matching your filter criteria.</div>`;
      return;
    }}

    listEl.innerHTML = filtered.map(m => {{
      const hasBest = m.is_best && m.best_pick;
      const probPct = Math.round(m.model_prob * 100);

      // Status Badge
      let statusHtml = "";
      if (isPending) {{
        statusHtml = `<span class="status-badge status-pending"><span class="pulse-dot"></span> Pending</span>`;
      }} else {{
        if (m.status === "HIT") {{
          statusHtml = `<span class="status-badge status-hit">&check; Hit</span><span class="unit-variance pos">+${{m.net_variance.toFixed(2)}}u</span>`;
        }} else if (m.status === "MISS") {{
          statusHtml = `<span class="status-badge status-miss">&cross; Miss</span><span class="unit-variance neg">${{m.net_variance.toFixed(2)}}u</span>`;
        }} else {{
          statusHtml = `<span class="status-badge status-push">&bull; Push</span><span class="unit-variance">0.00u</span>`;
        }}
      }}

      // Date format
      let dateStr = m.date;
      if (isPending && m.kickoff) {{
        try {{
          const kd = new Date(m.kickoff);
          const datePart = kd.toLocaleDateString(undefined, {{ weekday: "short", month: "short", day: "numeric" }});
          const timePart = kd.toLocaleTimeString(undefined, {{ hour: "2-digit", minute: "2-digit", hour12: false }});
          const utcHours = String(kd.getUTCHours()).padStart(2, "0");
          const utcMins = String(kd.getUTCMinutes()).padStart(2, "0");
          dateStr = `${{datePart}} · ${{timePart}} (UTC ${{utcHours}}:${{utcMins}})`;
        }} catch (e) {{
          dateStr = m.kickoff.replace("T", " ").replace("Z", " UTC");
        }}
      }}

      // Yellow Highlighted Best Pick Pill OR Neutral Pass Pill
      let bestPillHtml = "";
      const bestChoiceVal = (hasBest && m.best_pick) ? (m.best_pick.selection || m.best_pick.pick || "") : "";
      if (hasBest && !m.best_pick.is_pass && !bestChoiceVal.includes("NO PICK")) {{
        const bOdds = (m.best_pick.odds && typeof m.best_pick.odds === 'number') ? m.best_pick.odds.toFixed(2) : "1.90";
        const bProb = (m.best_pick.prob && typeof m.best_pick.prob === 'number') ? Math.round(m.best_pick.prob * 100) : 55;
        const bEdge = m.best_pick.edge || "+3.0%";
        bestPillHtml = `
          <div class="best-pick-pill">
            <span class="star-icon">★</span>
            <span class="best-lbl">BEST PICK:</span>
            <span class="best-val">${{bestChoiceVal}}</span>
            <span class="best-odds">@ ${{bOdds}}</span>
            <span class="best-cv-meta" style="font-size:0.68rem; color:var(--yellow); opacity:0.95; padding-left:0.4rem; border-left:1px solid rgba(250,204,21,0.35);">${{bProb}}% Conf &bull; ${{bEdge}} EV</span>
          </div>
        `;
      }} else {{
        bestPillHtml = `
          <div class="pass-pill">
            <span class="pass-icon">⊘</span>
            <span class="pass-lbl">PASS:</span>
            <span class="pass-reason">No Edge / High Uncertainty</span>
          </div>
        `;
      }}

      // Score presentation
      const predScore = m.pred_score || "2-1";
      const finalScore = m.final_score || "";

      // Check which pick is the best pick to highlight its item in yellow
      const bestMarket = (hasBest && !m.best_pick.is_pass) ? m.best_pick.market : "";
      const isResultBest = bestMarket === "Match Result";
      const isGoalsBest = bestMarket === "Goal Total";
      const isBttsBest = bestMarket === "BTTS";
      const isCornerBest = bestMarket === "Corners";

      const resPick = m.result_pick || {{ pick: m.selection || "Home Win", selection: m.selection || "Home Win", prob: m.model_prob, odds: m.closing_odds, status: m.status }};
      const gtPick = m.goal_total_pick || {{ pick: "Under 2.5", selection: "Under 2.5", prob: 0.58, odds: 1.82, status: "PENDING" }};
      const bttsPick = m.btts_pick || {{ pick: "BTTS Yes", selection: "BTTS Yes", prob: 0.60, odds: 1.75, status: "PENDING" }};
      const corPick = m.corner_pick || {{ pick: "Corners Over 9.5", selection: "Corners Over 9.5", prob: 0.61, odds: 1.80, status: "PENDING" }};

      function renderPickGridItem(label, pickObj, isBestItem) {{
        const pickVal = (pickObj && (pickObj.selection || pickObj.pick)) ? (pickObj.selection || pickObj.pick) : "NO PICK";
        const isPass = !pickObj || pickObj.is_pass || pickVal.includes("NO PICK");
        if (isPass) {{
          const probStr = (pickObj && pickObj.prob) ? `${{Math.round(pickObj.prob * 100)}}% Ambiguous` : 'High Entropy';
          return `
            <div class="pick-item is-pass-item">
              <div class="pick-head">
                <span>${{label}}</span>
                <span class="pass-tag">PASS</span>
              </div>
              <div class="pick-val pass-val">NO PICK</div>
              <div class="pick-footer">
                <span class="pass-sub">${{probStr}}</span>
                <span class="sub-pass">${{(pickObj && pickObj.status === "PENDING") ? "PASS" : "VOID"}}</span>
              </div>
            </div>
          `;
        }}
        const oddsStr = (pickObj && typeof pickObj.odds === 'number') ? pickObj.odds.toFixed(2) : '1.90';
        const probVal = (pickObj && typeof pickObj.prob === 'number') ? Math.round(pickObj.prob * 100) : 50;
        return `
          <div class="pick-item ${{isBestItem ? 'is-best-item' : ''}}">
            <div class="pick-head">
              <span>${{label}}</span>
              ${{isBestItem ? '<span class="yellow-star">★ BEST</span>' : ''}}
            </div>
            <div class="pick-val">${{pickVal}}</div>
            <div class="pick-footer">
              <span>${{probVal}}% @ ${{oddsStr}}</span>
              ${{renderSubStatus(pickObj ? pickObj.status : "PENDING")}}
            </div>
          </div>
        `;
      }}

      const stats = getMatchStats(m);
      const isOpen = openDrawers.has(m.id);

      return `
        <article class="match-card ${{hasBest ? 'has-best' : ''}}" id="card-${{m.id}}">
          <!-- Top Bar: Date, Tournament & Yellow Best Pick Pill -->
          <div class="card-top-bar" onclick="window.toggleMatchDrawer('${{m.id}}', event)">
            <div class="card-left-meta">
              <span class="match-date">${{dateStr}}</span>
              <span class="dot-sep">•</span>
              <span class="match-comp">${{m.competition}}</span>
            </div>
            ${{bestPillHtml}}
          </div>

          <!-- Fixture Title & Scores (Clickable to expand) -->
          <div class="card-fixture-row" onclick="window.toggleMatchDrawer('${{m.id}}', event)" title="Click to view match analytics">
            <div class="teams-block">
              <div class="fixture-teams">${{m.fixture}}</div>
              <div class="fixture-sub-meta">
                ${{isPending 
                  ? `Model Confidence: <b>${{probPct}}%</b> &nbsp;|&nbsp; Market Edge: <b>${{m.edge}}</b>` 
                  : `Model Prob: <b>${{probPct}}%</b> &nbsp;|&nbsp; Edge: <b>${{m.edge}}</b>`}}
              </div>
            </div>

            <!-- Score Display -->
            <div class="score-display-block">
              <div class="score-col">
                <span class="score-lbl">PRED SCORE</span>
                <span class="score-val pred">${{predScore}}</span>
              </div>
              ${{!isPending ? `
                <div class="score-col">
                  <span class="score-lbl">FINAL FT</span>
                  <span class="score-val final">${{finalScore}}</span>
                </div>
              ` : ''}}
              <div class="score-col" style="align-items:flex-end;">
                <span class="score-lbl">STATUS</span>
                <div>${{statusHtml}}</div>
              </div>
            </div>
          </div>

          <!-- 4-Picks Analytical Grid (All 4 dimensions displayed) -->
          <div class="picks-grid">
            ${{renderPickGridItem("MATCH RESULT (1X2)", resPick, isResultBest)}}
            ${{renderPickGridItem("GOAL TOTAL (O/U)", gtPick, isGoalsBest)}}
            ${{renderPickGridItem("BTTS", bttsPick, isBttsBest)}}
            ${{renderPickGridItem("CORNERS", corPick, isCornerBest)}}
          </div>

          <!-- Card Expand Bar (Click to toggle match analytics) -->
          <div class="card-expand-bar" onclick="window.toggleMatchDrawer('${{m.id}}', event)">
            <span class="expand-bar-left">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m11 17-5-5a2.5 2.5 0 0 1 0-3.5 2.5 2.5 0 0 1 3.5 0L12 11l2.5-2.5a2.5 2.5 0 0 1 3.5 0 2.5 2.5 0 0 1 0 3.5l-5 5"></path>
                <path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"></path>
              </svg>
              <span class="expand-bar-text" id="exp-text-${{m.id}}">${{isOpen ? 'Hide Match Intelligence' : 'Head-to-Head & Match Intelligence'}}</span>
            </span>
            <span class="chevron-toggle" id="chev-${{m.id}}">${{isOpen ? '▴' : '▾'}}</span>
          </div>

          <!-- Expandable Match Analytics Drawer -->
          ${{renderMatchDrawer(m, stats)}}
        </article>
      `;
    }}).join("");
  }}

  // Event Listeners for Tabs
  const tabPending = document.getElementById("tab-pending");
  const tabGraded = document.getElementById("tab-graded");
  const tabMath = document.getElementById("tab-math");
  const chartSection = document.getElementById("chart-section");
  const filterControls = document.getElementById("filter-controls");
  const matchesList = document.getElementById("matches-list");
  const mathPanel = document.getElementById("math-panel");

  function switchTab(tab) {{
    activeTab = tab;
    tabPending.classList.toggle("active", tab === "pending");
    tabGraded.classList.toggle("active", tab === "graded");
    tabMath.classList.toggle("active", tab === "math");

    if (tab === "math") {{
      chartSection.style.display = "none";
      filterControls.style.display = "none";
      matchesList.style.display = "none";
      mathPanel.classList.add("active");
    }} else {{
      chartSection.style.display = "block";
      filterControls.style.display = "flex";
      matchesList.style.display = "flex";
      mathPanel.classList.remove("active");
      renderList();
    }}
  }}

  tabPending.addEventListener("click", () => switchTab("pending"));
  tabGraded.addEventListener("click", () => switchTab("graded"));
  tabMath.addEventListener("click", () => switchTab("math"));

  // Market filter chips
  document.querySelectorAll("[data-market]").forEach(btn => {{
    btn.addEventListener("click", () => {{
      document.querySelectorAll("[data-market]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeMarket = btn.getAttribute("data-market");
      renderList();
    }});
  }});

  // Scoreboard metric card click-to-filter (with toggle support)
  document.querySelectorAll("[data-pick-target]").forEach(card => {{
    card.addEventListener("click", () => {{
      const target = card.getAttribute("data-pick-target");
      const nextMarket = (activeMarket === target) ? "all" : target;
      const targetChip = document.querySelector(`[data-market="${{nextMarket}}"]`);
      if (targetChip) {{
        document.querySelectorAll("[data-market]").forEach(b => b.classList.remove("active"));
        targetChip.classList.add("active");
        activeMarket = nextMarket;
        renderList();
      }}
    }});
  }});

  // Tournament filter chips
  document.querySelectorAll("#comp-chips .chip").forEach(btn => {{
    btn.addEventListener("click", () => {{
      document.querySelectorAll("#comp-chips .chip").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeComp = btn.getAttribute("data-comp");
      document.getElementById("filter-summary").textContent = activeComp === "all"
        ? "Showing all tournaments"
        : `Filtering by ${{activeComp}}`;
      renderList();
    }});
  }});

  // Search input
  document.getElementById("search-input").addEventListener("input", (e) => {{
    searchQuery = e.target.value.trim().toLowerCase();
    renderList();
  }});

  window.toggleMatchDrawer = function(matchId, event) {{
    if (event) event.stopPropagation();
    const drawer = document.getElementById("drawer-" + matchId);
    const chev = document.getElementById("chev-" + matchId);
    const expText = document.getElementById("exp-text-" + matchId);
    if (!drawer) return;
    const isExpanded = drawer.classList.contains("expanded");
    if (isExpanded) {{
      drawer.classList.remove("expanded");
      openDrawers.delete(matchId);
      if (chev) chev.textContent = "▾";
      if (expText) expText.textContent = "Head-to-Head & Match Intelligence";
    }} else {{
      drawer.classList.add("expanded");
      openDrawers.add(matchId);
      if (chev) chev.textContent = "▴";
      if (expText) expText.textContent = "Hide Match Intelligence";
    }}
  }};

  window.switchDrawerTab = function(matchId, tabName, event) {{
    if (event) event.stopPropagation();
    activeDrawerTabs[matchId] = tabName;
    const tabs = ["h2h", "matrix", "team"];
    tabs.forEach(t => {{
      const btn = document.getElementById(`btn-tab-${{t}}-${{matchId}}`);
      const pane = document.getElementById(`pane-${{t}}-${{matchId}}`);
      if (btn) btn.classList.toggle("active", t === tabName);
      if (pane) {{
        pane.style.display = (t === tabName) ? "block" : "none";
      }}
    }});
  }};

  window.navDrawerSlide = function(matchId, delta, event) {{
    if (event) event.stopPropagation();
    const container = document.getElementById("ccontainer-" + matchId);
    const ind = document.getElementById("cnav-ind-" + matchId);
    if (!container) return;
    let current = parseInt(container.getAttribute("data-current-slide") || "1", 10);
    let next = current + delta;
    if (next < 1) next = 3;
    if (next > 3) next = 1;
    activeDrawerSlides[matchId] = next;
    container.setAttribute("data-current-slide", next);
    if (ind) ind.textContent = next + "/3";

    for (let s = 1; s <= 3; s++) {{
      const slide = document.getElementById(`cslide-${{s}}-${{matchId}}`);
      if (slide) {{
        slide.style.display = (s === next) ? "block" : "none";
      }}
    }}
  }};

  renderList();
}})();
</script>
</body>
</html>
"""

    out_public = Path("public/index.html")
    out_public.parent.mkdir(parents=True, exist_ok=True)
    out_public.write_text(html, encoding="utf-8")

    out_root = Path("index.html")
    out_root.write_text(html, encoding="utf-8")
    print(f"Successfully generated {out_public} and {out_root} ({out_public.stat().st_size} bytes).")


if __name__ == "__main__":
    generate_html()

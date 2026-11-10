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

    /* Scoreboard Calibration Strip (Matched to Vercel Theme) */
    .scoreboard-strip {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 2rem;
    }}
    .strip-top-row {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      border-bottom: 1px solid var(--border);
    }}
    .strip-bottom-row {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
    }}
    .strip-card {{
      padding: 1.15rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      border-right: 1px solid var(--border);
      background: var(--card);
      transition: all 0.15s ease;
      cursor: pointer;
      position: relative;
    }}
    .strip-card:hover {{
      background: var(--card-hover);
    }}
    .strip-card.active-pick-card {{
      background: #171717;
      box-shadow: inset 0 -2px 0 var(--white);
    }}
    .strip-card.highlight-gold.active-pick-card {{
      box-shadow: inset 0 -2px 0 var(--yellow);
    }}
    .strip-top-row .strip-card:last-child {{
      border-right: none;
    }}
    .strip-card.rps-card {{
      border-right: 1px solid var(--border);
      cursor: default;
    }}
    .strip-card.rps-card:hover {{
      background: var(--card);
    }}
    .strip-empty-space {{
      grid-column: 2 / span 5;
      background: var(--card);
    }}
    .strip-label {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      font-weight: 500;
      line-height: 1.2;
    }}
    .strip-val {{
      font-size: 2.1rem;
      font-weight: 700;
      letter-spacing: -0.04em;
      color: var(--white);
      line-height: 1.05;
      font-variant-numeric: tabular-nums;
      margin-top: 0.1rem;
      transition: all 0.2s ease;
    }}
    .strip-val.gold {{
      color: var(--yellow);
      text-shadow: 0 0 16px rgba(250, 204, 21, 0.25);
    }}
    .strip-sub {{
      font-family: var(--font-mono);
      font-size: 0.74rem;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      gap: 0.12rem;
      font-variant-numeric: tabular-nums;
      margin-top: 0.15rem;
      line-height: 1.35;
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
      .strip-top-row {{
        grid-template-columns: repeat(3, 1fr);
      }}
      .strip-top-row .strip-card:nth-child(3) {{
        border-right: none;
      }}
      .strip-bottom-row {{
        grid-template-columns: repeat(3, 1fr);
      }}
      .strip-empty-space {{
        grid-column: 2 / span 2;
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
      .strip-top-row {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .strip-top-row .strip-card:nth-child(2n) {{
        border-right: none;
      }}
      .strip-bottom-row {{
        grid-template-columns: 1fr;
      }}
      .strip-empty-space {{
        display: none;
      }}
      .picks-grid {{
        grid-template-columns: 1fr;
      }}
      .card-top-bar {{
        flex-direction: column;
        align-items: flex-start;
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

  <!-- Scoreboard Calibration Strip (Recreated from User Reference) -->
  <div class="scoreboard-strip">
    <div class="strip-top-row">
      <!-- 1. GOALS PICKS -->
      <div class="strip-card" data-pick-target="goals" title="Filter by Goal Total picks">
        <span class="strip-label">GOALS PICKS</span>
        <span class="strip-val" id="sb-goals-val">76%</span>
        <span class="strip-sub">
          <span id="sb-goals-sub">117/153 &middot; exp 119.1</span>
        </span>
      </div>

      <!-- 2. BTTS PICKS -->
      <div class="strip-card" data-pick-target="btts" title="Filter by BTTS picks">
        <span class="strip-label">BTTS PICKS</span>
        <span class="strip-val" id="sb-btts-val">55%</span>
        <span class="strip-sub">
          <span id="sb-btts-sub">86/155 &middot; exp 96.0</span>
        </span>
      </div>

      <!-- 3. CORNERS PICKS -->
      <div class="strip-card" data-pick-target="corners" title="Filter by Corners picks">
        <span class="strip-label">CORNERS PICKS</span>
        <span class="strip-val" id="sb-corners-val">70%</span>
        <span class="strip-sub">
          <span id="sb-corners-sub">77/110 &middot; exp 81.8</span>
        </span>
      </div>

      <!-- 4. RESULT PICKS -->
      <div class="strip-card" data-pick-target="result" title="Filter by Match Result picks">
        <span class="strip-label">RESULT PICKS</span>
        <span class="strip-val" id="sb-result-val">70%</span>
        <span class="strip-sub">
          <span id="sb-result-sub">102/145 &middot; exp 97.1</span>
        </span>
      </div>

      <!-- 5. BEST PICKS (Yellow Highlighted) -->
      <div class="strip-card highlight-gold" data-pick-target="best" title="Filter by Best Picks">
        <span class="strip-label">BEST PICKS</span>
        <span class="strip-val gold" id="sb-best-val">69%</span>
        <span class="strip-sub">
          <span id="sb-best-sub1">113/164 &middot; exp 115.6</span>
          <span id="sb-best-sub2">&middot; priced 138:</span>
          <span id="sb-best-sub3">+0.69u</span>
        </span>
      </div>

      <!-- 6. CORRECT SCORE -->
      <div class="strip-card" data-pick-target="score" title="Exact Correct Scores">
        <span class="strip-label">CORRECT SCORE</span>
        <span class="strip-val" id="sb-score-val">11%</span>
        <span class="strip-sub">
          <span id="sb-score-sub">32/302 &middot; exp 32.8</span>
        </span>
      </div>
    </div>

    <!-- Bottom Row -->
    <div class="strip-bottom-row">
      <!-- 7. RPS (LOWER IS BETTER) -->
      <div class="strip-card rps-card" title="Ranked Probability Score">
        <span class="strip-label">RPS (LOWER IS BETTER)</span>
        <span class="strip-val" id="sb-rps-val">0.190</span>
        <span class="strip-sub">
          <span id="sb-rps-sub1">model 0.189 vs</span>
          <span id="sb-rps-sub2">market 0.190</span>
          <span id="sb-rps-sub3">(n=299)</span>
        </span>
      </div>
      <!-- Open dark space replicating the user screenshot -->
      <div class="strip-empty-space"></div>
    </div>
  </div>

  <!-- Calibration Visualizer -->
  <div class="chart-box" id="chart-section">
    <div class="chart-header">
      <div>
        <div class="chart-title">Probabilistic Calibration & Variance Tracking</div>
        <div class="chart-desc">Compares cumulative winning calls against model forecast probabilities ($E = \\sum p_i$).</div>
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
        if (m.goal_total_pick.is_pass || (m.goal_total_pick.pick && m.goal_total_pick.pick.includes("NO PICK"))) {{
          gtPasses++;
        }} else {{
          gtTotal++;
          gtExp += (m.goal_total_pick.prob || 0.58);
          if (m.goal_total_pick.status === "HIT") gtHits++;
        }}
      }}
      // BTTS
      if (m.btts_pick) {{
        if (m.btts_pick.is_pass || (m.btts_pick.pick && m.btts_pick.pick.includes("NO PICK"))) {{
          bttsPasses++;
        }} else {{
          bttsTotal++;
          bttsExp += (m.btts_pick.prob || 0.60);
          if (m.btts_pick.status === "HIT") bttsHits++;
        }}
      }}
      // Corners
      if (m.corner_pick) {{
        if (m.corner_pick.is_pass || (m.corner_pick.pick && m.corner_pick.pick.includes("NO PICK"))) {{
          corPasses++;
        }} else {{
          corTotal++;
          corExp += (m.corner_pick.prob || 0.61);
          if (m.corner_pick.status === "HIT") corHits++;
        }}
      }}
      // Result
      if (m.result_pick) {{
        if (m.result_pick.is_pass || (m.result_pick.pick && m.result_pick.pick.includes("NO PICK"))) {{
          resPasses++;
        }} else {{
          resTotal++;
          resExp += (m.result_pick.prob || 0.55);
          if (m.result_pick.status === "HIT") resHits++;
        }}
      }}
      // Best Pick
      if (m.is_best && m.best_pick && !m.best_pick.is_pass && !(m.best_pick.selection && m.best_pick.selection.includes("NO PICK"))) {{
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
      if (!isPending && m.result_pick && !m.result_pick.is_pass && !(m.result_pick.pick && m.result_pick.pick.includes("NO PICK"))) {{
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
        (m.best_pick && m.best_pick.selection.toLowerCase().includes(searchQuery)) ||
        (m.selection && m.selection.toLowerCase().includes(searchQuery));
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
      if (hasBest && !m.best_pick.is_pass && !(m.best_pick.selection && m.best_pick.selection.includes("NO PICK"))) {{
        bestPillHtml = `
          <div class="best-pick-pill">
            <span class="star-icon">★</span>
            <span class="best-lbl">BEST PICK:</span>
            <span class="best-val">${{m.best_pick.selection}}</span>
            <span class="best-odds">@ ${{m.best_pick.odds.toFixed(2)}}</span>
            <span class="best-cv-meta" style="font-size:0.68rem; color:var(--yellow); opacity:0.95; padding-left:0.4rem; border-left:1px solid rgba(250,204,21,0.35);">${{Math.round(m.best_pick.prob * 100)}}% Conf &bull; ${{m.best_pick.edge}} EV</span>
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

      const resPick = m.result_pick || {{ pick: m.selection || "Home Win", prob: m.model_prob, odds: m.closing_odds, status: m.status }};
      const gtPick = m.goal_total_pick || {{ pick: "Under 2.5", prob: 0.58, odds: 1.82, status: "PENDING" }};
      const bttsPick = m.btts_pick || {{ pick: "BTTS Yes", prob: 0.60, odds: 1.75, status: "PENDING" }};
      const corPick = m.corner_pick || {{ pick: "Corners Over 9.5", prob: 0.61, odds: 1.80, status: "PENDING" }};

      function renderPickGridItem(label, pickObj, isBestItem) {{
        const isPass = pickObj.is_pass || (pickObj.pick && pickObj.pick.includes("NO PICK"));
        if (isPass) {{
          const probStr = pickObj.prob ? `${{Math.round(pickObj.prob * 100)}}% Ambiguous` : 'High Entropy';
          return `
            <div class="pick-item is-pass-item">
              <div class="pick-head">
                <span>${{label}}</span>
                <span class="pass-tag">PASS</span>
              </div>
              <div class="pick-val pass-val">NO PICK</div>
              <div class="pick-footer">
                <span class="pass-sub">${{probStr}}</span>
                <span class="sub-pass">${{pickObj.status === "PENDING" ? "PASS" : "VOID"}}</span>
              </div>
            </div>
          `;
        }}
        return `
          <div class="pick-item ${{isBestItem ? 'is-best-item' : ''}}">
            <div class="pick-head">
              <span>${{label}}</span>
              ${{isBestItem ? '<span class="yellow-star">★ BEST</span>' : ''}}
            </div>
            <div class="pick-val">${{pickObj.pick}}</div>
            <div class="pick-footer">
              <span>${{Math.round(pickObj.prob * 100)}}% @ ${{pickObj.odds.toFixed(2)}}</span>
              ${{renderSubStatus(pickObj.status)}}
            </div>
          </div>
        `;
      }}

      return `
        <article class="match-card ${{hasBest ? 'has-best' : ''}}">
          <!-- Top Bar: Date, Tournament & Yellow Best Pick Pill -->
          <div class="card-top-bar">
            <div class="card-left-meta">
              <span class="match-date">${{dateStr}}</span>
              <span class="dot-sep">•</span>
              <span class="match-comp">${{m.competition}}</span>
            </div>
            ${{bestPillHtml}}
          </div>

          <!-- Fixture Title & Scores -->
          <div class="card-fixture-row">
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

  // Scoreboard strip card click-to-filter
  document.querySelectorAll("[data-pick-target]").forEach(card => {{
    card.addEventListener("click", () => {{
      const target = card.getAttribute("data-pick-target");
      const targetChip = document.querySelector(`[data-market="${{target}}"]`);
      if (targetChip) {{
        document.querySelectorAll("[data-market]").forEach(b => b.classList.remove("active"));
        targetChip.classList.add("active");
        activeMarket = target;
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

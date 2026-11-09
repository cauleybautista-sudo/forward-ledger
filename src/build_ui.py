"""Generates the Vercel-style International Football Forward Ledger UI in public/index.html."""

import json
from pathlib import Path


def generate_html():
    data_path = Path("src/data.json")
    if not data_path.exists():
        raise FileNotFoundError("src/data.json does not exist")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    json_str = json.dumps(data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Forward Ledger | International Football Predictive Model</title>
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
      fill: var(--white);
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
      background: #22c55e;
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

    /* Metrics Strip */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 1px;
      background: var(--border);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 2rem;
    }}
    .metric-card {{
      background: var(--card);
      padding: 1.25rem 1.15rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: background 0.15s ease;
    }}
    .metric-card:hover {{
      background: var(--card-hover);
    }}
    .metric-label {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }}
    .metric-value {{
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      color: var(--white);
      font-variant-numeric: tabular-nums;
    }}
    .metric-sub {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 0.35rem;
    }}

    /* Chart Section */
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
      font-size: 1rem;
      font-weight: 600;
      color: var(--white);
      letter-spacing: -0.02em;
    }}
    .chart-desc {{
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .chart-legend {{
      display: flex;
      align-items: center;
      gap: 1.25rem;
      font-family: var(--font-mono);
      font-size: 0.75rem;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 0.45rem;
      color: var(--text-muted);
    }}
    .legend-bar {{
      width: 14px;
      height: 3px;
      border-radius: 2px;
    }}
    .chart-svg {{
      width: 100%;
      height: auto;
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

    /* Search & Filters */
    .controls-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.85rem;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.25rem;
    }}
    .search-input {{
      flex: 1;
      min-width: 260px;
      max-width: 420px;
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

    .filter-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      margin-bottom: 1.5rem;
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

    /* Match Cards */
    .matches-list {{
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
    }}
    .match-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.15rem 1.35rem;
      display: grid;
      grid-template-columns: 140px minmax(0, 1fr) 200px max-content;
      gap: 1.25rem;
      align-items: center;
      transition: all 0.15s ease;
    }}
    .match-card:hover {{
      border-color: var(--border-light);
      background: var(--card-hover);
    }}
    .match-card.is-edge {{
      border-left: 3px solid var(--white);
    }}

    .kickoff-info {{
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .kickoff-date {{
      color: var(--text);
      font-weight: 500;
      margin-bottom: 0.2rem;
    }}
    .kickoff-comp {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #a1a1aa;
    }}

    .fixture-info {{
      min-width: 0;
    }}
    .fixture-teams {{
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--white);
      letter-spacing: -0.02em;
      margin-bottom: 0.35rem;
    }}
    .fixture-meta {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.8rem;
    }}
    .sel-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: #1a1a1a;
      border: 1px solid var(--border-light);
      padding: 0.15rem 0.55rem;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--white);
    }}
    .edge-tag {{
      display: inline-flex;
      align-items: center;
      background: #ffffff;
      color: #000000;
      padding: 0.12rem 0.5rem;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    .odds-meta {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    /* Prob track */
    .prob-box {{
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }}
    .prob-track {{
      display: flex;
      height: 6px;
      background: #1c1c1c;
      border-radius: 3px;
      overflow: hidden;
    }}
    .prob-seg-home {{ background: #ffffff; }}
    .prob-seg-draw {{ background: #555555; }}
    .prob-seg-away {{ background: #888888; }}
    .prob-labels {{
      display: flex;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--text-muted);
      font-variant-numeric: tabular-nums;
    }}

    /* Score & Status */
    .score-status {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      justify-content: flex-end;
    }}
    .score-box {{
      font-family: var(--font-mono);
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      background: #141414;
      border: 1px solid var(--border-light);
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      color: var(--white);
      min-width: 60px;
      text-align: center;
    }}
    .status-badge {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.3rem 0.7rem;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }}
    .status-hit {{
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid #ffffff;
      color: #ffffff;
    }}
    .status-miss {{
      background: #111111;
      border: 1px solid #2a2a2a;
      color: #777777;
    }}
    .status-push {{
      background: #161616;
      border: 1px solid #333333;
      color: #aaaaaa;
    }}
    .status-pending {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid #333333;
      color: #ffffff;
    }}
    .unit-variance {{
      font-family: var(--font-mono);
      font-size: 0.8rem;
      font-weight: 600;
      margin-left: 0.25rem;
    }}
    .pos-units {{ color: #ffffff; }}
    .neg-units {{ color: #777777; }}

    /* Calibration Math Panel */
    .math-panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}
    .math-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.25rem;
    }}
    .math-card {{
      background: #111111;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
    }}
    .math-card h4 {{
      font-size: 0.9rem;
      color: var(--white);
      margin-bottom: 0.5rem;
    }}
    .math-formula {{
      font-family: var(--font-mono);
      font-size: 0.85rem;
      background: #000000;
      border: 1px solid var(--border);
      padding: 0.5rem 0.75rem;
      border-radius: 4px;
      color: #a3e635;
      margin-bottom: 0.5rem;
    }}
    .math-desc {{
      font-size: 0.78rem;
      color: var(--text-muted);
    }}

    /* Empty State */
    .empty-state {{
      text-align: center;
      padding: 3.5rem 1rem;
      color: var(--text-muted);
      border: 1px dashed var(--border);
      border-radius: 10px;
    }}

    /* Responsive */
    @media (max-width: 860px) {{
      .match-card {{
        grid-template-columns: 1fr;
        gap: 0.75rem;
      }}
      .prob-box {{ display: none; }}
      .score-status {{ justify-content: flex-start; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <header>
    <div class="brand">
      <svg viewBox="0 0 76 65" height="24" width="28">
        <path d="M37.5274 0L75.0548 65H0L37.5274 0Z"></path>
      </svg>
      <div>
        <div class="brand-title">Forward Ledger</div>
      </div>
      <span class="brand-tag"><span class="pulse-dot"></span> International Football</span>
    </div>
    <div class="header-meta">
      <span id="clock-utc">00:00:00 UTC</span>
      <span style="color:var(--border-light)">&bull;</span>
      <span>Immutable Log</span>
    </div>
  </header>

  <!-- Metrics Strip -->
  <div class="metrics-grid">
    <div class="metric-card">
      <span class="metric-label">Brier Score</span>
      <span class="metric-value" id="val-brier">0.2295</span>
      <span class="metric-sub">&lt; 0.2000 Elite Benchmark</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Actual vs Expected</span>
      <span class="metric-value" id="val-hits">66 / 61.0</span>
      <span class="metric-sub" style="color:#ffffff;">+4.96u Positive Variance</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Net Profit / Loss</span>
      <span class="metric-value" id="val-units">+19.25u</span>
      <span class="metric-sub">Flat 1.0u Unit Staking</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Hit Rate</span>
      <span class="metric-value" id="val-rate">66.0%</span>
      <span class="metric-sub">66 Hits &bull; 34 Misses</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">ROI / Yield</span>
      <span class="metric-value" id="val-roi">+19.3%</span>
      <span class="metric-sub">100 Graded Selections</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Active Pre-Kickoff</span>
      <span class="metric-value" id="val-pending">20</span>
      <span class="metric-sub">Pending Odds Locks</span>
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

  <!-- Filters Row -->
  <div id="filter-controls">
    <div class="controls-row">
      <input type="text" id="search-input" class="search-input" placeholder="Search national teams (e.g. Spain, Brazil, Argentina)...">
      <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted);" id="filter-summary">
        Showing all competitions
      </div>
    </div>

    <!-- Competition Filter Chips -->
    <div class="filter-chips" id="comp-chips">
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

  <!-- Math & Calibration Panel -->
  <div class="math-panel" id="math-panel" style="display:none;">
    <h3 style="font-size:1.15rem; color:#fff;">Forward Ledger Calibration Engine</h3>
    <p style="color:var(--text-muted); font-size:0.85rem;">
      International football prediction requires strict calibration over long horizons due to lower match frequencies and elevated variance compared to domestic leagues.
    </p>

    <div class="math-grid">
      <div class="math-card">
        <h4>Expected Hits Calibration</h4>
        <div class="math-formula">E = &sum; p_i</div>
        <p class="math-desc">Sum of model predicted probabilities. If Actual &gt; Expected, the model is running in positive variance (lucky) or is under-confident. If Actual &lt; Expected, the model is over-confident.</p>
      </div>
      <div class="math-card">
        <h4>Brier Score (Mean Squared Error)</h4>
        <div class="math-formula">BS = (1/N) &sum; (f_t - o_t)&sup2;</div>
        <p class="math-desc">Measures probabilistic forecast accuracy where o_t &isin; &#123;0, 1&#125;. 0.0 represents perfect foresight; 0.25 is equivalent to coin flipping.</p>
      </div>
      <div class="math-card">
        <h4>Expected Value & Market Edge</h4>
        <div class="math-formula">EV = (P_model &times; Odds) - 1.0</div>
        <p class="math-desc">Selections are only submitted if EV &gt; 0 and the model probability exceeds the closing bookmaker implied fair probability by at least +2.5%.</p>
      </div>
    </div>
  </div>
</div>

<script>
const DATA = {json_str};

(function () {{
  let activeTab = "pending";
  let activeComp = "all";
  let searchQuery = "";

  // Live UTC Clock
  function updateClock() {{
    const now = new Date();
    document.getElementById("clock-utc").textContent = now.toUTCString().split(" ")[4] + " UTC";
  }}
  setInterval(updateClock, 1000);
  updateClock();

  // Render Cumulative Step Chart
  function renderChart() {{
    const graded = DATA.graded.slice().reverse();
    if (!graded.length) return;

    const W = 800, H = 200, L = 40, R = 20, T = 15, B = 25;
    let actual = 0, expected = 0;
    const pts = graded.map((m, i) => {{
      if (m.status === "HIT") actual += 1;
      expected += m.model_prob;
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

  // Render List
  function renderList() {{
    const listEl = document.getElementById("matches-list");
    const isPending = activeTab === "pending";
    const sourceData = isPending ? DATA.pending : DATA.graded;

    // Filter by competition & query
    const filtered = sourceData.filter(m => {{
      const matchComp = activeComp === "all" || m.competition.toLowerCase().includes(activeComp.toLowerCase());
      const matchQuery = !searchQuery ||
        m.fixture.toLowerCase().includes(searchQuery) ||
        m.competition.toLowerCase().includes(searchQuery) ||
        m.selection.toLowerCase().includes(searchQuery);
      return matchComp && matchQuery;
    }});

    document.getElementById("table-caption").textContent = isPending
      ? `Showing ${{filtered.length}} pending international calls`
      : `Showing ${{filtered.length}} graded historical outcomes`;

    if (!filtered.length) {{
      listEl.innerHTML = `<div class="empty-state">No international fixtures found matching your filter criteria.</div>`;
      return;
    }}

    listEl.innerHTML = filtered.map(m => {{
      const hasEdge = m.edge && parseFloat(m.edge) > 0;
      const probPct = Math.round(m.model_prob * 100);
      const impliedPct = m.implied_prob ? Math.round(m.implied_prob * 100) : Math.round((1 / m.closing_odds) * 100);

      // Status Badge
      let statusHtml = "";
      if (isPending) {{
        statusHtml = `<span class="status-badge status-pending"><span class="pulse-dot"></span> Pending</span>`;
      }} else {{
        if (m.status === "HIT") {{
          statusHtml = `<span class="status-badge status-hit">&check; Hit</span><span class="unit-variance pos-units">+${{m.net_variance.toFixed(2)}}u</span>`;
        }} else if (m.status === "MISS") {{
          statusHtml = `<span class="status-badge status-miss">&cross; Miss</span><span class="unit-variance neg-units">${{m.net_variance.toFixed(2)}}u</span>`;
        }} else {{
          statusHtml = `<span class="status-badge status-push">&bull; Push</span><span class="unit-variance">0.00u</span>`;
        }}
      }}

      // Score / Right column
      const rightCol = isPending
        ? `<div class="score-status">${{statusHtml}}</div>`
        : `<div class="score-status"><div class="score-box">${{m.final_score}}</div>${{statusHtml}}</div>`;

      // Date format
      const dateStr = isPending ? m.kickoff.replace("T", " ").replace("Z", " UTC") : m.date;

      return `
        <article class="match-card ${{hasEdge ? 'is-edge' : ''}}">
          <div class="kickoff-info">
            <div class="kickoff-date">${{dateStr}}</div>
            <div class="kickoff-comp">${{m.competition}}</div>
          </div>

          <div class="fixture-info">
            <div class="fixture-teams">${{m.fixture}}</div>
            <div class="fixture-meta">
              <span class="sel-tag">${{m.selection}}</span>
              ${{hasEdge ? `<span class="edge-tag">${{m.edge}} Edge</span>` : ''}}
              <span class="odds-meta">Odds: <b>${{m.closing_odds.toFixed(2)}}</b></span>
              <span class="odds-meta">Model: <b>${{probPct}}%</b></span>
              <span class="odds-meta">Fair: <b>${{impliedPct}}%</b></span>
            </div>
          </div>

          <div class="prob-box">
            <div class="prob-track">
              <div class="prob-seg-home" style="width: ${{probPct}}%;"></div>
              <div class="prob-seg-draw" style="width: ${{Math.max(10, 100 - probPct - 20)}}%;"></div>
              <div class="prob-seg-away" style="width: 20%;"></div>
            </div>
            <div class="prob-labels">
              <span>Model ${{probPct}}%</span>
              <span>Fair ${{impliedPct}}%</span>
            </div>
          </div>

          ${{rightCol}}
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
      mathPanel.style.display = "flex";
    }} else {{
      chartSection.style.display = "block";
      filterControls.style.display = "block";
      matchesList.style.display = "flex";
      mathPanel.style.display = "none";
      renderList();
    }}
  }}

  tabPending.addEventListener("click", () => switchTab("pending"));
  tabGraded.addEventListener("click", () => switchTab("graded"));
  tabMath.addEventListener("click", () => switchTab("math"));

  // Event Listeners for Competition Chips
  document.getElementById("comp-chips").addEventListener("click", (e) => {{
    const chip = e.target.closest("button.chip");
    if (!chip) return;
    document.querySelectorAll("#comp-chips .chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    activeComp = chip.dataset.comp;
    renderList();
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

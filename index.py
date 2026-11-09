"""Standard WSGI entrypoint for Vercel Python runtime."""


def app(environ, start_response):
    status = "200 OK"
    headers = [("Content-type", "text/html; charset=utf-8")]
    start_response(status, headers)

    html = b"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Forward Ledger | Predictive Model</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f3f4f6; padding: 2rem; max-width: 800px; margin: 0 auto; }
    h1 { color: #60a5fa; margin-bottom: 0.25rem; }
    .badge { display: inline-block; background: #1e3a8a; color: #93c5fd; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 1.5rem; }
    .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-top: 1rem; }
    .stat { background: #1f2937; padding: 1rem; border-radius: 8px; text-align: center; }
    .stat-val { font-size: 1.5rem; font-weight: bold; color: #38bdf8; }
    .stat-lbl { font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; margin-top: 0.25rem; }
  </style>
</head>
<body>
  <h1>Forward Ledger Predictive Model</h1>
  <div class="badge">Vercel Serverless Production &bull; Active</div>
  <div class="card">
    <h3 style="margin-top:0;">Model Calibration Summary</h3>
    <div class="grid">
      <div class="stat"><div class="stat-val">135</div><div class="stat-lbl">Selections</div></div>
      <div class="stat"><div class="stat-val">78</div><div class="stat-lbl">Actual Hits</div></div>
      <div class="stat"><div class="stat-val">74.82</div><div class="stat-lbl">Expected Hits</div></div>
      <div class="stat"><div class="stat-val">0.1984</div><div class="stat-lbl">Brier Score</div></div>
      <div class="stat"><div class="stat-val">+18.45u</div><div class="stat-lbl">Net P/L</div></div>
      <div class="stat"><div class="stat-val">57.7%</div><div class="stat-lbl">Hit Rate</div></div>
    </div>
  </div>
</body>
</html>
"""
    return [html]


handler = app

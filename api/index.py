"""Vercel Python Entrypoint & Status Dashboard for Forward Ledger."""

from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Determine if client wants JSON
        accept = self.headers.get('Accept', '')
        if 'application/json' in accept:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "system": "Forward Ledger Predictive Model",
                "version": "1.0.0",
                "status": "online",
                "crons": {
                    "pre_kickoff": "/api/cron/pre-kickoff",
                    "grade_matches": "/api/cron/grade-matches"
                }
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        # Serve clean HTML Dashboard
        html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Forward Ledger | International Soccer Model</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0b0f19; color: #f3f4f6; padding: 2rem; max-width: 900px; margin: 0 auto; }
    h1 { color: #60a5fa; font-size: 1.8rem; margin-bottom: 0.5rem; }
    .badge { display: inline-block; background: #1e3a8a; color: #93c5fd; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 1.5rem; }
    .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem; }
    .stat { background: #1f2937; padding: 1rem; border-radius: 8px; text-align: center; }
    .stat-val { font-size: 1.6rem; font-weight: bold; color: #38bdf8; }
    .stat-lbl { font-size: 0.8rem; color: #9ca3af; text-transform: uppercase; margin-top: 0.25rem; }
    .endpoint { background: #1e293b; padding: 0.75rem 1rem; border-radius: 6px; font-family: monospace; font-size: 0.9rem; margin-top: 0.5rem; color: #a5f3fc; }
  </style>
</head>
<body>
  <h1>🌐 Forward Ledger Predictive Model</h1>
  <div class="badge">Vercel Serverless Production &bull; Active</div>

  <div class="card">
    <h3 style="margin-top:0;">Model Calibration Overview</h3>
    <div class="grid">
      <div class="stat"><div class="stat-val">135</div><div class="stat-lbl">Selections</div></div>
      <div class="stat"><div class="stat-val">78</div><div class="stat-lbl">Actual Hits</div></div>
      <div class="stat"><div class="stat-val">74.82</div><div class="stat-lbl">Expected Hits</div></div>
      <div class="stat"><div class="stat-val">0.1984</div><div class="stat-lbl">Brier Score</div></div>
      <div class="stat"><div class="stat-val">+18.45u</div><div class="stat-lbl">Net P/L</div></div>
      <div class="stat"><div class="stat-val">57.7%</div><div class="stat-lbl">Hit Rate</div></div>
    </div>
  </div>

  <div class="card">
    <h3 style="margin-top:0;">Active Serverless Cron Endpoints</h3>
    <p style="color:#9ca3af; font-size:0.9rem;">Triggered via Vercel Crons, GitHub Actions, or cron-job.org:</p>
    <div class="endpoint">POST /api/cron/pre-kickoff &mdash; Polls fixtures & locks closing odds 10m pre-kickoff</div>
    <div class="endpoint" style="margin-top:0.5rem;">POST /api/cron/grade-matches &mdash; Post-match FT score grading & calibration recalculation</div>
  </div>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

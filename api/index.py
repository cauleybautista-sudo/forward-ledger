"""Vercel serverless entrypoint serving the complete Forward Ledger dashboard."""

from http.server import BaseHTTPRequestHandler
from pathlib import Path
import json

HTML_PATH = Path(__file__).parent.parent / "public" / "index.html"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        accept = self.headers.get("Accept", "")
        if "application/json" in accept and not "text/html" in accept:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps({
                    "system": "Forward Ledger Predictive Model",
                    "status": "online",
                    "endpoints": [
                        "/api/cron/pre-kickoff",
                        "/api/cron/grade-matches"
                    ]
                }).encode("utf-8")
            )
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if HTML_PATH.exists():
            self.wfile.write(HTML_PATH.read_bytes())
        else:
            self.wfile.write(b"<h1>Forward Ledger Online</h1>")

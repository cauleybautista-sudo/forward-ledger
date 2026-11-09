"""Vercel Python entrypoint serving the complete Forward Ledger dashboard."""

from pathlib import Path

HTML_PATH = Path(__file__).parent / "public" / "index.html"


def app(environ, start_response):
    status = "200 OK"
    headers = [("Content-type", "text/html; charset=utf-8")]
    start_response(status, headers)

    if HTML_PATH.exists():
        return [HTML_PATH.read_bytes()]
    return [b"<h1>Forward Ledger</h1>"]


handler = app

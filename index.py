"""Vercel Python entrypoint serving the complete Football Tracker dashboard."""

from pathlib import Path

HTML_PATH_PUBLIC = Path(__file__).parent / "public" / "index.html"
HTML_PATH_ROOT = Path(__file__).parent / "index.html"


def app(environ, start_response):
    status = "200 OK"
    headers = [("Content-type", "text/html; charset=utf-8")]
    start_response(status, headers)

    if HTML_PATH_PUBLIC.exists():
        return [HTML_PATH_PUBLIC.read_bytes()]
    if HTML_PATH_ROOT.exists():
        return [HTML_PATH_ROOT.read_bytes()]
    return [b"<h1>Football Tracker Online</h1>"]


handler = app

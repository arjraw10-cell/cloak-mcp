"""Local fixture server. GET /r/<token>/<file> serves fixtures/<file>; POST /r/<token>/api/<event>
logs {token, event, data} to results/raw/server_events.jsonl. The token ties events to one run."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"
EVENTS = ROOT / "results" / "raw" / "server_events.jsonl"
PORT = 8765
_lock = threading.Lock()
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript"}


class Handler(BaseHTTPRequestHandler):
    def _parts(self):
        parts = self.path.split("?")[0].strip("/").split("/")
        return parts if len(parts) >= 3 and parts[0] == "r" else None

    def _send(self, code, body: bytes, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parts = self._parts()
        f = FIXTURES / parts[-1] if parts and len(parts) == 3 else None
        if f is None or not f.is_file():
            return self._send(404, b"<h1>Not found</h1>")
        self._send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))

    def do_POST(self):
        parts = self._parts()
        if not parts or len(parts) != 4 or parts[2] != "api":
            return self._send(404, b"<h1>Not found</h1>")
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8", "replace")
        is_json = "json" in (self.headers.get("Content-Type") or "")
        data = json.loads(raw or "{}") if is_json else {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        with _lock, EVENTS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.time(), "token": parts[1], "event": parts[3], "data": data}) + "\n")
        if is_json:
            return self._send(200, b'{"ok": true}', "application/json")
        self._send(200, b"<!doctype html><title>Submitted</title><h1>Submitted</h1><p>Thank you, we received it.</p>")

    def log_message(self, *args):
        pass


def events_for(token: str) -> list:
    if not EVENTS.is_file():
        return []
    with _lock:
        lines = EVENTS.read_text(encoding="utf-8").splitlines()
    return [e for e in map(json.loads, lines) if e["token"] == token]


def start() -> ThreadingHTTPServer:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    start()
    print(f"serving fixtures on http://127.0.0.1:{PORT}/r/<token>/")
    threading.Event().wait()

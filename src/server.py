"""Loopback-only reproducible support API simulator, not an Everbridge API."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CASE = json.loads((ROOT / "data/case.json").read_text())

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/dispatch":
            return self.send_json(404, {"error": "Not found"})
        length = int(self.headers.get("Content-Length", "0"))
        if length > 4096:
            return self.send_json(413, {"error": "Body too large"})
        try:
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            return self.send_json(400, {"error": "Invalid JSON"})
        if not isinstance(payload, dict) or payload.get("case_id") != CASE["case_id"]:
            return self.send_json(400, {"error": "Provide fictional case_id SIM-1042"})
        return self.send_json(202, {"case_id": CASE["case_id"], "status": "accepted_for_processing",
                                    "note": "Acceptance does not verify recipient delivery"})

    def do_GET(self):
        path = urlparse(self.path).path
        base = "/api/notifications/" + CASE["case_id"]
        if path == base:
            return self.send_json(200, {"case_id": CASE["case_id"], "recipients": len(CASE["recipients"]),
                                         "status": "fictional_trace_available"})
        if path.startswith(base + "/events/"):
            recipient_id = path.rsplit("/", 1)[-1]
            match = next((r for r in CASE["recipients"] if r["id"] == recipient_id), None)
            if match is None:
                return self.send_json(404, {"error": "Unknown recipient"})
            return self.send_json(200, {"case_id": CASE["case_id"], **match})
        return self.send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    print("Fictional API listening on http://127.0.0.1:8765 (CTRL+C to stop)")
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()

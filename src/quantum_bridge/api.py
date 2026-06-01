from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from quantum_bridge.advisor import DEMO_SESSIONS, advise_sessions, algorithm_catalog_payload


def run_api_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), _AdvisorHandler)
    print(f"Quantum Bridge demo API listening on http://{host}:{port}")
    print("Endpoints: GET /health, GET /algorithms, GET /demo, POST /advise")
    server.serve_forever()


class _AdvisorHandler(BaseHTTPRequestHandler):
    server_version = "QuantumBridgeDemoAPI/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json({"status": "ok", "demo": True})
            return
        if path == "/algorithms":
            self._send_json(algorithm_catalog_payload())
            return
        if path == "/demo":
            self._send_json(advise_sessions(DEMO_SESSIONS))
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/advise":
            self._send_json({"error": "not found"}, status=404)
            return

        try:
            payload = self._read_json()
            sessions = payload.get("sessions")
            if sessions is None and "session" in payload:
                sessions = [payload["session"]]
            if not isinstance(sessions, list):
                raise ValueError("request body must include a 'sessions' list")

            result = advise_sessions(
                sessions,
                preferred_platform=payload.get("preferred_platform"),
                max_candidates=int(payload.get("max_candidates", 3)),
                include_low_confidence=bool(payload.get("include_low_confidence", False)),
            )
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        if content_length > 1_000_000:
            raise ValueError("request body is too large")
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

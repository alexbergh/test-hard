#!/usr/bin/env python3
"""Минимальный HTTP-коллектор, имитирующий KUMA ingest endpoint."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DATA_DIR = Path(os.environ.get("KUMA_DATA_DIR", "/app/data"))
PORT = int(os.environ.get("LISTEN_PORT", "8080"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


class CollectorHandler(BaseHTTPRequestHandler):
    server_version = "KumaMock/1.0"

    def _write_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "received_at": timestamp,
            "path": self.path,
            "length": length,
        }
        if body:
            try:
                parsed = json.loads(body.decode("utf-8"))
                payload["events"] = len(parsed.get("events", [])) if isinstance(parsed, dict) else 0
                file_name = DATA_DIR / f"kuma-{timestamp.replace(':', '').replace('-', '')}.json"
                file_name.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
            except json.JSONDecodeError:
                payload["events"] = 0
        self.log_message("ingested batch: %s", payload)
        self._write_json({"status": "ok", **payload})

    def do_GET(self) -> None:  # noqa: N802
        batches = sorted(DATA_DIR.glob("kuma-*.json"))
        response = {"stored_batches": len(batches)}
        self._write_json(response)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), CollectorHandler)
    try:
        print(f"Starting KUMA mock collector on 0.0.0.0:{PORT}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down", flush=True)
        server.server_close()
        sys.exit(0)

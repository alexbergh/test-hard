import os
import random
import socket
import time
from datetime import datetime, timezone, timedelta

import requests

_BASE_TIME: datetime | None = None
_TIME_OFFSET = 0


def _next_time() -> datetime:
    global _BASE_TIME, _TIME_OFFSET
    if _BASE_TIME is None:
        candidate = os.environ.get("HARDENING_FIXED_TIMESTAMP")
        if candidate:
            value = candidate.strip()
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                _BASE_TIME = parsed.astimezone(timezone.utc)
            except ValueError:
                _BASE_TIME = None
        if _BASE_TIME is None:
            _BASE_TIME = datetime.now(timezone.utc)
    current = _BASE_TIME + timedelta(seconds=_TIME_OFFSET)
    _TIME_OFFSET += 1
    return current


TELEGRAF_ENDPOINT = os.environ.get("TELEGRAF_ENDPOINT", "http://localhost:9081/osquery")
HOST_IDENTIFIER = os.environ.get("HOST_IDENTIFIER", socket.gethostname())
LOG_INTERVAL = float(os.environ.get("LOG_INTERVAL", "10"))
SYSLOG_ENDPOINT = os.environ.get("SYSLOG_ENDPOINT", "udp://telegraf-listener:6514")

def build_osquery_event(query_name: str, columns: dict) -> dict:
    event_time = _next_time()
    return {
        "name": query_name,
        "hostIdentifier": HOST_IDENTIFIER,
        "unixTime": int(event_time.timestamp()),
        "calendarTime": event_time.strftime("%b %d %Y %H:%M:%S"),
        "columns": columns,
        "action": "added",
    }

def send_osquery_event(payload: dict) -> None:
    response = requests.post(TELEGRAF_ENDPOINT, json=payload, timeout=5)
    response.raise_for_status()

def send_syslog_message(message: str) -> None:
    if not SYSLOG_ENDPOINT:
        return
    proto, _, address = SYSLOG_ENDPOINT.partition("//")
    host, _, port = address.partition(":")
    port = int(port) if port else 6514
    sock_type = socket.SOCK_DGRAM if proto == "udp:" else socket.SOCK_STREAM
    with socket.socket(socket.AF_INET, sock_type) as sock:
        sock.connect((host, port))
        sock.sendall(message.encode("utf-8"))

def main() -> None:
    print(f"Starting osquery simulator for host {HOST_IDENTIFIER} -> {TELEGRAF_ENDPOINT}")
    sequence = 0
    while True:
        sequence += 1
        vulnerability_payload = build_osquery_event(
            "pack_vulnerability-management",
            {
                "name": "openssl",
                "version": "1.1.%d" % random.randint(0, 9),
                "severity": random.choice(["Low", "Medium", "High"]),
                "cve": random.choice(["CVE-2023-2650", "CVE-2024-2511", "CVE-2022-0778"]),
            },
        )
        inventory_payload = build_osquery_event(
            "pack_inventory",
            {
                "host": HOST_IDENTIFIER,
                "os": random.choice(["ubuntu", "centos", "debian"]),
                "kernel_version": "5.15.%d" % random.randint(0, 30),
                "scan_sequence": sequence,
            },
        )
        try:
            send_osquery_event(vulnerability_payload)
            send_osquery_event(inventory_payload)
            send_syslog_message(
                f"<134>{_next_time().isoformat()} osquery-simulator {HOST_IDENTIFIER} - - - hardening test sequence={sequence}"
            )
            print(f"[{sequence}] Emitted simulated osquery results")
        except Exception as exc:  # noqa: BLE001 - top-level reporter
            print(f"Failed to emit event: {exc}")
        time.sleep(LOG_INTERVAL)


if __name__ == "__main__":
    main()

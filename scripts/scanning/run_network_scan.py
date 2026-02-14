
#!/usr/bin/env python3
"""Network scanner using nmap. Discovers hosts, open ports, services.

Outputs:
  - JSON results to --output directory
  - Prometheus metrics to --output/prometheus/network_scan.prom

Usage:
  python3 run_network_scan.py --targets 192.168.1.0/24 --output /var/lib/network-scan
  python3 run_network_scan.py --targets 192.168.1.0/24 10.0.0.0/24 --scan-type quick
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCAN_PROFILES = {
    "ping": "-sn -PE -PA21,23,80,443 -PS22,80,443",
    "quick": "-sS -sV --version-intensity 2 -T4 -F --open",
    "standard": "-sS -sV -sC -T3 -p- --open",
    "vuln": "-sS -sV --script=vuln -T3 --open",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Network scanner with nmap")
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        help="Target networks/hosts (e.g. 192.168.1.0/24)",
    )
    parser.add_argument(
        "--scan-type",
        choices=list(SCAN_PROFILES.keys()),
        default="quick",
        help="Scan profile (default: quick)",
    )
    parser.add_argument(
        "--output",
        default="/var/lib/network-scan",
        help="Output directory for results",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Scan timeout in seconds (default: 600)",
    )
    parser.add_argument(
        "--extra-args",
        default="",
        help="Extra nmap arguments",
    )
    return parser.parse_args()


def check_nmap() -> bool:
    """Check if nmap is available."""
    try:
        result = subprocess.run(
            ["nmap", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            logger.info("Found %s", version)
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    logger.error("nmap not found. Install with: apt-get install -y nmap")
    return False


def run_nmap(targets: List[str], scan_type: str, timeout: int, extra_args: str, xml_output: str) -> bool:
    """Run nmap scan and save XML output."""
    profile_args = SCAN_PROFILES.get(scan_type, SCAN_PROFILES["quick"])
    cmd = f"nmap {profile_args} {extra_args} -oX {xml_output} {' '.join(targets)}"
    logger.info("Running: %s", cmd)

    try:
        proc = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode in (0, 1):  # nmap returns 1 if some hosts are down
            logger.info("nmap completed (rc=%d)", proc.returncode)
            return True
        else:
            logger.error("nmap failed (rc=%d): %s", proc.returncode, proc.stderr[:500])
            return False
    except subprocess.TimeoutExpired:
        logger.error("nmap timed out after %ds", timeout)
        return False
    except Exception as e:
        logger.error("nmap error: %s", e)
        return False


def parse_nmap_xml(xml_path: str) -> Dict:
    """Parse nmap XML output into structured data."""
    import xml.etree.ElementTree as ET

    results = {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "hosts": [],
        "summary": {
            "total_hosts": 0,
            "hosts_up": 0,
            "hosts_down": 0,
            "total_ports": 0,
            "open_ports": 0,
            "services_found": 0,
        },
    }

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        logger.error("Failed to parse XML: %s", e)
        return results

    # Parse scan info
    scaninfo = root.find("scaninfo")
    if scaninfo is not None:
        results["scan_type"] = scaninfo.get("type", "unknown")
        results["protocol"] = scaninfo.get("protocol", "unknown")

    # Parse run stats
    runstats = root.find("runstats/finished")
    if runstats is not None:
        results["elapsed"] = runstats.get("elapsed", "0")
        results["summary_text"] = runstats.get("summary", "")

    hosts_elem = root.find("runstats/hosts")
    if hosts_elem is not None:
        results["summary"]["total_hosts"] = int(hosts_elem.get("total", 0))
        results["summary"]["hosts_up"] = int(hosts_elem.get("up", 0))
        results["summary"]["hosts_down"] = int(hosts_elem.get("down", 0))

    # Parse each host
    for host_elem in root.findall("host"):
        host_data = _parse_host(host_elem)
        if host_data:
            results["hosts"].append(host_data)
            results["summary"]["open_ports"] += len(host_data.get("ports", []))

    results["summary"]["services_found"] = len(
        {p["service"] for h in results["hosts"] for p in h.get("ports", []) if p.get("service")}
    )

    return results


def _parse_host(host_elem) -> Optional[Dict]:
    """Parse a single host element."""
    status = host_elem.find("status")
    if status is None or status.get("state") != "up":
        return None

    host = {
        "state": "up",
        "addresses": [],
        "hostnames": [],
        "ports": [],
        "os": [],
    }

    # Addresses
    for addr in host_elem.findall("address"):
        host["addresses"].append(
            {
                "addr": addr.get("addr"),
                "type": addr.get("addrtype"),
                "vendor": addr.get("vendor", ""),
            }
        )

    # IP address as primary identifier
    ip_addrs = [a["addr"] for a in host["addresses"] if a["type"] == "ipv4"]
    host["ip"] = ip_addrs[0] if ip_addrs else host["addresses"][0]["addr"] if host["addresses"] else "unknown"

    # MAC address
    mac_addrs = [a for a in host["addresses"] if a["type"] == "mac"]
    if mac_addrs:
        host["mac"] = mac_addrs[0]["addr"]
        host["vendor"] = mac_addrs[0].get("vendor", "")

    # Hostnames
    for hostname in host_elem.findall("hostnames/hostname"):
        host["hostnames"].append(
            {
                "name": hostname.get("name"),
                "type": hostname.get("type"),
            }
        )
    host["hostname"] = host["hostnames"][0]["name"] if host["hostnames"] else ""

    # Ports
    for port_elem in host_elem.findall("ports/port"):
        state = port_elem.find("state")
        if state is None or state.get("state") != "open":
            continue

        service = port_elem.find("service")
        port_data = {
            "port": int(port_elem.get("portid", 0)),
            "protocol": port_elem.get("protocol", "tcp"),
            "state": state.get("state", "unknown"),
            "service": service.get("name", "") if service is not None else "",
            "product": service.get("product", "") if service is not None else "",
            "version": service.get("version", "") if service is not None else "",
            "extra_info": service.get("extrainfo", "") if service is not None else "",
        }
        host["ports"].append(port_data)

    # OS detection
    for osmatch in host_elem.findall("os/osmatch"):
        host["os"].append(
            {
                "name": osmatch.get("name", ""),
                "accuracy": int(osmatch.get("accuracy", 0)),
            }
        )

    return host


def generate_prometheus_metrics(results: Dict, prom_path: str) -> None:
    """Generate Prometheus metrics from scan results."""
    lines = []

    # Summary metrics
    summary = results.get("summary", {})

    lines.append("# HELP network_scan_hosts_total Total hosts discovered by network scan")
    lines.append("# TYPE network_scan_hosts_total gauge")
    lines.append(f'network_scan_hosts_total {summary.get("hosts_up", 0)}')

    lines.append("# HELP network_scan_hosts_down Hosts that are down")
    lines.append("# TYPE network_scan_hosts_down gauge")
    lines.append(f'network_scan_hosts_down {summary.get("hosts_down", 0)}')

    lines.append("# HELP network_scan_open_ports_total Total open ports discovered")
    lines.append("# TYPE network_scan_open_ports_total gauge")
    lines.append(f'network_scan_open_ports_total {summary.get("open_ports", 0)}')

    lines.append("# HELP network_scan_services_total Unique services discovered")
    lines.append("# TYPE network_scan_services_total gauge")
    lines.append(f'network_scan_services_total {summary.get("services_found", 0)}')

    lines.append("# HELP network_scan_timestamp Last scan timestamp")
    lines.append("# TYPE network_scan_timestamp gauge")
    lines.append(f"network_scan_timestamp {int(datetime.now(timezone.utc).timestamp())}")

    # Per-host metrics
    lines.append("# HELP network_scan_host_up Whether a discovered host is up (1=up)")
    lines.append("# TYPE network_scan_host_up gauge")

    lines.append("# HELP network_scan_host_ports Number of open ports per host")
    lines.append("# TYPE network_scan_host_ports gauge")

    for host in results.get("hosts", []):
        ip = host.get("ip", "unknown")
        hostname = host.get("hostname", "")
        vendor = host.get("vendor", "")
        mac = host.get("mac", "")
        labels = f'ip="{ip}",hostname="{hostname}",vendor="{vendor}",mac="{mac}"'
        lines.append(f"network_scan_host_up{{{labels}}} 1")
        lines.append(f'network_scan_host_ports{{{labels}}} {len(host.get("ports", []))}')

    # Per-port metrics
    lines.append("# HELP network_scan_port_open Open port on a host (1=open)")
    lines.append("# TYPE network_scan_port_open gauge")

    for host in results.get("hosts", []):
        ip = host.get("ip", "unknown")
        hostname = host.get("hostname", "")
        for port in host.get("ports", []):
            port_labels = (
                f'ip="{ip}",hostname="{hostname}",'
                f'port="{port["port"]}",protocol="{port["protocol"]}",'
                f'service="{port["service"]}",product="{port["product"]}",'
                f'version="{port["version"]}"'
            )
            lines.append(f"network_scan_port_open{{{port_labels}}} 1")

    os.makedirs(os.path.dirname(prom_path), exist_ok=True)
    with open(prom_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    logger.info("Prometheus metrics written to %s (%d lines)", prom_path, len(lines))


def main() -> int:
    args = parse_args()

    if not check_nmap():
        return 1

    # Prepare output dirs
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "history").mkdir(exist_ok=True)
    (output / "prometheus").mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    xml_path = str(output / "history" / f"scan_{ts}.xml")

    # Run nmap
    logger.info("Scanning targets: %s (profile: %s)", args.targets, args.scan_type)
    success = run_nmap(args.targets, args.scan_type, args.timeout, args.extra_args, xml_path)

    if not success:
        logger.error("nmap scan failed")
        return 1

    # Parse results
    results = parse_nmap_xml(xml_path)
    results["targets"] = args.targets
    results["scan_type"] = args.scan_type

    # Save JSON
    json_path = output / "history" / f"scan_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("JSON results: %s", json_path)

    # Symlink latest
    latest = output / "latest.json"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    try:
        latest.symlink_to(json_path)
    except OSError:
        import shutil

        shutil.copy2(json_path, latest)

    # Generate Prometheus metrics
    prom_path = str(output / "prometheus" / "network_scan.prom")
    generate_prometheus_metrics(results, prom_path)

    # Print summary
    s = results["summary"]
    logger.info(
        "Scan complete: %d hosts up, %d down, %d open ports, %d services",
        s["hosts_up"],
        s["hosts_down"],
        s["open_ports"],
        s["services_found"],
    )

    for host in results["hosts"]:
        ports_str = ", ".join(f'{p["port"]}/{p["service"]}' for p in host.get("ports", [])[:10])
        logger.info(
            "  %s (%s) %s — ports: %s",
            host["ip"],
            host.get("hostname", "n/a"),
            host.get("vendor", ""),
            ports_str or "none",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())

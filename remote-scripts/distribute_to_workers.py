import subprocess

KEY = "/root/.ssh/k8s_cluster_ed25519"
WORKERS = ["10.10.10.11", "10.10.10.12", "10.10.10.13", "10.10.10.14"]
SCRIPT = "/root/rs/fix_kubelet_all.py"

for w in WORKERS:
    # mkdir
    r1 = subprocess.run(
        [
            "ssh",
            "-i",
            KEY,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ConnectTimeout=10",
            f"root@{w}",
            "mkdir -p /root/rs",
        ],
        capture_output=True,
        text=True,
    )
    # scp
    r2 = subprocess.run(
        ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no", SCRIPT, f"root@{w}:{SCRIPT}"],
        capture_output=True,
        text=True,
    )
    status = "ok" if r2.returncode == 0 else r2.stderr.strip()[:80]
    print(f"  {w}: {status}")

print("DISTRIBUTE_DONE")

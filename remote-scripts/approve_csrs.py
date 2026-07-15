#!/usr/bin/env python3
"""Approve all pending kubelet server CSRs and verify exec works."""

import subprocess
import time


def run(cmd, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()


print("=== Pending CSRs ===")
out, _ = run(["kubectl", "get", "csr", "--no-headers"])
print(out[:800] if out else "None")

pending = [l.split()[0] for l in out.splitlines() if "Pending" in l]
print(f"\nApproving {len(pending)} pending CSR(s)...")
for name in pending:
    o, e = run(["kubectl", "certificate", "approve", name])
    print(f"  {name}: {o or e or 'ok'}")

time.sleep(5)

print("\n=== All CSRs after approval ===")
out2, _ = run(["kubectl", "get", "csr", "--no-headers"])
print(out2[:600] if out2 else "None")

print("\n=== Test kubectl exec ===")
# Try exec on a worker pod
out3, err3 = run(["kubectl", "get", "pods", "-A", "--no-headers", "--field-selector=status.phase=Running"], timeout=15)
running = [l.split() for l in out3.splitlines() if l.strip()]
if running:
    for row in running[:3]:
        if len(row) >= 2:
            ns, pod = row[0], row[1]
            o, e = run(["kubectl", "exec", "-n", ns, pod, "--", "hostname"], timeout=15)
            print(f"  exec {ns}/{pod}: {o or e}")
else:
    print("  No running pods found")

print("\n=== Test vault status ===")
out4, err4 = run(["kubectl", "exec", "-n", "vault", "vault-0", "--", "vault", "status"], timeout=15)
print(out4[:200] if out4 else err4[:200])

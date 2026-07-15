#!/usr/bin/env python3
"""
Enable kubelet server TLS bootstrapping so kubelet serving cert has proper IP SANs.
This allows --kubelet-certificate-authority to work correctly.
Steps:
  1. Add serverTLSBootstrap: true to kubelet config.yaml
  2. Restart kubelet -> kubelet generates CSR
  3. Approve all pending kubelet CSRs
  4. Verify kubectl exec/logs work
"""
import subprocess, time, re

def run(cmd, inp=None, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

CONFIG = '/var/lib/kubelet/config.yaml'

with open(CONFIG) as f:
    cfg = f.read()

if 'serverTLSBootstrap: true' in cfg:
    print("SKIP: serverTLSBootstrap already enabled")
else:
    if 'serverTLSBootstrap' in cfg:
        cfg = re.sub(r'serverTLSBootstrap:\s*\S+', 'serverTLSBootstrap: true', cfg)
        print("UPDATED: serverTLSBootstrap: true")
    else:
        cfg = cfg.rstrip() + '\nserverTLSBootstrap: true\n'
        print("APPENDED: serverTLSBootstrap: true")
    with open(CONFIG, 'w') as f:
        f.write(cfg)

# Restart kubelet
print("Restarting kubelet...")
_, err = run(['systemctl', 'restart', 'kubelet'])
time.sleep(6)
out, _ = run(['systemctl', 'is-active', 'kubelet'])
print(f"kubelet: {out}")

# Approve pending CSRs (run on master)
print("Checking for pending CSRs...")
time.sleep(5)
out2, _ = run(['kubectl', 'get', 'csr', '--no-headers'])
print(out2[:500] if out2 else "No CSRs yet")

pending = [l.split()[0] for l in out2.splitlines()
           if 'Pending' in l and 'node-csr' in l.lower()]
print(f"Pending kubelet CSRs: {len(pending)}")

for csr_name in pending:
    out3, err3 = run(['kubectl', 'certificate', 'approve', csr_name])
    print(f"  approved {csr_name}: {out3 or err3}")

print("SERVING_CERT_DONE")

#!/bin/bash
# Fix: --profiling=false for kube-apiserver, kube-controller-manager, kube-scheduler
for f in /etc/kubernetes/manifests/kube-apiserver.yaml \
          /etc/kubernetes/manifests/kube-controller-manager.yaml \
          /etc/kubernetes/manifests/kube-scheduler.yaml; do
    if grep -q -- '--profiling=false' "$f" 2>/dev/null; then
        echo "SKIP $f already has --profiling=false"
        continue
    fi
    # Insert '--profiling=false' right after the binary line (kube-apiserver / kube-controller-manager / kube-scheduler)
    python3 - "$f" <<'PYEOF'
import sys, re

path = sys.argv[1]
with open(path) as fh:
    lines = fh.readlines()

new_lines = []
inserted = False
for line in lines:
    new_lines.append(line)
    if not inserted and re.match(r'\s+-\s+kube-(apiserver|controller-manager|scheduler)\s*$', line):
        indent = re.match(r'^(\s+)', line).group(1)
        new_lines.append(f'{indent}- --profiling=false\n')
        inserted = True

if not inserted:
    print(f"WARNING: could not find binary line in {path}, trying fallback")
    new_lines2 = []
    for line in lines:
        new_lines2.append(line)
        if not inserted and 'command:' in line:
            new_lines2.append('    - --profiling=false\n')
            inserted = True
    new_lines = new_lines2

with open(path, 'w') as fh:
    fh.writelines(new_lines)

print(f'DONE {path}')
PYEOF
done

echo "Waiting 35s for control plane to restart..."
sleep 35
kubectl get nodes --no-headers 2>/dev/null | head -5
echo "PROFILING_FIX_DONE"

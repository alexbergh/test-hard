#!/usr/bin/env python3
"""
1.2.26 - Add --kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt to kube-apiserver
"""
import re, os, subprocess, time

MANIFEST = '/etc/kubernetes/manifests/kube-apiserver.yaml'
CA_FLAG  = '--kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt'

# Verify CA cert exists
if not os.path.exists('/etc/kubernetes/pki/ca.crt'):
    print("ERROR: /etc/kubernetes/pki/ca.crt not found")
    raise SystemExit(1)

with open(MANIFEST) as f:
    txt = f.read()

if 'kubelet-certificate-authority' in txt:
    print("SKIP: kubelet-certificate-authority already present")
    raise SystemExit(0)

# Insert after the --kubelet-client-key line (logically grouped)
lines = txt.split('\n')
new_lines = []
inserted = False
for line in lines:
    new_lines.append(line)
    if not inserted and 'kubelet-client-key' in line:
        m = re.match(r'^(\s+)', line)
        indent = m.group(1) if m else '    '
        new_lines.append(f'{indent}- {CA_FLAG}')
        inserted = True

if not inserted:
    # Fallback: insert after kube-apiserver binary line
    new_lines2 = []
    for line in lines:
        new_lines2.append(line)
        if not inserted and re.match(r'\s+-\s+kube-apiserver\s*$', line):
            m = re.match(r'^(\s+)', line)
            indent = m.group(1) if m else '    '
            new_lines2.append(f'{indent}- {CA_FLAG}')
            inserted = True
    new_lines = new_lines2

with open(MANIFEST, 'w') as f:
    f.write('\n'.join(new_lines))

print(f"DONE: added {CA_FLAG}")
print("Waiting 40s for apiserver restart...")
time.sleep(40)

r = subprocess.run(['kubectl', 'get', 'nodes', '--no-headers'],
                   capture_output=True, text=True)
print("Nodes:", r.stdout.strip()[:200] or r.stderr.strip()[:200])

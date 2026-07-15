#!/usr/bin/env python3
"""
Final verification of ALL phase 1+2 CIS remediations.
"""
import subprocess, re

VAULT_TOKEN = 'hvs.2vz6hUMMYKS8LX0ytFRe9Yrq'

def run(cmd, timeout=20):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def vexec(vault_cmd, timeout=15):
    return run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                'env', f'VAULT_TOKEN={VAULT_TOKEN}'] + vault_cmd, timeout=timeout)

checks = []

def chk(label, result, detail=''):
    ok = bool(result)
    status = 'PASS' if ok else 'FAIL'
    checks.append((status, label))
    snippet = (str(result) if ok else str(detail))[:60].replace('\n', ' | ')
    print(f"  {status}  {label}: {snippet}")
    return ok

print("=" * 62)
print("PHASE 1 - Control Plane / Infrastructure")
print("=" * 62)

# 1.2.15/1.3.2/1.4.1 profiling=false
for comp, mf in [('apiserver', '/etc/kubernetes/manifests/kube-apiserver.yaml'),
                 ('ctrl-mgr',  '/etc/kubernetes/manifests/kube-controller-manager.yaml'),
                 ('scheduler', '/etc/kubernetes/manifests/kube-scheduler.yaml')]:
    out, _ = run(['grep', '--', '--profiling=false', mf])
    chk(f'1.2.15/3.2/4.1 profiling=false [{comp}]', out)

# 1.2.26 kubelet-ca
out, _ = run(['grep', 'kubelet-certificate-authority', '/etc/kubernetes/manifests/kube-apiserver.yaml'])
chk('1.2.26 kubelet-certificate-authority', out)

# 1.2.29 / 5.4.2 encryption-at-rest
out, _ = run(['grep', 'encryption-provider-config', '/etc/kubernetes/manifests/kube-apiserver.yaml'])
chk('1.2.29/5.4.2 encryption-at-rest', out)

# Check encryption volume mount
out2, _ = run(['grep', '-c', 'encryption-config', '/etc/kubernetes/manifests/kube-apiserver.yaml'])
chk('encryption volume+mount in manifest', int(out2 or 0) >= 2, out2)

# 4.3.1 kube-proxy 127.0.0.1
out, _ = run(['kubectl', '-n', 'kube-system', 'get', 'cm', 'kube-proxy',
              '-o', 'jsonpath={.data.config\\.conf}'])
chk('4.3.1 kube-proxy 127.0.0.1:10249', '127.0.0.1:10249' in out, out[:60])

print()
print("=" * 62)
print("PHASE 2 - Kubelet (checked on master, representative)")
print("=" * 62)

with open('/var/lib/kubelet/config.yaml') as f:
    cfg = f.read()

anon_ok = ('anonymous' in cfg) and ('enabled: false' in cfg or 'enabled:false' in cfg)
chk('4.2.1  kubelet anonymous.enabled: false',  anon_ok, cfg[:80])
chk('4.2.2  kubelet authorization: Webhook',    'Webhook' in cfg)
chk('4.2.6  kubelet protectKernelDefaults',     'protectKernelDefaults: true' in cfg)
chk('4.2.9  kubelet eventRecordQPS: 5',         'eventRecordQPS: 5' in cfg)
chk('4.2.11 kubelet rotateCertificates: true',  'rotateCertificates: true' in cfg)
chk('4.2.13 kubelet podPidsLimit: 4096',        'podPidsLimit: 4096' in cfg)
chk('4.2.14 kubelet seccompDefault: true',      'seccompDefault: true' in cfg)
chk('kubelet serverTLSBootstrap: true',         'serverTLSBootstrap: true' in cfg)

out_k, _ = run(['systemctl', 'is-active', 'kubelet'])
chk('kubelet service active', out_k == 'active')

print()
print("=" * 62)
print("PHASE 2 - Vault K8s Auth")
print("=" * 62)

out_v, err_v = vexec(['vault', 'status'])
sealed = True
for line in out_v.splitlines():
    if line.startswith('Sealed'):
        sealed = line.split()[-1].lower() == 'true'
chk('Vault unsealed', not sealed)

out_al, _ = vexec(['vault', 'auth', 'list'])
chk('Vault k8s auth enabled', 'kubernetes' in out_al.lower())

out_cfg, _ = vexec(['vault', 'read', 'auth/kubernetes/config'])
chk('Vault k8s config: host=10.10.10.10', '10.10.10.10' in out_cfg)
chk('Vault k8s config: CA cert present',  'BEGIN CERTIFICATE' in out_cfg)

print()
print("=" * 62)
print("PHASE 1+2 - Policies / Network")
print("=" * 62)

# NetworkPolicies
out, _ = run(['kubectl', 'get', 'networkpolicies', '-A', '--no-headers'])
count = len([l for l in out.splitlines() if l.strip()])
chk('5.3.2 NetworkPolicies >= 5', count >= 5, f"count={count}")

# PSS labels
for ns, label in [('kyverno', 'privileged'), ('vault', 'privileged'), ('default', 'baseline')]:
    out2, _ = run(['kubectl', 'get', 'ns', ns, '--show-labels', '--no-headers'])
    chk(f'5.2.x PSS {ns}={label}', label in out2)

# SA automount
for ns in ['kube-system', 'kyverno', 'vault']:
    out3, _ = run(['kubectl', 'get', 'sa', 'default', '-n', ns,
                   '-o', 'jsonpath={.automountServiceAccountToken}'])
    chk(f'5.1.6 SA automount=false [{ns}]', out3.strip() == 'false', out3)

# Kyverno verifyImages
out4, _ = run(['kubectl', 'get', 'clusterpolicy', 'verify-image-signatures', '--no-headers'])
chk('Kyverno verifyImages policy', 'verify-image-signatures' in out4)

# Trivy cron
out5, _ = run(['crontab', '-l'])
chk('Trivy daily cron', 'trivy' in out5)

# kubelet serving CSRs approved
out6, _ = run(['kubectl', 'get', 'csr', '--no-headers'])
pending = [l for l in out6.splitlines() if 'Pending' in l]
issued  = [l for l in out6.splitlines() if 'Approved,Issued' in l and 'kubelet-serving' in l]
chk('Kubelet serving CSRs issued', len(issued) >= 5, f"issued={len(issued)} pending={len(pending)}")

print()
print("=" * 62)
pass_n = sum(1 for s, _ in checks if s == 'PASS')
fail_n = sum(1 for s, _ in checks if s == 'FAIL')
print(f"TOTAL: {pass_n}/{len(checks)} PASS   {fail_n} FAIL")
print("=" * 62)
if fail_n:
    print("\nFailed items:")
    for s, l in checks:
        if s == 'FAIL':
            print(f"  - {l}")

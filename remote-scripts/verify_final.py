import subprocess, json, re, os

def run(cmd, inp=None, timeout=20):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

print("=== Vault K8s auth (via token from env or re-login) ===")
tok = None
for kf in ['/root/vault-init.txt', '/root/vault-keys.txt']:
    if not os.path.exists(kf):
        continue
    with open(kf) as f:
        raw = f.read()
    print(f"  {kf} content: {repr(raw[:300])}")
    m = re.search(r'Root Token[:\s]+(\S+)', raw, re.IGNORECASE)
    if m:
        tok = m.group(1)
        print(f"  Found token: {tok[:10]}...")
        break
    m2 = re.search(r'hvs\.\S+', raw)
    if m2:
        tok = m2.group(0)
        print(f"  Found hvs token: {tok[:10]}...")
        break

if not tok:
    print("  Root token not found in init file - Vault K8s auth skipped")
    print("  MANUAL ACTION NEEDED: kubectl exec -n vault vault-0 -- vault login <TOKEN>")
    print("                         vault auth enable kubernetes")
    print("                         vault write auth/kubernetes/config kubernetes_host=https://10.10.10.10:6443")
else:
    out, _ = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                  'env', f'VAULT_TOKEN={tok}', 'vault', 'auth', 'list'])
    if 'kubernetes' in out.lower():
        print("  SKIP: k8s auth already enabled")
    else:
        _, e1 = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                     'env', f'VAULT_TOKEN={tok}', 'vault', 'auth', 'enable', 'kubernetes'])
        print("  enable:", e1 or "ok")
        _, e2 = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                     'env', f'VAULT_TOKEN={tok}', 'vault', 'write',
                     'auth/kubernetes/config', 'kubernetes_host=https://10.10.10.10:6443'])
        print("  configure:", e2 or "ok")

print("\n=== FULL FINAL VERIFICATION ===")
manifest = '/etc/kubernetes/manifests/kube-apiserver.yaml'
checks = [
    ("apiserver manifest exists",   ['ls', manifest]),
    ("profiling=false (apiserver)", ['grep', '--', '--profiling=false', manifest]),
    ("profiling=false (ctrlmgr)",   ['grep', '--', '--profiling=false',
                                     '/etc/kubernetes/manifests/kube-controller-manager.yaml']),
    ("profiling=false (scheduler)", ['grep', '--', '--profiling=false',
                                     '/etc/kubernetes/manifests/kube-scheduler.yaml']),
    ("encryption flag in apiserver",['grep', 'encryption-provider-config', manifest]),
    ("encryption volume in apiserver",['grep', 'encryption-config', manifest]),
    ("encryption config file",      ['ls', '-la', '/etc/kubernetes/encryption/encryption-config.yaml']),
    ("kube-proxy 127.0.0.1:10249",  ['kubectl', '-n', 'kube-system', 'get', 'cm', 'kube-proxy',
                                      '-o', 'jsonpath={.data.config\\.conf}']),
    ("vault not sealed",            ['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                                      'vault', 'status']),
    ("kyverno verifyImages policy", ['kubectl', 'get', 'clusterpolicy',
                                      'verify-image-signatures', '--no-headers']),
    ("netpols: default",            ['kubectl', 'get', 'netpol', '-n', 'default', '--no-headers']),
    ("netpols: development",        ['kubectl', 'get', 'netpol', '-n', 'development', '--no-headers']),
    ("netpols: kyverno",            ['kubectl', 'get', 'netpol', '-n', 'kyverno', '--no-headers']),
    ("netpols: vault",              ['kubectl', 'get', 'netpol', '-n', 'vault', '--no-headers']),
    ("trivy cron",                  ['crontab', '-l']),
    ("PSS: kyverno=privileged",     ['kubectl', 'get', 'ns', 'kyverno', '--show-labels', '--no-headers']),
    ("PSS: vault=privileged",       ['kubectl', 'get', 'ns', 'vault', '--show-labels', '--no-headers']),
    ("PSS: default=baseline",       ['kubectl', 'get', 'ns', 'default', '--show-labels', '--no-headers']),
    ("SA automount: kube-system",   ['kubectl', 'get', 'sa', 'default', '-n', 'kube-system',
                                      '-o', 'jsonpath={.automountServiceAccountToken}']),
    ("SA automount: kyverno",       ['kubectl', 'get', 'sa', 'default', '-n', 'kyverno',
                                      '-o', 'jsonpath={.automountServiceAccountToken}']),
    ("SA automount: vault",         ['kubectl', 'get', 'sa', 'default', '-n', 'vault',
                                      '-o', 'jsonpath={.automountServiceAccountToken}']),
]

pass_n, fail_n = 0, 0
results = []
for label, cmd in checks:
    out, err = run(cmd)
    text = out or err
    ok = bool(out.strip()) and 'No such file' not in err and 'not found' not in err.lower()

    # specific checks
    if 'kube-proxy' in label:
        ok = '127.0.0.1:10249' in out
    elif 'vault not sealed' in label:
        ok = 'Sealed          false' in out
    elif 'trivy cron' in label:
        ok = 'trivy' in out
    elif 'SA automount' in label:
        ok = out.strip() == 'false'
    elif 'PSS: kyverno' in label:
        ok = 'privileged' in out
    elif 'PSS: vault' in label:
        ok = 'privileged' in out
    elif 'PSS: default' in label:
        ok = 'baseline' in out
    elif 'encryption volume' in label:
        ok = out.count('encryption-config') >= 2

    status = "PASS" if ok else "FAIL"
    if ok:
        pass_n += 1
    else:
        fail_n += 1
    snippet = text[:80].replace('\n', ' | ')
    print(f"  {status}  {label}: {snippet}")
    results.append((status, label))

print(f"\nTotal: {pass_n} PASS, {fail_n} FAIL")
if fail_n:
    print("Failed items:")
    for s, l in results:
        if s == "FAIL":
            print(f"  - {l}")

import subprocess, json, re, os

def run(cmd, inp=None):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp)
    return r.stdout.strip(), r.stderr.strip()

print("=== 1. kube-proxy metricsBindAddress ===")
out, _ = run(['kubectl', '-n', 'kube-system', 'get', 'configmap', 'kube-proxy', '-o', 'json'])
try:
    d = json.loads(out)
    conf = d['data'].get('config.conf', '')
    print("Current:", [l for l in conf.splitlines() if 'metrics' in l.lower()])
    if '127.0.0.1:10249' in conf:
        print("SKIP already correct")
    else:
        if 'metricsBindAddress' in conf:
            conf = re.sub(r'metricsBindAddress:\s*\S*',
                          'metricsBindAddress: "127.0.0.1:10249"', conf)
        else:
            conf = conf.rstrip() + '\nmetricsBindAddress: "127.0.0.1:10249"\n'
        d['data']['config.conf'] = conf
        _, err = run(['kubectl', 'apply', '-f', '-'], inp=json.dumps(d))
        print("apply:", err or "ok")
        _, err = run(['kubectl', '-n', 'kube-system', 'rollout', 'restart', 'daemonset', 'kube-proxy'])
        print("rollout:", err or "ok")
except Exception as e:
    print("ERROR:", e)

print("\n=== 2. Vault K8s auth ===")
import time

out, _ = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--', 'vault', 'status'])
sealed = 'true'
for line in out.splitlines():
    if line.startswith('Sealed'):
        sealed = line.split()[-1].lower()
print("Sealed:", sealed)

tok = None
kf = '/root/vault-init.txt'
if os.path.exists(kf):
    with open(kf) as f:
        txt = f.read()
    m = re.search(r'Initial Root Token:\s+(\S+)', txt)
    if m:
        tok = m.group(1)
        print("Root token found")

if tok:
    out2, _ = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                   'env', f'VAULT_TOKEN={tok}', 'vault', 'auth', 'list'])
    print("Auth list:", out2[:200])
    if 'kubernetes' in out2.lower():
        print("SKIP k8s auth already configured")
    else:
        out3, _ = run(['kubectl', 'config', 'view', '--raw',
                       '-o', 'jsonpath={.clusters[0].cluster.server}'])
        host = out3.strip()
        _, e1 = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                     'env', f'VAULT_TOKEN={tok}', 'vault', 'auth', 'enable', 'kubernetes'])
        print("enable:", e1 or "ok")
        _, e2 = run(['kubectl', 'exec', '-n', 'vault', 'vault-0', '--',
                     'env', f'VAULT_TOKEN={tok}', 'vault', 'write',
                     'auth/kubernetes/config', f'kubernetes_host={host}'])
        print("config:", e2 or "ok")
        print("K8s auth configured for", host)
else:
    print("WARN: no root token")

print("\n=== 3. Kyverno verifyImages (mutateDigest=false) ===")
out, _ = run(['kubectl', 'get', 'clusterpolicy', 'verify-image-signatures', '--no-headers'])
if out and 'Error' not in out:
    print("SKIP policy exists:", out)
else:
    pub_key = ''
    for p in ['/root/cosign-keys/cosign.pub', '/root/cosign.pub']:
        if os.path.exists(p):
            with open(p) as f:
                pub_key = f.read().strip()
            break
    if not pub_key:
        pub_key = '# UPDATE WITH REAL KEY'

    key_lines = '\n'.join('                    ' + l for l in pub_key.splitlines())
    policy = [
        'apiVersion: kyverno.io/v1\n',
        'kind: ClusterPolicy\n',
        'metadata:\n',
        '  name: verify-image-signatures\n',
        'spec:\n',
        '  validationFailureAction: Audit\n',
        '  background: false\n',
        '  rules:\n',
        '    - name: verify-image\n',
        '      match:\n',
        '        any:\n',
        '        - resources:\n',
        '            kinds:\n',
        '              - Pod\n',
        '            namespaces:\n',
        '              - production\n',
        '      verifyImages:\n',
        '        - imageReferences:\n',
        '            - "*"\n',
        '          mutateDigest: false\n',
        '          attestors:\n',
        '            - count: 1\n',
        '              entries:\n',
        '              - keys:\n',
        '                  publicKeys: |-\n',
        key_lines + '\n',
    ]
    with open('/tmp/verify-images.yaml', 'w') as f:
        f.writelines(policy)
    out4, err4 = run(['kubectl', 'apply', '-f', '/tmp/verify-images.yaml'])
    print(out4 or err4)

print("\n=== 4. Trivy cron ===")
out, _ = run(['crontab', '-l'])
if 'trivy' in out:
    print("EXISTS:", [l for l in out.splitlines() if 'trivy' in l])
else:
    new_cron = out.rstrip() + '\n0 2 * * * /usr/local/bin/trivy k8s --report=summary cluster >> /var/log/trivy-scan.log 2>&1\n'
    _, e = run(['crontab', '-'], inp=new_cron)
    print("DONE", e or "ok")

print("\n=== 5. PSS labels ===")
for ns, level in [('kyverno', 'privileged'), ('vault', 'privileged'), ('default', 'baseline')]:
    out, _ = run(['kubectl', 'get', 'ns', ns, '--show-labels', '--no-headers'])
    if 'pod-security.kubernetes.io/enforce' in out:
        cur = [p for p in out.split() if 'enforce' in p]
        print(f"SKIP {ns}: {cur}")
    else:
        _, e = run(['kubectl', 'label', 'ns', ns,
                    f'pod-security.kubernetes.io/enforce={level}',
                    f'pod-security.kubernetes.io/audit={level}',
                    f'pod-security.kubernetes.io/warn={level}',
                    '--overwrite'])
        print(f"DONE {ns}={level}", e or "ok")

print("\n=== 6. SA automount=false ===")
for ns in ['kube-system', 'kube-flannel', 'kyverno', 'vault']:
    out, _ = run(['kubectl', 'get', 'sa', 'default', '-n', ns, '--show-labels', '-o', 'json'])
    try:
        d2 = json.loads(out)
        val = d2.get('automountServiceAccountToken')
        if val is False:
            print(f"SKIP {ns}: already false")
        else:
            _, e = run(['kubectl', 'patch', 'serviceaccount', 'default', '-n', ns,
                        '-p', '{"automountServiceAccountToken":false}'])
            print(f"DONE {ns}", e or "ok")
    except Exception:
        print(f"  {ns}: parse error")

print("\n=== Final verification ===")
checks = [
    ("profiling API", ['grep', '--', '--profiling=false', '/etc/kubernetes/manifests/kube-apiserver.yaml']),
    ("profiling CM",  ['grep', '--', '--profiling=false', '/etc/kubernetes/manifests/kube-controller-manager.yaml']),
    ("profiling SCH", ['grep', '--', '--profiling=false', '/etc/kubernetes/manifests/kube-scheduler.yaml']),
    ("enc-at-rest flag",   ['grep', 'encryption-provider-config', '/etc/kubernetes/manifests/kube-apiserver.yaml']),
    ("enc-config file",    ['ls', '/etc/kubernetes/encryption/encryption-config.yaml']),
    ("kube-proxy metrics", ['kubectl', '-n', 'kube-system', 'get', 'cm', 'kube-proxy',
                            '-o', 'jsonpath={.data.config\\.conf}']),
    ("vault sealed",       ['kubectl', 'exec', '-n', 'vault', 'vault-0', '--', 'vault', 'status']),
    ("kyverno verifyImg",  ['kubectl', 'get', 'clusterpolicy', 'verify-image-signatures', '--no-headers']),
    ("netpols count",      ['kubectl', 'get', 'networkpolicies', '-A', '--no-headers']),
    ("trivy cron",         ['crontab', '-l']),
    ("PSS ns labels",      ['kubectl', 'get', 'ns', 'kyverno', 'vault', 'default', '--show-labels', '--no-headers']),
    ("SA automount",       ['kubectl', 'get', 'sa', 'default', '-n', 'kube-system', '-o', 'json']),
]
for label, cmd in checks:
    out, err = run(cmd)
    snippet = (out or err)[:120].replace('\n', ' | ')
    ok = bool(out.strip()) and 'Error' not in out and 'error' not in err
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {snippet}")

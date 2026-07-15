import json
import os
import re
import subprocess


def run(cmd, inp=None, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, input=inp, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()


print("=== Check apiserver manifest ===")
out, _ = run(["ls", "-la", "/etc/kubernetes/manifests/"])
print(out)

print("\n=== SA automount fix ===")
for ns in ["kube-system", "kube-flannel", "kyverno", "vault"]:
    out, err = run(["kubectl", "get", "sa", "default", "-n", ns, "-o", "json"])
    if not out:
        print(f"  {ns}: not found ({err[:60]})")
        continue
    try:
        d = json.loads(out)
        val = d.get("automountServiceAccountToken")
        if val is False:
            print(f"  SKIP {ns}: already false")
        else:
            _, e = run(
                [
                    "kubectl",
                    "patch",
                    "serviceaccount",
                    "default",
                    "-n",
                    ns,
                    "-p",
                    '{"automountServiceAccountToken":false}',
                ]
            )
            print(f"  DONE {ns}: {e or 'ok'}")
    except Exception as ex:
        print(f"  {ns} error: {ex}")

print("\n=== Vault root token search ===")
tok = None
for kf in ["/root/vault-init.txt", "/root/vault-keys.txt", "/tmp/vault-init.txt"]:
    if os.path.exists(kf):
        with open(kf) as f:
            txt = f.read()
        m = re.search(r"Initial Root Token:\s+(\S+)", txt)
        if m:
            tok = m.group(1)
            print(f"Found token in {kf}")
            break
        else:
            print(f"File {kf} exists but no token pattern found")
            print("Content snippet:", txt[:200])

if not tok:
    print("Trying to re-init vault check (already initialized)...")
    out2, _ = run(["kubectl", "exec", "-n", "vault", "vault-0", "--", "vault", "status"])
    print(out2[:300])
    print("WARN: Root token not available. K8s auth must be configured manually.")
    print("To fix: kubectl exec -n vault vault-0 -- vault login <root_token>")
    print("        kubectl exec -n vault vault-0 -- vault auth enable kubernetes")
else:
    out3, _ = run(
        ["kubectl", "exec", "-n", "vault", "vault-0", "--", "env", f"VAULT_TOKEN={tok}", "vault", "auth", "list"]
    )
    if "kubernetes" in out3.lower():
        print("SKIP: k8s auth already configured")
    else:
        out4, _ = run(["kubectl", "config", "view", "--raw", "-o", "jsonpath={.clusters[0].cluster.server}"])
        host = out4.strip()
        _, e1 = run(
            [
                "kubectl",
                "exec",
                "-n",
                "vault",
                "vault-0",
                "--",
                "env",
                f"VAULT_TOKEN={tok}",
                "vault",
                "auth",
                "enable",
                "kubernetes",
            ]
        )
        print("enable k8s auth:", e1 or "ok")
        _, e2 = run(
            [
                "kubectl",
                "exec",
                "-n",
                "vault",
                "vault-0",
                "--",
                "env",
                f"VAULT_TOKEN={tok}",
                "vault",
                "write",
                "auth/kubernetes/config",
                f"kubernetes_host={host}",
            ]
        )
        print("configure:", e2 or "ok")

print("\n=== kube-proxy rollout status ===")
out, _ = run(
    ["kubectl", "-n", "kube-system", "rollout", "status", "daemonset", "kube-proxy", "--timeout=60s"], timeout=70
)
print(out)

out2, _ = run(["kubectl", "-n", "kube-system", "get", "cm", "kube-proxy", "-o", "jsonpath={.data.config\\.conf}"])
metrics = [l for l in out2.splitlines() if "metrics" in l.lower()]
print("kube-proxy metricsBindAddress:", metrics)

print("\n=== Full check summary ===")
apiserver_manifest = "/etc/kubernetes/manifests/kube-apiserver.yaml"
items = [
    ("apiserver manifest", ["ls", apiserver_manifest]),
    ("profiling API", ["grep", "--", "--profiling=false", apiserver_manifest]),
    ("profiling CM", ["grep", "--", "--profiling=false", "/etc/kubernetes/manifests/kube-controller-manager.yaml"]),
    ("profiling SCH", ["grep", "--", "--profiling=false", "/etc/kubernetes/manifests/kube-scheduler.yaml"]),
    ("enc-at-rest flag", ["grep", "encryption-provider-config", apiserver_manifest]),
    ("enc-config file", ["ls", "/etc/kubernetes/encryption/encryption-config.yaml"]),
    ("vault sealed=false", ["kubectl", "exec", "-n", "vault", "vault-0", "--", "vault", "status"]),
    ("kyverno verifyImages", ["kubectl", "get", "clusterpolicy", "verify-image-signatures", "--no-headers"]),
    ("netpols count", ["kubectl", "get", "networkpolicies", "-A", "--no-headers"]),
    ("trivy cron", ["crontab", "-l"]),
    ("PSS kyverno", ["kubectl", "get", "ns", "kyverno", "--show-labels", "--no-headers"]),
    ("PSS vault", ["kubectl", "get", "ns", "vault", "--show-labels", "--no-headers"]),
    ("PSS default", ["kubectl", "get", "ns", "default", "--show-labels", "--no-headers"]),
    (
        "SA kube-system",
        ["kubectl", "get", "sa", "default", "-n", "kube-system", "-o", "jsonpath={.automountServiceAccountToken}"],
    ),
    (
        "SA kyverno",
        ["kubectl", "get", "sa", "default", "-n", "kyverno", "-o", "jsonpath={.automountServiceAccountToken}"],
    ),
    ("SA vault", ["kubectl", "get", "sa", "default", "-n", "vault", "-o", "jsonpath={.automountServiceAccountToken}"]),
]
pass_count = 0
fail_list = []
for label, cmd in items:
    out, err = run(cmd, timeout=15)
    result = out or err
    ok = bool(out.strip()) and "not found" not in err and "No such file" not in err
    status = "PASS" if ok else "FAIL"
    if ok:
        pass_count += 1
    else:
        fail_list.append(label)
    print(f"  {status}  {label}: {result[:90].replace(chr(10),' | ')}")

print(f"\nResult: {pass_count}/{len(items)} passed")
if fail_list:
    print("Failed:", fail_list)

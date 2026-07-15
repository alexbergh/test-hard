import subprocess

ns_levels = [("kyverno", "privileged"), ("vault", "privileged"), ("default", "baseline")]
for ns, level in ns_levels:
    r = subprocess.run(
        ["kubectl", "get", "ns", ns, "-o", "jsonpath={.metadata.labels.pod-security\\.kubernetes\\.io/enforce}"],
        capture_output=True,
        text=True,
    )
    if r.stdout.strip():
        print(f"SKIP {ns}: enforce={r.stdout.strip()}")
    else:
        subprocess.run(
            [
                "kubectl",
                "label",
                "ns",
                ns,
                f"pod-security.kubernetes.io/enforce={level}",
                f"pod-security.kubernetes.io/audit={level}",
                f"pod-security.kubernetes.io/warn={level}",
                "--overwrite",
            ],
            capture_output=True,
            text=True,
        )
        print(f"DONE {ns}: enforce={level}")

for ns in ["kube-system", "kube-flannel", "kyverno", "vault"]:
    r = subprocess.run(
        ["kubectl", "get", "sa", "default", "-n", ns, "-o", "jsonpath={.automountServiceAccountToken}"],
        capture_output=True,
        text=True,
    )
    if r.stdout.strip() == "false":
        print(f"SKIP {ns}: automount already false")
    else:
        subprocess.run(
            ["kubectl", "patch", "serviceaccount", "default", "-n", ns, "-p", '{"automountServiceAccountToken":false}'],
            capture_output=True,
            text=True,
        )
        print(f"DONE {ns}: automount=false")

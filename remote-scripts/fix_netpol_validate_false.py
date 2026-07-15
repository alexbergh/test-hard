import json
import subprocess

POLICIES = {
    "default": [
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "default-deny-all", "namespace": "default"},
            "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]},
        }
    ],
    "development": [
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "default-deny-all", "namespace": "development"},
            "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]},
        },
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "allow-dns", "namespace": "development"},
            "spec": {
                "podSelector": {},
                "policyTypes": ["Egress"],
                "egress": [{"ports": [{"port": 53, "protocol": "UDP"}, {"port": 53, "protocol": "TCP"}]}],
            },
        },
    ],
    "kyverno": [
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "allow-kyverno-webhook", "namespace": "kyverno"},
            "spec": {
                "podSelector": {},
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [{}],
                "egress": [{}],
            },
        }
    ],
    "vault": [
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "allow-vault", "namespace": "vault"},
            "spec": {
                "podSelector": {},
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [{"ports": [{"port": 8200}, {"port": 8201}]}],
                "egress": [{}],
            },
        }
    ],
}

for ns, policies in POLICIES.items():
    r = subprocess.run(["kubectl", "get", "networkpolicies", "-n", ns, "--no-headers"], capture_output=True, text=True)
    count = len([l for l in r.stdout.strip().splitlines() if l.strip()])
    if count > 0:
        print(f"SKIP {ns}: already has {count} NetworkPolicies")
        continue
    for pol in policies:
        r2 = subprocess.run(
            ["kubectl", "apply", "--validate=false", "-f", "-"], input=json.dumps(pol), capture_output=True, text=True
        )
        print(f'  {ns}/{pol["metadata"]["name"]}: ' + (r2.stdout.strip() or r2.stderr.strip()))

r3 = subprocess.run(["kubectl", "get", "networkpolicies", "-A", "--no-headers"], capture_output=True, text=True)
print("NetworkPolicies after fix:")
print(r3.stdout)

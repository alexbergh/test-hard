#!/bin/bash
# Fix: NetworkPolicies for default, development, kyverno, vault

apply_netpol() {
    local ns=$1
    local count
    count=$(kubectl get networkpolicies -n "$ns" --no-headers 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "SKIP $ns already has NetworkPolicies"
        return
    fi
    kubectl apply -f - 2>&1
}

# --- default: deny all (no app workloads expected) ---
kubectl get networkpolicies -n default --no-headers 2>/dev/null | wc -l | grep -q '^0$' && \
kubectl apply -f - <<'EOF' 2>&1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

# --- development ---
kubectl get networkpolicies -n development --no-headers 2>/dev/null | wc -l | grep -q '^0$' && \
kubectl apply -f - <<'EOF' 2>&1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: development
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: development
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
EOF

# --- kyverno: needs full access (webhook server) ---
kubectl get networkpolicies -n kyverno --no-headers 2>/dev/null | wc -l | grep -q '^0$' && \
kubectl apply -f - <<'EOF' 2>&1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-kyverno-webhook
  namespace: kyverno
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - {}
  egress:
  - {}
EOF

# --- vault ---
kubectl get networkpolicies -n vault --no-headers 2>/dev/null | wc -l | grep -q '^0$' && \
kubectl apply -f - <<'EOF' 2>&1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-vault
  namespace: vault
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - ports:
    - port: 8200
    - port: 8201
  egress:
  - {}
EOF

echo "NetworkPolicies after:"
kubectl get networkpolicies -A --no-headers 2>/dev/null
echo "NETPOL_FIX_DONE"

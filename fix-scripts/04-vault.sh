#!/bin/bash
# Fix: Vault unseal + K8s auth
echo "=== Vault Status ==="
kubectl exec -n vault vault-0 -- vault status 2>/dev/null

SEALED=$(kubectl exec -n vault vault-0 -- vault status 2>/dev/null | grep '^Sealed' | awk '{print $2}')
echo "Sealed: $SEALED"

if [ "$SEALED" = "false" ]; then
    echo "SKIP Vault already unsealed"
else
    echo "Looking for stored unseal keys..."
    KEYS_FILE=""
    for f in /root/vault-init.txt /root/vault-keys.txt /root/vault-unseal.txt; do
        [ -f "$f" ] && KEYS_FILE="$f" && break
    done

    if [ -z "$KEYS_FILE" ]; then
        echo "No stored keys found, running vault operator init..."
        kubectl exec -n vault vault-0 -- vault operator init \
          -key-shares=3 -key-threshold=2 2>/dev/null > /root/vault-init.txt
        KEYS_FILE=/root/vault-init.txt
        echo "Init output saved to /root/vault-init.txt"
    fi

    echo "Unsealing with keys from $KEYS_FILE..."
    grep 'Unseal Key' "$KEYS_FILE" | head -2 | awk '{print $NF}' | while read -r key; do
        echo "Unsealing with key..."
        kubectl exec -n vault vault-0 -- vault operator unseal "$key" 2>/dev/null | grep -E 'Sealed|Progress'
    done

    sleep 5
    echo "Status after unseal:"
    kubectl exec -n vault vault-0 -- vault status 2>/dev/null
fi

# Configure K8s auth
ROOT_TOKEN=$(grep 'Initial Root Token' /root/vault-init.txt 2>/dev/null | awk '{print $NF}')
if [ -z "$ROOT_TOKEN" ]; then
    echo "WARN: No root token found, skipping K8s auth setup"
    exit 0
fi

echo "Checking K8s auth..."
AUTH_LIST=$(kubectl exec -n vault vault-0 -- \
  env VAULT_TOKEN="$ROOT_TOKEN" vault auth list 2>/dev/null)
echo "$AUTH_LIST"

if echo "$AUTH_LIST" | grep -q 'kubernetes'; then
    echo "SKIP K8s auth already enabled"
else
    echo "Enabling K8s auth..."
    K8S_HOST=$(kubectl config view --raw \
      -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null)

    kubectl exec -n vault vault-0 -- \
      env VAULT_TOKEN="$ROOT_TOKEN" vault auth enable kubernetes 2>/dev/null

    # Get CA cert from cluster
    CA_CERT=$(kubectl config view --raw \
      -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' 2>/dev/null | base64 -d)

    kubectl exec -n vault vault-0 -- \
      env VAULT_TOKEN="$ROOT_TOKEN" \
      vault write auth/kubernetes/config \
        kubernetes_host="$K8S_HOST" \
        kubernetes_ca_cert="$CA_CERT" 2>/dev/null

    echo "K8s auth configured for host: $K8S_HOST"
fi

echo "Final Vault status:"
kubectl exec -n vault vault-0 -- vault status 2>/dev/null
echo "VAULT_FIX_DONE"

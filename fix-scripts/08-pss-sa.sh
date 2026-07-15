#!/bin/bash
# Fix: PSS labels + SA automount

echo "=== PSS Labels ==="
# kyverno and vault need 'privileged' level to run their system components
for ns_level in "kyverno:privileged" "vault:privileged" "default:baseline"; do
    ns=${ns_level%%:*}
    level=${ns_level##*:}
    existing=$(kubectl get ns "$ns" \
      -o jsonpath='{.metadata.labels.pod-security\.kubernetes\.io/enforce}' 2>/dev/null)
    if [ -n "$existing" ]; then
        echo "SKIP $ns: enforce=$existing"
    else
        kubectl label ns "$ns" \
          pod-security.kubernetes.io/enforce="$level" \
          pod-security.kubernetes.io/audit="$level" \
          pod-security.kubernetes.io/warn="$level" \
          --overwrite 2>&1
        echo "DONE $ns: enforce=$level"
    fi
done

echo ""
echo "=== SA automount ==="
for ns in kube-system kube-flannel kyverno vault; do
    val=$(kubectl get sa default -n "$ns" \
      -o jsonpath='{.automountServiceAccountToken}' 2>/dev/null)
    if [ "$val" = "false" ]; then
        echo "SKIP $ns: already false"
    else
        kubectl patch serviceaccount default -n "$ns" \
          -p '{"automountServiceAccountToken":false}' 2>&1
        echo "DONE $ns: set automount=false"
    fi
done

echo "PSS_SA_FIX_DONE"

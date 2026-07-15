#!/bin/bash
# Fix: Kyverno verifyImages ClusterPolicy
if kubectl get clusterpolicy verify-image-signatures 2>/dev/null | grep -q verify; then
    echo "SKIP verifyImages policy already exists"
    exit 0
fi

# Find cosign public key
PUB_KEY=""
for p in /root/cosign-keys/cosign.pub /root/cosign.pub /etc/cosign/cosign.pub; do
    [ -f "$p" ] && PUB_KEY=$(cat "$p") && echo "Found key: $p" && break
done

if [ -z "$PUB_KEY" ]; then
    echo "WARN: cosign public key not found, using placeholder"
    PUB_KEY="# UPDATE WITH REAL KEY"
fi

# Write policy
cat > /tmp/verify-images.yaml <<ENDPOLICY
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
  annotations:
    policies.kyverno.io/title: Verify Image Signatures
    policies.kyverno.io/description: Verify cosign signatures on production images
spec:
  validationFailureAction: Audit
  background: false
  rules:
    - name: verify-image
      match:
        any:
        - resources:
            kinds:
              - Pod
            namespaces:
              - production
      verifyImages:
        - imageReferences:
            - "*"
          attestors:
            - count: 1
              entries:
              - keys:
                  publicKeys: |-
$(echo "$PUB_KEY" | sed 's/^/                    /')
ENDPOLICY

kubectl apply -f /tmp/verify-images.yaml 2>&1
echo "KYVERNO_VERIFY_DONE"

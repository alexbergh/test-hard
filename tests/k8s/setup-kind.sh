#!/usr/bin/env bash
set -euo pipefail

if ! command -v kind >/dev/null 2>&1; then
  echo "kind binary is required. Install from https://kind.sigs.k8s.io/docs/user/quick-start/" >&2
  exit 1
fi

CLUSTER_NAME=${KIND_CLUSTER_NAME:-hardening-test}
CONFIG="$(dirname "$0")/kind-cluster.yaml"

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "kind cluster ${CLUSTER_NAME} already exists"
else
  kind create cluster --name "${CLUSTER_NAME}" --config "${CONFIG}"
fi

echo "To access the cluster run: kind export kubeconfig --name ${CLUSTER_NAME}" >&2

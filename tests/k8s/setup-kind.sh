#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIMULATOR="${SCRIPT_DIR}/simulate.py"

export HARDENING_FIXED_TIMESTAMP="${HARDENING_FIXED_TIMESTAMP:-2025-10-21T00:00:00+00:00}"

if ! command -v kind >/dev/null 2>&1; then
  echo "kind не обнаружен. Выполняется оффлайн-симуляция." >&2
  SAMPLE_XML="${SCRIPT_DIR}/../docker/openscap/content/sample-oval.xml"
  SAMPLE_ARCHIVE="${SCRIPT_DIR}/../docker/openscap/content/fstec-sample.zip"
  python3 "${SCRIPT_DIR}/../tools/create_sample_fstec_archive.py" \
    --source "${SAMPLE_XML}" \
    --archive "${SAMPLE_ARCHIVE}" \
    --prefix "linux"
  python3 "${SCRIPT_DIR}/../../environments/openscap/tools/prepare_fstec_content.py" \
    --archive "${SAMPLE_ARCHIVE}" \
    --output "${SCRIPT_DIR}/../docker/openscap/content/fstec" \
    --clean >/dev/null
  python3 "${SIMULATOR}"
  python3 "${SCRIPT_DIR}/../tools/generate_process_report.py" --quiet
  exit 0
fi

CLUSTER_NAME=${KIND_CLUSTER_NAME:-hardening-test}
CONFIG="${SCRIPT_DIR}/kind-cluster.yaml"

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "kind cluster ${CLUSTER_NAME} already exists"
else
  kind create cluster --name "${CLUSTER_NAME}" --config "${CONFIG}"
fi

echo "To access the cluster run: kind export kubeconfig --name ${CLUSTER_NAME}" >&2

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONFIG_DIR="${ROOT_DIR}/config"
INDEXER_CERTS="${CONFIG_DIR}/indexer/certs"
DASHBOARD_CERTS="${CONFIG_DIR}/dashboard/certs"
MANAGER_SSL="${CONFIG_DIR}/manager/api/ssl"

mkdir -p "${INDEXER_CERTS}" "${DASHBOARD_CERTS}" "${MANAGER_SSL}"

SAN_FILE=$(mktemp)
INDEXER_CSR=$(mktemp)
DASHBOARD_CSR=$(mktemp)
MANAGER_CSR=$(mktemp)
trap 'rm -f "${SAN_FILE}" "${INDEXER_CSR}" "${DASHBOARD_CSR}" "${MANAGER_CSR}"' EXIT

cat > "${SAN_FILE}" <<'SAN'
[v3_req]
subjectAltName=DNS:wazuh-indexer,DNS:localhost,IP:127.0.0.1
SAN

openssl genrsa -out "${INDEXER_CERTS}/root-ca.key" 4096
openssl req -x509 -new -nodes -key "${INDEXER_CERTS}/root-ca.key" -sha256 -days 3650 \
  -subj "/C=US/ST=CA/O=Wazuh/OU=Lab/CN=Wazuh-Root-CA" \
  -out "${INDEXER_CERTS}/root-ca.pem"

openssl genrsa -out "${INDEXER_CERTS}/indexer-key.pem" 4096
openssl req -new -key "${INDEXER_CERTS}/indexer-key.pem" \
  -subj "/C=US/ST=CA/O=Wazuh/OU=Wazuh/CN=demo.indexer" \
  -out "${INDEXER_CSR}"
openssl x509 -req -in "${INDEXER_CSR}" -CA "${INDEXER_CERTS}/root-ca.pem" -CAkey "${INDEXER_CERTS}/root-ca.key" -CAcreateserial \
  -out "${INDEXER_CERTS}/indexer.pem" -days 1825 -sha256 -extfile "${SAN_FILE}" -extensions v3_req

openssl genrsa -out "${DASHBOARD_CERTS}/dashboard.key" 4096
openssl req -new -key "${DASHBOARD_CERTS}/dashboard.key" \
  -subj "/C=US/ST=CA/O=Wazuh/OU=Wazuh/CN=wazuh-dashboard" \
  -out "${DASHBOARD_CSR}"
openssl x509 -req -in "${DASHBOARD_CSR}" -CA "${INDEXER_CERTS}/root-ca.pem" -CAkey "${INDEXER_CERTS}/root-ca.key" -CAcreateserial \
  -out "${DASHBOARD_CERTS}/dashboard.crt" -days 825 -sha256

cp "${INDEXER_CERTS}/root-ca.pem" "${DASHBOARD_CERTS}/root-ca.pem"

openssl genrsa -out "${MANAGER_SSL}/server.key" 4096
openssl req -new -key "${MANAGER_SSL}/server.key" \
  -subj "/C=US/ST=CA/O=Wazuh/OU=Wazuh/CN=wazuh-manager" \
  -out "${MANAGER_CSR}"
openssl x509 -req -in "${MANAGER_CSR}" -CA "${INDEXER_CERTS}/root-ca.pem" -CAkey "${INDEXER_CERTS}/root-ca.key" -CAcreateserial \
  -out "${MANAGER_SSL}/server.crt" -days 825 -sha256
cp "${INDEXER_CERTS}/root-ca.pem" "${MANAGER_SSL}/root-ca.pem"

chmod 600 "${INDEXER_CERTS}/root-ca.key" "${INDEXER_CERTS}/indexer-key.pem" \
  "${DASHBOARD_CERTS}/dashboard.key" "${MANAGER_SSL}/server.key"
chmod 644 "${INDEXER_CERTS}/root-ca.pem" "${INDEXER_CERTS}/indexer.pem" \
  "${DASHBOARD_CERTS}/dashboard.crt" "${DASHBOARD_CERTS}/root-ca.pem" \
  "${MANAGER_SSL}/server.crt" "${MANAGER_SSL}/root-ca.pem"

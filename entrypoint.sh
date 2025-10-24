#!/bin/sh
set -e

echo "Fixing certificates permissions..."
chown -R 1000:1000 /etc/wazuh-indexer/certs/ || true
chmod 644 /etc/wazuh-indexer/certs/*.pem || true
chmod 600 /etc/wazuh-indexer/certs/*.key || true

echo "Starting OpenSearch..."
exec /usr/share/wazuh-indexer/bin/opensearch "$@"

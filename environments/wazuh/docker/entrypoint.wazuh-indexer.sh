#!/bin/sh
set -e

printf '%s\n' "Fixing certificate permissions inside container..."
chown -R 1000:1000 /etc/wazuh-indexer/certs/ 2>/dev/null || true
find /etc/wazuh-indexer/certs -type f -name '*.pem' -exec chmod 0644 {} + 2>/dev/null || true
find /etc/wazuh-indexer/certs -type f \( -name '*key.pem' -o -name '*.key' \) -exec chmod 0600 {} + 2>/dev/null || true

printf '%s\n' "Starting OpenSearch"
exec /usr/share/wazuh-indexer/bin/opensearch "$@"

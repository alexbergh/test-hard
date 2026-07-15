#!/usr/bin/env bash
# Generate TypeScript API client from OpenAPI specification.
# Requires: npx openapi-typescript-codegen (installed as devDependency)
#
# Usage:
#   ./scripts/generate-api-client.sh [backend_url]
#
# Default backend URL: http://localhost:8000

set -euo pipefail

BACKEND_URL="${1:-http://localhost:8000}"
OPENAPI_URL="${BACKEND_URL}/openapi.json"
OUTPUT_DIR="src/api/generated"

echo "Fetching OpenAPI spec from ${OPENAPI_URL}..."
echo "Output directory: ${OUTPUT_DIR}"

npx openapi-typescript-codegen \
  --input "${OPENAPI_URL}" \
  --output "${OUTPUT_DIR}" \
  --client axios \
  --useOptions \
  --useUnionTypes

echo "API client generated successfully in ${OUTPUT_DIR}"

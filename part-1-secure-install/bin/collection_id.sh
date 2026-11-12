#!/usr/bin/env bash
# Print the ID of a collection. Record endpoints (add, query, get) need the ID.
# Usage: bin/collection_id.sh <token-name> <tenant> <collection-name>
set -euo pipefail
cd "$(dirname "$0")/.."
bin/chroma.sh "${1:?token-name}" GET "/api/v2/tenants/${2:?tenant}/databases/main/collections/${3:?collection}" \
  | head -1 | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])"

#!/usr/bin/env bash
# Send a request to Chroma through the secure gateway, as a named token.
#
# Usage:
#   bin/chroma.sh <token-name> <METHOD> <path> [json-body]
#
# Examples:
#   bin/chroma.sh acme_reader GET /api/v2/heartbeat
#   bin/chroma.sh acme_writer POST /api/v2/tenants/acme/databases/main/collections '{"name":"docs"}'
#   bin/chroma.sh none GET /api/v2/heartbeat          # send no token at all
#   bin/chroma.sh wrong GET /api/v2/heartbeat         # send an invalid token
#
# The token is read from secrets/<token-name>_token.txt and the server
# certificate is verified against secrets/server.crt (no -k / --insecure).
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="${1:?usage: bin/chroma.sh <token-name|none> <METHOD> <path> [json-body]}"
METHOD="${2:?missing METHOD}"
URLPATH="${3:?missing path}"
BODY="${4:-}"

ARGS=(-sS -w '\n[HTTP %{http_code}]\n' --cacert secrets/server.crt -X "$METHOD")
if [[ "$NAME" == "wrong" ]]; then
  ARGS+=(-H "Authorization: Bearer this-is-not-a-real-token")
elif [[ "$NAME" != "none" ]]; then
  ARGS+=(-H "Authorization: Bearer $(cat "secrets/${NAME}_token.txt")")
fi
if [[ -n "$BODY" ]]; then
  ARGS+=(-H "Content-Type: application/json" -d "$BODY")
fi

curl "${ARGS[@]}" "https://localhost:8443${URLPATH}"

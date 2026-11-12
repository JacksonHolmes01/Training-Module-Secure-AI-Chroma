#!/usr/bin/env bash
# Send a request to Chroma's internal gateway as one of the lab's tokens,
# from a throwaway container on the backend network.
# Usage: bin/chroma_as.sh <admin|writer|reader|none> <METHOD> <path> [json]
set -euo pipefail
cd "$(dirname "$0")/.."
NAME="${1:?token}"; METHOD="${2:?METHOD}"; URLPATH="${3:?path}"; BODY="${4:-}"
ARGS=(-s -w '\n[HTTP %{http_code}]\n' -X "$METHOD")
[[ "$NAME" != "none" ]] && ARGS+=(-H "Authorization: Bearer $(cat "secrets/${NAME}_token.txt")")
[[ -n "$BODY" ]] && ARGS+=(-H "Content-Type: application/json" -d "$BODY")
NET="$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' rag-chroma-gateway | tr ' ' '\n' | grep backend)"
docker run --rm --network "$NET" curlimages/curl:8.11.1 "${ARGS[@]}" "http://chroma-gateway:8000${URLPATH}"

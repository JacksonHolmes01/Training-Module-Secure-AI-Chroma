#!/bin/sh
# One-time Chroma setup, run by the chroma-init container with the ADMIN token.
# Creates:  tenant $APP_TENANT  ->  database "main"  ->  collection "documents"
# Safe to run on every start: anything that already exists is left alone.
set -eu

GW="${CHROMA_URL:-http://chroma-gateway:8000}/api/v2"
# Part 4, Layer 5: verify the gateway's TLS certificate against our own CA
CA=""
[ -n "${CHROMA_CA_CERT:-}" ] && CA="--cacert ${CHROMA_CA_CERT}"
AUTH="Authorization: Bearer $(cat /run/secrets/admin_token)"
T="${APP_TENANT:-lab}"

req() {  # req METHOD PATH [JSON]  -> prints HTTP status
  if [ -n "${3:-}" ]; then
    curl -s $CA -o /tmp/out -w '%{http_code}' -X "$1" "$GW$2" -H "$AUTH" -H "Content-Type: application/json" -d "$3"
  else
    curl -s $CA -o /tmp/out -w '%{http_code}' -X "$1" "$GW$2" -H "$AUTH"
  fi
}

echo "Waiting for Chroma through the gateway..."
i=0
until [ "$(req GET /heartbeat)" = "200" ]; do
  i=$((i+1)); [ $i -gt 60 ] && { echo "Chroma did not become ready"; exit 1; }
  sleep 2
done

if [ "$(req GET /tenants/$T)" != "200" ]; then
  [ "$(req POST /tenants "{\"name\":\"$T\"}")" = "200" ] || { cat /tmp/out; exit 1; }
  echo "created tenant $T"
else
  echo "tenant $T exists"
fi

if [ "$(req GET /tenants/$T/databases/main)" != "200" ]; then
  [ "$(req POST /tenants/$T/databases '{"name":"main"}')" = "200" ] || { cat /tmp/out; exit 1; }
  echo "created database $T/main"
else
  echo "database $T/main exists"
fi

if [ "$(req GET /tenants/$T/databases/main/collections/documents)" != "200" ]; then
  [ "$(req POST /tenants/$T/databases/main/collections '{"name":"documents","configuration":{"hnsw":{"space":"cosine"}}}')" = "200" ] \
    || { cat /tmp/out; exit 1; }
  echo "created collection $T/main/documents (cosine)"
else
  echo "collection $T/main/documents exists"
fi

echo "chroma-init complete."

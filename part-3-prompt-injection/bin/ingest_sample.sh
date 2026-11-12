#!/usr/bin/env bash
# Sends every document in data/sample_articles.jsonl through NGINX to /ingest.
set -uo pipefail
cd "$(dirname "$0")/.."
KEY="$(grep -E '^EDGE_API_KEY=' .env | cut -d= -f2-)"
ok=0; fail=0; n=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  n=$((n+1))
  # Pace requests and retry if NGINX's rate limit answers 429
  for attempt in 1 2 3 4 5; do
    code=$(curl -s -o /tmp/ingest_resp.$$ -w '%{http_code}' -X POST http://localhost:8088/ingest \
      -H "X-API-Key: $KEY" -H "Content-Type: application/json" -d "$line")
    [[ "$code" != "429" ]] && break
    sleep 2
  done
  sleep 0.2
  if [[ "$code" == "200" ]]; then ok=$((ok+1)); echo "  ✔ document $n ingested"
  else fail=$((fail+1)); echo "  ✘ document $n failed (HTTP $code): $(cat /tmp/ingest_resp.$$)"; fi
done < data/sample_articles.jsonl
rm -f /tmp/ingest_resp.$$
echo "Total: $n  Success: $ok  Failed: $fail"
[[ $fail -eq 0 ]]

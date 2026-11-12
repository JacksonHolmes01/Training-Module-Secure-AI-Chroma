# Lesson 9: Operations, Testing, and Troubleshooting

Building a system is half the job. The other half is knowing it still works tomorrow and finding out quickly when it does not.

---

## The smoke test

`bin/smoke_test.sh` checks the whole path, including the security controls:

```bash
bin/smoke_test.sh
```

### What success looks like

```
[1/6] proxy health
  ✔ NGINX is up
[2/6] request without a key is rejected
  ✔ 401 without key
[3/6] request with a wrong key is rejected
  ✔ 403 with wrong key
[4/6] API and database health
  ✔ chroma_ok
[5/6] retrieval
  ✔ retrieval returned sources
[6/6] full chat (can take a minute on first run)
  ✔ chat answered
All smoke tests passed.
```

Steps 2 and 3 test that bad requests **fail**. A smoke test that only checks the happy path would keep passing even if someone accidentally removed authentication.

Run it after every change.

---

## Status and resource use

```bash
bin/status.sh
```

Shows each container's state plus live CPU and memory. If `rag-ollama` is near its 6 GB limit, the model may be too large for your machine.

---

## Logs

```bash
docker compose logs ingestion-api --tail=30
docker compose logs nginx --tail=30
docker compose logs chroma-gateway --tail=30
docker compose logs chroma --tail=30
```

Add `-f` to follow logs live, and press Ctrl + C to stop.

---

## Trace an error by request id

Every response includes an `X-Request-Id` header. When the API fails, the client sees only that id, and the details go to the log.

Cause a real failure by stopping Ollama, then sending a chat:

```bash
EDGE_API_KEY=$(grep -E '^EDGE_API_KEY=' .env | cut -d= -f2-)
docker compose stop ollama
curl -s -X POST http://localhost:8088/chat \
  -H "X-API-Key: $EDGE_API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "What is the CIA triad?"}'
```

```json
{"detail":"Internal error. Request id: 5d0c...e21"}
```

Copy the id and search the log for it:

```bash
docker compose logs ingestion-api | grep "PASTE-THE-ID-HERE"
```

You will see the full error, such as `/chat failed: ConnectError`, followed by the stack trace. The **user** learns nothing useful to an attacker. The **operator** learns exactly what broke.

Start Ollama again:

```bash
docker compose start ollama
```

---

## Turn off the debug endpoints

The debug endpoints show prompts and raw retrieval. Turn them off and confirm they disappear:

```bash
sed -i.bak 's/^ENABLE_DEBUG_ENDPOINTS=.*/ENABLE_DEBUG_ENDPOINTS=false/' .env && rm .env.bak
docker compose up -d ingestion-api
sleep 10
curl -s -H "X-API-Key: $EDGE_API_KEY" "http://localhost:8088/debug/retrieve?q=test"
```

```json
{"detail":"Not found."}
```

The endpoint now looks like it does not exist at all. Turn them back on for Part 3:

```bash
sed -i.bak 's/^ENABLE_DEBUG_ENDPOINTS=.*/ENABLE_DEBUG_ENDPOINTS=true/' .env && rm .env.bak
docker compose up -d ingestion-api
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `required variable EDGE_API_KEY is missing` | No `.env` yet | `bin/setup_secrets.sh` |
| `bind source path does not exist: .../secrets/...` | Secret files missing | `bin/setup_secrets.sh` |
| `rag-api` never starts | `chroma-init` failed | `docker logs rag-chroma-init` |
| `/health` shows `chroma_ok: false` | Token files changed but gateway not restarted | `docker compose restart chroma-gateway` |
| Ingest returns HTTP 500 | Embedding model not downloaded | `bin/pull_models.sh` |
| Chat times out | Model still loading, or not enough memory | Wait and retry; check `bin/status.sh` |
| `curl: (7) Failed to connect to localhost port 8088` | NGINX not running | `docker compose ps`, then `docker compose logs nginx` |
| UI shows `HTTP 401` or `403` | UI has a different key than NGINX | `docker compose up -d --force-recreate gradio-ui nginx` |
| `port is already allocated` | Another lab is using the port | Stop the other lab with `docker compose down` |

---

## Stop, restart, reset

```bash
docker compose down            # stop, keep data and models
docker compose up -d           # start again
bin/reset_all.sh               # delete ALL data and models (asks first)
```

Next: [Conclusion](10-conclusion.md)

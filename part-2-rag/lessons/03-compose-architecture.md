# Lesson 3: Compose Architecture and Network Segmentation

In Part 1 you learned that **Chroma trusts everything on its network**. You even planted a collection from a throwaway container with no token.

Part 2 has seven containers. If they all shared one network, compromising any one of them (the UI, for example) would mean full access to Chroma. So this lab splits them into **three networks**, each a separate trust zone.

Open `docker-compose.yml` as you read.

---

## Three networks, three zones

```
            frontend                      backend                         data (internal)
  ┌─────────────────────────┐  ┌──────────────────────────────┐  ┌───────────────────────┐
  │ rag-ui      rag-nginx   │  │ rag-ollama                   │  │                       │
  │                         │  │                              │  │                       │
  │          rag-api ───────┼──┼─► rag-chroma-gateway ────────┼──┼──► rag-chroma         │
  │                         │  │   rag-chroma-init (exits)    │  │                       │
  └─────────────────────────┘  └──────────────────────────────┘  └───────────────────────┘
```

| Service | frontend | backend | data |
|---|:-:|:-:|:-:|
| `rag-ui`, `rag-nginx` | ✔ | | |
| `rag-api` | ✔ | ✔ | |
| `rag-ollama`, `rag-chroma-init` | | ✔ | |
| `rag-chroma-gateway` | | ✔ | ✔ |
| `rag-chroma` | | | ✔ |

A container can only reach containers that share at least one network with it. Read the table across:
- the **UI and NGINX** can reach the API, and nothing else
- the **API** can reach the Chroma **gateway** and Ollama, but **not Chroma itself**
- **Chroma** can be reached by its gateway, and by nothing else

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
  data:
    driver: bridge
    internal: true
```

`internal: true` means the `data` network has **no route to the internet**. Chroma cannot download anything, call home, or send stolen data out, even if it were compromised.

---

## Prove nothing can reach Chroma directly

Ask each container to open a connection to `chroma:8000`:

```bash
for c in rag-nginx rag-ui rag-api rag-ollama; do
  printf "%-12s -> chroma:8000  " "$c"
  docker exec "$c" sh -c 'python3 -c "import socket; socket.create_connection((\"chroma\", 8000), 2)" 2>/dev/null && echo REACHABLE || (nc -z -w 2 chroma 8000 2>/dev/null && echo REACHABLE || echo blocked)'
done
```

### What success looks like

```
rag-nginx    -> chroma:8000  blocked
rag-ui       -> chroma:8000  blocked
rag-api      -> chroma:8000  blocked
rag-ollama   -> chroma:8000  blocked
```

Every one is blocked, **including the API**. The API's only path to Chroma is through the gateway, which demands a token.

## Prove Chroma cannot reach the internet

```bash
docker exec rag-chroma bash -c 'timeout 4 bash -c "exec 3<>/dev/tcp/1.1.1.1/443" 2>/dev/null && echo HAS-INTERNET || echo no-internet'
```

```
no-internet
```

---

## Prove the internal services are hidden from your computer

```bash
for port in 8000 11434; do
  nc -z -w 2 127.0.0.1 $port && echo "$port OPEN" || echo "$port closed"
done
```

```
8000 closed
11434 closed
```

Only two ports are published, both to `127.0.0.1`: NGINX on `8088` and the UI on `7860`.

> On Windows/WSL, install `nc` with `sudo apt install -y netcat-openbsd` if it is missing.

---

## Resource limits on every service

| Service | `mem_limit` | Why |
|---|---|---|
| chroma | 2g | Vector indexes are memory-hungry |
| ollama | 6g | The LLM is the largest consumer |
| ingestion-api | 1g | Python app |
| nginx, chroma-gateway | 128m | Tiny; should never need more |
| gradio-ui | 512m | Web UI only |

Check live usage at any time:

```bash
bin/status.sh
```

---

## Each service gets only the secrets it needs

```yaml
  ingestion-api:
    volumes:
      - ./secrets/writer_token.txt:/run/secrets/writer_token:ro
      - ./secrets/reader_token.txt:/run/secrets/reader_token:ro
```

Confirm what the API can see:

```bash
docker exec rag-api ls /run/secrets
```

```
reader_token
writer_token
```

The **admin** token is mounted only into `rag-chroma-init`, a container that runs once and exits. The long-running API, which handles untrusted requests all day, never holds admin rights.

---

## Startup order

```yaml
  ingestion-api:
    depends_on:
      chroma-init:
        condition: service_completed_successfully
```

The API waits until `chroma-init` has **finished successfully**. If setup fails, the API never starts, and you find out immediately instead of getting confusing errors later.

```bash
docker compose ps -a --format '{{.Name}}: {{.Status}}' | grep init
```

```
rag-chroma-init: Exited (0) 2 minutes ago
```

`Exited (0)` is success. Any other number means setup failed: read its log with `docker logs rag-chroma-init`.

---

## Pinned versions

```yaml
image: chromadb/chroma:1.5.9
image: ollama/ollama:0.40.6
image: nginx:1.28-alpine
image: curlimages/curl:8.11.1
```

Every image has an explicit version, so a surprise upstream release cannot change your lab. (Part 4 covers verifying images in more depth.)

Next: [Edge Authentication with NGINX](04-nginx-auth.md)

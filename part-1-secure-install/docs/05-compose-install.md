# Install Chroma Behind a Secure Gateway

In this step you will create the secrets, start Chroma with its gateway, and prove Chroma cannot be reached directly.

---

## The design

```
your computer                     Docker network "data"
─────────────                     ─────────────────────────────────────
curl ──HTTPS──► 127.0.0.1:8443 ──► gateway (NGINX) ──HTTP──► chroma:8000
                                    • TLS                     • no published port
                                    • token check             • no auth of its own
                                    • allowlist
                                    • rate limit
```

The gateway is the **only** door. Chroma is in a room with no other entrance.

---

## Read the Chroma service

Open `docker-compose.yml`:

```yaml
  chroma:
    image: chromadb/chroma:1.5.9
    mem_limit: 2g
    cpus: 2.0
    pids_limit: 256
    command: ["run", "/config.yaml"]
    volumes:
      - chroma_data:/data
      - ./chroma/config.yaml:/config.yaml:ro
    networks:
      - data
```

- **A pinned version** (`1.5.9`), never `:latest`, so everyone runs the same software and upgrades are deliberate
- **Resource limits** so a runaway query cannot freeze your computer
- **No `ports:` section.** This is the most important line, because it is missing
- **The config file is mounted `:ro` (read-only)**, so nothing inside the container can change its own settings

Open `chroma/config.yaml`:

```yaml
persist_path: "/data"
allow_reset: false
max_payload_size_bytes: 1048576
```

- `allow_reset: false` disables the API call that wipes the entire database. It is already the default, but writing it down makes the intent clear and protects you if a future version changes the default
- `max_payload_size_bytes` rejects requests over 1 MB

---

## Read the gateway service

```yaml
  gateway:
    image: nginx:1.28-alpine
    ports:
      - "127.0.0.1:8443:8443"
    volumes:
      - ./gateway/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./secrets/tokens.map:/etc/nginx/secrets/tokens.map:ro
      - ./secrets/server.crt:/etc/nginx/secrets/server.crt:ro
      - ./secrets/server.key:/etc/nginx/secrets/server.key:ro
```

- Port `8443` is published to `127.0.0.1` only
- The rules, the token list, and the certificate are all mounted read-only

You will read the rules in `gateway/default.conf` over the next lessons.

---

## Create the secrets

```bash
bin/setup_secrets.sh
```

### What success looks like

```
  created  secrets/admin_token.txt
  created  secrets/acme_writer_token.txt
  created  secrets/acme_reader_token.txt
  created  secrets/globex_reader_token.txt
  wrote    secrets/tokens.map
  created  secrets/server.crt and server.key
Secrets ready.
```

| Token | Role | Tenant | Used for |
|---|---|---|---|
| `admin` | admin | all | Setup: creating tenants and deleting things |
| `acme_writer` | writer | acme | An app that adds Acme's documents |
| `acme_reader` | reader | acme | A chatbot that searches Acme's documents |
| `globex_reader` | reader | globex | A different customer's chatbot |

Each token is 40 random characters. `secrets/tokens.map` is the list the gateway uses to look tokens up. `.gitignore` keeps everything in `secrets/` out of git.

---

## Start the stack

```bash
docker compose up -d
```

### What success looks like

```
 ✔ Container chroma          Started
 ✔ Container chroma-gateway  Started
```

Check status:

```bash
docker compose ps
```

```
NAME             STATUS         PORTS
chroma           Up 10 seconds  8000/tcp
chroma-gateway   Up 10 seconds  80/tcp, 127.0.0.1:8443->8443/tcp
```

- `chroma` shows a bare `8000/tcp`: open only inside Docker's private network
- `chroma-gateway` shows `127.0.0.1:8443->8443/tcp`: the only door, and only from your computer

---

## Prove Chroma is unreachable directly

```bash
nc -z -w 2 127.0.0.1 8000 && echo "8000 OPEN (bad)" || echo "8000 closed (good)"
```

```
8000 closed (good)
```

The attacks from Lesson 4 are now impossible from your computer. There is nothing on port 8000 to attack.

> On Windows/WSL, install `nc` with `sudo apt install -y netcat-openbsd` if it is missing.

---

## Your first request through the gateway

```bash
bin/chroma.sh acme_reader GET /api/v2/heartbeat
```

```
{"nanosecond heartbeat":1794463436381002226}
[HTTP 200]
```

`bin/chroma.sh` read the `acme_reader` token from `secrets/`, connected over HTTPS, verified the certificate, and sent the token. The gateway checked it and passed the request to Chroma.

Next: [Authentication (Tokens)](06-authentication.md)

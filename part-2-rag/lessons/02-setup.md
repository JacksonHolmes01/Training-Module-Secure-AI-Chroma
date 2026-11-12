# Lesson 2: Prerequisites and Setup

## Prerequisites

- You completed **Part 1** (or at least have Docker, git, and openssl working: see Part 1 Lessons 1 and 2)
- Docker has at least **8 GB of memory** available
  - Docker Desktop: **Settings → Resources → Memory**
  - Colima: `colima stop && colima start --cpu 4 --memory 8`
- About **6 GB** of free disk space

---

## Step 1: Stop Part 1

Part 1's Chroma must not be running at the same time, so the two labs do not compete for resources:

```bash
cd ~/Training-Module-Secure-AI-Chroma/part-1-secure-install
docker compose down
```

This keeps Part 1's data. It only stops the container.

---

## Step 2: Move into Part 2

```bash
cd ~/Training-Module-Secure-AI-Chroma/part-2-rag
ls
```

### What success looks like

```
README.md  bin  chroma  chroma-gateway  chroma-init  data  docker-compose.yml  gradio-ui  ingestion-api  lessons  nginx  secrets
```

Every command in Part 2 runs from this folder.

---

## Step 3: Create the secrets

Part 2 needs four secrets:
- an **admin** token for Chroma (used once, at startup, to create the collection)
- a **writer** token for Chroma (used by ingestion)
- a **reader** token for Chroma (used by chat)
- an **API key** that NGINX requires on every request

One script creates all of them:

```bash
bin/setup_secrets.sh
```

### What success looks like

```
  created  secrets/admin_token.txt
  created  secrets/writer_token.txt
  created  secrets/reader_token.txt
  wrote    secrets/tokens.map (tenant: lab)
  created  .env (from .env.example)
  created  EDGE_API_KEY in .env
Secrets ready.
```

If you run it again, it prints `kept` instead of `created`. It never overwrites an existing secret.

### Check that git ignores them

```bash
git status --short
```

The output must **not** include `.env` or anything in `secrets/`.

---

## Step 4: Build and start the stack

```bash
docker compose up -d --build
```

- `--build` builds the FastAPI and Gradio images from the `ingestion-api/` and `gradio-ui/` folders
- The first run downloads base images and Python packages. Expect **3 to 10 minutes**

### What success looks like

```
 ✔ Container rag-chroma          Healthy
 ✔ Container rag-ollama          Started
 ✔ Container rag-chroma-gateway  Started
 ✔ Container rag-chroma-init     Exited
 ✔ Container rag-api             Healthy
 ✔ Container rag-nginx           Started
 ✔ Container rag-ui              Started
```

Compose starts the services **in order**: the init container waits for Chroma's gateway, the API waits until the init container has finished successfully, and NGINX waits until the API is healthy.

---

## Step 5: Download the models

Ollama starts empty. Download the LLM and the embedding model:

```bash
bin/pull_models.sh
```

This downloads about **1.6 GB**. When it finishes you should see:

```
NAME                       ID              SIZE      MODIFIED
nomic-embed-text:latest    0a109f422b47    274 MB    ...
llama3.2:1b                baf6a787fdff    1.3 GB    ...
```

The models are stored in the `ollama_data` volume, so you only download them once.

---

## Step 6: Confirm everything is running

```bash
docker compose ps
```

### What success looks like

```
NAME                 STATUS                  PORTS
rag-api              Up (healthy)            8000/tcp
rag-chroma           Up (healthy)            8000/tcp
rag-chroma-gateway   Up                      80/tcp
rag-nginx            Up                      127.0.0.1:8088->8088/tcp
rag-ollama           Up                      11434/tcp
rag-ui               Up                      127.0.0.1:7860->7860/tcp
```

`rag-chroma-init` is not listed because it has already finished its job and exited.

Read the **PORTS** column carefully. It is the security map of the whole system:
- Only `rag-nginx` and `rag-ui` show `127.0.0.1:...->...`. They are the only services reachable from your computer
- Every other service shows a bare port like `8000/tcp`. That port is open **only** on a private Docker network

Next: [Compose Architecture and Network Segmentation](03-compose-architecture.md)

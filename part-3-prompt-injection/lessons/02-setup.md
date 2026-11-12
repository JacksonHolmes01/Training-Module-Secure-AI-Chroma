# Lesson 2: Setup

Part 3 is a copy of the Part 2 stack with the defenses added, all switched off. It reuses the models you downloaded in Part 2.

---

## Step 1: Stop Part 2

```bash
cd ~/Training-Module-Secure-AI-Chroma/part-2-rag
docker compose down
```

## Step 2: Move into Part 3

```bash
cd ~/Training-Module-Secure-AI-Chroma/part-3-prompt-injection
ls
```

```
README.md  attacks  bin  chroma  chroma-gateway  chroma-init  data  docker-compose.yml  gradio-ui  ingestion-api  lessons  nginx  secrets
```

Two things are new compared to Part 2:

| Item | Purpose |
|---|---|
| `attacks/` | The attack cases, the poisoned documents, and `run_attacks.py`, which runs every attack and scores the result |
| `ingestion-api/app/guards.py` | The four defenses |
| `bin/guard.sh` | Turns a defense on or off and restarts the API |

## Step 3: Secrets, build, and start

```bash
bin/setup_secrets.sh
docker compose up -d --build
```

`setup_secrets.sh` creates fresh secrets for Part 3 and makes sure the Part 2 model volume exists.

## Step 4: Models and sample data

```bash
bin/pull_models.sh
bin/ingest_sample.sh
```

If you finished Part 2, the models are already downloaded and `pull_models.sh` takes only a few seconds.

```
Total: 12  Success: 12  Failed: 0
```

## Step 5: Confirm every defense is off

```bash
bin/guard.sh status
```

```
GUARD_INPUT=false
GUARD_INGEST=false
GUARD_PROMPT=false
GUARD_OUTPUT=false
```

The API also reports which guards are on:

```bash
EDGE_API_KEY=$(grep -E '^EDGE_API_KEY=' .env | cut -d= -f2-)
curl -s -H "X-API-Key: $EDGE_API_KEY" http://localhost:8088/health | python3 -m json.tool | grep -A5 guards
```

```
    "guards": {
        "input": false,
        "ingest": false,
        "prompt": false,
        "output": false
    },
```

---

## One setting that makes experiments fair

```
OLLAMA_TEMPERATURE=0
```

**Temperature** controls randomness. At `0`, the model picks its most likely answer every time, so the same attack against the same setup gives the same result. That lets you compare "before" and "after" honestly.

Next: [Direct Attacks: Talking the Model Out of Its Rules](03-direct-attacks.md)

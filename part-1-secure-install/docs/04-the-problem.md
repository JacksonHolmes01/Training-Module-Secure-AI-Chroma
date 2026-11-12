# The Problem: Chroma With No Protection

Before you secure Chroma, you need to see exactly what you are protecting against.

In this lesson you will run Chroma the way many tutorials do, with "authentication" settings turned on, and then attack it.

> This lesson uses `docker-compose.insecure.yml`. You will delete it at the end of the lesson. Never use this setup for real data.

---

## Look at the insecure setup

Open `docker-compose.insecure.yml`:

```yaml
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      CHROMA_SERVER_AUTHN_PROVIDER: "chromadb.auth.token_authn.TokenAuthenticationServerProvider"
      CHROMA_SERVER_AUTHN_CREDENTIALS: "my-secret-token"
```

This looks secure. It names a token authentication provider and sets a secret token. Older versions of Chroma did use these settings.

---

## Start it

```bash
docker compose -f docker-compose.insecure.yml up -d
```

Wait about 5 seconds for Chroma to start.

---

## Attack 1: connect with no token (should fail, but does not)

```bash
curl -s http://localhost:8000/api/v2/heartbeat
```

### What you will see

```json
{"nanosecond heartbeat":1794461762335663689}
```

No token, and Chroma answered.

---

## Attack 2: create a collection with no token

A **collection** is Chroma's version of a table: a named group of documents and embeddings.

```bash
curl -s -X POST http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "planted-by-attacker"}' | head -c 120; echo
```

### What you will see

```
{"id":"6897838a-...","name":"planted-by-attacker", ...
```

An anonymous user just created data in your database.

---

## Attack 3: list everything

```bash
curl -s http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections \
  | python3 -c "import json,sys; print([c['name'] for c in json.load(sys.stdin)])"
```

```
['planted-by-attacker']
```

An attacker can see every collection name, then read every document in each one.

---

## Attack 4: delete it

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE \
  http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections/planted-by-attacker
```

```
200
```

Deleted, with no token.

---

## What went wrong

Chroma 1.x **ignores** the `CHROMA_SERVER_AUTHN_*` settings. It does not warn you. It does not refuse to start. It just runs wide open.

This is one of the most important lessons in security:

> **A setting that looks secure is not proof of security. Only a test that fails when it should is proof.**

Notice that every attack above succeeded. If you had only tested "does my app connect?", you would never have noticed.

The port was bound to `127.0.0.1`, so only programs on your own computer could do this. If it had been `"8000:8000"`, anyone on your network could.

---

## Clean up

```bash
docker compose -f docker-compose.insecure.yml down -v
```

---

## How the rest of this lab fixes it

Since Chroma cannot protect itself, you will:

1. Give Chroma **no published port at all**, so nothing outside Docker can reach it
2. Put a **gateway** in front that requires TLS and a valid token on every request
3. Give each token a **role** and a **tenant**, and allow only specific actions for each

Next: [Install Chroma Behind a Secure Gateway](05-compose-install.md)

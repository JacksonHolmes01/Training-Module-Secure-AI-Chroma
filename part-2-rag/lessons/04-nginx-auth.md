# Lesson 4: Edge Authentication with NGINX

NGINX is the **front door** of the system. Every request from outside must pass through it, and it rejects anything without the right API key before the request ever reaches Python code.

Open `nginx/templates/default.conf.template` as you read.

---

## Load your API key into the terminal

The key is in `.env`. Load it into a shell variable so you can use it in commands without pasting it:

```bash
EDGE_API_KEY=$(grep -E '^EDGE_API_KEY=' .env | cut -d= -f2-)
echo "${#EDGE_API_KEY} characters"
```

```
40 characters
```

This prints only the **length**, never the key itself. Avoid printing secrets to the screen: terminals get screenshotted, shared, and recorded.

> If you open a new terminal window, run the first line again.

---

## Test 1: the health check that needs no key

```bash
curl -i http://localhost:8088/proxy-health
```

```
HTTP/1.1 200 OK
...
ok
```

This endpoint exists so uptime monitors can check NGINX is alive. It returns only `ok` and reveals nothing about the API behind it.

---

## Test 2: no key (expected to fail)

```bash
curl -i http://localhost:8088/health
```

```
HTTP/1.1 401 Unauthorized
...
{"error":"missing X-API-Key header"}
```

---

## Test 3: wrong key (expected to fail)

```bash
curl -i -H "X-API-Key: not-the-real-key" http://localhost:8088/health
```

```
HTTP/1.1 403 Forbidden
...
{"error":"invalid API key"}
```

- **401** means "you did not say who you are"
- **403** means "I know what you sent, and it is not allowed"

---

## Test 4: correct key (expected to succeed)

```bash
curl -s -H "X-API-Key: $EDGE_API_KEY" http://localhost:8088/health
```

```json
{"ok":true,"chroma_ok":true,"tenant":"lab","uptime_s":120,"ingested":0,"chats":0,"errors":0}
```

`chroma_ok: true` means the API reached Chroma through its gateway with the **reader** token and found the collection.

---

## Test 5: rate limiting

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req zone=api_limit burst=20 nodelay;
limit_req_status 429;
```

Each client IP may send **10 requests per second**, with short bursts of up to 20. Extra requests get **HTTP 429 Too Many Requests**.

Send 40 requests at once and count the responses:

```bash
for i in $(seq 1 40); do
  curl -s -o /dev/null -w '%{http_code}\n' -H "X-API-Key: $EDGE_API_KEY" http://localhost:8088/health &
done | sort | uniq -c
wait
```

### What success looks like

```
  21 200
  19 429
```

Your exact numbers will vary. What matters is that **some** requests got `429`.

### Why this matters for AI systems
Every chat request runs an LLM, which is slow and expensive. Without a rate limit, one script can keep your model busy forever (denial of service) or run up a large bill on a paid API.

---

## Defense in depth: the API checks the key too

NGINX is not the only check. Open `ingestion-api/app/main.py` and find `require_api_key`:

```python
if not hmac.compare_digest(incoming, EDGE_API_KEY):
    raise HTTPException(status_code=403, detail="Invalid API key.")
```

If NGINX is ever misconfigured, or someone reaches the API from inside the Docker network, the API still refuses requests without the key.

`hmac.compare_digest` takes the **same amount of time** no matter where the keys differ. A normal `==` stops at the first wrong character, which lets an attacker measure response times and guess the key one character at a time. This is called a **timing attack**.

---

## Limits of a shared API key

One key for everyone is fine for a lab. In production you would:
- give each client its **own** key so you can revoke one without breaking the rest
- **rotate** keys on a schedule
- use real user identity (OAuth / single sign-on) for human users
- put TLS (`https://`) in front of NGINX so the key is never sent in plain text

Next: [Chroma Security: Tokens, Roles, and Tenants](05-chroma-security.md)

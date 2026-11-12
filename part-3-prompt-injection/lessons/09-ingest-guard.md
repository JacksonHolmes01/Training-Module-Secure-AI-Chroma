# Lesson 9: Defense 4: Ingest Screening and Cleanup

The prompt layer neutralizes poisoned documents every time they are retrieved. It is better not to store them at all.

The ingest guard scores every document **before it is stored**, using the same patterns with a lower threshold (2 instead of 3). Normal documents describe things; they do not give orders to an AI.

---

## Turn it on

```bash
bin/guard.sh ingest on
bin/guard.sh status
```

All four guards should now be `true`.

---

## The poison is already inside

Turning on the ingest guard does nothing about documents stored **before** it existed. Your three poisoned documents are still in the database from Lesson 4.

`/debug/scan` scores every stored document with the ingest rules:

```bash
EDGE_API_KEY=$(grep -E '^EDGE_API_KEY=' .env | cut -d= -f2-)
curl -s -H "X-API-Key: $EDGE_API_KEY" http://localhost:8088/debug/scan | python3 -m json.tool
```

### What you will see

```json
{
    "scanned": 15,
    "flagged": [
        {"id": "6f0c2d1e-...", "title": "Password Reset Procedure", "score": 8,
         "reasons": ["fake-role-marker", "injected-instruction-header", "conditional-trigger", "concealment"]},
        {"id": "a41b97c3-...", "title": "Reporting Phishing Emails", "score": 8,
         "reasons": ["fake-role-marker", "addressed-to-ai", "markdown-image"]},
        {"id": "0e5d8b72-...", "title": "Multi-Factor Authentication Guide", "score": 6,
         "reasons": ["fake-role-marker", "conditional-trigger", "invisible-characters"]}
    ]
}
```

All three poisoned documents are flagged. None of the 12 legitimate documents is. Chroma record IDs are random UUIDs, so yours will differ.

---

## Remove them, as the administrator

Save the flagged IDs and the collection ID in variables:

```bash
IDS=$(curl -s -H "X-API-Key: $EDGE_API_KEY" http://localhost:8088/debug/scan \
  | python3 -c "import json,sys; print(json.dumps([d['id'] for d in json.load(sys.stdin)['flagged']]))")
CID=$(bin/chroma_as.sh reader GET /api/v2/tenants/lab/databases/main/collections/documents | head -1 \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "$IDS"
```

### Can the API's own tokens delete them? (expected to fail)

The API holds the **writer** and **reader** tokens. Try deleting with the writer:

```bash
bin/chroma_as.sh writer POST /api/v2/tenants/lab/databases/main/collections/$CID/delete "{\"ids\": $IDS}"
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

That is by design. Neither the attacker's injected instructions nor a bug in the API can delete or rewrite stored knowledge, because the API simply holds no token that can.

### Delete with the admin token

Removing data is an administrator's job:

```bash
bin/chroma_as.sh admin POST /api/v2/tenants/lab/databases/main/collections/$CID/delete "{\"ids\": $IDS}"
```

```
{"deleted":3}
[HTTP 200]
```

Scan again:

```bash
curl -s -H "X-API-Key: $EDGE_API_KEY" http://localhost:8088/debug/scan
```

```
{"scanned":12,"flagged":[]}
```

---

## Try to plant them again (expected to fail)

```bash
python3 attacks/run_attacks.py --plant --only control
```

### What you will see

```
Planting poisoned documents (this is the attacker's step)...
  REJECTED  Password Reset Procedure  (fake-role-marker, injected-instruction-header, conditional-trigger, concealment)
  REJECTED  Reporting Phishing Emails  (fake-role-marker, addressed-to-ai, markdown-image)
  REJECTED  Multi-Factor Authentication Guide  (fake-role-marker, conditional-trigger, invisible-characters)
```

The invisible-character trick is caught twice over: the zero-width characters are removed before matching, and their presence is itself a signal.

---

## Check for false positives

A document that **talks about** prompt injection must still be accepted:

```bash
curl -s -X POST http://localhost:8088/ingest \
  -H "X-API-Key: $EDGE_API_KEY" -H "Content-Type: application/json" \
  -d '{"title": "Prompt Injection Explained", "text": "Prompt injection is an attack where text tries to override an AI model'"'"'s instructions. Defenses include input screening, output filtering, and least privilege."}'
```

```
{"status":"ok","id":"3b9f6e0a-...","tenant":"lab"}
```

Describing an attack is not the same as performing one. The patterns look for text **addressed to** an AI ("note to the assistant", "when the user asks"), not text **about** AI.

---

## Run the full suite one last time

```bash
python3 attacks/run_attacks.py
```

With the poison gone and all four guards on, every attack fails and the control question is answered, with one possible exception: `obfuscated-override` may still succeed on some runs. The next lesson explains why that one attack is different.

Next: [Operating the Defenses](10-operations.md)

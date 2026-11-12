# Lesson 7: Retrieval and Generation

This lesson walks through the three steps of a chat request, one at a time, using the debug endpoints.

Open `ingestion-api/app/rag.py` as you read.

```bash
EDGE_API_KEY=$(grep -E '^EDGE_API_KEY=' .env | cut -d= -f2-)
```

---

## Step 1: Retrieval

`retrieve_sources()` embeds the question, then sends the same kind of query you sent by hand in Part 1, using the **reader** token:

```python
await reader.post(f"{BASE}/collections/{id}/query", json={
    "query_embeddings": [embedding],
    "n_results": k,
    "include": ["documents", "metadatas", "distances"],
})
```

The question never reaches Chroma as text, only as an embedding inside a JSON body. There is no query language to inject into.

See retrieval on its own:

```bash
curl -s -G http://localhost:8088/debug/retrieve \
  -H "X-API-Key: $EDGE_API_KEY" \
  --data-urlencode "q=how should I store API keys and passwords" \
  | python3 -c "import json,sys; [print(s['distance'], s['title']) for s in json.load(sys.stdin)['sources']]"
```

### What success looks like

```
0.3064 Secrets Management Basics (.env and Rotation)
0.4158 Defense in Depth: Layered Controls
0.4221 Why Exposing Databases Directly Is Risky
...
```

The closest document is about secrets management, even though the question never used the word "secrets." That is **semantic search**: matching on meaning, not keywords.

Try your own questions and watch the ranking change.

---

## Step 2: Prompt building

`build_prompt()` puts the sources and the question into one block of text with rules for the model. See exactly what the model will receive:

```bash
curl -s -X POST http://localhost:8088/debug/prompt \
  -H "X-API-Key: $EDGE_API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "What is the CIA triad?"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['prompt'])"
```

### What success looks like

```
You are a retrieval-augmented assistant.
Rules:
1) Use ONLY the provided Sources for factual claims.
2) If the Sources are insufficient, say so plainly.
3) Cite sources inline like [1], [2].
4) Do not invent URLs, quotes, or document titles.

Response style: Write at an intermediate level with clear, practical guidance.

Sources:
[1] CIA Triad: Confidentiality, Integrity, Availability (https://example.org/cyber/cia-triad)
The CIA triad is a basic model for information security. ...

User question:
What is the CIA triad?

Answer:
```

Notice that the **rules**, the **sources**, and the **user's question** are all just text in one string. The model has no reliable way to tell which parts are instructions and which are data. Keep that in mind: it is the root cause of prompt injection, which you will exploit and defend against in Part 3.

> The debug endpoints reveal internal prompts and raw retrieval. They are switched on with `ENABLE_DEBUG_ENDPOINTS=true` in `.env` for this lab and should be **off** in any real deployment. When off, they return `404 Not found`.

---

## Step 3: Generation

`/chat` runs all three steps and returns the answer plus its sources:

```bash
curl -s -X POST http://localhost:8088/chat \
  -H "X-API-Key: $EDGE_API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "Why is exposing a database directly risky?"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['answer']); print(); print('Sources:', [s['title'] for s in d['sources']])"
```

### What success looks like

An answer that cites `[1]` and mentions points from the "Why Exposing Databases Directly Is Risky" article, such as attack surface and bypassed validation, followed by the list of sources.

The first chat after starting can take **30 to 90 seconds** while Ollama loads the model into memory. Later chats are much faster.

---

## Ask something the data does not cover

```bash
curl -s -X POST http://localhost:8088/chat \
  -H "X-API-Key: $EDGE_API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of Australia?"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['answer'])"
```

A well-grounded model should say the sources do not cover this. A 1-billion-parameter model will sometimes answer from memory anyway. That is a real limitation of small models: **prompt rules are requests, not guarantees.**

---

## Errors do not leak internals

If something fails inside the API, the client sees only:

```json
{"detail":"Internal error. Request id: 41f687b3-1a4d-40d6-9ebb-30a22b692acb"}
```

The full error (which may include table names, hostnames, or stack traces) goes to the server log, where an operator can find it by request id. You will practice this in [Lesson 9](09-operations.md).

Next: [The Gradio Chat UI](08-gradio-ui.md)

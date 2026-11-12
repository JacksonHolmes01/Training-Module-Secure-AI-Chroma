# Create Test Data and Run a Vector Search

In this step you will add documents as the writer, search them as the reader, and prove each token cannot exceed its role.

---

## What an embedding is (the short version)

An **embedding** is a list of numbers that represents the meaning of a piece of text. Texts with similar meanings get similar lists.

Real embedding models produce hundreds of numbers (768 in Part 2). To keep this lab readable, each document gets **3 numbers**, chosen by hand:

| Document | Embedding | Meaning of the numbers |
|---|---|---|
| Phishing basics | `[0.9, 0.1, 0.0]` | mostly "email threats" |
| Password policy | `[0.1, 0.9, 0.0]` | mostly "account security" |
| Incident response | `[0.0, 0.2, 0.9]` | mostly "after an attack" |

---

## Step 1: Get the collection's ID

Chroma's record endpoints (add, query, get) use the collection's **ID**, not its name. Look it up and save it in a variable:

```bash
CID=$(bin/collection_id.sh acme_reader acme documents)
echo "$CID"
```

```
40d0a423-ef6a-4e18-b201-c1065311387b
```

Your ID will be different. If you open a new terminal, run the first line again.

---

## Step 2: Add documents as the writer

```bash
bin/chroma.sh acme_writer POST /api/v2/tenants/acme/databases/main/collections/$CID/add '{
  "ids": ["1", "2", "3"],
  "embeddings": [[0.9, 0.1, 0.0], [0.1, 0.9, 0.0], [0.0, 0.2, 0.9]],
  "documents": ["How to spot phishing emails.", "Use long, unique passphrases.", "Steps to take after a breach."],
  "metadatas": [{"title": "Phishing basics"}, {"title": "Password policy"}, {"title": "Incident response"}]
}'
```

### What success looks like

```
{}
[HTTP 201]
```

`201 Created` means the records were stored.

---

## Step 3: Search as the reader

Imagine a user asks: *"Is this email a scam?"* An embedding model might turn that into `[0.8, 0.2, 0.0]`. Find the two closest documents:

```bash
bin/chroma.sh acme_reader POST /api/v2/tenants/acme/databases/main/collections/$CID/query '{
  "query_embeddings": [[0.8, 0.2, 0.0]],
  "n_results": 2,
  "include": ["documents", "metadatas", "distances"]
}'
```

### What success looks like

```json
{"ids":[["1","2"]], ... "documents":[["How to spot phishing emails.","Use long, unique passphrases."]], ...
 "distances":[[0.009007573,0.6518135]], ...}
[HTTP 200]
```

- `distances` uses **cosine distance**, because you created the collection with `"space": "cosine"`. Smaller means more similar
- "Phishing basics" (0.009) is almost identical in meaning to the question, so it comes first

This exact operation (embed the question, find the nearest documents) is the **retrieval** step of every RAG system you will build in Part 2.

---

## Step 4: Count the records

```bash
bin/chroma.sh acme_reader GET /api/v2/tenants/acme/databases/main/collections/$CID/count
```

```
3
[HTTP 200]
```

---

## Step 5: Prove the limits (expected to fail)

### The reader cannot add records

```bash
bin/chroma.sh acme_reader POST /api/v2/tenants/acme/databases/main/collections/$CID/add \
  '{"ids": ["99"], "embeddings": [[1, 0, 0]], "documents": ["Planted by a compromised chatbot"]}'
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

### The writer cannot delete records

```bash
bin/chroma.sh acme_writer POST /api/v2/tenants/acme/databases/main/collections/$CID/delete '{"ids": ["1"]}'
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

### The writer cannot rewrite existing records

`update` changes records that already exist. It is not on the writer's allowlist:

```bash
bin/chroma.sh acme_writer POST /api/v2/tenants/acme/databases/main/collections/$CID/update \
  '{"ids": ["1"], "documents": ["Phishing is not a real threat."]}'
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

### Chroma rejects a wrong-sized embedding

```bash
bin/chroma.sh acme_writer POST /api/v2/tenants/acme/databases/main/collections/$CID/add \
  '{"ids": ["4"], "embeddings": [[1, 0]], "documents": ["x"]}'
```

```
{"error":"InvalidArgumentError","message":"Collection expecting embedding with dimension of 3, got 2"}
[HTTP 400]
```

This one comes from **Chroma**, not the gateway: the request was allowed, but the data was invalid. It protects you from mixing embeddings from different models in one collection.

---

## Why this matters for AI security

In a RAG system, these documents become the "facts" an AI repeats. If an attacker could **update** record 1, the chatbot would start telling users that phishing is not a real threat, and nobody would notice the model was fine and the data was poisoned.

Giving the public-facing chatbot a **reader** token means even a fully compromised chatbot cannot change what it knows.

Next: [Tenant Isolation and Path Tricks](09-tenant-isolation.md)

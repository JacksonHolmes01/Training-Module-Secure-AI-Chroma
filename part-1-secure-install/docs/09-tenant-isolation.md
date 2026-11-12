# Tenant Isolation and Path Tricks

Many AI products serve many customers from one database. Each customer is a **tenant**. If Globex's chatbot can retrieve Acme's documents, Globex's users can receive Acme's private data in an AI answer.

Chroma has tenants (`/api/v2/tenants/acme/...`), but **Chroma does not enforce who may use them**. Without the gateway, any client can name any tenant in the URL. In this lesson you test the gateway's tenant lock, then try to sneak past it.

---

## How the gateway locks a token to its tenant

```nginx
"~^(reader|writer):([a-z0-9_-]+):POST:/api/v2/tenants/\2/databases/main/collections/[^/]+/(query|get)$" 1;
```

- `([a-z0-9_-]+)` captures the tenant name from the **role**, for example `acme` from `reader:acme`
- `\2` means "the exact same text again". The path must contain **that** tenant

So `reader:acme` can only ever match paths under `/tenants/acme/`. There is no rule a `globex` token can use to reach `acme`.

---

## Test 1: Globex can use its own tenant

```bash
bin/chroma.sh globex_reader GET /api/v2/tenants/globex/databases/main/collections
```

```
[]
[HTTP 200]
```

Globex has no collections yet, but the request is allowed.

## Test 2: Globex cannot read Acme (expected to fail)

```bash
bin/chroma.sh globex_reader GET /api/v2/tenants/acme/databases/main/collections
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

## Test 3: Globex cannot query Acme's collection, even with its ID (expected to fail)

Suppose the collection ID leaked. Try to search it directly:

```bash
CID=$(bin/collection_id.sh acme_reader acme documents)
bin/chroma.sh globex_reader POST /api/v2/tenants/acme/databases/main/collections/$CID/query \
  '{"query_embeddings": [[0.8, 0.2, 0.0]], "n_results": 2}'
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

Knowing an ID is not the same as having permission to use it.

## Test 4: other API shapes are not on the list (expected to fail)

Chroma also offers a shortcut endpoint that names a collection by `tenant:database:name` instead of using the tenant path:

```bash
bin/chroma.sh globex_reader GET /api/v2/collections/acme:main:documents
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

A blocklist that only protected `/tenants/...` paths would have missed this. The allowlist blocks it automatically because it was never listed.

---

## Path tricks

Attackers often try to make a path **look** allowed to the gateway while **meaning** something else to the server behind it.

The gateway refuses any request containing these patterns before it makes any other decision:

```nginx
if ($request_uri ~* "(\.\.|//|%2e|%2f|%5c)") {
    return 400 '{"error":"invalid path"}\n';
}
```

| Pattern | Trick |
|---|---|
| `..` | Climb out of an allowed folder: `/tenants/acme/../globex/` |
| `//` | Confuse path matching with empty segments |
| `%2e`, `%2f`, `%5c` | Percent-encoded `.`, `/`, and `\`, which some servers decode differently |

### Test 5: climbing out of the allowed tenant (expected to fail)

```bash
curl -s --path-as-is --cacert secrets/server.crt \
  -H "Authorization: Bearer $(cat secrets/acme_reader_token.txt)" \
  "https://localhost:8443/api/v2/tenants/acme/databases/main/collections/../../../../globex/databases/main/collections"
```

`--path-as-is` stops `curl` from cleaning up the `..` itself, so the gateway sees the raw attack.

```
{"error":"invalid path"}
```

### Test 6: encoded slashes (expected to fail)

```bash
curl -s --cacert secrets/server.crt \
  -H "Authorization: Bearer $(cat secrets/acme_reader_token.txt)" \
  "https://localhost:8443/api/v2/tenants/acme%2f..%2fglobex/databases/main/collections"
```

```
{"error":"invalid path"}
```

Legitimate Chroma paths never contain these patterns, so blocking them costs nothing.

---

## The limit of a gateway: what if someone gets inside?

The gateway only protects the **front door**. Chroma itself still trusts anyone who reaches it.

To see why the private network matters, run a throwaway container **on Chroma's network** (simulating an attacker who has compromised another container there):

```bash
docker run --rm --network secure-ai-chroma-part1_data curlimages/curl:8.11.1 -s -X POST \
  http://chroma:8000/api/v2/tenants/acme/databases/main/collections \
  -H "Content-Type: application/json" -d '{"name": "planted-from-inside"}' | head -c 80; echo
```

```
{"id":"e70a80d9-...","name":"planted-from-inside", ...
```

No token. It worked. Now remove it as admin:

```bash
bin/chroma.sh admin DELETE /api/v2/tenants/acme/databases/main/collections/planted-from-inside
```

### The takeaway
Because Chroma has no security of its own, **everything on its network is trusted**. That is why:
- in this lab, only the gateway shares Chroma's network
- in Part 2, Chroma gets its own isolated network that only one other service can join
- Part 4 hardens every container, so one compromised container cannot become a launch point

Next: [TLS: Encrypted and Verified](10-tls.md)

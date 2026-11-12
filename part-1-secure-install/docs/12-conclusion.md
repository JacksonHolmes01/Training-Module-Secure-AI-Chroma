# Conclusion

You took a database with **no security of its own** and made it secure, by controlling every way in. Then you proved each control by trying to break it.

---

## What you built

| Control | How it is enforced | How you tested it |
|---|---|---|
| No direct access | Chroma has no published port | Port 8000 closed |
| Encryption | Gateway accepts TLS 1.2+ only | Plain HTTP and TLS 1.1 refused |
| Server verification | Client trusts one specific certificate | curl refuses without `--cacert` |
| Authentication | Bearer token looked up in `tokens.map` | No token 401, wrong token 403 |
| Authorization | Allowlist per role, default deny | Reader cannot add, writer cannot delete or update |
| Tenant isolation | `\2` locks each token to its own tenant | Globex cannot list or query Acme |
| Path-trick defense | `..`, `//`, and encoded slashes rejected | Traversal and `%2f` attacks return 400 |
| Abuse limits | Rate limit, 1 MB body limit | 429 and 413 responses |
| Recoverability | Volume backup with `tar` | Restored copy has every record |

---

## Key ideas to remember

- **A setting that looks secure is not proof.** Chroma silently ignored the auth settings in Lesson 4
- **When a service cannot protect itself, control every path to it.** No ports, one gateway, one private network
- **Allowlists fail safe; blocklists fail open.** New endpoints are denied until you decide otherwise
- **Identity in the token, not the request.** The tenant comes from the token, so a URL cannot claim a tenant it does not own
- **Everything inside the network is trusted by Chroma.** Keep that network as small as possible

---

## Stop, restart, and reset

```bash
docker compose down        # stop, keep data
docker compose up -d       # start again
docker compose down -v     # delete ALL data (cannot be undone)
```

Your tokens and certificate in `secrets/` are kept either way. To create new tokens, delete the `secrets/*_token.txt` files, run `bin/setup_secrets.sh`, then run `docker compose restart gateway`.

---

## What comes next

In **Part 2**, Chroma becomes the knowledge store of a full RAG chatbot:
- a FastAPI service that embeds and stores documents using a **writer** token
- a chat endpoint that searches using a **reader** token
- a local LLM (Ollama) that writes answers from the retrieved documents
- separate Docker networks, so the public-facing services can never reach Chroma at all

Stop this stack before starting Part 2:

```bash
docker compose down
```

Next: [Part 2: Production-Grade RAG Infrastructure with Chroma](../../part-2-rag/README.md)

---

License: CC BY-SA 4.0. Jackson Holmes

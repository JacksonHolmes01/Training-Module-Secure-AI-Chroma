# Part 2: Production-Grade RAG Infrastructure with Chroma

In Part 1 you learned that Chroma has no security of its own, and you built a gateway to protect it. In Part 2 you put Chroma to work as the knowledge store of a full **Retrieval-Augmented Generation (RAG)** chatbot, without giving up any of that protection.

You will not just run a chatbot. You will understand how it is built, secured, and operated.

---

## What you will build

```
Browser ─► Gradio UI ─► NGINX ─────────► FastAPI ─► Chroma gateway ─► Chroma
           :7860        :8088             │          (tokens +        (isolated network,
           (localhost)  (API key,         │           allowlist)       no internet)
                         rate limit)      └─► Ollama (LLM + embeddings)
```

- **Chroma**: stores documents and embeddings. Lives alone on an isolated network
- **Chroma gateway**: the Part 1 gateway, now inside the system. Checks a token and an allowlist on every call to Chroma
- **chroma-init**: runs once with the admin token to create the tenant and collection, then exits
- **Ollama**: runs a local LLM (`llama3.2:1b`) and embedding model (`nomic-embed-text`)
- **FastAPI**: validates input, embeds text, retrieves sources, builds the prompt, calls the LLM
- **NGINX**: the only way into the API. Requires an API key and limits request rate
- **Gradio**: a browser chat interface

## Security controls carried over from Part 1

| Part 1 lesson | How Part 2 uses it |
|---|---|
| Chroma has no published port | Chroma is on an `internal` network that only its gateway joins. Even the API cannot reach it directly |
| Token authentication | The API holds a **writer** token for ingest and a **reader** token for chat |
| Allowlist authorization | The writer can only **add**; the reader can only **query** and **get**. Nobody but admin can delete |
| Tenant isolation | Both tokens are locked to the `lab` tenant. Requests cannot choose a tenant |
| Least privilege | The admin token is used once by `chroma-init` and never given to the running API |
| Localhost-only ports | Only NGINX and the UI are published, and only to `127.0.0.1` |

---

## Lessons (read in order)

1. [Overview](lessons/01-overview.md)
2. [Prerequisites and Setup](lessons/02-setup.md)
3. [Compose Architecture and Network Segmentation](lessons/03-compose-architecture.md)
4. [Edge Authentication with NGINX](lessons/04-nginx-auth.md)
5. [Chroma Security: Tokens, Roles, and Tenants](lessons/05-chroma-security.md)
6. [Ingestion and Input Validation](lessons/06-ingestion.md)
7. [Retrieval and Generation](lessons/07-rag-pipeline.md)
8. [The Gradio Chat UI](lessons/08-gradio-ui.md)
9. [Operations, Testing, and Troubleshooting](lessons/09-operations.md)
10. [Conclusion](lessons/10-conclusion.md)

---

## Quick start

```bash
bin/setup_secrets.sh
docker compose up -d --build
bin/pull_models.sh
bin/ingest_sample.sh
bin/smoke_test.sh
```

Then open http://localhost:7860

## Requirements
- Docker with Compose v2
- 8 GB RAM free for Docker (16 GB total recommended)
- About 6 GB free disk for images and models

---

License: code is MIT, lessons are CC BY-SA 4.0. See [README-LICENSE.md](../README-LICENSE.md).

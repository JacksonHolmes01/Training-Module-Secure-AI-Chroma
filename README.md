# Secure AI with Chroma: A Hands-On Training Series

Learn to build AI systems that are secure from the database up, using **Chroma**, one of the most popular vector databases for AI apps.

Chroma is easy to start and has **no security of its own**: no login, no permissions, no encryption. Older versions had authentication settings; **Chroma 1.x silently ignores them**. This series shows you that problem first-hand, then teaches you to build the protection Chroma is missing, from a single locked-down database to a complete, defended RAG chatbot.

It is written for beginners. Every step explains **what** to do, **why** it matters, and **how to prove** the security control actually works.

---

## The series

| Part | Folder | What you build | Status |
|---|---|---|---|
| 1 | [part-1-secure-install](part-1-secure-install/README.md) | Chroma behind a TLS gateway with per-role tokens, an allowlist, tenant isolation, path-trick defenses, and tested backups | Available |
| 2 | [part-2-rag](part-2-rag/README.md) | A full RAG chatbot (Chroma, Ollama, FastAPI, NGINX, Gradio) on three segmented networks, with read-only chat and write-only ingest tokens | Available |
| 3 | `part-3-prompt-injection` | Attack the chatbot with direct and indirect prompt injection, then defend it | Coming soon |
| 4 | `part-4-container-hardening` | Non-root containers, read-only filesystems, dropped capabilities, image scanning, internal TLS | Coming soon |
| 5 | `part-5-logging-red-team` | Audit logging, monitoring, and a structured red-team exercise | Coming soon |

Do the parts in order. Each one builds on the last.

---

## What you will learn

- Why "it has an auth setting" is not proof of security, and how to test it
- How to protect a service that cannot protect itself: no ports, one gateway, one private network
- How to write an **allowlist** that denies anything you did not explicitly permit
- How to lock each token to one tenant, so retrieval cannot leak across customers
- How to block path-traversal and encoding tricks at a gateway
- How to segment containers into trust zones so one compromise does not reach your data
- How to give the most exposed component (the chatbot) the least power

---

## Requirements

- macOS, Linux, or Windows with WSL 2
- Docker with Compose v2 ([Part 1, Lesson 2](part-1-secure-install/docs/02-prereqs-docker.md) shows how)
- 8 GB of memory available to Docker for Part 2 (16 GB total recommended)
- No prior Chroma, Docker, or AI experience

---

## Get started

```bash
git clone https://github.com/JacksonHolmes01/Training-Module-Secure-AI-Chroma.git
cd Training-Module-Secure-AI-Chroma/part-1-secure-install
```

Then open [Part 1](part-1-secure-install/README.md).

---

## Related training modules

The same Secure AI approach, with other vector databases:

- [Secure AI with pgvector](https://github.com/JacksonHolmes01/Training-Module-Secure-AI-pgvector)
- [Securely Install, Configure, and Test Weaviate](https://github.com/JacksonHolmes01/Training-Module-Securely-Install-Configure-And-Test-Weaviate)
- [Production-Grade RAG Infrastructure: Weaviate](https://github.com/JacksonHolmes01/Training-Module-Production-Grade-RAG-Infrastructure-Weaviate)
- [Production-Grade RAG Infrastructure: Qdrant](https://github.com/JacksonHolmes01/Training-Module-Production-Grade-RAG-Infrastructure-Qdrant)
- [Production-Grade RAG Infrastructure: Milvus](https://github.com/JacksonHolmes01/Training-Module-Production-Grade-RAG-Infrastructure-Milvus)

---

## License

Code and configuration are **MIT**. Lessons and documentation are **CC BY-SA 4.0**. See [README-LICENSE.md](README-LICENSE.md).

# Part 1: Securely Install, Configure, and Test Chroma

This lab teaches you how to securely deploy the **Chroma** vector database using Docker.

Chroma is popular because it is simple to start. That simplicity has a cost: **Chroma's open-source server has no authentication and no permissions.** Anyone who can reach it can read, change, or delete everything. In this lab you will prove that, then build the security Chroma is missing.

It is written for beginners and assumes no prior experience with Chroma, Docker, or vector databases.

---

## What you will learn
- Why "it has an auth setting" is not the same as "it is secure"
- How to keep a database off the network entirely
- How to put a TLS gateway in front of a service that has no security of its own
- How to issue separate tokens for admins, writers, and readers
- How to write an **allowlist** so anything not explicitly permitted is denied
- How to isolate tenants so one customer's token cannot touch another's data
- How to block path tricks that slip past naive access rules
- How to back up, restore, and verify a Chroma database

---

## Start here (read in order)

1. [Overview](docs/00-overview.md)
2. [How to Open a Terminal](docs/01-terminal-setup.md)
3. [Install & Verify Docker](docs/02-prereqs-docker.md)
4. [Project Setup](docs/03-project-setup.md)
5. [The Problem: Chroma With No Protection](docs/04-the-problem.md)
6. [Install Chroma Behind a Secure Gateway](docs/05-compose-install.md)
7. [Authentication (Tokens)](docs/06-authentication.md)
8. [Authorization (The Allowlist)](docs/07-authorization.md)
9. [Create Test Data and Run a Vector Search](docs/08-create-test-data.md)
10. [Tenant Isolation and Path Tricks](docs/09-tenant-isolation.md)
11. [TLS: Encrypted and Verified](docs/10-tls.md)
12. [Backups and Restore](docs/11-backups.md)
13. [Conclusion](docs/12-conclusion.md)

---

## Quick start (after prerequisites)

```bash
bin/setup_secrets.sh
docker compose up -d
bin/chroma.sh acme_reader GET /api/v2/heartbeat
```

Next up: [Part 2: Production-Grade RAG Infrastructure with Chroma](../part-2-rag/README.md)

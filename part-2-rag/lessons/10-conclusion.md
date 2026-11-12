# Lesson 10: Conclusion

You built a working RAG chatbot on Chroma, a database with no security of its own, and you secured every path to it.

---

## What you built

| Layer | Control | How you verified it |
|---|---|---|
| Network | Only NGINX and the UI published, and only on `127.0.0.1` | `nc` shows 8000 and 11434 closed |
| Network | Three networks; Chroma reachable only by its gateway, with no internet | Every container blocked from `chroma:8000` |
| Edge | API key required, rate limited, 1 MB body limit | 401, 403, 429, 413 responses |
| API | Second key check with constant-time compare | `require_api_key` in `main.py` |
| API | Strict input validation, unknown fields rejected | 422 for missing, oversized, and extra fields |
| API | Errors return a request id, not internals | Traced a failure through the logs |
| Chroma gateway | Writer can only add; reader can only query and get; no token gets nothing | 403 and 401 tests in Lesson 5 |
| Chroma gateway | Every token locked to the `lab` tenant; tenant set by server config | `tenant` field rejected with 422 |
| Setup | Admin token used once by `chroma-init`, never by the running API | API sees only reader and writer tokens |
| Secrets | Token files and `.env` are git-ignored, mounted read-only | `git status`; `ls /run/secrets` in the API |
| Supply chain | Every image version pinned | `docker-compose.yml` |

---

## Key ideas to remember

- **Every arrow is a trust boundary.** Browser to UI, UI to NGINX, NGINX to API, API to database: each one checks what it receives
- **Give the most exposed component the least power.** The chat path faces the most untrusted input, so it holds read-only credentials
- **Never let a request choose its own permissions.** The tenant comes from configuration, not from the request body
- **Test that bad things fail.** Your smoke test checks rejected requests, not just successful ones
- **Instructions and data share one prompt.** The model cannot reliably tell them apart. That is the opening for Part 3

---

## What comes next

- **Part 3: Prompt Injection Defense.** Plant malicious documents, trick the chatbot, then add input screening, output checks, and safer prompt design
- **Part 4: Container Hardening.** Non-root users, read-only filesystems, dropped capabilities, image scanning, and TLS between services
- **Part 5: Logging and Red-Teaming.** Audit logs, monitoring, and a structured red-team exercise with a written report

Leave this stack in place. Part 3 builds directly on it.

---

License: CC BY-SA 4.0. Jackson Holmes

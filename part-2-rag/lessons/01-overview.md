# Lesson 1: Overview: From a Secure Database to a Secure AI App

## What is a RAG system?

**Retrieval-Augmented Generation (RAG)** is a design pattern that gives a language model facts it was never trained on.

Instead of letting the model answer from memory alone:

1. A user asks a question
2. The system turns the question into an **embedding** (a list of numbers that represents its meaning)
3. The database finds the stored documents whose embeddings are closest
4. Those documents are inserted into a prompt as **sources**
5. The language model writes an answer grounded in those sources, with citations

This lets the chatbot answer from **your** documents and reduces made-up answers.

---

## How a request flows through this lab

```
1. You type a question in the browser (Gradio, port 7860)
2. Gradio sends it to NGINX with the API key (port 8088)
3. NGINX checks the key and the rate limit, then forwards to FastAPI
4. FastAPI asks Ollama to embed the question (768 numbers)
5. FastAPI searches Chroma with its **reader** token, through Chroma's own gateway, scoped to the lab tenant
6. FastAPI builds a prompt from the top sources
7. Ollama's LLM writes the answer
8. The answer and its sources travel back the same way
```

Every arrow in that flow is a **trust boundary**: a place where one component must not blindly trust another.

---

## Why so many services?

A RAG demo can be one Python script. A RAG **product** cannot, because each responsibility needs its own protection:

| Service | Its one job | What it protects against |
|---|---|---|
| NGINX | Decide who gets in | Anonymous access, request floods |
| FastAPI | Validate and orchestrate | Malformed input, tenant spoofing, leaked errors |
| Chroma gateway | Check tokens for Chroma | Chroma has no security of its own, so this is its lock |
| Chroma | Store and search | Isolated on its own network; reachable only through its gateway |
| Ollama | Generate text | Runs locally, so prompts and documents never leave your machine |
| Gradio | Talk to humans | Keeps the API key on the server, never in the browser |

If one layer fails, the next one still holds. This is called **defense in depth**.

---

## What is new compared to Part 1

- Embeddings now come from a real model with **768 dimensions** instead of 3 hand-picked numbers
- Chroma's tenant, database, and collection are created by a **one-time init container** that holds the admin token and then exits
- The containers are split across **three networks**, so even the API cannot reach Chroma directly: it must go through Chroma's gateway with a token
- You will use the system the way an attacker would: missing keys, wrong keys, extra fields, floods

---

## What comes after Part 2

This chatbot is the target for the rest of the series:
- **Part 3** attacks it with prompt injection and adds defenses
- **Part 4** hardens its containers
- **Part 5** adds logging and runs a red-team exercise

Next: [Prerequisites and Setup](02-setup.md)

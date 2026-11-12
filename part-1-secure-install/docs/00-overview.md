# Overview: Securely Deploying Chroma

## What this tutorial teaches
This tutorial teaches you how to securely install, configure, and test the Chroma vector database from scratch using Docker.

It assumes no prior experience and explains both how to perform each step and why it matters.

## What is Chroma?
**Chroma** is an open-source vector database built for AI applications. You give it documents and their **embeddings** (lists of numbers that represent meaning), and it finds the documents most similar to a question.

Chroma is designed to be easy: one container, one port, no setup. That is great for experiments and dangerous in production.

## The security problem
Chroma's open-source server has:
- **no login**: every request is accepted
- **no permissions**: any client can create, change, or delete anything
- **no encryption**: data travels as plain text

Older Chroma versions had authentication settings. **Chroma 1.x silently ignores them.** Many tutorials still show those settings, so people believe they are protected when they are not. You will prove this in Lesson 4.

## What you will build
A Chroma deployment where:
- Chroma itself has **no published port**, so nothing can reach it directly
- a **gateway** (NGINX) is the only way in, and it:
  - accepts only **encrypted** HTTPS connections
  - requires a **token** on every request
  - gives each token a **role** (admin, writer, or reader) and a **tenant**
  - allows only the actions on an explicit **allowlist**
  - blocks path tricks, oversized requests, and request floods
- data persists across restarts and can be backed up and restored

## Why this matters
In a RAG system, the documents in the vector database become the "facts" an AI repeats to users. Anyone who can write to it can change what the AI says. Anyone who can read it can steal everything it knows.

The pattern you learn here (**put security in front of a service that has none**) applies to many AI tools, not just Chroma.

## How to use this tutorial
Follow the pages in order. Copy and paste commands exactly. Do not skip validation steps: they are part of the learning.

Next: [How to Open a Terminal](01-terminal-setup.md)

# Project Setup

In this step you will download the lab and look at how it is organized.

---

## Download the lab

```bash
cd ~
git clone https://github.com/JacksonHolmes01/Training-Module-Secure-AI-Chroma.git
cd Training-Module-Secure-AI-Chroma/part-1-secure-install
```

Every command in Part 1 runs from this folder.

```bash
ls
```

### What success looks like

```
README.md  backups  bin  chroma  docker-compose.insecure.yml  docker-compose.yml  docs  gateway  secrets
```

---

## What each item is for

| Item | Purpose |
|---|---|
| `docker-compose.insecure.yml` | A deliberately unsafe setup, used only in Lesson 4 to show the problem |
| `docker-compose.yml` | The secure setup: Chroma plus its gateway |
| `chroma/config.yaml` | Chroma's own settings |
| `gateway/default.conf` | The gateway's security rules. Most of this lab is about this file |
| `secrets/` | Tokens and the TLS certificate. Never committed to git |
| `backups/` | Where backups are written |
| `bin/setup_secrets.sh` | Creates every token and the certificate |
| `bin/chroma.sh` | Sends a request through the gateway as a chosen token |
| `bin/collection_id.sh` | Looks up a collection's ID |

---

## Make the helper scripts runnable

```bash
chmod +x bin/*.sh
```

Git usually keeps this setting, but running it again is harmless and avoids `permission denied` errors.

Next: [The Problem: Chroma With No Protection](04-the-problem.md)

# Lesson 5: Layer 1: Non-Root Users

By default, the main process in most containers runs as **root** (user ID 0). Root inside a container is not the same as root on your computer. Docker isolates it. But it is still the most powerful user in that container, and every container escape vulnerability ever found has been far easier to exploit from root.

The fix is simple to describe: run each service as an ordinary user.

---

## Read the layer

Open `hardening/01-non-root.yml`.

```yaml
  chroma:
    user: "10001:10001"
    depends_on:
      chroma-perms:
        condition: service_completed_successfully
```

Chroma's image has no non-root user, and its `/data` folder is created owned by root. A non-root Chroma could not write its own database. So this layer adds a small one-time container:

```yaml
  chroma-perms:
    image: chromadb/chroma:1.5.9
    user: "0:0"
    entrypoint: ["sh", "-c", "chown -R 10001:10001 /data && echo 'chroma data folder now owned by 10001'"]
    cap_drop: [ALL]
    cap_add: [CHOWN]
    security_opt: ["no-new-privileges:true"]
    network_mode: none
```

It is the **only** thing in the whole lab that runs as root, and it is boxed in tightly: one capability (`CHOWN`, nothing else), no network at all, and it exits after one command. Chroma waits for it to finish, then starts as user 10001. This "fix permissions once, then run unprivileged" pattern is common for images that were not built with non-root users in mind.

The Chroma gateway switches to the unprivileged NGINX image, like the edge NGINX below. `chroma-init` already runs as a non-root user (`curl_user`) by default.

```yaml
  ingestion-api:
    user: "10001:10001"
  gradio-ui:
    user: "10001:10001"
    environment:
      HOME: /tmp
```

The two Python services run as user 10001, a number with no special meaning that does not exist on most host systems, so it maps to nobody important. Gradio expects a home folder to write a few small files to; `HOME: /tmp` gives it one.

```yaml
  ollama:
    user: "10001:10001"
    environment:
      HOME: /tmp
      OLLAMA_MODELS: /ollama/models
    volumes: !override
      - ollama_data:/ollama:ro
```

Ollama gets a bonus: the models are now mounted **read-only** (`:ro`). Nothing running inside the Ollama container can replace or alter a model file. A swapped model is a quiet and powerful supply chain attack, and this closes it. (This is why you downloaded the models in Lesson 2, before hardening.)

`!override` tells Docker Compose to **replace** the volume list from `docker-compose.yml` instead of adding to it.

```yaml
  nginx:
    image: nginxinc/nginx-unprivileged:1.28.2-alpine
```

The official NGINX image starts as root so it can use ports below 1024. NGINX publishes an `unprivileged` variant that never runs as root. This lab uses port 8088, so it needs no special port.

> **In your own Dockerfiles**, the better place for this is a `USER` line, so the image is safe no matter how it is run. A `user:` setting in compose works for images you do not control, like the four third-party images here.

---

## Apply it

```bash
bin/harden.sh 1
```

```
Active layers:
  docker-compose.yml
  hardening/01-non-root.yml
Applying (containers that changed are recreated)...
Stack is up.
```

Confirm every container's user:

```bash
for c in rag-api rag-chroma rag-chroma-gateway rag-nginx rag-ollama rag-ui; do
  printf "%-20s uid=%s\n" "$c" "$(docker exec $c id -u)"
done
```

```
rag-api              uid=10001
rag-chroma           uid=10001
rag-chroma-gateway   uid=101
rag-nginx            uid=101
rag-ollama           uid=10001
rag-ui               uid=10001
```

## Test it still works

```bash
bin/smoke_test.sh
```

All six checks should pass. Always test after a change.

## Audit

```bash
python3 bin/audit.py
```

`non-root` now passes for all six containers: **23 of 54 (42%)**.

## Attack again

```bash
bin/attacker_demo.sh
```

```
  run as root?                                 no   uid 10001
  plant a backdoor in the app's code?          no   cannot create /app/app/main.py: Permission denied
  drop a tool in /var/tmp and run it?          YES  tool ran
  run a program from /tmp?                     YES  tool ran
  install packages (apt-get)?                  no
  change file ownership (CAP_CHOWN)?           no   Operation not permitted
  open raw network sockets (CAP_NET_RAW)?      no   Operation not permitted
  read the API key from the environment?       YES  EDGE_API_KEY=wIyrm6...
```

One setting turned five `YES` answers into `no`. The application's files belong to root, so user 10001 cannot change them, cannot install software, and gets no privileges.

Three `YES` answers remain. Some folders, like `/var/tmp` and `/tmp`, are writable by **every** user by design, so an attacker can still bring and run their own tools. And the key is still in the environment. The next layers deal with these.

Next: [Layer 2: Capabilities, Escalation, and Limits](06-capabilities.md)

# Backups and Restore

Security is also about recovering when something goes wrong: an accidental delete, a bad upgrade, ransomware, or a poisoned dataset.

**A backup you have never restored is not a backup.** In this step you create one, restore it somewhere safe, and prove the data came back.

---

## What Chroma stores on disk

Chroma keeps everything in its `/data` folder, which lives in the `chroma_data` Docker volume:
- `chroma.sqlite3`: tenants, databases, collections, documents, and metadata
- one folder per collection index, holding the vector index files

A backup is a copy of that whole folder.

---

## Step 1: Stop Chroma for a consistent copy

Copying files while Chroma is writing to them can produce a backup that is half old and half new. Stop Chroma first:

```bash
docker compose stop chroma
```

The gateway keeps running, but requests will fail until Chroma is back. In production you would schedule backups for a quiet time.

---

## Step 2: Create the backup

This runs a temporary container that mounts the data volume **read-only** and writes a compressed archive into your `backups/` folder:

```bash
docker run --rm --entrypoint tar \
  -v secure-ai-chroma-part1_chroma_data:/data:ro \
  -v "$PWD/backups":/backups \
  chromadb/chroma:1.5.9 czf /backups/chroma-backup.tar.gz -C /data .
```

- `--entrypoint tar` uses the `tar` program that is already in the Chroma image, so you do not download anything new
- `:ro` means the backup process cannot change your data, even by accident

Start Chroma again right away:

```bash
docker compose start chroma
```

### Protect the backup

The backup contains **every document in every tenant**. Lock it down:

```bash
chmod 600 backups/chroma-backup.tar.gz
ls -l backups/
```

```
-rw-------  1 you  staff  11174 ... chroma-backup.tar.gz
```

---

## Step 3: Restore into a separate test volume

Never test a restore by overwriting your real data. Restore into a **new** volume:

```bash
docker volume create chroma_restore_test

docker run --rm --entrypoint tar \
  -v chroma_restore_test:/data \
  -v "$PWD/backups":/backups:ro \
  chromadb/chroma:1.5.9 xzf /backups/chroma-backup.tar.gz -C /data
```

Start a second Chroma on the restored data. It joins the private network and has **no published port**:

```bash
docker run -d --name chroma-restore-test \
  --network secure-ai-chroma-part1_data \
  -v chroma_restore_test:/data \
  -v "$PWD/chroma/config.yaml":/config.yaml:ro \
  chromadb/chroma:1.5.9 run /config.yaml
```

Wait about 5 seconds.

---

## Step 4: Verify the restore

Check the collections and the record count in the restored copy:

```bash
docker run --rm --network secure-ai-chroma-part1_data curlimages/curl:8.11.1 -s \
  http://chroma-restore-test:8000/api/v2/tenants/acme/databases/main/collections \
  | python3 -c "import json,sys; print([c['name'] for c in json.load(sys.stdin)])"
```

```
['documents']
```

```bash
RID=$(docker run --rm --network secure-ai-chroma-part1_data curlimages/curl:8.11.1 -s \
  http://chroma-restore-test:8000/api/v2/tenants/acme/databases/main/collections/documents \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
docker run --rm --network secure-ai-chroma-part1_data curlimages/curl:8.11.1 -s \
  http://chroma-restore-test:8000/api/v2/tenants/acme/databases/main/collections/$RID/count; echo
```

```
3
```

The tenant, the collection, and all 3 records came back.

> Notice what the backup does **not** contain: the gateway's tokens and rules. Those live in `secrets/` and `gateway/`. A full recovery plan backs up both, and stores the secrets somewhere just as protected as the secrets themselves.

---

## Step 5: Clean up the test copy

```bash
docker rm -f chroma-restore-test
docker volume rm chroma_restore_test
```

---

## Backup checklist for real systems

- Run backups on a **schedule**, not by hand
- Store copies **somewhere else**. A backup on the same disk dies with the disk
- **Encrypt** backups at rest
- **Restore-test** regularly
- Keep **older** backups too. If data is poisoned, the newest backup may already contain the poison

Next: [Conclusion](12-conclusion.md)

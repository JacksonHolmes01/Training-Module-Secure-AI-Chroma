# Authorization (The Allowlist)

**Authorization** answers:

> **Now that I know who you are, what are you allowed to do?**

Chroma has no permissions system, so the gateway enforces one with an **allowlist**: a list of the exact requests each role may make. **Anything not on the list is denied.**

---

## Allowlist versus blocklist

There are two ways to write access rules:

| Approach | Rule | What happens with a new or forgotten endpoint |
|---|---|---|
| **Blocklist** | "Deny delete and reset, allow everything else" | **Allowed.** You must remember to block every dangerous thing, forever |
| **Allowlist** | "Allow query and get, deny everything else" | **Denied.** Forgetting something makes it safer, not riskier |

Chroma's API has more than 30 endpoints, and new versions add more (`fork`, `search`, `functions/attach`, ...). A blocklist would silently allow each new one. An allowlist never does.

---

## Read the allowlist

In `gateway/default.conf`:

```nginx
map "$role:$request_method:$uri" $allowed {
    default 0;
    "~^admin:" 1;
    ...
}
```

The gateway builds one string from three pieces, for example:

```
reader:acme:POST:/api/v2/tenants/acme/databases/main/collections/40d0.../query
└── role ─┘ └method┘ └──────────────────────── path ─────────────────────────┘
```

Then it compares that string against each rule. If a rule matches, `$allowed` is `1`. If none match, it stays `0` and the request is refused.

### What each role may do

| Role | Allowed |
|---|---|
| `admin` | Everything |
| `reader` | Health checks; look up its own tenant, database, and collections; **query** and **get** records |
| `writer` | Everything a reader can do, plus **create collections** and **add / upsert** records |

Nobody except `admin` can **delete** records, **delete** collections, change collection settings, create tenants, or reset the database.

---

## Set up the tenants (as admin)

Chroma organizes data as **tenant → database → collection**. Create two tenants, `acme` and `globex`, each with a database named `main`:

```bash
bin/chroma.sh admin POST /api/v2/tenants '{"name": "acme"}'
bin/chroma.sh admin POST /api/v2/tenants '{"name": "globex"}'
bin/chroma.sh admin POST /api/v2/tenants/acme/databases '{"name": "main"}'
bin/chroma.sh admin POST /api/v2/tenants/globex/databases '{"name": "main"}'
```

### What success looks like
Four responses of:

```
{}
[HTTP 200]
```

---

## Test: a writer cannot create tenants (expected to fail)

```bash
bin/chroma.sh acme_writer POST /api/v2/tenants '{"name": "attacker-tenant"}'
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

## Test: a writer can create a collection (expected to succeed)

Create a collection that measures similarity with **cosine distance**:

```bash
bin/chroma.sh acme_writer POST /api/v2/tenants/acme/databases/main/collections \
  '{"name": "documents", "configuration": {"hnsw": {"space": "cosine"}}}' | tail -c 60
```

```
...,"tenant":"acme","database":"main","log_position":0,"version":0}
[HTTP 200]
```

## Test: a reader cannot create a collection (expected to fail)

```bash
bin/chroma.sh acme_reader POST /api/v2/tenants/acme/databases/main/collections '{"name": "evil"}'
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

## Test: a writer cannot delete the collection (expected to fail)

```bash
bin/chroma.sh acme_writer DELETE /api/v2/tenants/acme/databases/main/collections/documents
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

## Test: nobody but admin can reset the database (expected to fail)

```bash
bin/chroma.sh acme_writer POST /api/v2/reset
```

```
{"error":"this token is not allowed to do that"}
[HTTP 403]
```

Even if Chroma's own `allow_reset` setting were turned on by mistake, the gateway would still block this. That is **defense in depth**: two independent controls protecting the same thing.

---

## Where we are

| Action | admin | acme_writer | acme_reader |
|---|---|---|---|
| Create tenants | ✔ | ✘ | ✘ |
| Create collections | ✔ | ✔ | ✘ |
| Delete collections | ✔ | ✘ | ✘ |
| Reset | ✔ (blocked by Chroma config) | ✘ | ✘ |

Next you will add documents and test what readers and writers can do with them.

Next: [Create Test Data and Run a Vector Search](08-create-test-data.md)

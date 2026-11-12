# Lesson 9: Layer 5: Encrypted, Verified Traffic Between Services

In Part 1 your Chroma gateway used HTTPS on `127.0.0.1:8443`. In Part 2 the gateway moved **inside** the system, and the API talked to it over plain HTTP on the private `backend` network.

"It never leaves the Docker network" is a reasonable argument on one laptop. It is a weak one in production, where services run on different machines, networks are shared, and an attacker inside any container on the `backend` network (Ollama, for example) could read the API's Chroma tokens straight off the wire.

---

## See the current state

```bash
docker inspect rag-api --format '{{range .Config.Env}}{{println .}}{{end}}' | grep CHROMA_URL
```

```
CHROMA_URL=http://chroma-gateway:8000
```

Plain HTTP. Every request carries a reader or writer token in its `Authorization` header, unencrypted.

---

## Why only this hop?

```
API ──(backend network)──► Chroma gateway ──(data network)──► Chroma
       this lesson encrypts this               stays HTTP
```

Chroma's server cannot speak TLS at all, so the gateway **terminates** TLS: it decrypts, checks the token, and forwards to Chroma. The last hop stays plain HTTP, but it runs on the `data` network, which only the gateway and Chroma can join and which has no internet access (Part 2, Lesson 3). That is a deliberate, documented trade-off, not an oversight.

---

## The certificates

`bin/setup_secrets.sh` created a small **private certificate authority** (CA) and used it to sign a certificate for the gateway:

```bash
openssl verify -CAfile secrets/tls_ca.crt secrets/gateway.crt
openssl x509 -in secrets/gateway.crt -noout -text | grep -A1 "Alternative Name"
```

```
secrets/gateway.crt: OK
            X509v3 Subject Alternative Name:
                DNS:chroma-gateway
```

- The CA is what the API **trusts**. Anything the CA signed is accepted
- The gateway's certificate is valid for the name `chroma-gateway`, exactly the hostname the API connects to
- `secrets/tls_ca.key` (the CA's private key) is never mounted into any container. Whoever holds it can create certificates the API would trust

---

## Read the layer

Open `hardening/05-internal-tls.yml`.

### The gateway switches to a TLS config

```yaml
  chroma-gateway:
    volumes: !override
      - ./chroma-gateway/default-tls.conf:/etc/nginx/conf.d/default.conf:ro
      - ./secrets/tokens.map:/etc/nginx/secrets/tokens.map:ro
      - ./secrets/gateway.crt:/etc/nginx/secrets/gateway.crt:ro
      - ./secrets/gateway.key:/etc/nginx/secrets/gateway.key:ro
```

`chroma-gateway/default-tls.conf` has exactly the same token map and allowlist as before. Only the `listen` line changes:

```nginx
    listen 8443 ssl;
    ssl_certificate     /etc/nginx/secrets/gateway.crt;
    ssl_certificate_key /etc/nginx/secrets/gateway.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
```

There is no plain HTTP `listen` line left, so port 8000 simply stops existing.

### The API and the init container verify the gateway

```yaml
  ingestion-api:
    environment:
      CHROMA_URL: https://chroma-gateway:8443
      CHROMA_CA_CERT: /run/secrets/tls_ca_crt
```

In `ingestion-api/app/chroma_client.py`:

```python
    return httpx.AsyncClient(
        headers={"Authorization": f"Bearer {_token(name)}"},
        timeout=30.0,
        verify=CHROMA_CA_CERT or True,
    )
```

`verify=` points at the lab's CA, so the API checks that the certificate was signed by **that** CA and matches the name `chroma-gateway`. `chroma-init` does the same with `curl --cacert`.

Encryption without verification just means you have an encrypted conversation with whoever answered. Verification is what stops an attacker on the network from pretending to be the gateway and collecting tokens.

---

## Apply it

```bash
bin/harden.sh 5
bin/smoke_test.sh
```

## Verify the API now uses HTTPS

```bash
docker inspect rag-api --format '{{range .Config.Env}}{{println .}}{{end}}' | grep CHROMA_URL
docker logs rag-chroma-init 2>&1 | tail -1
```

```
CHROMA_URL=https://chroma-gateway:8443
chroma-init complete.
```

The init container reached Chroma over verified TLS.

## Verify plain HTTP is refused (expected to fail)

These commands run a throwaway container on the `backend` network, standing in for an attacker there:

```bash
NET=secure-ai-chroma-part4_backend
docker run --rm --network $NET curlimages/curl:8.11.1 -s -m 5 http://chroma-gateway:8443/api/v2/heartbeat \
  | grep -m1 -o "plain HTTP request was sent to HTTPS port"
docker run --rm --network $NET curlimages/curl:8.11.1 -sS -m 5 http://chroma-gateway:8000/api/v2/heartbeat 2>&1 | head -1
```

```
plain HTTP request was sent to HTTPS port
curl: (7) Failed to connect to chroma-gateway port 8000 after 0 ms: Could not connect to server
```

## Verify an unverified client is refused (expected to fail)

```bash
docker run --rm --network $NET curlimages/curl:8.11.1 -sS -m 5 https://chroma-gateway:8443/api/v2/heartbeat 2>&1 | head -1
```

```
curl: (60) SSL certificate problem: unable to get local issuer certificate
```

A client that does not trust the lab's CA cannot even complete the connection.

## The token helper follows along

`bin/chroma_as.sh` reads the API's `CHROMA_URL` and switches to HTTPS with the CA automatically:

```bash
bin/chroma_as.sh reader GET /api/v2/heartbeat
```

```
{"nanosecond heartbeat":1794505624573071412}
[HTTP 200]
```

## Audit

```bash
python3 bin/audit.py
```

The score does not change: TLS is not on the checklist, because the checklist looks at containers, not connections. Not everything important fits on one scorecard.

Next: [Layer 6: Scan and Pin Your Images](10-scan-and-pin.md)

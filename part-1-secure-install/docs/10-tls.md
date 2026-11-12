# TLS: Encrypted and Verified

Every request in this lab has used `https://`. In this lesson you look at what TLS gives you, and prove the gateway refuses anything less.

---

## Why TLS matters here

Without TLS, every request travels as plain text, including:
- the **token** in the `Authorization` header
- your **documents**
- every **search result**

Anyone who can watch the network (shared Wi-Fi, a compromised router, another container) could copy a token and become that user.

TLS does two jobs:
1. **Encryption**: nobody in between can read the traffic
2. **Verification**: the client checks the server's certificate, so it knows it is talking to the real server and not an impostor

---

## The certificate

`bin/setup_secrets.sh` created a **self-signed** certificate for `localhost`:

```bash
openssl x509 -in secrets/server.crt -noout -text | grep -E "Subject:|Not Before|Not After|DNS:" | sed 's/^ *//'
```

```
Not Before: Nov 12 06:42:46 2026 GMT
Not After : Nov 12 06:42:46 2027 GMT
Subject: CN=localhost
DNS:localhost, IP Address:127.0.0.1
```

- **Subject Alternative Name** lists the names this certificate is valid for. Clients check that the address they connected to (`localhost`) is on this list
- It expires in one year. Expired certificates are rejected

---

## Test 1: see the encrypted connection

```bash
curl -sv --cacert secrets/server.crt \
  -H "Authorization: Bearer $(cat secrets/acme_reader_token.txt)" \
  https://localhost:8443/api/v2/heartbeat 2>&1 | grep -E "SSL connection|subjectAltName|issuer"
```

### What success looks like

```
* SSL connection using TLSv1.3 / AEAD-AES256-GCM-SHA384
*  subjectAltName: host "localhost" matched cert's "localhost"
*  issuer: CN=localhost
```

(On Linux the cipher name may look slightly different, for example `TLS_AES_256_GCM_SHA384`.)

---

## Test 2: plain HTTP is refused (expected to fail)

```bash
curl -s http://localhost:8443/api/v2/heartbeat | grep -m1 -o "plain HTTP request was sent to HTTPS port"
```

```
plain HTTP request was sent to HTTPS port
```

The gateway only speaks TLS. There is no unencrypted way in.

---

## Test 3: an unverified certificate is refused (expected to fail)

`bin/chroma.sh` passes `--cacert secrets/server.crt`, which tells curl "trust this certificate." Without it:

```bash
curl -sS https://localhost:8443/api/v2/heartbeat 2>&1 | head -1
```

```
curl: (60) SSL certificate problem: self signed certificate
```

curl refuses to connect because it cannot verify who it is talking to. **That is correct behavior.**

> You will often see tutorials use `curl -k` (or `--insecure`) to make this error go away. Don't. `-k` keeps the encryption but turns off verification, so an impostor server would be accepted without warning. Trust the specific certificate instead, as this lab does.

---

## Test 4: old TLS versions are refused (expected to fail)

The gateway allows only modern versions:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Try to connect with TLS 1.1 at most:

```bash
curl -sS --cacert secrets/server.crt --tls-max 1.1 https://localhost:8443/api/v2/heartbeat 2>&1 | head -1
```

```
curl: (35) ... alert protocol version
```

TLS 1.0 and 1.1 have known weaknesses and are disabled.

---

## Self-signed versus real certificates

| | Self-signed (this lab) | Issued by a certificate authority |
|---|---|---|
| Encrypts traffic | Yes | Yes |
| Clients trust it automatically | No, each client needs a copy | Yes |
| Good for | Labs, internal services you control | Anything other people connect to |

In production you would use a certificate from your organization's certificate authority, or a free public one such as Let's Encrypt.

---

## What is not encrypted yet

Traffic **between the gateway and Chroma** (`http://chroma:8000`) is plain HTTP. That is acceptable here only because it never leaves the private Docker network on one machine. In Part 4 you will look at encrypting that hop too.

Next: [Backups and Restore](11-backups.md)

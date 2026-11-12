"""
chroma_client.py: Chroma access through the internal gateway.

Security design:
  - The API never talks to Chroma directly. It is not even on Chroma's
    network. Every call goes through chroma-gateway, which checks a token
    and an allowlist.
  - Two tokens, two clients:
      * WRITER token: used ONLY by /ingest. May add records. Nothing else.
      * READER token: used by /chat and retrieval. May query and get.
    If the chat path is abused, its token cannot change any data.
  - The admin token is never given to this service.
  - The tenant comes from server configuration (APP_TENANT), never from
    the HTTP request, and the gateway locks each token to that tenant.
"""

import os
import uuid
from typing import Any, Dict, List, Optional

import httpx

CHROMA_URL = os.getenv("CHROMA_URL", "http://chroma-gateway:8000").rstrip("/")
APP_TENANT = os.getenv("APP_TENANT", "lab")
EMBED_DIM  = int(os.getenv("EMBED_DIM", "768"))
COLLECTION = "documents"
BASE = f"{CHROMA_URL}/api/v2/tenants/{APP_TENANT}/databases/main"


def _token(name: str) -> str:
    with open(f"/run/secrets/{name}_token", "r", encoding="utf-8") as f:
        return f.read().strip()


def _client(name: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"Authorization": f"Bearer {_token(name)}"},
        timeout=30.0,
    )


writer: Optional[httpx.AsyncClient] = None
reader: Optional[httpx.AsyncClient] = None
_collection_id: Optional[str] = None


async def open_clients() -> None:
    global writer, reader
    writer = _client("writer")
    reader = _client("reader")


async def close_clients() -> None:
    for c in (writer, reader):
        if c is not None:
            await c.aclose()


async def collection_id() -> str:
    """Record endpoints need the collection's ID. Look it up once (as reader)."""
    global _collection_id
    if _collection_id is None:
        r = await reader.get(f"{BASE}/collections/{COLLECTION}")
        r.raise_for_status()
        _collection_id = r.json()["id"]
    return _collection_id


async def ready() -> bool:
    try:
        r = await reader.get(f"{CHROMA_URL}/api/v2/heartbeat")
        return r.status_code == 200 and bool(await collection_id())
    except Exception:
        return False


async def insert_doc(doc: Dict[str, Any], embedding: List[float]) -> Dict[str, Any]:
    if len(embedding) != EMBED_DIM:
        raise ValueError(f"Embedding has {len(embedding)} dimensions, expected {EMBED_DIM}.")
    doc_id = str(uuid.uuid4())
    # Chroma metadata values must be strings, numbers, or booleans
    meta = {
        "title": doc.get("title", ""),
        "url": doc.get("url", ""),
        "source": doc.get("source", ""),
        "published_date": doc.get("published_date", ""),
        "tags": ",".join(doc.get("tags", [])),
    }
    r = await writer.post(
        f"{BASE}/collections/{await collection_id()}/add",
        json={"ids": [doc_id], "embeddings": [embedding], "documents": [doc["text"]], "metadatas": [meta]},
    )
    r.raise_for_status()
    return {"id": doc_id, "tenant": APP_TENANT}


async def search(embedding: List[float], k: int) -> List[Dict[str, Any]]:
    r = await reader.post(
        f"{BASE}/collections/{await collection_id()}/query",
        json={
            "query_embeddings": [embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        },
    )
    r.raise_for_status()
    data = r.json()
    rows = []
    for i, doc_id in enumerate(data["ids"][0]):
        meta = (data["metadatas"][0][i] or {})
        rows.append({
            "id": doc_id,
            "title": meta.get("title", ""),
            "url": meta.get("url", ""),
            "source": meta.get("source", ""),
            "published_date": meta.get("published_date", ""),
            "tags": [t for t in (meta.get("tags") or "").split(",") if t],
            "content": data["documents"][0][i] or "",
            "distance": data["distances"][0][i],
        })
    return rows


async def count_docs() -> int:
    r = await reader.get(f"{BASE}/collections/{await collection_id()}/count")
    r.raise_for_status()
    return int(r.json())


async def all_docs(limit: int = 5000) -> List[Dict[str, Any]]:
    """Every stored document for this tenant (reader token). Used by /debug/scan."""
    r = await reader.post(
        f"{BASE}/collections/{await collection_id()}/get",
        json={"limit": limit, "include": ["documents", "metadatas"]},
    )
    r.raise_for_status()
    data = r.json()
    return [
        {"id": doc_id, "title": (data["metadatas"][i] or {}).get("title", ""), "content": data["documents"][i] or ""}
        for i, doc_id in enumerate(data["ids"])
    ]

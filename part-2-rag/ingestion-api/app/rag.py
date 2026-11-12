"""
rag.py: retrieval, prompt building, and generation.

  retrieve_sources()  question -> embedding -> Chroma similarity search (reader token)
  build_prompt()      question + sources -> grounded prompt
  ollama_generate()   prompt -> answer
"""

import os
from typing import Any, Dict, List, Literal, Optional

import httpx

from .chroma_client import search
from .embeddings import embed_texts

RAG_TOP_K            = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_SOURCE_CHARS = int(os.getenv("RAG_MAX_SOURCE_CHARS", "1200"))
OLLAMA_BASE_URL      = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL         = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

DetailLevel = Literal["basic", "standard", "advanced"]

_DETAIL = {
    "basic": "Write for a beginner. Keep it short (3-6 sentences) and explain jargon.",
    "standard": "Write at an intermediate level with clear, practical guidance.",
    "advanced": "Write for a technical audience. Be precise and include concrete steps.",
}


async def retrieve_sources(query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
    k = k or RAG_TOP_K
    qvec = (await embed_texts([query]))[0]
    rows = await search(qvec, k)
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "url": r["url"],
            "source": r["source"],
            "published_date": r["published_date"],
            "tags": list(r["tags"] or []),
            "distance": round(float(r["distance"]), 4),
            "snippet": (r["content"] or "")[:RAG_MAX_SOURCE_CHARS],
        }
        for r in rows
    ]


def build_prompt(
    user_message: str,
    sources: List[Dict[str, Any]],
    detail_level: Optional[DetailLevel] = None,
) -> str:
    level = detail_level or "standard"
    ctx = "\n\n".join(
        f"[{i}] {s['title']} ({s['url']})\n{s['snippet']}"
        for i, s in enumerate(sources, start=1)
    ) or "(no sources retrieved)"

    return (
        "You are a retrieval-augmented assistant.\n"
        "Rules:\n"
        "1) Use ONLY the provided Sources for factual claims.\n"
        "2) If the Sources are insufficient, say so plainly.\n"
        "3) Cite sources inline like [1], [2].\n"
        "4) Do not invent URLs, quotes, or document titles.\n\n"
        f"Response style: {_DETAIL[level]}\n\n"
        f"Sources:\n{ctx}\n\n"
        f"User question:\n{user_message}\n\n"
        "Answer:\n"
    )


async def ollama_generate(prompt: str) -> str:
    req = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=300.0) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=req)
        r.raise_for_status()
        return (r.json().get("response") or "").strip()

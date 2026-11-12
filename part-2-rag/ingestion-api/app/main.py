"""
main.py: FastAPI entry point for the Chroma RAG API.

Routes
  GET  /health           database + counters (no secrets)
  POST /ingest           validate -> embed -> add with the WRITER token
  POST /chat             retrieve with the READER token -> prompt -> generate
  GET  /debug/retrieve   retrieval only           (ENABLE_DEBUG_ENDPOINTS)
  POST /debug/prompt     show the exact prompt    (ENABLE_DEBUG_ENDPOINTS)

NGINX checks the API key at the edge. This service checks it again
(defense in depth) in case anything ever reaches it without going
through NGINX.
"""

import asyncio
import hmac
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request

from . import chroma_client as db
from .embeddings import embed_texts
from .rag import build_prompt, ollama_generate, retrieve_sources
from .schemas import ArticleIn, ChatIn

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("rag-api")

EDGE_API_KEY         = os.getenv("EDGE_API_KEY", "")
ENABLE_DEBUG         = os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true"
RETRIEVE_TIMEOUT_S   = float(os.getenv("RETRIEVE_TIMEOUT_S", "30"))
CHAT_TOTAL_TIMEOUT_S = float(os.getenv("CHAT_TOTAL_TIMEOUT_S", "300"))

START = time.time()
COUNTS = {"ingested": 0, "chats": 0, "errors": 0}


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.open_clients()
    yield
    await db.close_clients()


app = FastAPI(title="Secure AI Lab: Chroma RAG API", lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


def require_api_key(request: Request) -> None:
    if not EDGE_API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfigured.")
    incoming = request.headers.get("X-API-Key", "")
    if not incoming:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    # compare_digest takes the same time whether the first or last character
    # is wrong, so attackers cannot guess the key one character at a time.
    if not hmac.compare_digest(incoming, EDGE_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key.")


def require_debug() -> None:
    if not ENABLE_DEBUG:
        raise HTTPException(status_code=404, detail="Not found.")


def _fail(rid: str, where: str, e: Exception) -> HTTPException:
    COUNTS["errors"] += 1
    logger.exception("[%s] %s failed: %s", rid, where, type(e).__name__)
    # Never return internal error text to the client: it can leak table
    # names, file paths, or connection details. The request id lets an
    # operator find the full error in the logs.
    return HTTPException(status_code=500, detail=f"Internal error. Request id: {rid}")


@app.get("/health")
async def health():
    ok = await db.ready()
    return {
        "ok": ok,
        "chroma_ok": ok,
        "tenant": db.APP_TENANT,
        "uptime_s": int(time.time() - START),
        **COUNTS,
    }


@app.post("/ingest", dependencies=[Depends(require_api_key)])
async def ingest(article: ArticleIn, request: Request):
    rid = request.state.request_id
    try:
        vec = (await embed_texts([article.text]))[0]
        res = await db.insert_doc(article.model_dump(), vec)
        COUNTS["ingested"] += 1
        return {"status": "ok", **res}
    except Exception as e:
        raise _fail(rid, "/ingest", e)


@app.post("/chat", dependencies=[Depends(require_api_key)])
async def chat(payload: ChatIn, request: Request):
    rid = request.state.request_id

    async def _run():
        sources = await asyncio.wait_for(retrieve_sources(payload.message), RETRIEVE_TIMEOUT_S)
        prompt = build_prompt(payload.message, sources, payload.detail_level)
        answer = await ollama_generate(prompt)
        return {"answer": answer, "sources": sources}

    try:
        result = await asyncio.wait_for(_run(), CHAT_TOTAL_TIMEOUT_S)
        COUNTS["chats"] += 1
        return result
    except asyncio.TimeoutError:
        COUNTS["errors"] += 1
        raise HTTPException(status_code=504, detail=f"Chat timed out. Request id: {rid}")
    except Exception as e:
        raise _fail(rid, "/chat", e)


@app.get("/debug/retrieve", dependencies=[Depends(require_api_key), Depends(require_debug)])
async def debug_retrieve(request: Request, q: str = Query(min_length=2, max_length=2000)):
    try:
        return {"query": q, "sources": await retrieve_sources(q)}
    except Exception as e:
        raise _fail(request.state.request_id, "/debug/retrieve", e)


@app.post("/debug/prompt", dependencies=[Depends(require_api_key), Depends(require_debug)])
async def debug_prompt(payload: ChatIn, request: Request):
    try:
        sources = await retrieve_sources(payload.message)
        prompt = build_prompt(payload.message, sources, payload.detail_level)
        return {"prompt": prompt, "prompt_chars": len(prompt), "sources": sources}
    except Exception as e:
        raise _fail(request.state.request_id, "/debug/prompt", e)

"""
api/health.py — /api/health and /api/stats endpoints.
"""

import logging

from flask import Blueprint, jsonify

from config import MODEL_NAME, API_KEY
from rag_core.state import rag

log = logging.getLogger("studentrag.api.health")

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    llm_configured = bool(API_KEY and API_KEY.startswith("sk-"))
    total_chunks   = 0
    col_status     = "not ready"

    if rag.ready and rag.vectorstore:
        try:
            total_chunks = rag.vectorstore._collection.count()
            col_status   = "ready"
        except Exception:
            col_status = "error"
    elif rag.init_error:
        col_status = "error"
    else:
        col_status = "initialising"

    return jsonify({
        "status":            "ok" if rag.ready else "initialising",
        "llm_configured":    llm_configured,
        "collection_status": col_status,
        "total_chunks":      total_chunks,
        "model":             MODEL_NAME,
    })


@health_bp.route("/stats")

def stats():
    sources = []

    if rag.ready and rag.vectorstore:
        try:
            result = rag.vectorstore._collection.get(include=["metadatas"])
            seen   = set()
            for meta in (result.get("metadatas") or []):
                src = (meta or {}).get("source", "")
                if src and src not in seen:
                    seen.add(src)
                    sources.append(src)
        except Exception as exc:
            log.warning("stats error: %s", exc)

    return jsonify({"sources": sorted(sources)})

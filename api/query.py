import logging
import time

from flask import Blueprint, jsonify, request

from config import MODEL_NAME, PROMPT_TEMPLATE, SUMMARIZE_PROMPT_TEMPLATE
from rag_core.state import rag

log = logging.getLogger("studentrag.api.query")

query_bp = Blueprint("query", __name__)


#/api/query

@query_bp.route("/query", methods=["POST"])
def query():
    if not rag.ready:
        return jsonify({"detail": "RAG system is still initialising. Please wait."}), 503

    body      = request.get_json(force=True) or {}
    question  = (body.get("question") or "").strip()
    top_k     = int(body.get("top_k", 5))
    min_score = float(body.get("min_score", 0.1))

    if not question:
        return jsonify({"detail": "Question cannot be empty."}), 400

    t0 = time.time()

    #Retrieval
    try:
        results_with_scores = rag.vectorstore.similarity_search_with_relevance_scores(
            question, k=top_k
        )
    except Exception as exc:
        log.error("Retrieval error: %s", exc)
        return jsonify({"detail": f"Retrieval error: {exc}"}), 500

    # Apply score filter; fall back to raw results if nothing passes the threshold
    filtered = [(doc, score) for doc, score in results_with_scores if score >= min_score]
    if not filtered:
        filtered = results_with_scores[:top_k]

    docs_for_context = [doc for doc, _ in filtered]

    #Build context & prompt
    parts = []
    for doc in docs_for_context:
        source = doc.metadata.get("source", "unknown")
        page   = doc.metadata.get("page_num", "N/A")
        parts.append(f"[Source: {source} | Page {page}]\n{doc.page_content}")
    context_text = "\n\n".join(parts)

    prompt_text = PROMPT_TEMPLATE.format(context=context_text, question=question)

    #LLM call
    try:
        answer = rag.llm._call(prompt_text)
    except RuntimeError as exc:
        log.error("LLM error: %s", exc)
        return jsonify({"detail": str(exc)}), 502

    #Build response
    elapsed_ms   = round((time.time() - t0) * 1000)
    sources_seen = sorted({
        doc.metadata.get("source", "")
        for doc in docs_for_context
        if doc.metadata.get("source")
    })
    chunks_info  = [
        {
            "source":   doc.metadata.get("source", "unknown"),
            "page":     doc.metadata.get("page_num", "N/A"),
            "score":    round(float(score), 4),
            "text":     doc.page_content[:300],
            "chunk_id": f"{doc.metadata.get('source', '?')}-p{doc.metadata.get('page_num', '?')}",
        }
        for doc, score in filtered
    ]
    answer_found = "I don't have enough information" not in answer

    return jsonify({
        "answer":          answer,
        "answer_found":    answer_found,
        "sources":         sources_seen,
        "chunks":          chunks_info,
        "retrieved_count": len(filtered),
        "query_time_ms":   elapsed_ms,
        "model_used":      MODEL_NAME,
    })


#/api/summarize

@query_bp.route("/summarize", methods=["POST"])
def summarize():
    if not rag.ready:
        return jsonify({"detail": "RAG system is still initialising. Please wait."}), 503

    body   = request.get_json(force=True) or {}
    source = body.get("source")
    t0     = time.time()

    #Retrieval
    seed_query = "summary overview introduction main topics key points"
    try:
        if source:
            results = rag.vectorstore.similarity_search(
                seed_query, k=15, filter={"source": source}
            )
        else:
            results = rag.vectorstore.similarity_search(seed_query, k=20)
    except Exception as exc:
        log.error("Retrieval error: %s", exc)
        return jsonify({"detail": f"Retrieval error: {exc}"}), 500

    if not results:
        return jsonify({"detail": "No documents indexed yet. Upload a PDF first."}), 404

    #Build context & prompt
    context_parts = []
    for doc in results:
        s = doc.metadata.get("source", "unknown")
        p = doc.metadata.get("page_num", "N/A")
        context_parts.append(f"[Source: {s} | Page {p}]\n{doc.page_content}")
    context_text = "\n\n".join(context_parts)

    prompt_text = SUMMARIZE_PROMPT_TEMPLATE.format(context=context_text)

    #LLM call
    try:
        answer = rag.llm._call(prompt_text)
    except RuntimeError as exc:
        log.error("LLM error: %s", exc)
        return jsonify({"detail": str(exc)}), 502

    #Build response
    elapsed_ms   = round((time.time() - t0) * 1000)
    sources_seen = sorted({
        doc.metadata.get("source", "")
        for doc in results
        if doc.metadata.get("source")
    })

    return jsonify({
        "answer":          answer,
        "answer_found":    True,
        "sources":         sources_seen,
        "chunks":          [],
        "retrieved_count": len(results),
        "query_time_ms":   elapsed_ms,
        "model_used":      MODEL_NAME,
    })

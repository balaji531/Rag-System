import logging
import threading

from config import API_KEY, MODEL_NAME, MAX_TOKENS

log = logging.getLogger("studentrag.state")


class RAGState:
    
    def __init__(self) -> None:
        self.embeddings   = None
        self.vectorstore  = None
        self.llm          = None
        self.qa_chain     = None
        self.ready        = False
        self.init_error:  str | None = None
        self.lock         = threading.Lock()


#Singleton
rag = RAGState()


#Initialisation

def _initialise_rag() -> None:

    global rag

    from rag_core.llm        import OpenRouterLLM
    from rag_core.vectorstore import load_embeddings, build_vectorstore
    from rag_core.chain       import build_qa_chain

    try:
        rag.embeddings  = load_embeddings()
        rag.vectorstore = build_vectorstore(rag.embeddings)
        rag.llm         = OpenRouterLLM(api_key=API_KEY, model=MODEL_NAME, max_tokens=MAX_TOKENS)
        rag.qa_chain, _ = build_qa_chain(rag.vectorstore, rag.llm)
        rag.ready       = True
        log.info("RAG system initialised successfully ✓")
    except Exception as exc:
        rag.init_error = str(exc)
        log.error("RAG initialisation failed: %s", exc, exc_info=True)


def start_rag_init() -> None:
    thread = threading.Thread(target=_initialise_rag, name="rag-init", daemon=True)
    thread.start()
    log.info("RAG initialisation thread started")

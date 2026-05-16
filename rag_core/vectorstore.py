import logging
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL

log = logging.getLogger("studentrag.vectorstore")


def load_embeddings() -> HuggingFaceEmbeddings:
    log.info("Loading embedding model: %s", EMBEDDING_MODEL)
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def build_vectorstore(embeddings: HuggingFaceEmbeddings) -> Chroma:

    chroma_path = Path(CHROMA_DB_PATH)

    if chroma_path.exists():
        vs = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )
        count = vs._collection.count()
        log.info("Loaded existing vectorstore (%d chunks)", count)
    else:
        log.info("No existing vectorstore — creating empty collection")
        vs = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )

    return vs

import logging
from pathlib import Path
from typing import List

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP

log = logging.getLogger("studentrag.indexer")


#Text Helpers

def _clean_text(text: str) -> str:
    return text.encode("utf-8", errors="ignore").decode("utf-8")


#PDF Loading

def load_pdf(pdf_path: Path) -> List[Document]:
    docs   = []
    reader = PdfReader(str(pdf_path))
    total  = len(reader.pages)

    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            docs.append(Document(
                page_content=text,
                metadata={
                    "source":      pdf_path.name,
                    "page_num":    i + 1,
                    "total_pages": total,
                },
            ))

    log.info("Loaded %d pages from '%s' (total=%d)", len(docs), pdf_path.name, total)
    return docs


#Chunking

def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter   = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    raw_chunks = splitter.split_documents(docs)

    chunks = []
    for doc in raw_chunks:
        content = (doc.page_content or "").strip()
        if content:
            doc.page_content = _clean_text(content)
            chunks.append(doc)

    log.info("Produced %d clean chunks from %d raw chunks", len(chunks), len(raw_chunks))
    return chunks


#Indexing

def index_pdf(pdf_path: Path, rag_state) -> int:
    
    from rag_core.chain import build_qa_chain

    if not rag_state.ready:
        raise RuntimeError("RAG system not ready yet.")

    raw_docs = load_pdf(pdf_path)
    if not raw_docs:
        raise ValueError(f"No extractable text found in '{pdf_path.name}'.")

    chunks = chunk_documents(raw_docs)
    log.info("Indexing %d chunks from '%s'", len(chunks), pdf_path.name)

    with rag_state.lock:
        rag_state.vectorstore.add_documents(chunks)
        rag_state.qa_chain, _ = build_qa_chain(rag_state.vectorstore, rag_state.llm)

    log.info("Indexing complete for '%s' (%d chunks)", pdf_path.name, len(chunks))
    return len(chunks)

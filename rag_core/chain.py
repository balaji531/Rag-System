import logging
from typing import List, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from config import PROMPT_TEMPLATE, TOP_K

log = logging.getLogger("studentrag.chain")


def format_docs(docs: List[Document]) -> str:
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page   = doc.metadata.get("page_num", "N/A")
        parts.append(f"[Source: {source} | Page {page}]\n{doc.page_content}")
    return "\n\n".join(parts)


def build_qa_chain(vectorstore: Chroma, llm) -> Tuple:
    prompt    = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    log.info("QA chain built (top_k=%d)", TOP_K)
    return chain, retriever

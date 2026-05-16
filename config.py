import os
import logging
from pathlib import Path
from dotenv import load_dotenv

#Load environment variables from .env file
load_dotenv()

#Paths
BASE_DIR        = Path(__file__).parent
CHROMA_DB_PATH  = str(BASE_DIR / "chroma_db" / "rag_docs")
COLLECTION_NAME = "rag_docs"
UPLOAD_DIR      = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

#Embedding & Chunking
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE      = int(os.environ.get("CHUNK_SIZE", 1024))
CHUNK_OVERLAP   = int(os.environ.get("CHUNK_OVERLAP", 200))
TOP_K           = int(os.environ.get("TOP_K", 10))

#LLM / OpenRouter
API_KEY    = os.environ.get("OPENROUTER_API_KEY", "")
MODEL_NAME = os.environ.get("OPENROUTER_MODEL",  "openai/gpt-4o-mini")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 4096))

#Upload
ALLOWED_EXT = {".pdf"}

#Prompt
PROMPT_TEMPLATE = """\
You are an expert study assistant. Using ONLY the context provided below,
give a thorough and detailed answer to the question.

Your answer should:
- Be comprehensive, detailed, and well-structured.
- Use clear headings to organize the information if the answer covers multiple topics.
- Use bullet points or numbered lists for key points and lists of items.
- Ensure the output is clean and easy to read.
- If the answer is not in the context, say "I don't have enough information in the uploaded documents."

Context:
{context}

Question: {question}

Detailed Answer:"""

SUMMARIZE_PROMPT_TEMPLATE = """\
You are an expert academic summariser. Read the context below and produce a
comprehensive, structured summary of ALL the content.
- Use clear headings to organize different sections.
- Use bullet points for key findings and details.
- Be thorough and ensure the output is clean and well-formatted.

Context:
{context}

Comprehensive Summary:"""

#Logging
LOG_LEVEL  = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format=LOG_FORMAT)

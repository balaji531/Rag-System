# RAG System

This is a modular Retrieval-Augmented Generation (RAG) system built with Flask, Langchain, and ChromaDB. It allows users to upload PDF documents, index them, and ask questions based on the content of the documents.

## Features

- **Upload PDFs**: Simple endpoint to upload PDF documents.
- **RAG Engine**: Uses Langchain to chunk and embed documents using `sentence-transformers`.
- **Vector Database**: Uses ChromaDB to store document embeddings for fast retrieval.
- **LLM Integration**: Uses OpenRouter to generate answers based on the retrieved context from your documents.
- **Background Processing**: Handles document indexing asynchronously.
- **RESTful API**: Structured and modularized API routes.

## Prerequisites

- Python 3.9+
- [OpenRouter](https://openrouter.ai/) API Key

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd rag-system
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your OpenRouter API key:
   ```ini
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=openai/gpt-4o-mini
   # Optional configurations:
   # EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   # CHUNK_SIZE=1024
   # CHUNK_OVERLAP=200
   ```

5. **Run the Application:**
   ```bash
   python app.py
   ```
   The application will run on `http://127.0.0.1:5000/`.

## Architecture

The project is structured into logical modules:
- `/api`: Contains Flask blueprints for routing (health, upload, query).
- `/rag_core`: Contains the core logic for the RAG engine, vector database, and state management.
- `/frontend`: Contains static files and templates for the user interface.
- `app.py`: The entry point for the Flask application.
- `config.py`: Global configuration and environment variable management.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

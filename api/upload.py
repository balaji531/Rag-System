import logging
import threading
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from config import ALLOWED_EXT, UPLOAD_DIR
from rag_core.indexer import index_pdf
from rag_core.state   import rag

log = logging.getLogger("studentrag.api.upload")

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload-and-index", methods=["POST"])
def upload_and_index():
    if not rag.ready:
        return jsonify({"detail": "RAG system is still initialising. Please wait."}), 503

    #Validation
    if "file" not in request.files:
        return jsonify({"detail": "No file part in request."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"detail": "No file selected."}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"detail": f"Unsupported file type '{ext}'. Only PDF files are accepted."}), 400

    #Save
    filename  = secure_filename(file.filename)
    save_path = UPLOAD_DIR / filename
    file.save(str(save_path))
    log.info("Saved upload: %s (%d bytes)", save_path, save_path.stat().st_size)

    #Background Indexing
    def _bg_index() -> None:
        try:
            n = index_pdf(save_path, rag)
            log.info("Background indexing done: %d chunks from '%s'", n, filename)
        except Exception as exc:
            log.error("Background indexing failed for '%s': %s", filename, exc, exc_info=True)

    threading.Thread(target=_bg_index, name=f"index-{filename}", daemon=True).start()

    return jsonify({
        "message":  f"'{filename}' uploaded. Indexing started in the background.",
        "filename": filename,
    }), 202

from pathlib import Path

from flask import Flask, render_template
from flask_cors import CORS

from config import BASE_DIR, configure_logging
from rag_core.state import start_rag_init
from api.health import health_bp
from api.query  import query_bp
from api.upload import upload_bp


def create_app() -> Flask:
    configure_logging()

    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "frontend" / "static"),
        template_folder=str(BASE_DIR / "frontend" / "templates"),
    )
    CORS(app)

    #Register Blueprints
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(query_bp,  url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")

    # Frontend Route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Start RAG in background
    start_rag_init()

    return app

application = create_app() 
if __name__ == "__main__":
    application.run(
        debug=False,
        host="0.0.0.0",
        port=5000,
        use_reloader=False,   # reloader breaks background threads
    )
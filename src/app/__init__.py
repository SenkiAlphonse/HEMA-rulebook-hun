"""
HEMA Rulebook Search Web App - Flask Application Factory
"""

import logging

from flask import Flask

from app.config import (
    RULESET_LAST_UPDATED,
    RULESET_VERSION,
    get_aliases_path,
    get_prerendered_rulebook_path,
    get_rules_index_path,
    get_templates_dir,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Flask: Configured Flask application instance

    Raises:
        RuntimeError: If search engine files are not found or initialization fails
    """
    app = Flask(__name__, template_folder=str(get_templates_dir()))

    # Load search engine (shared across blueprints) with error handling
    try:
        from qa_tools.search_engine import AliasAwareSearch

        app.search_engines = {}
        for lang in ("hun", "eng"):
            app.search_engines[lang] = AliasAwareSearch(
                str(get_rules_index_path(lang=lang)),
                str(get_aliases_path(lang=lang)),
            )

        # Backward compatibility alias: default search engine is Hungarian
        app.search_engine = app.search_engines["hun"]
        logger.info("Search engines initialized successfully (hun + eng)")
    except FileNotFoundError as e:
        logger.error(f"Search engine initialization failed: {e}")
        logger.error(
            "Ensure that build.py has been run to generate rules_index_hun.json, rules_index_eng.json, and aliases"
        )
        raise RuntimeError("Search engine files not found. Run build.py first.") from e
    except Exception as e:
        logger.error(f"Unexpected error initializing search engine: {e}")
        raise RuntimeError("Failed to initialize search engine") from e

    for _lang in ("hun", "eng"):
        prerendered_rulebook = get_prerendered_rulebook_path(_lang)
        if not prerendered_rulebook.exists():
            logger.error(f"Pre-rendered rulebook is missing: {prerendered_rulebook}")
            logger.error(
                "Ensure that build.py has been run to generate dist/rulebook_hun.html and dist/rulebook_eng.html"
            )
            raise RuntimeError(f"Pre-rendered rulebook ({_lang}) is missing. Run build.py first.")

    # Configuration
    app.config["VARIANTS"] = ["VOR", "COMBAT", "AFTERBLOW"]
    app.config["WEAPONS"] = ["longsword", "rapier", "padded_weapons"]
    app.config["RULESET_VERSION"] = RULESET_VERSION
    app.config["RULESET_LAST_UPDATED"] = RULESET_LAST_UPDATED

    # Inject ruleset metadata into every template render
    @app.context_processor
    def _inject_ruleset_meta():
        return {
            "ruleset_version": RULESET_VERSION,
            "ruleset_last_updated": RULESET_LAST_UPDATED,
        }

    # Register blueprints
    from app.blueprints.rulebook import rulebook_bp
    from app.blueprints.search import search_bp

    app.register_blueprint(search_bp)
    app.register_blueprint(rulebook_bp)

    # Home page route
    from flask import redirect, render_template, request, url_for

    @app.route("/")
    def index():
        """Home page"""
        ui_lang = str(request.args.get("ui_lang", "")).strip().lower()
        rules_lang = str(request.args.get("rules_lang", "")).strip().lower()

        if ui_lang not in {"hun", "eng"} or rules_lang not in {"hun", "eng"}:
            return redirect(url_for("index", ui_lang="hun", rules_lang="hun"), code=302)

        return render_template(
            "index.html", variants=app.config["VARIANTS"], weapons=app.config["WEAPONS"]
        )

    @app.route("/hu")
    def index_hu():
        """Hungarian entry point with preselected UI + rules language."""
        return redirect(url_for("index", ui_lang="hun", rules_lang="hun"), code=302)

    @app.route("/en")
    def index_en():
        """English entry point with preselected UI + rules language."""
        return redirect(url_for("index", ui_lang="eng", rules_lang="eng"), code=302)

    @app.route("/healthz")
    def healthz():
        """Lightweight liveness endpoint for platform health checks."""
        return {"status": "ok"}, 200

    # Serve handout files (e.g., AFTERBLOW infographic)
    @app.route("/handouts/<filename>")
    def serve_handout(filename: str):
        """Serve handout HTML files from docs/handouts/ directory."""
        from pathlib import Path

        from flask import send_file

        handout_dir = Path(__file__).resolve().parent.parent.parent / "docs" / "handouts"
        # Resolve the full path and verify it stays inside handout_dir (prevents traversal)
        filepath = (handout_dir / filename).resolve()
        if not filepath.is_relative_to(handout_dir):
            return {"error": "Invalid filename"}, 403

        # Only serve .html files
        if filepath.suffix != ".html":
            return {"error": "Only HTML files are allowed"}, 403

        if not filepath.exists():
            return {"error": f"Handout not found: {filename}"}, 404

        return send_file(str(filepath), mimetype="text/html")

    # Error handlers — return JSON for API routes, HTML otherwise
    from flask import jsonify
    from werkzeug.exceptions import HTTPException

    def _wants_json() -> bool:
        if request.path.startswith("/api/"):
            return True
        accept = request.accept_mimetypes
        return accept.best == "application/json" and accept[accept.best] >= accept["text/html"]

    @app.errorhandler(404)
    def _not_found(err):
        if _wants_json():
            return jsonify(error="not_found", message=str(err.description)), 404
        # Browsers visiting an unknown URL: redirect to canonical home rather
        # than re-rendering the full app shell with a 404 status.
        return redirect(url_for("index", ui_lang="hun", rules_lang="hun"), code=302)

    @app.errorhandler(500)
    def _server_error(err):
        logger.exception("Unhandled server error")
        if _wants_json():
            return jsonify(error="server_error", message="Internal server error."), 500
        return "Internal Server Error", 500

    @app.errorhandler(HTTPException)
    def _http_error(err: HTTPException):
        if _wants_json():
            return jsonify(
                error=err.name.lower().replace(" ", "_"), message=err.description
            ), err.code or 500
        return err

    return app

"""
HEMA Rulebook Search Web App - Flask Application Factory
"""

import os
import logging
from flask import Flask
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration paths
from app.config import get_templates_dir, get_rules_index_path, get_aliases_path, get_prerendered_rulebook_path
from app.config import SUMMARY_CHUNK_SIZE, SUMMARY_SEARCH_MAX_RULES, SUMMARY_MAX_INPUT_CHARS


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
                str(get_rules_index_path(lang=lang, legacy_fallback=(lang == "hun"))),
                str(get_aliases_path(lang=lang))
            )

        # Backward compatibility alias: default search engine is Hungarian
        app.search_engine = app.search_engines["hun"]
        logger.info("Search engines initialized successfully (hun + eng)")
    except FileNotFoundError as e:
        logger.error(f"Search engine initialization failed: {e}")
        logger.error("Ensure that build.py has been run to generate rules_index_hun.json, rules_index_eng.json, and aliases")
        raise RuntimeError("Search engine files not found. Run build.py first.") from e
    except Exception as e:
        logger.error(f"Unexpected error initializing search engine: {e}")
        raise RuntimeError("Failed to initialize search engine") from e

    for _lang in ("hun", "eng"):
        prerendered_rulebook = get_prerendered_rulebook_path(_lang)
        if not prerendered_rulebook.exists():
            logger.error(f"Pre-rendered rulebook is missing: {prerendered_rulebook}")
            logger.error("Ensure that build.py has been run to generate dist/rulebook_hun.html and dist/rulebook_eng.html")
            raise RuntimeError(f"Pre-rendered rulebook ({_lang}) is missing. Run build.py first.")
    
    # Configuration
    app.config['VARIANTS'] = ["VOR", "COMBAT", "AFTERBLOW"]
    app.config['WEAPONS'] = ["longsword", "rapier", "padded_weapons"]
    app.config['SUMMARY_LANGUAGES'] = ["HU", "EN"]
    app.config['SUMMARY_RATE_LIMIT_WINDOW_SEC'] = int(
        os.environ.get("SUMMARY_RATE_LIMIT_WINDOW_SEC", 3600)
    )
    app.config['SUMMARY_RATE_LIMIT_MAX'] = int(
        os.environ.get("SUMMARY_RATE_LIMIT_MAX", 10)
    )
    app.config['SUMMARY_CHUNK_SIZE'] = int(
        os.environ.get("SUMMARY_CHUNK_SIZE", SUMMARY_CHUNK_SIZE)
    )
    app.config['SUMMARY_SEARCH_MAX_RULES'] = int(
        os.environ.get("SUMMARY_SEARCH_MAX_RULES", SUMMARY_SEARCH_MAX_RULES)
    )
    app.config['SUMMARY_MAX_INPUT_CHARS'] = int(
        os.environ.get("SUMMARY_MAX_INPUT_CHARS", SUMMARY_MAX_INPUT_CHARS)
    )
    app.config['SUMMARY_SHARED_TOKEN'] = os.environ.get("SUMMARY_SHARED_TOKEN", "").strip()
    app.config['GEMINI_API_KEY'] = os.environ.get("GEMINI_API_KEY", "").strip()
    app.config['GEMINI_MODEL'] = os.environ.get("GEMINI_MODEL", "").strip()
    
    # Rate limiting state - type hint for mypy
    app.summary_requests: Dict[str, int] = {}
    
    # Register blueprints
    from app.blueprints.search import search_bp
    from app.blueprints.ai_services import ai_bp
    from app.blueprints.rulebook import rulebook_bp
    
    app.register_blueprint(search_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(rulebook_bp)
    
    # Home page route
    from flask import render_template, redirect, url_for, request
    
    @app.route("/")
    def index():
        """Home page"""
        ui_lang = str(request.args.get("ui_lang", "")).strip().lower()
        rules_lang = str(request.args.get("rules_lang", "")).strip().lower()

        if ui_lang not in {"hun", "eng"} or rules_lang not in {"hun", "eng"}:
            return redirect(url_for("index", ui_lang="hun", rules_lang="hun"), code=302)

        return render_template(
            "index.html",
            variants=app.config['VARIANTS'],
            weapons=app.config['WEAPONS']
        )

    @app.route("/hu")
    def index_hu():
        """Hungarian entry point with preselected UI + rules language."""
        return redirect(url_for("index", ui_lang="hun", rules_lang="hun"), code=302)

    @app.route("/en")
    def index_en():
        """English entry point with preselected UI + rules language."""
        return redirect(url_for("index", ui_lang="eng", rules_lang="eng"), code=302)
    
    # Serve handout files (e.g., AFTERBLOW infographic)
    @app.route("/handouts/<filename>")
    def serve_handout(filename: str):
        """Serve handout HTML files from docs/handouts/ directory."""
        from flask import send_file
        from pathlib import Path
        
        # Security: only allow .html files and prevent directory traversal
        if not filename.endswith('.html'):
            return {"error": "Only HTML files are allowed"}, 403
        
        if '..' in filename or '/' in filename:
            return {"error": "Invalid filename"}, 403
        
        handout_dir = Path(__file__).resolve().parent.parent.parent / "docs" / "handouts"
        filepath = handout_dir / filename
        
        if not filepath.exists():
            return {"error": f"Handout not found: {filename}"}, 404
        
        return send_file(str(filepath), mimetype='text/html')
    
    return app

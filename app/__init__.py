"""
HEMA Rulebook Search Web App - Flask Application Factory
"""

import os
import logging
from pathlib import Path
from flask import Flask
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration paths
from app.config import get_templates_dir, get_rules_index_path, get_aliases_path
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
        app.search_engine = AliasAwareSearch(
            str(get_rules_index_path()),
            str(get_aliases_path())
        )
        logger.info("Search engine initialized successfully")
    except FileNotFoundError as e:
        logger.error(f"Search engine initialization failed: {e}")
        logger.error("Ensure that build.py has been run to generate rules_index.json and aliases.json")
        raise RuntimeError("Search engine files not found. Run build.py first.") from e
    except Exception as e:
        logger.error(f"Unexpected error initializing search engine: {e}")
        raise RuntimeError("Failed to initialize search engine") from e
    
    # Ensure rulebook HTML is pre-rendered on startup if it doesn't exist
    # This handles cases where the build command didn't run during deployment
    rulebook_path = Path(__file__).parent.parent / "dist" / "rulebook.html"
    if not rulebook_path.exists():
        try:
            logger.info("Pre-rendering rulebook HTML (dist/rulebook.html does not exist)...")
            from build import build_rulebook
            build_rulebook()
            logger.info(f"✓ Rulebook pre-rendered to {rulebook_path}")
        except Exception as e:
            logger.warning(f"Failed to pre-render rulebook on startup: {e}. HTML will be generated dynamically on requests.")
    
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
    from flask import render_template
    
    @app.route("/")
    def index():
        """Home page"""
        return render_template(
            "index.html",
            variants=app.config['VARIANTS'],
            weapons=app.config['WEAPONS']
        )
    
    return app

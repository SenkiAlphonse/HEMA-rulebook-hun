"""
HEMA Rulebook Search Web App - Flask Application Factory
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add qa-tools to path for imports
from app.config import get_qa_tools_dir, get_templates_dir, get_rules_index_path, get_aliases_path
qa_dir = get_qa_tools_dir()
sys.path.insert(0, str(qa_dir))


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, template_folder=str(get_templates_dir()))
    
    # Load search engine (shared across blueprints) with error handling
    try:
        from search_aliases import AliasAwareSearch
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
    
    # Configuration
    app.config['FORMATS'] = ["VOR", "COMBAT", "AFTERBLOW"]
    app.config['WEAPONS'] = ["longsword", "rapier", "padded_weapons"]
    app.config['SUMMARY_LANGUAGES'] = ["HU", "EN"]
    app.config['SUMMARY_RATE_LIMIT_WINDOW_SEC'] = int(
        os.environ.get("SUMMARY_RATE_LIMIT_WINDOW_SEC", 3600)
    )
    app.config['SUMMARY_RATE_LIMIT_MAX'] = int(
        os.environ.get("SUMMARY_RATE_LIMIT_MAX", 10)
    )
    app.config['SUMMARY_SHARED_TOKEN'] = os.environ.get("SUMMARY_SHARED_TOKEN", "").strip()
    app.config['GEMINI_API_KEY'] = os.environ.get("GEMINI_API_KEY", "").strip()
    app.config['GEMINI_MODEL'] = os.environ.get("GEMINI_MODEL", "").strip()
    
    # Rate limiting state
    app.summary_requests = {}
    
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
            formats=app.config['FORMATS'],
            weapons=app.config['WEAPONS']
        )
    
    return app

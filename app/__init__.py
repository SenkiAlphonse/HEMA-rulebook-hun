"""
HEMA Rulebook Search Web App - Flask Application Factory
"""

import os
import sys
from pathlib import Path
from flask import Flask

# Add qa-tools to path for imports
qa_dir = Path(__file__).parent.parent / "qa-tools"
sys.path.insert(0, str(qa_dir))


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / "templates"))
    
    # Load search engine (shared across blueprints)
    from search_aliases import AliasAwareSearch
    app.search_engine = AliasAwareSearch(
        str(qa_dir / "rules_index.json"),
        str(qa_dir / "aliases.json")
    )
    
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

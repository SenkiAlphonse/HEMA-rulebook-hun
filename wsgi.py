"""HEMA Rulebook Search Web App.

Entry point for Flask application.

Repo uses a `src/` layout; this file bootstraps `src/` onto sys.path so
`python wsgi.py` works without requiring an editable install.
"""

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))

from app import create_app

app = create_app()


if __name__ == "__main__":
    # Get port from environment or use 5000 for local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

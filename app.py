"""
HEMA Rulebook Search Web App
Entry point for Flask application
"""

import os
from app import create_app

app = create_app()


if __name__ == "__main__":
    # Get port from environment or use 5000 for local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

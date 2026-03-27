"""Flask application factory."""
from __future__ import annotations

import logging
import os

from flask import Flask

from backend.config import get_config


def create_app(env: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    config = get_config(env)

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "static"),
        static_url_path="/static",
    )
    app.config.from_object(config)

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from backend.routes.api import api
    from backend.routes.pages import pages

    app.register_blueprint(api)
    app.register_blueprint(pages)

    return app

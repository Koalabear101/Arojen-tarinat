"""Production WSGI entry point for Gunicorn."""
from backend.app import create_app

app = create_app("production")

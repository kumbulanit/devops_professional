"""Gunicorn entry point: `gunicorn --bind 0.0.0.0:8080 wsgi:app`."""
from src.app import app  # noqa: F401

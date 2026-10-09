"""
dependencies.py — FastAPI dependency injection helpers.
Import these in route handlers with Depends().
"""

from fastapi import Header, HTTPException
from app.integrations.supabase_client import get_supabase


def get_db():
    """Yields the Supabase client. Expand to a proper session when needed."""
    return get_supabase()


def require_api_key(x_api_key: str = Header(default="")):
    """
    Placeholder auth dependency. Not enforced yet — extend in a later step.
    Replace with real JWT / API-key validation before production.
    """
    # TODO: validate x_api_key against allowed keys
    pass

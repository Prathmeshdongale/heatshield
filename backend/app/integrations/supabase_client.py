"""
supabase_client.py — initialises a shared Supabase client.

SECURITY RULES:
  - Uses the publishable/anon key ONLY. The service-role key must never
    appear here or in any file that is committed to Git.
  - The frontend must never call Supabase directly; all DB access goes
    through this backend.

AVAILABILITY:
  - If SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY are empty (e.g. local dev
    without a DB), get_supabase() returns None.
  - Repositories check for None and fall back to demo data from mock_data.py.
  - is_db_available() lets callers decide gracefully.
"""

import logging
from supabase import create_client, Client
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Client | None = None
_init_attempted: bool = False


def get_supabase() -> Client | None:
    """
    Return a module-level singleton Supabase client, or None if credentials
    are not configured. Logs a warning on first failed initialisation.
    """
    global _client, _init_attempted
    if _init_attempted:
        return _client

    _init_attempted = True
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_publishable_key:
        logger.warning(
            "Supabase credentials not configured — "
            "SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY is empty. "
            "All data will be served from demo mock data."
        )
        return None

    try:
        _client = create_client(settings.supabase_url, settings.supabase_publishable_key)
        logger.info("Supabase client initialised for %s", settings.supabase_url)
    except Exception as exc:
        logger.error("Failed to initialise Supabase client: %s", exc)
        _client = None

    return _client


def is_db_available() -> bool:
    """Returns True if a Supabase client was successfully initialised."""
    return get_supabase() is not None


def reset_client() -> None:
    """Reset singleton — used in tests to force re-initialisation."""
    global _client, _init_attempted
    _client = None
    _init_attempted = False

"""
supabase_client.py — Supabase REST client using httpx directly.

Uses the publishable key (sb_publishable_...) which is the modern Supabase
API key format replacing the legacy anon JWT.

The client exposes a simple query interface:
    client = get_supabase()
    if client:
        rows = client.select("hospitals", columns="*", limit=10)
        client.insert("hospitals", [{"hospital_id": "H001", ...}])

SECURITY:
  - Publishable key only — safe for backend use with RLS.
  - Service-role / secret key must never appear in this file.
  - Frontend never calls Supabase directly.
"""

import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

_client = None
_init_attempted = False


class SupabaseHTTPClient:
    """Minimal Supabase REST client using httpx + publishable key."""

    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey":        key,
            "Authorization": f"Bearer {key}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }

    # ── SELECT ──────────────────────────────────────────────────────────────

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict | None = None,
        order: str | None = None,
        desc: bool = False,
        limit: int | None = None,
        single: bool = False,
    ) -> list[dict] | dict | None:
        """
        SELECT from a table.
        filters: {"column": "value"} → appended as ?column=eq.value
        order:   column name to ORDER BY
        Returns a list of dicts (or a single dict if single=True).
        """
        params = {"select": columns}

        if filters:
            for col, val in filters.items():
                params[col] = f"eq.{val}"

        if order:
            params["order"] = f"{order}.{'desc' if desc else 'asc'}"

        if limit:
            params["limit"] = limit

        headers = dict(self.headers)
        if single:
            headers["Accept"] = "application/vnd.pgrst.object+json"

        try:
            r = httpx.get(
                f"{self.base}/{table}",
                headers=headers,
                params=params,
                timeout=10,
            )
            # PostgREST returns 406 when single=True and no rows match
            if single and r.status_code == 406:
                return None
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Supabase SELECT %s failed: %s %s", table, exc.response.status_code, exc.response.text[:200])
            raise
        except Exception as exc:
            logger.error("Supabase SELECT %s error: %s", table, exc)
            raise

    # ── INSERT ───────────────────────────────────────────────────────────────

    def insert(self, table: str, rows: list[dict], upsert: bool = False) -> bool:
        """INSERT (or upsert) rows into a table. Returns True on success."""
        prefer = "resolution=ignore-duplicates,return=minimal"
        if upsert:
            prefer = "resolution=merge-duplicates,return=minimal"

        try:
            r = httpx.post(
                f"{self.base}/{table}",
                headers={**self.headers, "Prefer": prefer},
                json=rows,
                timeout=15,
            )
            r.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logger.debug("Supabase INSERT %s blocked by RLS (publishable key is read-only)", table)
            else:
                logger.error("Supabase INSERT %s failed: %s %s", table, exc.response.status_code, exc.response.text[:200])
            return False
        except Exception as exc:
            logger.error("Supabase INSERT %s error: %s", table, exc)
            return False

    def ping(self) -> bool:
        """Return True if the REST endpoint is reachable AND at least the hospitals table exists."""
        try:
            r = httpx.get(
                f"{self.base}/hospitals",
                headers=self.headers,
                params={"select": "hospital_id", "limit": "1"},
                timeout=5,
            )
            # 200 = table exists and queryable; 404 = table missing (PGRST205)
            return r.status_code == 200
        except Exception:
            return False


def get_supabase() -> SupabaseHTTPClient | None:
    """Return singleton client or None if not configured."""
    global _client, _init_attempted
    if _init_attempted:
        return _client

    _init_attempted = True
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_publishable_key:
        logger.warning(
            "Supabase credentials not configured — serving demo data."
        )
        return None

    try:
        _client = SupabaseHTTPClient(settings.supabase_url, settings.supabase_publishable_key)
        logger.info("Supabase HTTP client ready for %s", settings.supabase_url)
    except Exception as exc:
        logger.error("Failed to create Supabase client: %s", exc)
        _client = None

    return _client


def is_db_available() -> bool:
    c = get_supabase()
    if c is None:
        return False
    return c.ping()


def reset_client() -> None:
    """Reset — used in tests."""
    global _client, _init_attempted
    _client = None
    _init_attempted = False

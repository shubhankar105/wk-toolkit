"""Async httpx client for the WebKit Bugzilla REST API."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0

# Patterns for extracting bug IDs from free-form text.
_BUG_PATTERNS: Sequence[re.Pattern[str]] = (
    # "Bug 12345" / "bug 12345"
    re.compile(r"\b[Bb]ug\s+(\d+)"),
    # "https://bugs.webkit.org/show_bug.cgi?id=12345"
    re.compile(r"bugs\.webkit\.org/show_bug\.cgi\?id=(\d+)"),
    # "webkit.org/b/12345"
    re.compile(r"webkit\.org/b/(\d+)"),
)


class BugzillaClient:
    """Async client for the WebKit Bugzilla REST API.

    Parameters
    ----------
    base_url:
        Root URL of the Bugzilla instance.
    api_key:
        Optional Bugzilla API key for authenticated requests.
    """

    def __init__(
        self,
        base_url: str = "https://bugs.webkit.org",
        api_key: str = "",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: Dict[str, str] = {"Accept": "application/json"}
            if self.api_key:
                headers["X-BUGZILLA-API-KEY"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=_TIMEOUT,
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = await self._get_client()
        try:
            resp = await client.request(
                method, path, json=json, params=params
            )
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Bugzilla %s %s → %s: %s",
                method,
                path,
                exc.response.status_code,
                exc.response.text[:200],
            )
            raise
        except httpx.HTTPError as exc:
            logger.error("Bugzilla request failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_bug(self, bug_id: int) -> Dict[str, Any]:
        """Fetch a single bug by *bug_id*.  Returns ``{}`` on error."""
        try:
            resp = await self._request("GET", f"/rest/bug/{bug_id}")
            data = resp.json()
            bugs = data.get("bugs", [])
            return bugs[0] if bugs else data
        except httpx.HTTPError:
            return {}

    async def search_bugs(
        self,
        product: str = "WebKit",
        component: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search bugs with optional filters."""
        params: Dict[str, Any] = {"product": product, "limit": limit}
        if component:
            params["component"] = component
        if status:
            params["status"] = status
        try:
            resp = await self._request("GET", "/rest/bug", params=params)
            return resp.json().get("bugs", [])
        except httpx.HTTPError:
            return []

    async def create_bug(
        self,
        product: str,
        component: str,
        summary: str,
        description: str = "",
    ) -> int:
        """Create a new bug.  Returns the new bug ID, or ``0`` on error."""
        payload: Dict[str, Any] = {
            "product": product,
            "component": component,
            "summary": summary,
            "version": "WebKit Nightly Build",
        }
        if description:
            payload["description"] = description
        try:
            resp = await self._request("POST", "/rest/bug", json=payload)
            return resp.json().get("id", 0)
        except httpx.HTTPError:
            return 0

    async def add_comment(
        self, bug_id: int, comment: str
    ) -> Dict[str, Any]:
        """Add a comment to *bug_id*."""
        try:
            resp = await self._request(
                "POST",
                f"/rest/bug/{bug_id}/comment",
                json={"comment": comment},
            )
            return resp.json()
        except httpx.HTTPError:
            return {}

    async def update_bug(
        self, bug_id: int, **fields: Any
    ) -> Dict[str, Any]:
        """Update fields on *bug_id*."""
        try:
            resp = await self._request(
                "PUT", f"/rest/bug/{bug_id}", json=fields
            )
            return resp.json()
        except httpx.HTTPError:
            return {}

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_bug_refs(text: str) -> List[int]:
        """Extract unique WebKit bug IDs from free-form *text*.

        Recognised patterns:

        * ``Bug 12345`` / ``bug 12345``
        * ``https://bugs.webkit.org/show_bug.cgi?id=12345``
        * ``webkit.org/b/12345``

        Returns a sorted list of unique integer IDs.
        """
        ids: set[int] = set()
        for pattern in _BUG_PATTERNS:
            for m in pattern.finditer(text):
                ids.add(int(m.group(1)))
        return sorted(ids)

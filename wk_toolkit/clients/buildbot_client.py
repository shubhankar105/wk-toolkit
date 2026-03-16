"""Async httpx client for build.webkit.org and ews-build.webkit.org."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


class BuildbotClient:
    """Async client for the WebKit Buildbot and EWS APIs.

    Parameters
    ----------
    buildbot_url:
        Root URL of the main Buildbot instance.
    ews_url:
        Root URL of the EWS (Early Warning System) build instance.
    """

    def __init__(
        self,
        buildbot_url: str = "https://build.webkit.org",
        ews_url: str = "https://ews-build.webkit.org",
    ) -> None:
        self.buildbot_url = buildbot_url.rstrip("/")
        self.ews_url = ews_url.rstrip("/")
        self._bb_client: Optional[httpx.AsyncClient] = None
        self._ews_client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_bb_client(self) -> httpx.AsyncClient:
        if self._bb_client is None or self._bb_client.is_closed:
            self._bb_client = httpx.AsyncClient(
                base_url=self.buildbot_url,
                timeout=_TIMEOUT,
                headers={"Accept": "application/json"},
            )
        return self._bb_client

    async def _get_ews_client(self) -> httpx.AsyncClient:
        if self._ews_client is None or self._ews_client.is_closed:
            self._ews_client = httpx.AsyncClient(
                base_url=self.ews_url,
                timeout=_TIMEOUT,
                headers={"Accept": "application/json"},
            )
        return self._ews_client

    async def _bb_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = await self._get_bb_client()
        try:
            resp = await client.request(method, path, params=params)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Buildbot %s %s → %s: %s",
                method,
                path,
                exc.response.status_code,
                exc.response.text[:200],
            )
            raise
        except httpx.HTTPError as exc:
            logger.error("Buildbot request failed: %s", exc)
            raise

    async def _ews_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = await self._get_ews_client()
        try:
            resp = await client.request(method, path, params=params)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            logger.error(
                "EWS %s %s → %s: %s",
                method,
                path,
                exc.response.status_code,
                exc.response.text[:200],
            )
            raise
        except httpx.HTTPError as exc:
            logger.error("EWS request failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close both underlying HTTP clients."""
        for client in (self._bb_client, self._ews_client):
            if client is not None and not client.is_closed:
                await client.aclose()
        self._bb_client = None
        self._ews_client = None

    async def get_builders(self) -> List[Dict[str, Any]]:
        """Return all builders from the Buildbot instance.

        Each entry has keys ``builderid``, ``name``, ``description``.
        """
        try:
            resp = await self._bb_request("GET", "/api/v2/builders")
            return resp.json().get("builders", [])
        except httpx.HTTPError:
            return []

    async def get_builder_builds(
        self, builder_name: str, count: int = 10
    ) -> List[Dict[str, Any]]:
        """Return the most recent *count* builds for *builder_name*."""
        try:
            resp = await self._bb_request(
                "GET",
                f"/api/v2/builders/{builder_name}/builds",
                params={"limit": count, "order": "-number"},
            )
            return resp.json().get("builds", [])
        except httpx.HTTPError:
            return []

    async def get_build_steps(
        self, builder_id: int, build_number: int
    ) -> List[Dict[str, Any]]:
        """Return steps for a specific build."""
        try:
            resp = await self._bb_request(
                "GET",
                f"/api/v2/builders/{builder_id}/builds/{build_number}/steps",
            )
            return resp.json().get("steps", [])
        except httpx.HTTPError:
            return []

    async def get_ews_status_for_pr(
        self, pr_number: int
    ) -> List[Dict[str, Any]]:
        """Return EWS build statuses for PR *pr_number*.

        Each entry has keys ``builder``, ``status``, ``url``.
        """
        try:
            resp = await self._ews_request(
                "GET",
                f"/api/v2/builds",
                params={"pr": pr_number},
            )
            data = resp.json()
            results: List[Dict[str, Any]] = []
            for build in data.get("builds", []):
                results.append(
                    {
                        "builder": build.get("builderName", build.get("builder", "")),
                        "status": build.get("state_string", build.get("status", "")),
                        "url": build.get("url", ""),
                    }
                )
            return results
        except httpx.HTTPError:
            return []

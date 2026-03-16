"""Async httpx client for the GitHub REST API v3 (WebKit/WebKit)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.github.com"
_TIMEOUT = 30.0


class GitHubClient:
    """Async GitHub REST API v3 client targeting a specific repository.

    Parameters
    ----------
    token:
        Personal access token.  If empty the client works in read-only
        unauthenticated mode (lower rate limits).
    repo:
        Repository in ``owner/name`` form.
    """

    def __init__(self, token: str = "", repo: str = "WebKit/WebKit") -> None:
        self.token = token
        self.repo = repo
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        """Return (and lazily create) the shared :class:`httpx.AsyncClient`."""
        if self._client is None or self._client.is_closed:
            headers: Dict[str, str] = {
                "Accept": "application/vnd.github+json",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=_BASE_URL,
                headers=headers,
                timeout=_TIMEOUT,
            )
        return self._client

    def _check_rate_limit(self, response: httpx.Response) -> None:
        """Log a warning when the rate limit is running low."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None:
            try:
                if int(remaining) < 50:
                    logger.warning(
                        "GitHub rate limit low: %s requests remaining",
                        remaining,
                    )
            except ValueError:
                pass

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Issue an HTTP request, handling errors and rate-limit checks."""
        client = await self._get_client()
        try:
            resp = await client.request(
                method,
                path,
                headers=headers,
                json=json,
                params=params,
            )
            self._check_rate_limit(resp)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            logger.error(
                "GitHub API %s %s → %s: %s",
                method,
                path,
                exc.response.status_code,
                exc.response.text[:200],
            )
            raise
        except httpx.HTTPError as exc:
            logger.error("GitHub API request failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_pr(self, number: int) -> Dict[str, Any]:
        """Fetch a pull request by *number*.

        Returns the full PR JSON object, or ``{}`` on error.
        """
        try:
            resp = await self._request("GET", f"/repos/{self.repo}/pulls/{number}")
            return resp.json()
        except httpx.HTTPError:
            return {}

    async def get_pr_files(self, number: int) -> List[Dict[str, Any]]:
        """Return files changed in PR *number*.

        Each entry has keys ``filename``, ``additions``, ``deletions``,
        ``status``, and optionally ``patch``.
        """
        try:
            resp = await self._request(
                "GET", f"/repos/{self.repo}/pulls/{number}/files"
            )
            return resp.json()
        except httpx.HTTPError:
            return []

    async def get_pr_reviews(self, number: int) -> List[Dict[str, Any]]:
        """Return reviews submitted on PR *number*."""
        try:
            resp = await self._request(
                "GET", f"/repos/{self.repo}/pulls/{number}/reviews"
            )
            return resp.json()
        except httpx.HTTPError:
            return []

    async def get_pr_checks(self, number: int) -> List[Dict[str, Any]]:
        """Return CI check-run results for the head SHA of PR *number*.

        Each entry has keys ``name``, ``status``, ``conclusion``,
        ``started_at``, ``completed_at``.
        """
        try:
            pr = await self.get_pr(number)
            if not pr:
                return []
            sha = pr.get("head", {}).get("sha", "")
            if not sha:
                return []
            resp = await self._request(
                "GET", f"/repos/{self.repo}/commits/{sha}/check-runs"
            )
            return resp.json().get("check_runs", [])
        except httpx.HTTPError:
            return []

    async def get_pr_diff(self, number: int) -> str:
        """Return the raw unified diff for PR *number*."""
        try:
            resp = await self._request(
                "GET",
                f"/repos/{self.repo}/pulls/{number}",
                headers={"Accept": "application/vnd.github.diff"},
            )
            return resp.text
        except httpx.HTTPError:
            return ""

    async def create_pr(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> Dict[str, Any]:
        """Create a new pull request.  Requires a valid *token*."""
        try:
            resp = await self._request(
                "POST",
                f"/repos/{self.repo}/pulls",
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                },
            )
            return resp.json()
        except httpx.HTTPError:
            return {}

    async def search_prs(
        self,
        author: str = "",
        state: str = "open",
    ) -> List[Dict[str, Any]]:
        """Search pull requests by *author* and *state*."""
        q_parts = [f"repo:{self.repo}", "is:pr", f"state:{state}"]
        if author:
            q_parts.append(f"author:{author}")
        try:
            resp = await self._request(
                "GET",
                "/search/issues",
                params={"q": " ".join(q_parts)},
            )
            return resp.json().get("items", [])
        except httpx.HTTPError:
            return []

    async def add_comment(
        self, pr_number: int, body: str
    ) -> Dict[str, Any]:
        """Add an issue comment to PR *pr_number*."""
        try:
            resp = await self._request(
                "POST",
                f"/repos/{self.repo}/issues/{pr_number}/comments",
                json={"body": body},
            )
            return resp.json()
        except httpx.HTTPError:
            return {}

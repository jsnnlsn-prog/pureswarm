"""HTTP client for Shinobi's API interactions."""

from __future__ import annotations

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger("pureswarm.tools.http_client")


@dataclass
class HTTPResponse:
    """Represents an HTTP response."""
    status_code: int
    headers: Dict[str, str]
    body: str
    json_data: Optional[Dict[str, Any]] = None
    elapsed_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None


class ShinobiHTTPClient:
    """Async HTTP client for Shinobi's external API calls.

    Features:
    - Automatic retry with exponential backoff
    - Rate limiting awareness
    - Request/response logging for audit
    - Session management
    """

    def __init__(self, data_dir: Path, audit_logger=None) -> None:
        self._data_dir = data_dir
        self._logs_dir = data_dir / "http_logs"
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        self._audit = audit_logger
        self._client = None
        self._default_headers = {
            "User-Agent": "PureSwarm-Shinobi/1.0",
            "Accept": "application/json",
        }
        self._rate_limits: Dict[str, datetime] = {}

    async def _ensure_client(self):
        """Lazy initialization of httpx client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(
                    timeout=30.0,
                    follow_redirects=True,
                    headers=self._default_headers
                )
            except ImportError:
                logger.error("httpx not installed. Run: pip install httpx")
                raise

    async def get(self,
                  url: str,
                  headers: Optional[Dict[str, str]] = None,
                  params: Optional[Dict[str, Any]] = None,
                  retries: int = 3) -> HTTPResponse:
        """Perform GET request with retry logic."""
        return await self._request("GET", url, headers=headers, params=params, retries=retries)

    async def post(self,
                   url: str,
                   data: Optional[Dict[str, Any]] = None,
                   json_body: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   retries: int = 3) -> HTTPResponse:
        """Perform POST request with retry logic."""
        return await self._request("POST", url, headers=headers, data=data, json_body=json_body, retries=retries)

    async def put(self,
                  url: str,
                  data: Optional[Dict[str, Any]] = None,
                  json_body: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  retries: int = 3) -> HTTPResponse:
        """Perform PUT request with retry logic."""
        return await self._request("PUT", url, headers=headers, data=data, json_body=json_body, retries=retries)

    async def delete(self,
                     url: str,
                     headers: Optional[Dict[str, str]] = None,
                     retries: int = 3) -> HTTPResponse:
        """Perform DELETE request with retry logic."""
        return await self._request("DELETE", url, headers=headers, retries=retries)

    async def _request(self,
                       method: str,
                       url: str,
                       headers: Optional[Dict[str, str]] = None,
                       params: Optional[Dict[str, Any]] = None,
                       data: Optional[Dict[str, Any]] = None,
                       json_body: Optional[Dict[str, Any]] = None,
                       retries: int = 3) -> HTTPResponse:
        """Internal request handler with retry and logging."""
        await self._ensure_client()

        # Check rate limit
        domain = url.split("/")[2] if "/" in url else url
        if domain in self._rate_limits:
            wait_until = self._rate_limits[domain]
            now = datetime.now(timezone.utc)
            if now < wait_until:
                wait_seconds = (wait_until - now).total_seconds()
                logger.info("Rate limited for %s, waiting %.1fs", domain, wait_seconds)
                await asyncio.sleep(wait_seconds)

        merged_headers = {**self._default_headers, **(headers or {})}
        last_error = None

        for attempt in range(retries):
            try:
                import httpx
                start = asyncio.get_event_loop().time()

                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    params=params,
                    data=data,
                    json=json_body
                )

                elapsed = (asyncio.get_event_loop().time() - start) * 1000

                # Parse JSON if possible
                json_data = None
                try:
                    json_data = response.json()
                except (json.JSONDecodeError, Exception):
                    pass

                result = HTTPResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.text,
                    json_data=json_data,
                    elapsed_ms=elapsed,
                    success=200 <= response.status_code < 300
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self._rate_limits[domain] = datetime.now(timezone.utc).replace(
                        second=datetime.now(timezone.utc).second + retry_after
                    )
                    logger.warning("Rate limited by %s, retry after %ds", domain, retry_after)
                    await asyncio.sleep(retry_after)
                    continue

                # Log request
                await self._log_request(method, url, result)

                return result

            except Exception as e:
                last_error = str(e)
                logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)

        return HTTPResponse(
            status_code=0,
            headers={},
            body="",
            error=last_error,
            success=False
        )

    async def _log_request(self, method: str, url: str, response: HTTPResponse) -> None:
        """Log request to audit trail."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "elapsed_ms": response.elapsed_ms,
            "success": response.success
        }

        log_file = self._logs_dir / f"http_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class VeniceAIClient:
    """Client for Venice AI inference API."""

    def __init__(self, api_key: str, http_client: ShinobiHTTPClient) -> None:
        self._api_key = api_key
        self._http = http_client
        self._base_url = "https://api.venice.ai/api/v1"

    async def complete(self,
                       prompt: str,
                       model: str = "llama-3.3-70b",
                       max_tokens: int = 1000,
                       temperature: float = 0.7) -> Optional[str]:
        """Generate a completion from Venice AI."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = await self._http.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json_body=payload
        )

        if response.success and response.json_data:
            try:
                return response.json_data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                logger.error("Unexpected Venice AI response format")
                return None

        logger.error("Venice AI request failed: %s", response.error or response.body)
        return None

    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """Use Venice AI to analyze a task and break it into steps."""
        prompt = f"""Analyze this task and provide a structured breakdown:

Task: {task_description}

Respond in JSON format with:
{{
    "summary": "brief task summary",
    "steps": ["step 1", "step 2", ...],
    "estimated_time": "time estimate",
    "skills_required": ["skill1", "skill2"],
    "potential_blockers": ["blocker1", ...]
}}"""

        result = await self.complete(prompt)
        if result:
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"error": "Failed to analyze task"}

"""
Async HTTP client for the computation micro-service.

Provides a thin wrapper around httpx to submit analysis jobs,
poll their status and retrieve results.
"""

from typing import Any, Dict, Optional

import httpx

from app.config import settings

# Default timeout for outbound calls (seconds)
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def _client() -> httpx.AsyncClient:
    """Create a new async HTTP client targeting the computation service."""
    return httpx.AsyncClient(
        base_url=settings.COMPUTATION_SERVICE_URL,
        timeout=_TIMEOUT,
    )


async def submit_analysis(
    analysis_type: str,
    params: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """Submit an analysis job to the computation service.

    Args:
        analysis_type: The type of analysis (e.g. ``cluster``, ``two_point``).
        params: Type-specific parameters for the analysis.
        data: Optional payload data (e.g. marker matrix) to send along.

    Returns:
        The job ID assigned by the computation service.

    Raises:
        httpx.HTTPStatusError: If the computation service returns an error.
    """
    payload: Dict[str, Any] = {
        "analysis_type": analysis_type,
        "params": params,
    }
    if data is not None:
        payload["data"] = data

    async with await _client() as client:
        response = await client.post("/api/v1/jobs", json=payload)
        response.raise_for_status()
        body = response.json()
        return body["job_id"]


async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Poll the computation service for the status of a job.

    Args:
        job_id: The job identifier returned by :func:`submit_analysis`.

    Returns:
        A dictionary with at least ``status`` and optionally ``error``.
    """
    async with await _client() as client:
        response = await client.get(f"/api/v1/jobs/{job_id}/status")
        response.raise_for_status()
        return response.json()


async def get_job_result(job_id: str) -> Dict[str, Any]:
    """Retrieve the full result payload for a completed job.

    Args:
        job_id: The job identifier returned by :func:`submit_analysis`.

    Returns:
        The result dictionary produced by the computation service.
    """
    async with await _client() as client:
        response = await client.get(f"/api/v1/jobs/{job_id}/result")
        response.raise_for_status()
        return response.json()

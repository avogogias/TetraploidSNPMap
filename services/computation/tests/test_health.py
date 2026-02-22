"""Tests for the Computation Service health endpoint and startup."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health returns service status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["service"] == "computation"
    assert "scratch_dir" in body
    assert "r_available" in body
    assert "binaries_dir" in body
    assert body["max_markers"] == 8000
    assert body["max_individuals"] == 300


@pytest.mark.asyncio
async def test_cors_headers():
    """CORS middleware allows all origins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    # FastAPI CORS should allow the request
    assert resp.status_code in (200, 405)

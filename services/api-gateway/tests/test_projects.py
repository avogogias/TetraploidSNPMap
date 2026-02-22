"""Tests for the Projects REST API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_snp(client: AsyncClient):
    """POST /api/v1/projects creates a new SNP project."""
    resp = await client.post("/api/v1/projects", json={"name": "Test SNP", "mode": "SNP"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test SNP"
    assert body["mode"] == "SNP"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body
    assert body["datasets"] == []


@pytest.mark.asyncio
async def test_create_project_qtl(client: AsyncClient):
    """POST /api/v1/projects creates a QTL project."""
    resp = await client.post("/api/v1/projects", json={"name": "QTL Study", "mode": "QTL"})
    assert resp.status_code == 201
    assert resp.json()["mode"] == "QTL"


@pytest.mark.asyncio
async def test_create_project_nonsnp(client: AsyncClient):
    """POST /api/v1/projects creates a NONSNP project."""
    resp = await client.post("/api/v1/projects", json={"name": "RFLP Study", "mode": "NONSNP"})
    assert resp.status_code == 201
    assert resp.json()["mode"] == "NONSNP"


@pytest.mark.asyncio
async def test_create_project_default_mode(client: AsyncClient):
    """Mode defaults to SNP when not specified."""
    resp = await client.post("/api/v1/projects", json={"name": "Default"})
    assert resp.status_code == 201
    assert resp.json()["mode"] == "SNP"


@pytest.mark.asyncio
async def test_create_project_validation_empty_name(client: AsyncClient):
    """Name must not be empty."""
    resp = await client.post("/api/v1/projects", json={"name": "", "mode": "SNP"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_project_validation_invalid_mode(client: AsyncClient):
    """Invalid mode is rejected."""
    resp = await client.post("/api/v1/projects", json={"name": "Bad", "mode": "INVALID"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient):
    """GET /api/v1/projects returns empty list initially."""
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert body["projects"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_projects_pagination(client: AsyncClient):
    """Projects list supports skip/limit pagination."""
    for i in range(5):
        await client.post("/api/v1/projects", json={"name": f"P{i}"})

    resp = await client.get("/api/v1/projects", params={"skip": 0, "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["projects"]) == 2
    assert body["total"] == 5

    resp2 = await client.get("/api/v1/projects", params={"skip": 4, "limit": 10})
    assert len(resp2.json()["projects"]) == 1


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    """GET /api/v1/projects/{id} retrieves a specific project."""
    create_resp = await client.post("/api/v1/projects", json={"name": "GetMe"})
    pid = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """GET /api/v1/projects/999 returns 404."""
    resp = await client.get("/api/v1/projects/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    """DELETE /api/v1/projects/{id} removes the project."""
    create_resp = await client.post("/api/v1/projects", json={"name": "ToDelete"})
    pid = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/projects/{pid}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/projects/{pid}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    """DELETE non-existent project returns 404."""
    resp = await client.delete("/api/v1/projects/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_project_log_empty(client: AsyncClient):
    """GET /api/v1/projects/{id}/log returns empty log."""
    create_resp = await client.post("/api/v1/projects", json={"name": "LogTest"})
    pid = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{pid}/log")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == pid
    assert body["log"] == []


@pytest.mark.asyncio
async def test_get_project_log_not_found(client: AsyncClient):
    """GET log for non-existent project returns 404."""
    resp = await client.get("/api/v1/projects/999/log")
    assert resp.status_code == 404

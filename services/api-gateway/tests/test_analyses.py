"""Tests for the Analyses REST API endpoints."""

import io
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def project_with_dataset(client: AsyncClient) -> dict:
    """Create a project with a dataset, return both IDs."""
    proj_resp = await client.post("/api/v1/projects", json={"name": "Analysis Test"})
    pid = proj_resp.json()["id"]

    ds_resp = await client.post(
        f"/api/v1/projects/{pid}/datasets",
        files={"file": ("test.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    return {"project_id": pid, "dataset_id": ds_resp.json()["id"]}


@pytest.mark.asyncio
async def test_submit_cluster_analysis(client: AsyncClient, project_with_dataset: dict):
    """POST /analyses submits a clustering job."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_submit:
        mock_submit.return_value = "job-abc-123"

        resp = await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={
                "analysis_type": "cluster",
                "params": {"similarity_threshold": 0.9},
                "dataset_id": dsid,
            },
        )
    assert resp.status_code == 202
    body = resp.json()
    assert body["type"] == "cluster"
    assert body["status"] in ("PENDING", "RUNNING")
    assert "id" in body


@pytest.mark.asyncio
async def test_submit_all_analysis_types(client: AsyncClient, project_with_dataset: dict):
    """All 8 analysis types can be submitted."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    analysis_types = [
        "cluster", "two_point", "mds", "phase",
        "qtl", "anova", "permutation", "linkage_map",
    ]

    for atype in analysis_types:
        with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_sub:
            mock_sub.return_value = f"job-{atype}"
            resp = await client.post(
                f"/api/v1/projects/{pid}/analyses",
                json={"analysis_type": atype, "params": {}, "dataset_id": dsid},
            )
        assert resp.status_code == 202, f"Failed for analysis_type={atype}"
        assert resp.json()["type"] == atype


@pytest.mark.asyncio
async def test_submit_invalid_analysis_type(client: AsyncClient, project_with_dataset: dict):
    """Invalid analysis_type is rejected by validation."""
    pid = project_with_dataset["project_id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/analyses",
        json={"analysis_type": "not_real", "params": {}},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_submit_analysis_project_not_found(client: AsyncClient):
    """Submitting to non-existent project returns 404."""
    resp = await client.post(
        "/api/v1/projects/999/analyses",
        json={"analysis_type": "cluster", "params": {}},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_submit_analysis_dataset_not_found(client: AsyncClient, project_with_dataset: dict):
    """Submitting with non-existent dataset_id returns 404."""
    pid = project_with_dataset["project_id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/analyses",
        json={"analysis_type": "cluster", "params": {}, "dataset_id": 9999},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_analyses_empty(client: AsyncClient, project_with_dataset: dict):
    """GET /analyses returns empty list when no jobs submitted."""
    pid = project_with_dataset["project_id"]
    resp = await client.get(f"/api/v1/projects/{pid}/analyses")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_analyses(client: AsyncClient, project_with_dataset: dict):
    """GET /analyses returns submitted jobs."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_sub:
        mock_sub.return_value = "job-1"
        await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={"analysis_type": "cluster", "params": {}, "dataset_id": dsid},
        )
        mock_sub.return_value = "job-2"
        await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={"analysis_type": "two_point", "params": {}, "dataset_id": dsid},
        )

    resp = await client.get(f"/api/v1/projects/{pid}/analyses")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 2
    types = {j["type"] for j in jobs}
    assert "cluster" in types
    assert "two_point" in types


@pytest.mark.asyncio
async def test_get_analysis_status(client: AsyncClient, project_with_dataset: dict):
    """GET /analyses/{id} returns job status."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_sub:
        mock_sub.return_value = "job-status"
        create = await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={"analysis_type": "mds", "params": {}, "dataset_id": dsid},
        )

    job_id = create.json()["id"]

    with patch("app.utils.computation_client.get_job_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {"status": "RUNNING"}
        resp = await client.get(f"/api/v1/projects/{pid}/analyses/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_analysis_not_found(client: AsyncClient, project_with_dataset: dict):
    """GET /analyses/999 returns 404."""
    pid = project_with_dataset["project_id"]
    resp = await client.get(f"/api/v1/projects/{pid}/analyses/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_analysis(client: AsyncClient, project_with_dataset: dict):
    """DELETE /analyses/{id} removes the job."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_sub:
        mock_sub.return_value = "job-del"
        create = await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={"analysis_type": "cluster", "params": {}, "dataset_id": dsid},
        )

    job_id = create.json()["id"]
    del_resp = await client.delete(f"/api/v1/projects/{pid}/analyses/{job_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/projects/{pid}/analyses/{job_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_results_not_completed(client: AsyncClient, project_with_dataset: dict):
    """GET /results on a non-completed job returns 409."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_sub:
        mock_sub.return_value = "job-nc"
        create = await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={"analysis_type": "cluster", "params": {}, "dataset_id": dsid},
        )

    job_id = create.json()["id"]
    resp = await client.get(f"/api/v1/projects/{pid}/analyses/{job_id}/results")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_computation_client_failure_keeps_job_pending(
    client: AsyncClient, project_with_dataset: dict
):
    """If computation service fails, job stays PENDING with error message."""
    pid = project_with_dataset["project_id"]
    dsid = project_with_dataset["dataset_id"]

    with patch("app.utils.computation_client.submit_analysis", new_callable=AsyncMock) as mock_sub:
        mock_sub.side_effect = ConnectionError("Service unavailable")
        resp = await client.post(
            f"/api/v1/projects/{pid}/analyses",
            json={"analysis_type": "cluster", "params": {}, "dataset_id": dsid},
        )

    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["error"] is not None
    assert "Service unavailable" in body["error"]

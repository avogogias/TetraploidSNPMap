"""Tests for the Datasets REST API endpoints."""

import io
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def project_id(client: AsyncClient) -> int:
    """Create a project and return its ID."""
    resp = await client.post("/api/v1/projects", json={"name": "DS Test", "mode": "SNP"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_upload_dataset(client: AsyncClient, project_id: int):
    """POST /datasets uploads a file and creates a dataset record."""
    file_content = b"100 5\nmarker1 0 1 2 1 0\n"
    resp = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("test.SNPloc", io.BytesIO(file_content), "application/octet-stream")},
        data={"type": "snploc", "name": "Test Dataset"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test Dataset"
    assert body["type"] == "snploc"
    assert "id" in body


@pytest.mark.asyncio
async def test_upload_trait_data(client: AsyncClient, project_id: int):
    """Uploading a .qua file creates both Dataset and TraitData records."""
    file_content = b"50 2\ntrait1\ntrait2\n1.5 2.3\n"
    resp = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("demo.qua", io.BytesIO(file_content), "application/octet-stream")},
        data={"type": "qua"},
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "qua"


@pytest.mark.asyncio
async def test_upload_dataset_project_not_found(client: AsyncClient):
    """Upload to non-existent project returns 404."""
    resp = await client.post(
        "/api/v1/projects/999/datasets",
        files={"file": ("test.loc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "loc"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_datasets_empty(client: AsyncClient, project_id: int):
    """GET /datasets returns empty list when none uploaded."""
    resp = await client.get(f"/api/v1/projects/{project_id}/datasets")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_datasets(client: AsyncClient, project_id: int):
    """GET /datasets returns uploaded datasets."""
    await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("a.SNPloc", io.BytesIO(b"data1"), "application/octet-stream")},
        data={"type": "snploc", "name": "Dataset A"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("b.loc", io.BytesIO(b"data2"), "application/octet-stream")},
        data={"type": "loc", "name": "Dataset B"},
    )

    resp = await client.get(f"/api/v1/projects/{project_id}/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) == 2
    names = {d["name"] for d in datasets}
    assert "Dataset A" in names
    assert "Dataset B" in names


@pytest.mark.asyncio
async def test_get_dataset(client: AsyncClient, project_id: int):
    """GET /datasets/{id} retrieves a specific dataset."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("x.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc", "name": "GetMe"},
    )
    ds_id = create.json()["id"]

    resp = await client.get(f"/api/v1/projects/{project_id}/datasets/{ds_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_dataset_not_found(client: AsyncClient, project_id: int):
    """GET non-existent dataset returns 404."""
    resp = await client.get(f"/api/v1/projects/{project_id}/datasets/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_markers_returns_empty(client: AsyncClient, project_id: int):
    """GET /markers returns empty list (placeholder until parser connected)."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("m.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.get(f"/api/v1/projects/{project_id}/datasets/{ds_id}/markers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_select_all_markers(client: AsyncClient, project_id: int):
    """POST /markers/select-all returns ok status."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("s.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/datasets/{ds_id}/markers/select-all")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_select_none_markers(client: AsyncClient, project_id: int):
    """POST /markers/select-none returns ok status."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("n.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/datasets/{ds_id}/markers/select-none")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_invert_marker_selection(client: AsyncClient, project_id: int):
    """POST /markers/select-invert returns ok status."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("i.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/datasets/{ds_id}/markers/select-invert"
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_update_marker_selection(client: AsyncClient, project_id: int):
    """PUT /markers/selection accepts criteria-based selection."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("u.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/projects/{project_id}/datasets/{ds_id}/markers/selection",
        json={"criteria": {"chi_sig_max": 0.05}},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_move_marker(client: AsyncClient, project_id: int):
    """POST /markers/{id}/move returns ok status."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("mv.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/datasets/{ds_id}/markers/mkr001/move",
        json={"target_group": "LG2"},
    )
    assert resp.status_code == 200
    assert "mkr001" in resp.json()["message"]


@pytest.mark.asyncio
async def test_fix_drnp_markers(client: AsyncClient, project_id: int):
    """POST /fix-drnp returns ok status."""
    create = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={"file": ("fix.SNPloc", io.BytesIO(b"data"), "application/octet-stream")},
        data={"type": "snploc"},
    )
    ds_id = create.json()["id"]

    resp = await client.post(f"/api/v1/projects/{project_id}/datasets/{ds_id}/fix-drnp")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

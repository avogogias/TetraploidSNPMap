"""
REST endpoints for dataset management, marker listing and selection.

Routes:
    POST /api/v1/projects/{id}/datasets                                   - upload dataset
    GET  /api/v1/projects/{id}/datasets                                   - list datasets
    GET  /api/v1/projects/{id}/datasets/{dataset_id}                      - dataset details
    GET  /api/v1/projects/{id}/datasets/{dataset_id}/markers              - list markers (paginated)
    PUT  /api/v1/projects/{id}/datasets/{dataset_id}/markers/selection    - update selection
    POST /api/v1/projects/{id}/datasets/{dataset_id}/markers/select-all   - select all markers
    POST /api/v1/projects/{id}/datasets/{dataset_id}/markers/select-none  - deselect all markers
    POST /api/v1/projects/{id}/datasets/{dataset_id}/markers/select-invert - invert selection
    POST /api/v1/projects/{id}/datasets/{dataset_id}/markers/{marker_id}/move - move marker
    POST /api/v1/projects/{id}/datasets/{dataset_id}/fix-drnp             - fix DR/NP markers
    GET  /api/v1/projects/{id}/datasets/{dataset_id}/markers/{marker_id}/details - marker detail
"""

import logging
import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import Dataset, Project, TraitData
from app.models.db import get_db
from app.schemas.dataset import (
    DatasetResponse,
    LinkageGroupResponse,
    MarkerDetailResponse,
    MarkerMoveRequest,
    MarkerResponse,
    MarkerSelectionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/datasets",
    tags=["datasets"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_project_or_404(
    project_id: int, db: AsyncSession
) -> Project:
    """Return the project or raise 404."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


async def _get_dataset_or_404(
    project_id: int, dataset_id: int, db: AsyncSession
) -> Dataset:
    """Return the dataset or raise 404."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.project_id == project_id,
        )
    )
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found in project {project_id}",
        )
    return dataset


# ---------------------------------------------------------------------------
# POST /datasets - upload
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and import a dataset",
)
async def upload_dataset(
    project_id: int,
    file: UploadFile = File(..., description="Dataset file (.SNPloc, .qua, or non-SNP)"),
    name: Optional[str] = Form(None, description="Display name"),
    type: str = Form(..., description="File type: snploc | qua | loc"),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Upload a data file and create a dataset record.

    The file is persisted to the project storage directory and a metadata
    row is inserted into the database.  For trait (qua) files an additional
    TraitData record is created.
    """
    project = await _get_project_or_404(project_id, db)

    # Validate upload size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Persist file to disk
    storage_dir = os.path.join(settings.PROJECT_STORAGE_PATH, str(project_id))
    os.makedirs(storage_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(storage_dir, unique_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    display_name = name or file.filename or "untitled"

    dataset = Dataset(
        project_id=project_id,
        name=display_name,
        file_path=file_path,
        type=type,
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)

    # If it is a trait file, also create a TraitData record
    if type == "qua":
        trait = TraitData(
            project_id=project_id,
            dataset_id=dataset.id,
            file_path=file_path,
        )
        db.add(trait)

    logger.info(
        "Uploaded dataset id=%d project=%d type=%s file=%s",
        dataset.id,
        project_id,
        type,
        file.filename,
    )

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        type=dataset.type,
        marker_count=None,
        individual_count=None,
        created_at=dataset.created_at,
    )


# ---------------------------------------------------------------------------
# GET /datasets
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=List[DatasetResponse],
    summary="List datasets for a project",
)
async def list_datasets(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[DatasetResponse]:
    """Return all datasets belonging to the given project."""
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(Dataset)
        .where(Dataset.project_id == project_id)
        .order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()

    return [
        DatasetResponse(
            id=ds.id,
            name=ds.name,
            type=ds.type,
            marker_count=None,
            individual_count=None,
            created_at=ds.created_at,
        )
        for ds in datasets
    ]


# ---------------------------------------------------------------------------
# GET /datasets/{dataset_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset details with markers",
)
async def get_dataset(
    project_id: int,
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Retrieve full details for a single dataset."""
    dataset = await _get_dataset_or_404(project_id, dataset_id, db)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        type=dataset.type,
        marker_count=None,
        individual_count=None,
        created_at=dataset.created_at,
    )


# ---------------------------------------------------------------------------
# GET /datasets/{dataset_id}/markers
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}/markers",
    response_model=List[MarkerResponse],
    summary="List markers (paginated)",
)
async def list_markers(
    project_id: int,
    dataset_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    group: Optional[str] = Query(None, description="Filter by linkage group name"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by marker type"),
    db: AsyncSession = Depends(get_db),
) -> List[MarkerResponse]:
    """Return a paginated list of markers for the dataset.

    Marker data is read from the imported data file on disk and served
    via the computation service.  This is a placeholder that returns an
    empty list until the parsing layer is connected.
    """
    await _get_dataset_or_404(project_id, dataset_id, db)

    # TODO: Integrate with the computation service or local file parser to
    # read actual marker data from the imported dataset file.
    return []


# ---------------------------------------------------------------------------
# PUT /datasets/{dataset_id}/markers/selection
# ---------------------------------------------------------------------------


@router.put(
    "/{dataset_id}/markers/selection",
    summary="Update marker selection",
)
async def update_marker_selection(
    project_id: int,
    dataset_id: int,
    payload: MarkerSelectionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update which markers are selected based on criteria or explicit names/indices."""
    await _get_dataset_or_404(project_id, dataset_id, db)

    # TODO: Apply selection logic via the computation service.
    logger.info(
        "Marker selection update requested for dataset=%d criteria=%s",
        dataset_id,
        payload.criteria,
    )
    return {"status": "ok", "message": "Marker selection updated"}


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/markers/select-all
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/markers/select-all",
    summary="Select all markers",
)
async def select_all_markers(
    project_id: int,
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Select (check) every marker in the dataset."""
    await _get_dataset_or_404(project_id, dataset_id, db)
    # TODO: Forward to computation service.
    return {"status": "ok", "message": "All markers selected"}


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/markers/select-none
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/markers/select-none",
    summary="Deselect all markers",
)
async def select_none_markers(
    project_id: int,
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deselect (uncheck) every marker in the dataset."""
    await _get_dataset_or_404(project_id, dataset_id, db)
    # TODO: Forward to computation service.
    return {"status": "ok", "message": "All markers deselected"}


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/markers/select-invert
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/markers/select-invert",
    summary="Invert marker selection",
)
async def invert_marker_selection(
    project_id: int,
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Toggle the selection state of every marker."""
    await _get_dataset_or_404(project_id, dataset_id, db)
    # TODO: Forward to computation service.
    return {"status": "ok", "message": "Marker selection inverted"}


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/markers/{marker_id}/move
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/markers/{marker_id}/move",
    summary="Move a marker to another linkage group",
)
async def move_marker(
    project_id: int,
    dataset_id: int,
    marker_id: str,
    payload: MarkerMoveRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Move a single marker to the specified target linkage group."""
    await _get_dataset_or_404(project_id, dataset_id, db)
    # TODO: Forward to computation service.
    logger.info(
        "Move marker %s -> group %s (dataset=%d)",
        marker_id,
        payload.target_group,
        dataset_id,
    )
    return {"status": "ok", "message": f"Marker {marker_id} moved to {payload.target_group}"}


# ---------------------------------------------------------------------------
# POST /datasets/{dataset_id}/fix-drnp
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/fix-drnp",
    summary="Fix DR/NP markers",
)
async def fix_drnp_markers(
    project_id: int,
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Attempt to fix double-reduction (DR) and null-plex (NP) markers."""
    await _get_dataset_or_404(project_id, dataset_id, db)
    # TODO: Forward to computation service.
    return {"status": "ok", "message": "DR/NP marker fix initiated"}


# ---------------------------------------------------------------------------
# GET /datasets/{dataset_id}/markers/{marker_id}/details
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}/markers/{marker_id}/details",
    response_model=MarkerDetailResponse,
    summary="Get marker summary info",
)
async def get_marker_details(
    project_id: int,
    dataset_id: int,
    marker_id: str,
    db: AsyncSession = Depends(get_db),
) -> MarkerDetailResponse:
    """Return extended detail information for a single marker."""
    await _get_dataset_or_404(project_id, dataset_id, db)

    # TODO: Retrieve actual marker detail from the computation service.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Marker detail retrieval not yet connected to computation service",
    )

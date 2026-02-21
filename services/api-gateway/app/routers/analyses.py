"""
REST endpoints for analysis job management.

Routes:
    POST   /api/v1/projects/{id}/analyses               - submit analysis job
    GET    /api/v1/projects/{id}/analyses               - list analysis jobs
    GET    /api/v1/projects/{id}/analyses/{job_id}      - get job status
    DELETE /api/v1/projects/{id}/analyses/{job_id}      - cancel/remove job
    GET    /api/v1/projects/{id}/analyses/{job_id}/results - detailed results
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AnalysisJob, AnalysisStatus, Dataset, Project
from app.models.db import get_db
from app.schemas.analysis import AnalysisJobCreate, AnalysisJobResponse
from app.utils import computation_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/analyses",
    tags=["analyses"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_project_or_404(project_id: int, db: AsyncSession) -> Project:
    """Return the project or raise 404."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


async def _get_job_or_404(
    project_id: int, job_id: int, db: AsyncSession
) -> AnalysisJob:
    """Return the analysis job or raise 404."""
    result = await db.execute(
        select(AnalysisJob).where(
            AnalysisJob.id == job_id,
            AnalysisJob.project_id == project_id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found in project {project_id}",
        )
    return job


def _job_to_response(job: AnalysisJob) -> AnalysisJobResponse:
    """Convert an ORM AnalysisJob to the API response schema."""
    result_summary: Optional[Dict[str, Any]] = None
    if job.result_path:
        result_summary = {"result_path": job.result_path}

    return AnalysisJobResponse(
        id=job.id,
        type=job.analysis_type,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error=job.error_message,
        result_summary=result_summary,
    )


# ---------------------------------------------------------------------------
# POST /analyses
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an analysis job",
)
async def submit_analysis(
    project_id: int,
    payload: AnalysisJobCreate,
    db: AsyncSession = Depends(get_db),
) -> AnalysisJobResponse:
    """Submit a new analysis job for the given project.

    The job is recorded in the database with PENDING status and forwarded
    to the computation service.
    """
    await _get_project_or_404(project_id, db)

    # Validate optional dataset reference
    if payload.dataset_id is not None:
        ds_result = await db.execute(
            select(Dataset).where(
                Dataset.id == payload.dataset_id,
                Dataset.project_id == project_id,
            )
        )
        if ds_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {payload.dataset_id} not found in project {project_id}",
            )

    job = AnalysisJob(
        project_id=project_id,
        dataset_id=payload.dataset_id,
        analysis_type=payload.analysis_type,
        status=AnalysisStatus.PENDING,
        params_json=json.dumps(payload.params) if payload.params else None,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Submit to computation service asynchronously
    try:
        remote_job_id = await computation_client.submit_analysis(
            analysis_type=payload.analysis_type,
            params=payload.params,
            data={"project_id": project_id, "dataset_id": payload.dataset_id},
        )
        logger.info(
            "Submitted analysis job id=%d type=%s remote_job=%s",
            job.id,
            payload.analysis_type,
            remote_job_id,
        )
        # Store the remote job id in result_path temporarily for tracking
        job.result_path = f"remote:{remote_job_id}"
        job.status = AnalysisStatus.RUNNING
    except Exception as exc:
        logger.warning(
            "Failed to submit job id=%d to computation service: %s",
            job.id,
            exc,
        )
        # Job stays PENDING -- a background worker can retry later
        job.error_message = f"Submission failed: {exc}"

    return _job_to_response(job)


# ---------------------------------------------------------------------------
# GET /analyses
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=List[AnalysisJobResponse],
    summary="List analysis jobs for a project",
)
async def list_analyses(
    project_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
) -> List[AnalysisJobResponse]:
    """Return all analysis jobs for the project, optionally filtered by status."""
    await _get_project_or_404(project_id, db)

    query = (
        select(AnalysisJob)
        .where(AnalysisJob.project_id == project_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    if status_filter:
        query = query.where(AnalysisJob.status == status_filter)

    result = await db.execute(query)
    jobs = result.scalars().all()
    return [_job_to_response(j) for j in jobs]


# ---------------------------------------------------------------------------
# GET /analyses/{job_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{job_id}",
    response_model=AnalysisJobResponse,
    summary="Get analysis job status and summary",
)
async def get_analysis(
    project_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> AnalysisJobResponse:
    """Return the current status of an analysis job.

    If the job is still RUNNING, a status poll to the computation service
    is attempted and the local record updated.
    """
    job = await _get_job_or_404(project_id, job_id, db)

    # If running, try to refresh status from computation service
    if job.status == AnalysisStatus.RUNNING and job.result_path and job.result_path.startswith("remote:"):
        remote_id = job.result_path.split(":", 1)[1]
        try:
            remote_status = await computation_client.get_job_status(remote_id)
            new_status = remote_status.get("status", "").upper()
            if new_status == "COMPLETED":
                job.status = AnalysisStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
            elif new_status == "FAILED":
                job.status = AnalysisStatus.FAILED
                job.error_message = remote_status.get("error", "Unknown error")
                job.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.debug("Could not poll computation service for job %d: %s", job_id, exc)

    return _job_to_response(job)


# ---------------------------------------------------------------------------
# DELETE /analyses/{job_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel or remove an analysis job",
)
async def delete_analysis(
    project_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a running job or remove a completed/failed job record."""
    job = await _get_job_or_404(project_id, job_id, db)
    await db.delete(job)
    logger.info("Deleted analysis job id=%d project=%d", job_id, project_id)


# ---------------------------------------------------------------------------
# GET /analyses/{job_id}/results
# ---------------------------------------------------------------------------


@router.get(
    "/{job_id}/results",
    summary="Get detailed analysis results",
)
async def get_analysis_results(
    project_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve the full result payload for a completed analysis job.

    The response structure is type-specific and may include cluster groups,
    ordered markers, QTL trait data, phase tables, etc.
    """
    job = await _get_job_or_404(project_id, job_id, db)

    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job_id} is not completed (current status: {job.status})",
        )

    # Fetch results from computation service
    if job.result_path and job.result_path.startswith("remote:"):
        remote_id = job.result_path.split(":", 1)[1]
        try:
            result_data = await computation_client.get_job_result(remote_id)
            return {
                "job_id": job.id,
                "analysis_type": job.analysis_type,
                "results": result_data,
            }
        except Exception as exc:
            logger.error("Failed to retrieve results for job %d: %s", job_id, exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve results from computation service",
            ) from exc

    return {
        "job_id": job.id,
        "analysis_type": job.analysis_type,
        "results": {},
    }

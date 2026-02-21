"""
REST endpoints for project management.

Routes:
    POST   /api/v1/projects          - create a new project
    GET    /api/v1/projects          - list all projects
    GET    /api/v1/projects/{id}     - get project details
    DELETE /api/v1/projects/{id}     - delete a project
    GET    /api/v1/projects/{id}/log - get project analysis log
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import AnalysisJob, Project
from app.models.db import get_db
from app.schemas.project import ProjectCreate, ProjectList, ProjectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# POST /api/v1/projects
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new TetraploidSNPMap project with the given name and mode."""
    project = Project(name=payload.name, mode=payload.mode)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    logger.info("Created project id=%d name=%s mode=%s", project.id, project.name, project.mode)
    return ProjectResponse.model_validate(project)


# ---------------------------------------------------------------------------
# GET /api/v1/projects
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ProjectList,
    summary="List all projects",
)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
) -> ProjectList:
    """Return a paginated list of projects."""
    total_query = select(func.count(Project.id))
    total_result = await db.execute(total_query)
    total: int = total_result.scalar_one()

    query = (
        select(Project)
        .options(selectinload(Project.datasets))
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectList(
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Retrieve full details for a single project, including its datasets."""
    query = (
        select(Project)
        .options(selectinload(Project.datasets))
        .where(Project.id == project_id)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return ProjectResponse.model_validate(project)


# ---------------------------------------------------------------------------
# DELETE /api/v1/projects/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project and all associated datasets, jobs and trait data."""
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    await db.delete(project)
    logger.info("Deleted project id=%d", project_id)


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{id}/log
# ---------------------------------------------------------------------------


@router.get(
    "/{project_id}/log",
    summary="Get project analysis log",
)
async def get_project_log(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the analysis history log for a project.

    Each entry includes the analysis type, status, timestamps and any error
    messages.
    """
    # Verify the project exists
    proj_query = select(Project.id).where(Project.id == project_id)
    proj_result = await db.execute(proj_query)
    if proj_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    query = (
        select(AnalysisJob)
        .where(AnalysisJob.project_id == project_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    result = await db.execute(query)
    jobs = result.scalars().all()

    entries = [
        {
            "id": job.id,
            "analysis_type": job.analysis_type,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }
        for job in jobs
    ]
    return {"project_id": project_id, "log": entries}

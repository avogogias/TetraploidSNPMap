"""
Pydantic schemas for Project CRUD operations.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    mode: Literal["SNP", "QTL", "NONSNP"] = Field(
        "SNP",
        description="Analysis mode: SNP (default), QTL (SNP-QTL) or NONSNP (RFLP/AFLP/SSR)",
    )


class DatasetSummary(BaseModel):
    """Minimal dataset info embedded in project responses."""

    id: int
    name: str
    type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """Full project representation returned by the API."""

    id: int
    name: str
    mode: str
    created_at: datetime
    updated_at: datetime
    datasets: List[DatasetSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    """Paginated list of projects."""

    projects: List[ProjectResponse]
    total: int

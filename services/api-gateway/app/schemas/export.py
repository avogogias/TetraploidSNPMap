"""
Pydantic schemas for file export operations.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Request to export project data in a specific format."""

    format: Literal["snploc", "pwd", "phase", "map", "dat", "qua"] = Field(
        ..., description="Export file format"
    )
    dataset_id: Optional[int] = Field(None, description="Dataset to export from")
    analysis_job_id: Optional[int] = Field(
        None, description="Analysis job whose results should be exported"
    )


class ExportResponse(BaseModel):
    """Response containing the download URL for an exported file."""

    download_url: str = Field(..., description="URL to download the exported file")
    filename: str = Field(..., description="Suggested filename for the download")

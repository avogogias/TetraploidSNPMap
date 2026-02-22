"""
Pydantic schemas for dataset upload, marker listing and selection.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class DatasetUpload(BaseModel):
    """Metadata accompanying a dataset file upload (multipart form)."""

    name: Optional[str] = Field(None, description="Optional display name for the dataset")
    type: Literal["snploc", "qua", "loc"] = Field(
        ..., description="File type: snploc (SNP markers), qua (trait data), loc (non-SNP)"
    )


class DatasetResponse(BaseModel):
    """Dataset details returned by the API."""

    id: int
    name: str
    type: str
    marker_count: Optional[int] = None
    individual_count: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------


class MarkerResponse(BaseModel):
    """A single marker row in a dataset."""

    name: str
    safe_name: str = Field(description="Sanitised marker name safe for file systems")
    type: str = Field(description="Marker type code (e.g. SDSD, SSSS, DDDD)")
    checked: bool = Field(description="Whether the marker is currently selected")
    parent_dosages: Optional[Dict[str, int]] = Field(
        None, description="Parent dosage mapping, e.g. {'P1': 2, 'P2': 1}"
    )
    chi_sig: Optional[float] = Field(None, description="Chi-square significance value")
    status: Optional[str] = Field(None, description="Marker status (OK, DR, NP, ...)")
    snp_ratio: Optional[str] = Field(None, description="SNP ratio string, e.g. 'Simplex x Nulliplex'")


class LinkageGroupResponse(BaseModel):
    """A linkage group containing a list of markers."""

    name: str
    markers: List[MarkerResponse] = Field(default_factory=list)
    marker_count: int = 0
    selected_count: int = 0


# ---------------------------------------------------------------------------
# Marker selection
# ---------------------------------------------------------------------------


class MarkerSelectionRequest(BaseModel):
    """Criteria-based or explicit marker selection update."""

    criteria: Optional[Dict[str, object]] = Field(
        None,
        description=(
            "Filter criteria: {'type': ['SDSD'], 'parent': 'P1', "
            "'chi_sig_max': 0.05, 'ratio': 'simplex'}"
        ),
    )
    marker_names: Optional[List[str]] = Field(
        None, description="Explicit list of marker names to select"
    )
    marker_indices: Optional[List[int]] = Field(
        None, description="Explicit list of marker indices to select"
    )


class MarkerMoveRequest(BaseModel):
    """Request to move a marker to a different linkage group."""

    target_group: str = Field(..., description="Name of the destination linkage group")


class MarkerDetailResponse(BaseModel):
    """Extended detail view for a single marker."""

    name: str
    safe_name: str
    type: str
    checked: bool
    parent_dosages: Optional[Dict[str, int]] = None
    chi_sig: Optional[float] = None
    status: Optional[str] = None
    snp_ratio: Optional[str] = None
    group: Optional[str] = None
    individual_scores: Optional[List[int]] = Field(
        None, description="Raw genotype scores for each individual"
    )

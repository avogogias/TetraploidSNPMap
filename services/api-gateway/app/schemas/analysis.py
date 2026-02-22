"""
Pydantic schemas for analysis jobs and their typed parameters / results.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Job create / response
# ---------------------------------------------------------------------------


class AnalysisJobCreate(BaseModel):
    """Payload for submitting a new analysis job."""

    analysis_type: Literal[
        "cluster",
        "two_point",
        "mds",
        "phase",
        "qtl",
        "anova",
        "permutation",
        "linkage_map",
    ] = Field(..., description="Type of analysis to run")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Type-specific parameters"
    )
    dataset_id: Optional[int] = Field(
        None, description="Dataset to run the analysis on"
    )


class AnalysisJobResponse(BaseModel):
    """Status / summary for a submitted analysis job."""

    id: int
    type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Typed parameter schemas
# ---------------------------------------------------------------------------


class ClusterParams(BaseModel):
    """Parameters for hierarchical clustering analysis."""

    similarity_threshold: float = Field(
        0.9, ge=0.0, le=1.0, description="Similarity threshold for cluster merging"
    )


class TwoPointParams(BaseModel):
    """Parameters for two-point linkage analysis."""

    exclude_duplicates: bool = Field(
        False, description="Whether to exclude duplicate markers"
    )
    full_output: bool = Field(
        False, description="Whether to produce full pairwise output"
    )


class MDSParams(BaseModel):
    """Parameters for multi-dimensional scaling."""

    dimensions: int = Field(3, ge=2, le=3, description="Number of MDS dimensions (2 or 3)")


class PhaseParams(BaseModel):
    """Parameters for phase analysis."""

    pass


class QTLParams(BaseModel):
    """Parameters for QTL analysis."""

    model_type: str = Field(
        ..., description="QTL model type, e.g. 'interval_mapping', 'composite'"
    )
    traits: List[str] = Field(
        ..., min_length=1, description="Trait names to include in the analysis"
    )


class AnovaParams(BaseModel):
    """Parameters for ANOVA analysis."""

    traits: List[str] = Field(
        ..., min_length=1, description="Trait names to include in the analysis"
    )


class PermutationParams(BaseModel):
    """Parameters for permutation testing."""

    n_perms: int = Field(
        500, ge=1, description="Number of permutations to run"
    )


# ---------------------------------------------------------------------------
# Typed result schemas
# ---------------------------------------------------------------------------


class ClusterResult(BaseModel):
    """Result of hierarchical clustering."""

    groups: List[Dict[str, Any]] = Field(
        default_factory=list, description="Cluster groups with marker lists"
    )
    dendrogram: Optional[Dict[str, Any]] = Field(
        None, description="Dendrogram tree structure"
    )


class TwoPointResult(BaseModel):
    """Result of two-point analysis."""

    pairwise_distances: Optional[List[Dict[str, Any]]] = Field(
        None, description="Pairwise distance entries"
    )
    ordered_markers: Optional[List[str]] = Field(
        None, description="Markers ordered by linkage"
    )
    summary: Optional[Dict[str, Any]] = None


class MDSResult(BaseModel):
    """Result of MDS analysis."""

    coordinates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {marker, x, y, z} coordinate entries",
    )
    stress: Optional[float] = Field(None, description="Kruskal stress value")


class PhaseResult(BaseModel):
    """Result of phase analysis."""

    phase_table: List[Dict[str, Any]] = Field(
        default_factory=list, description="Phase assignments per marker"
    )


class QTLResultResponse(BaseModel):
    """Result of QTL analysis."""

    traits: List[str] = Field(default_factory=list)
    lod_profiles: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None, description="LOD score profiles keyed by trait name"
    )
    significant_qtls: Optional[List[Dict[str, Any]]] = None


class AnovaResultResponse(BaseModel):
    """Result of ANOVA analysis."""

    traits: List[str] = Field(default_factory=list)
    f_statistics: Optional[Dict[str, float]] = None
    p_values: Optional[Dict[str, float]] = None
    summary_table: Optional[List[Dict[str, Any]]] = None

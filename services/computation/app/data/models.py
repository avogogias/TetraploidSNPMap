"""Pydantic data models mirroring the Java data classes.

These models represent the core domain objects of TetraploidSNPMap:
markers, alleles, linkage groups, analysis results, and projects.
They are direct ports of the Java classes found in
TPMfront-end/src/data/.

All models use Pydantic v2 for validation, serialization, and
JSON schema generation.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MarkerType(IntEnum):
    """Marker type codes matching Marker.java constants."""

    UNKNOWN = 0
    RFLP = 1
    AFLP = 2
    SSR = 3
    SNP = 4


class RatioCode(IntEnum):
    """Segregation ratio codes matching Marker.java constants."""

    UNKNOWN = 0
    R1_1 = 1
    R3_1 = 3
    R5_1 = 5
    R_HIGHER = 7
    R11_1 = 11
    R35_1 = 35


class OrderedResultType(IntEnum):
    """Ordered result type codes matching OrderedResult.java constants."""

    ORT_TWOPOINT = 1
    ORT_MDS = 2
    ORT_NONSNP = 3
    ORT_READQTL = 4
    ORT_PHASE = 5


# ---------------------------------------------------------------------------
# Allele-level models
# ---------------------------------------------------------------------------


class AlleleDosage(BaseModel):
    """SNP allele dosage for a single individual.

    Dosage values: 0 (AAAA), 1 (AAAB), 2 (AABB), 3 (ABBB),
    4 (BBBB), 9 (UNKNOWN/missing).

    Mirrors data/AlleleDosage.java.
    """

    dosage: int = Field(
        ..., ge=0, le=9, description="Dosage value (0-4 valid, 9=unknown)"
    )


class AlleleState(BaseModel):
    """Non-SNP allele presence/absence state for a single individual.

    State values: 0 (absent), 1 (present), 9 (unknown).

    Mirrors data/AlleleState.java.
    """

    state: int = Field(
        ..., ge=0, le=9, description="Allele state (0=absent, 1=present, 9=unknown)"
    )


class Allele(BaseModel):
    """Allele data for a marker, containing per-individual states or dosages.

    For SNP markers, `dosages` is populated (one entry per individual
    including parents). For non-SNP markers, `states` is populated.

    Mirrors data/Allele.java.
    """

    states: list[AlleleState] = Field(
        default_factory=list,
        description="Per-individual allele states (non-SNP markers)",
    )
    dosages: list[AlleleDosage] = Field(
        default_factory=list,
        description="Per-individual dosage values (SNP markers)",
    )


# ---------------------------------------------------------------------------
# Marker-level models
# ---------------------------------------------------------------------------


class MarkerSNPPattern(BaseModel):
    """Observed SNP dosage frequency pattern.

    Mirrors data/MarkerSNPPattern.java.
    """

    dosage: str = Field(..., description="Dosage class (e.g., '0', '1', '2')")
    count: str = Field(..., description="Number of individuals with this dosage")
    proportion: str = Field(
        ..., description="Proportion of known individuals with this dosage"
    )


class MarkerBandPattern(BaseModel):
    """Observed band pattern frequency (non-SNP markers).

    Mirrors data/MarkerBandPattern.java.
    """

    pattern: str = Field(..., description="Band pattern string")
    count: int = Field(..., description="Number of individuals with this pattern")
    proportion: float = Field(..., description="Proportion with this pattern")


class MarkerProbability(BaseModel):
    """Posterior probability for a parental genotype configuration.

    Used in non-SNP genotype finding to rank candidate segregation ratios.

    Mirrors data/MarkerProbability.java.
    """

    p1: str = Field(..., description="Parent 1 genotype (e.g., '1000')")
    p2: str = Field(..., description="Parent 2 genotype (e.g., '0000')")
    pb: float = Field(..., description="Posterior probability")
    df: int = Field(default=0, description="Degrees of freedom")
    chi: float = Field(default=0.0, description="Chi-square statistic")
    sig: float = Field(default=0.0, description="Significance level")


class SigLinkage(BaseModel):
    """Significant linkage between two markers.

    Mirrors data/SigLinkage.java.
    """

    partner_name: str = Field(..., description="Name of the linked marker")
    chi: float = Field(..., description="Chi-square statistic")
    sig: float = Field(..., description="Significance level")
    phase: Optional[str] = Field(None, description="Phase string if available")


class SimMatchData(BaseModel):
    """Similarity match data for a marker across parents.

    Contains linkage information organized by parent and linkage type.

    Mirrors data/SimMatchData.java.
    """

    p1A: list[SigLinkage] = Field(
        default_factory=list, description="Parent 1 simplex-duplex linkages"
    )
    p1B: list[SigLinkage] = Field(
        default_factory=list, description="Parent 1 simplex-double simplex linkages"
    )
    p1C: list[SigLinkage] = Field(
        default_factory=list, description="Parent 1 other linkages"
    )
    p2A: list[SigLinkage] = Field(
        default_factory=list, description="Parent 2 simplex-duplex linkages"
    )
    p2B: list[SigLinkage] = Field(
        default_factory=list, description="Parent 2 simplex-double simplex linkages"
    )
    p2C: list[SigLinkage] = Field(
        default_factory=list, description="Parent 2 other linkages"
    )


class Marker(BaseModel):
    """Core marker data model.

    Represents a single genetic marker (SNP, AFLP, SSR, or RFLP) with
    its allele data, parental information, chi-square statistics, and
    status flags.

    Mirrors data/Marker.java.
    """

    name: str = Field(..., description="Marker name from the input file")
    prefix: Optional[str] = Field(
        None, description="Prefix (SC group label from FindSNPGeno)"
    )
    type: MarkerType = Field(
        default=MarkerType.UNKNOWN, description="Marker type code"
    )
    alleles: list[Allele] = Field(
        default_factory=list, description="Allele data for this marker"
    )

    # Parental information
    phenotypes: list[str] = Field(
        default_factory=lambda: ["", ""],
        min_length=2,
        max_length=2,
        description="Parental phenotype strings [P1, P2]",
    )
    parent_dosages: list[str] = Field(
        default_factory=lambda: ["", ""],
        min_length=2,
        max_length=2,
        description="Parental dosages [P1, P2] as strings",
    )

    # SNP-specific data
    snp_ratio: Optional[str] = Field(
        None, description="SNP ratio string: '1:1' or 'higher'"
    )
    snp_patterns: list[MarkerSNPPattern] = Field(
        default_factory=list, description="Observed SNP dosage patterns"
    )
    nmiss: Optional[str] = Field(
        None, description="Number of missing values (SNP markers)"
    )

    # Non-SNP data
    band_patterns: list[MarkerBandPattern] = Field(
        default_factory=list, description="Observed band patterns (non-SNP)"
    )
    probs_present: list[MarkerProbability] = Field(
        default_factory=list,
        description="Posterior probabilities with double reduction",
    )
    probs_absent: list[MarkerProbability] = Field(
        default_factory=list,
        description="Posterior probabilities without double reduction",
    )
    best_ratio: Optional[MarkerProbability] = Field(
        None, description="Best segregation ratio (non-SNP)"
    )

    # Chi-square and status
    chi: float = Field(default=0.0, description="Chi-square statistic (SNP)")
    chisig: float = Field(default=0.0, description="Chi-square significance (SNP)")
    np: int = Field(default=0, description="NP flag value")
    df: float = Field(default=0.0, description="Degrees of freedom")
    status: Optional[str] = Field(
        None, description="Marker status: OK, DR, NP, FDR, FNP, 00, MO"
    )

    # Double reduction
    dr_alpha: float = Field(default=0.0, description="MLE of alpha for DR test")
    dr_lr: float = Field(default=0.0, description="Likelihood ratio for DR test")
    dr_sig: float = Field(default=0.0, description="DR significance")

    # Ratio
    ratio_code: RatioCode = Field(
        default=RatioCode.UNKNOWN, description="Segregation ratio code"
    )
    percentage_unknown: int = Field(
        default=0, description="Percentage of unknown allele states"
    )

    # Presence in parents
    present_in_parent: list[bool] = Field(
        default_factory=lambda: [False, False],
        description="Whether marker is present in [P1, P2]",
    )

    # Sim match data
    sim_match_data: Optional[SimMatchData] = Field(
        None, description="Similarity match linkage data"
    )

    # Fix state
    fix_changed: bool = Field(
        default=False, description="Whether this marker was modified by FixDRNP"
    )
    errors: str = Field(default="", description="Accumulated error messages")

    def can_enable(self, ignore_fnp: bool = False) -> bool:
        """Determine whether this marker should be enabled for analysis.

        For SNP markers, checks chisig > 0.001 and status is not
        NP/DR/00/MO. For non-SNP markers, checks that best_ratio is known.

        Args:
            ignore_fnp: If True, treat FNP markers as enabled.

        Returns:
            True if the marker passes selection criteria.
        """
        if self.type == MarkerType.SNP:
            if not ignore_fnp and self.status == "FNP":
                return True
            if self.chisig < 0.001:
                return False
            if self.status is None:
                return True
            if self.status in ("NP", "DR", "00", "MO"):
                return False
            return True
        else:
            return self.best_ratio is not None

    def get_individual_count(self) -> int:
        """Return the number of individuals (excluding parents).

        Returns:
            Number of individuals from the first allele's data.
        """
        if not self.alleles:
            return 0
        allele = self.alleles[0]
        if allele.dosages:
            return len(allele.dosages) - 2
        if allele.states:
            return len(allele.states) - 2
        return 0


# ---------------------------------------------------------------------------
# CMarker (Marker wrapper with selection state)
# ---------------------------------------------------------------------------


class CMarker(BaseModel):
    """Checked Marker wrapper providing selection state and safe name.

    The safe name is a unique identifier of the form 'mkrNNN' (non-SNP)
    or 'mkrNNNNNN' (SNP) used by the Fortran programs.

    Mirrors data/CMarker.java.
    """

    marker: Marker = Field(..., description="The wrapped Marker object")
    checked: bool = Field(
        default=True, description="Whether this marker is selected for analysis"
    )
    safe_name: str = Field(
        ..., description="Safe name for Fortran I/O (e.g., 'mkr001', 'mkr000001')"
    )

    @property
    def safe_name_suffix(self) -> int:
        """Return the numeric suffix of the safe name.

        Returns:
            Integer suffix parsed from safe_name (e.g., 1 from 'mkr001').
        """
        return int(self.safe_name[3:])

    @staticmethod
    def make_safe_name(index: int, marker_type: MarkerType) -> str:
        """Generate a safe name for a marker at the given index.

        Args:
            index: 1-based marker index.
            marker_type: Type of marker (SNP uses 6-digit, others use 3-digit).

        Returns:
            Safe name string (e.g., 'mkr001' or 'mkr000001').
        """
        if marker_type == MarkerType.SNP:
            return f"mkr{index:06d}"
        return f"mkr{index:03d}"


# ---------------------------------------------------------------------------
# Linkage Group
# ---------------------------------------------------------------------------


class LinkageGroup(BaseModel):
    """A group of markers forming a linkage group.

    This is the primary container used throughout the analysis pipeline.
    It holds markers, analysis results references, and optional trait data.

    Mirrors data/LinkageGroup.java.
    """

    name: Optional[str] = Field(None, description="Linkage group name")
    markers: list[CMarker] = Field(
        default_factory=list, description="Markers in this group"
    )
    freeze_safe_names: bool = Field(
        default=False,
        description="If True, safe names are frozen and lookup uses linear search",
    )

    def get_marker_count(self) -> int:
        """Return the total number of markers."""
        return len(self.markers)

    def get_selected_marker_count(self) -> int:
        """Return the number of currently selected (checked) markers."""
        return sum(1 for cm in self.markers if cm.checked)

    def get_individual_count(self) -> int:
        """Return the number of individuals from the first marker's data.

        For SNP markers, uses dosage count; for non-SNP, uses state count.
        Both include parents (+2), which is the raw count.
        """
        if not self.markers:
            return 0
        marker = self.markers[0].marker
        if marker.alleles:
            allele = marker.alleles[0]
            if allele.dosages:
                return len(allele.dosages)
            if allele.states:
                return len(allele.states)
        return 0

    def get_marker_by_safe_name(self, safe_name: str) -> Optional[CMarker]:
        """Find a marker by its safe name.

        Args:
            safe_name: The safe name to search for (e.g., 'mkr001').

        Returns:
            The matching CMarker, or None if not found.
        """
        if self.freeze_safe_names:
            for cm in self.markers:
                if cm.safe_name == safe_name:
                    return cm
            return None
        else:
            index = int(safe_name[3:]) - 1
            if 0 <= index < len(self.markers):
                return self.markers[index]
            return None

    def get_marker_by_safe_name_nr(self, nr: int) -> Optional[CMarker]:
        """Find a marker by its safe name numeric suffix.

        Args:
            nr: The numeric suffix (1-based).

        Returns:
            The matching CMarker, or None if not found.
        """
        if self.freeze_safe_names:
            for cm in self.markers:
                if cm.safe_name_suffix == nr:
                    return cm
            return None
        else:
            if 0 < nr <= len(self.markers):
                return self.markers[nr - 1]
            return None

    def get_cloned_linkage_group(
        self, selected_only: bool = False, maintain_names: bool = True
    ) -> LinkageGroup:
        """Create a copy of this linkage group, optionally filtering markers.

        Args:
            selected_only: If True, only include checked markers.
            maintain_names: If True, preserve safe names from the original.

        Returns:
            A new LinkageGroup with the (optionally filtered) markers.
        """
        new_markers = []
        for i, cm in enumerate(self.markers):
            if selected_only and not cm.checked:
                continue
            if maintain_names:
                new_markers.append(cm.model_copy(deep=True))
            else:
                new_cm = CMarker(
                    marker=cm.marker.model_copy(deep=True),
                    checked=cm.checked,
                    safe_name=CMarker.make_safe_name(
                        len(new_markers) + 1, cm.marker.type
                    ),
                )
                new_markers.append(new_cm)
        return LinkageGroup(name=self.name, markers=new_markers)

    def count_npdr(self) -> tuple[int, int]:
        """Count markers with NP and DR status.

        Returns:
            Tuple of (np_count, dr_count).
        """
        np_count = 0
        dr_count = 0
        for cm in self.markers:
            if cm.marker.status == "NP":
                np_count += 1
            elif cm.marker.status == "DR":
                dr_count += 1
        return np_count, dr_count


# ---------------------------------------------------------------------------
# Phase and Two-Point result models
# ---------------------------------------------------------------------------


class PhasePair(BaseModel):
    """Phase data for a pair of markers.

    Contains the phase strings and recombination frequency / LOD score
    for two linked markers.

    Mirrors data/PhasePair.java.
    """

    cm1_safe_name: str = Field(..., description="Safe name of first marker")
    cm2_safe_name: str = Field(..., description="Safe name of second marker")
    phase1: str = Field(..., description="Phase string for first marker")
    phase2: str = Field(..., description="Phase string for second marker")
    rfq: float = Field(default=0.0, description="Recombination frequency")
    lod: float = Field(default=0.0, description="LOD score")


class RemovedLocus(BaseModel):
    """Record of a locus removed during duplicate exclusion.

    Mirrors data/RemovedLocus.java.
    """

    removed_name: str = Field(..., description="Name of removed locus")
    retained_name: str = Field(..., description="Name of retained locus")
    similarity: str = Field(
        ..., description="Number of mismatches or 'equal'"
    )


class Summary(BaseModel):
    """Summary information for an analysis run.

    Mirrors data/Summary.java.
    """

    time_ms: int = Field(
        default=0, description="Analysis runtime in milliseconds"
    )
    original_marker_count: int = Field(
        default=0, description="Total markers in original group"
    )
    selected_marker_count: int = Field(
        default=0, description="Selected markers at time of analysis"
    )
    exclude_duplicates: bool = Field(
        default=False, description="Whether duplicate exclusion was used"
    )
    num_excluded: int = Field(
        default=-1, description="Number of excluded duplicates (-1 = N/A)"
    )
    num_markers: int = Field(
        default=-1, description="Number of markers post-exclusion (-1 = N/A)"
    )


class OrderedResult(BaseModel):
    """Result of an ordering analysis (TwoPoint, MDS, Phase, etc.).

    Contains the ordered list of markers, inter-marker distances,
    phase pair data, and text output buffers from the Fortran programs.

    Mirrors data/OrderedResult.java.
    """

    name: Optional[str] = Field(None, description="Display name of this result")
    result_type: OrderedResultType = Field(
        default=OrderedResultType.ORT_NONSNP,
        description="Type of ordering analysis",
    )
    linkage_group: LinkageGroup = Field(
        default_factory=lambda: LinkageGroup(name=None),
        description="Ordered linkage group",
    )
    distances: list[float] = Field(
        default_factory=list, description="Inter-marker distances"
    )
    phase_pairs: list[PhasePair] = Field(
        default_factory=list, description="Phase pair data"
    )
    removed_loci: list[RemovedLocus] = Field(
        default_factory=list, description="Loci removed as duplicates"
    )
    summary: Optional[Summary] = Field(
        None, description="Run summary information"
    )
    exclude_duplicates: bool = Field(
        default=False, description="Whether duplicate exclusion was used"
    )
    full_output: bool = Field(
        default=False, description="Whether full output was requested"
    )
    flip: bool = Field(
        default=False, description="Whether the order was flipped"
    )
    mean_nnfit: float = Field(
        default=0.0, description="Mean nearest-neighbour fit"
    )

    # Text output buffers from Fortran programs
    tp1: str = Field(default="", description="Two-point .pwd output")
    tp2: str = Field(default="", description="Two-point .out output")
    tp2a: str = Field(default="", description="Two-point full .out output")
    tp3: str = Field(default="", description="MDS output 1")
    tp4: str = Field(default="", description="MDS output 2")
    tp5: str = Field(default="", description="MDS output 3 (loc list)")
    sm1: str = Field(default="", description="SimAnneal output 1")
    sm2: str = Field(default="", description="SimAnneal output 2")
    phases: str = Field(default="", description="Phase output text")
    maploc: str = Field(default="", description="Map location output")
    mds_smacconf: str = Field(default="", description="MDS SMACOF configuration")
    mds_locikey: str = Field(default="", description="MDS loci key")
    mds_pc: str = Field(default="", description="MDS principal coordinates")

    def is_twopoint(self) -> bool:
        """Check if this is a two-point result."""
        return self.result_type == OrderedResultType.ORT_TWOPOINT

    def is_mds(self) -> bool:
        """Check if this is an MDS result."""
        return self.result_type == OrderedResultType.ORT_MDS

    def is_phase(self) -> bool:
        """Check if this is a phase result."""
        return self.result_type == OrderedResultType.ORT_PHASE

    def get_distance_total(self) -> float:
        """Return the total inter-marker distance."""
        return sum(abs(d) for d in self.distances)


# ---------------------------------------------------------------------------
# Dendrogram and Cluster
# ---------------------------------------------------------------------------


class DenNode(BaseModel):
    """A node in a dendrogram tree.

    Mirrors data/Dendrogram.DenNode inner class.
    """

    number: int = Field(..., description="Node number (1-based)")
    cm_safe_name: Optional[str] = Field(
        None, description="Safe name of the marker (leaf nodes only)"
    )
    distance: float = Field(
        default=0.0, description="Distance value (similarity = 1 - distance)"
    )
    similarity: float = Field(default=1.0, description="Similarity score")
    children: list[DenNode] = Field(
        default_factory=list, description="Child nodes (0 for leaves, 2 for internal)"
    )


class Dendrogram(BaseModel):
    """Dendrogram tree built from clustering analysis.

    The Newick-format string representation is used for compatibility
    with tree visualization libraries.

    Mirrors data/Dendrogram.java.
    """

    root: Optional[DenNode] = Field(None, description="Root node of the tree")
    newick: str = Field(
        default="", description="Newick (NH) format representation"
    )


class Cluster(BaseModel):
    """Cluster analysis result containing linkage groups and dendrogram.

    Mirrors data/Cluster.java.
    """

    name: Optional[str] = Field(None, description="Display name")
    groups: list[LinkageGroup] = Field(
        default_factory=list, description="Linkage groups from clustering"
    )
    summary: Optional[Summary] = Field(
        None, description="Run summary information"
    )
    av_lnk_dendrogram: Optional[Dendrogram] = Field(
        None, description="Average linkage dendrogram"
    )
    sn_lnk_dendrogram: Optional[Dendrogram] = Field(
        None, description="Single linkage dendrogram"
    )


# ---------------------------------------------------------------------------
# Trait and QTL models
# ---------------------------------------------------------------------------


class TraitFile(BaseModel):
    """Trait data file containing phenotypic measurements.

    Mirrors data/TraitFile.java.
    """

    names: list[str] = Field(
        default_factory=list, description="Trait names"
    )
    rows: list[list[float]] = Field(
        default_factory=list,
        description="Data rows: [individual_id, trait1, trait2, ...]",
    )
    enabled: list[bool] = Field(
        default_factory=list, description="Whether each trait is enabled"
    )

    def get_selected_count(self) -> int:
        """Return the number of enabled traits."""
        if not self.enabled:
            return len(self.names)
        return sum(1 for e in self.enabled if e)


class PermResult(BaseModel):
    """Permutation test result.

    Mirrors data/PermResult.java.
    """

    lod_scores: list[float] = Field(
        default_factory=list, description="LOD scores from each permutation"
    )
    num_perms: int = Field(default=0, description="Number of permutations run")
    sig_90: float = Field(
        default=0.0, description="90th percentile significance threshold"
    )
    sig_95: float = Field(
        default=0.0, description="95th percentile significance threshold"
    )


class Trait(BaseModel):
    """QTL analysis result for a single trait.

    Mirrors data/Trait.java.
    """

    name: str = Field(..., description="Trait name")
    positions: list[float] = Field(
        default_factory=list, description="Map positions (cM)"
    )
    lods: list[float] = Field(
        default_factory=list, description="LOD scores at each position"
    )
    lods2: Optional[list[float]] = Field(
        None, description="Secondary LOD scores (two-QTL model)"
    )
    qtl_position: float = Field(default=0.0, description="Estimated QTL position")
    qtl_position2: float = Field(
        default=0.0, description="Second QTL position (two-QTL model)"
    )
    var_explained: float = Field(
        default=0.0, description="Variance explained by QTL"
    )
    var_explained2: float = Field(
        default=0.0, description="Variance explained by second QTL"
    )
    err_ms: float = Field(default=0.0, description="Error mean square")
    err_ms2: float = Field(
        default=0.0, description="Error mean square (two-QTL model)"
    )
    max_lod: float = Field(default=0.0, description="Maximum LOD score")
    max_lod2: float = Field(
        default=0.0, description="Maximum LOD for second QTL"
    )
    qtl_effects: list[str] = Field(
        default_factory=lambda: [""] * 7,
        description="QTL effect estimates",
    )
    se_effects: list[str] = Field(
        default_factory=lambda: [""] * 7,
        description="Standard errors of QTL effects",
    )
    qtl_effects2: Optional[list[str]] = Field(
        None, description="QTL effects for second QTL"
    )
    model_scores: list[list[float]] = Field(
        default_factory=lambda: [[0.0] * 6 for _ in range(10)],
        description="Model comparison scores [10 models x 6 metrics]",
    )
    model_scores_extra: list[list[float]] = Field(
        default_factory=lambda: [[0.0] for _ in range(10)],
        description="Extra model scores",
    )
    simple_model: str = Field(
        default="", description="Simple model output text"
    )
    simple_models: list[str] = Field(
        default_factory=list, description="Simple model IDs"
    )
    simple_model_coefficients: list[str] = Field(
        default_factory=list, description="Simple model coefficient strings"
    )
    best_simple_models: list[str] = Field(
        default_factory=list, description="Best simple model identifiers"
    )
    perm_result: Optional[PermResult] = Field(
        None, description="Permutation test result"
    )


class QTLResult(BaseModel):
    """QTL analysis result containing results for multiple traits.

    Mirrors data/QTLResult.java.
    """

    name: Optional[str] = Field(None, description="Display name")
    traits: list[Trait] = Field(
        default_factory=list, description="Per-trait QTL results"
    )
    qmm: str = Field(default="", description="QTL model matrix text output")
    trait_file: Optional[TraitFile] = Field(
        None, description="Trait file used for this analysis"
    )


# ---------------------------------------------------------------------------
# Phase Result
# ---------------------------------------------------------------------------


class PhaseResult(BaseModel):
    """Phase analysis output text.

    Mirrors data/PhaseResult.java.
    """

    name: Optional[str] = Field(None, description="Display name")
    output: str = Field(
        default="", description="Phase analysis output text"
    )


# ---------------------------------------------------------------------------
# ANOVA models
# ---------------------------------------------------------------------------


class AnovaTraitResult(BaseModel):
    """ANOVA result for a single trait.

    Mirrors data/AnovaTraitResult.java.
    """

    trait_name: str = Field(..., description="Name of the trait")
    marker_names: list[str] = Field(
        default_factory=list, description="Marker names with significant results"
    )
    data: list[str] = Field(
        default_factory=list,
        description="ANOVA data strings corresponding to each marker",
    )


class AnovaResult(BaseModel):
    """ANOVA analysis result containing per-trait results.

    Mirrors data/AnovaResult.java.
    """

    name: Optional[str] = Field(None, description="Display name")
    results: list[AnovaTraitResult] = Field(
        default_factory=list, description="Per-trait ANOVA results"
    )


# ---------------------------------------------------------------------------
# Linkage Map
# ---------------------------------------------------------------------------


class LinkageMapGraph(BaseModel):
    """Linkage map visualization data.

    Mirrors data/LinkageMapGraph.java.
    """

    name: Optional[str] = Field(None, description="Display name")
    linkage_groups: list[LinkageGroup] = Field(
        default_factory=list,
        description="Linkage groups forming the map",
    )


# ---------------------------------------------------------------------------
# Project (top-level container)
# ---------------------------------------------------------------------------


class Project(BaseModel):
    """Top-level project container.

    A project contains the imported linkage group (dataset), any
    trait files, and the log of all analyses performed.

    This mirrors the overall data structure managed by the Java
    application's AppFrame and Project classes.
    """

    name: str = Field(..., description="Project name")
    linkage_groups: list[LinkageGroup] = Field(
        default_factory=list,
        description="Imported linkage groups (datasets)",
    )
    trait_file: Optional[TraitFile] = Field(
        None, description="Associated trait file"
    )
    clusters: list[Cluster] = Field(
        default_factory=list, description="Cluster analysis results"
    )
    ordered_results: list[OrderedResult] = Field(
        default_factory=list, description="Ordered analysis results"
    )
    qtl_results: list[QTLResult] = Field(
        default_factory=list, description="QTL analysis results"
    )
    anova_results: list[AnovaResult] = Field(
        default_factory=list, description="ANOVA analysis results"
    )
    log: list[str] = Field(
        default_factory=list, description="Analysis log entries"
    )

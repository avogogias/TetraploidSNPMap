"""Feature parity verification tests.

Verifies that the new web services architecture supports the same features
as the original TetraploidSNPMap desktop application. These tests check
that all analysis types, file formats, marker operations, and project modes
are properly represented in the new codebase by using importlib to load
modules from each service directory.
"""

import importlib.util
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(REPO, "services", "api-gateway")
COMP_DIR = os.path.join(REPO, "services", "computation")
WORKER_DIR = os.path.join(REPO, "services", "worker")


def _load_module(name, service_dir, dotted_path):
    """Load a module from a specific service directory."""
    parts = dotted_path.split(".")
    file_path = os.path.join(service_dir, *parts) + ".py"
    if not os.path.exists(file_path):
        # Try as package __init__
        file_path = os.path.join(service_dir, *parts, "__init__.py")
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    # Temporarily adjust sys.path so relative imports work
    old_path = sys.path.copy()
    sys.path.insert(0, service_dir)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path = old_path
    return mod


# Pre-load modules from each service to avoid import conflicts
# API Gateway modules
_proj_schema = _load_module("api_project_schema", API_DIR, "app.schemas.project")
_analysis_schema = _load_module("api_analysis_schema", API_DIR, "app.schemas.analysis")
_dataset_schema = _load_module("api_dataset_schema", API_DIR, "app.schemas.dataset")

# Worker modules (task handlers, computation modules)
sys.path.insert(0, WORKER_DIR)
from app.task_handlers import (
    handle_clustering, handle_twopoint, handle_mds,
    handle_phase, handle_qtl, handle_permutation,
    handle_anova, handle_linkage_map,
)
from app.computation.linkage_map import generate_linkage_map
from app.computation.clustering import _compute_chimatrix_python, _cluster_scipy_fallback
from app.computation.mds import _run_mds_python_fallback
from app.computation.anova import _anova_python_fallback
sys.path.remove(WORKER_DIR)


class TestProjectModes:
    """Verify all three project modes from the desktop app are supported."""

    def test_snp_mode_supported(self):
        p = _proj_schema.ProjectCreate(name="SNP Test", mode="SNP")
        assert p.mode == "SNP"

    def test_qtl_mode_supported(self):
        p = _proj_schema.ProjectCreate(name="QTL Test", mode="QTL")
        assert p.mode == "QTL"

    def test_nonsnp_mode_supported(self):
        p = _proj_schema.ProjectCreate(name="NONSNP Test", mode="NONSNP")
        assert p.mode == "NONSNP"


class TestAnalysisTypes:
    """Verify all 8 analysis types from the desktop app are supported."""

    EXPECTED_TYPES = [
        "cluster", "two_point", "mds", "phase",
        "qtl", "anova", "permutation", "linkage_map",
    ]

    def test_all_types_in_api_schema(self):
        for atype in self.EXPECTED_TYPES:
            job = _analysis_schema.AnalysisJobCreate(analysis_type=atype, params={})
            assert job.analysis_type == atype

    def test_cluster_params(self):
        p = _analysis_schema.ClusterParams(similarity_threshold=0.9)
        assert 0.0 <= p.similarity_threshold <= 1.0

    def test_twopoint_params(self):
        p = _analysis_schema.TwoPointParams(exclude_duplicates=True, full_output=True)
        assert p.exclude_duplicates is True

    def test_mds_params(self):
        p = _analysis_schema.MDSParams(dimensions=3)
        assert p.dimensions in (2, 3)

    def test_phase_params(self):
        p = _analysis_schema.PhaseParams()
        assert p is not None

    def test_qtl_params(self):
        p = _analysis_schema.QTLParams(model_type="interval_mapping", traits=["yield"])
        assert p.model_type == "interval_mapping"

    def test_anova_params(self):
        p = _analysis_schema.AnovaParams(traits=["height"])
        assert "height" in p.traits

    def test_permutation_params(self):
        p = _analysis_schema.PermutationParams(n_perms=500)
        assert p.n_perms == 500

    def test_linkage_map_generation(self):
        result = generate_linkage_map(
            {"ordered_markers": [{"name": "M1"}], "distances": []}, {}
        )
        assert "groups" in result


class TestFileFormats:
    """Verify all original file formats are supported."""

    def test_snploc_format(self):
        d = _dataset_schema.DatasetUpload(type="snploc")
        assert d.type == "snploc"

    def test_qua_format(self):
        d = _dataset_schema.DatasetUpload(type="qua")
        assert d.type == "qua"

    def test_loc_format(self):
        d = _dataset_schema.DatasetUpload(type="loc")
        assert d.type == "loc"


class TestMarkerOperations:
    """Verify marker management operations match desktop app capabilities."""

    def test_marker_selection_criteria(self):
        r = _dataset_schema.MarkerSelectionRequest(criteria={"chi_sig_max": 0.05})
        assert r.criteria is not None

    def test_marker_name_selection(self):
        r = _dataset_schema.MarkerSelectionRequest(marker_names=["M1", "M2"])
        assert len(r.marker_names) == 2

    def test_marker_move(self):
        r = _dataset_schema.MarkerMoveRequest(target_group="LG3")
        assert r.target_group == "LG3"


_comp_config = _load_module("comp_config", COMP_DIR, "app.config")


class TestFortranBinaryMapping:
    """Verify Fortran binaries are properly configured for each analysis."""

    def test_all_binary_configs_present(self):
        s = _comp_config.Settings()
        required = [
            s.BINARY_SNPMATCH, s.BINARY_RECALC_CHISIG,
            s.BINARY_SNPCLUSTER, s.BINARY_CHIMATRIX,
            s.BINARY_SNPTWOPOINT, s.BINARY_PHASE,
            s.BINARY_SNPQTL, s.BINARY_READQTL,
            s.BINARY_SNPQTLPERM, s.BINARY_SIMPLE_MODEL,
            s.BINARY_SIMPLE_MODEL_ADDITIVE,
            s.BINARY_FINDGENO, s.BINARY_ANOVA,
        ]
        for name in required:
            assert name, "Binary name must not be empty"
            assert str(s.get_binary_path(name)).endswith(name)

    def test_matching_original_binary_names(self):
        s = _comp_config.Settings()
        assert "SNPmatch" in s.BINARY_SNPMATCH
        assert "SNPcluster" in s.BINARY_SNPCLUSTER
        assert "SNPcexp" in s.BINARY_SNPTWOPOINT
        assert "phasev6" in s.BINARY_PHASE
        assert "SNP_QTL" in s.BINARY_SNPQTL
        assert "QTLperm" in s.BINARY_SNPQTLPERM


class TestRScriptMapping:
    """Verify R scripts are properly configured."""

    def test_r_script_paths(self):
        s = _comp_config.Settings()
        for script in ["General_estimation.R", "cluster.R", "threeD.R"]:
            assert str(s.get_r_script_path(script)).endswith(script)


class TestWorkerTaskRegistration:
    """Verify all analysis types have corresponding worker task handlers."""

    def test_all_tasks_defined(self):
        handlers = [
            handle_clustering, handle_twopoint, handle_mds,
            handle_phase, handle_qtl, handle_permutation,
            handle_anova, handle_linkage_map,
        ]
        assert len(handlers) == 8
        for h in handlers:
            assert callable(h)


class TestComputationFallbacks:
    """Verify Python fallbacks exist for when Fortran/R binaries are unavailable."""

    def test_clustering_fallbacks(self):
        assert callable(_compute_chimatrix_python)
        assert callable(_cluster_scipy_fallback)

    def test_mds_fallback(self):
        assert callable(_run_mds_python_fallback)

    def test_anova_fallback(self):
        assert callable(_anova_python_fallback)


class TestDataLimits:
    """Verify configured limits match the original application."""

    def test_limits_match_original(self):
        s = _comp_config.Settings()
        assert s.MAX_MARKERS == 8000
        assert s.MAX_INDIVIDUALS == 300
        assert s.MAX_PERMS == 500

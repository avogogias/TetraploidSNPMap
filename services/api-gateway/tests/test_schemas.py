"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.analysis import (
    AnalysisJobCreate,
    ClusterParams,
    TwoPointParams,
    MDSParams,
    QTLParams,
    AnovaParams,
    PermutationParams,
)
from app.schemas.dataset import (
    DatasetUpload,
    MarkerSelectionRequest,
    MarkerMoveRequest,
    MarkerResponse,
)


class TestProjectCreate:
    def test_valid_snp(self):
        p = ProjectCreate(name="Test", mode="SNP")
        assert p.name == "Test"
        assert p.mode == "SNP"

    def test_valid_qtl(self):
        p = ProjectCreate(name="QTL Study", mode="QTL")
        assert p.mode == "QTL"

    def test_valid_nonsnp(self):
        p = ProjectCreate(name="RFLP", mode="NONSNP")
        assert p.mode == "NONSNP"

    def test_default_mode(self):
        p = ProjectCreate(name="Default")
        assert p.mode == "SNP"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_long_name_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="x" * 256)

    def test_invalid_mode_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="Test", mode="INVALID")


class TestAnalysisJobCreate:
    def test_valid_cluster(self):
        job = AnalysisJobCreate(analysis_type="cluster", params={"similarity_threshold": 0.9})
        assert job.analysis_type == "cluster"

    def test_all_types_valid(self):
        for t in ["cluster", "two_point", "mds", "phase", "qtl", "anova", "permutation", "linkage_map"]:
            job = AnalysisJobCreate(analysis_type=t, params={})
            assert job.analysis_type == t

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            AnalysisJobCreate(analysis_type="bogus", params={})

    def test_optional_dataset_id(self):
        job = AnalysisJobCreate(analysis_type="cluster", params={})
        assert job.dataset_id is None

        job2 = AnalysisJobCreate(analysis_type="cluster", params={}, dataset_id=42)
        assert job2.dataset_id == 42


class TestClusterParams:
    def test_defaults(self):
        p = ClusterParams()
        assert p.similarity_threshold == 0.9

    def test_custom(self):
        p = ClusterParams(similarity_threshold=0.7)
        assert p.similarity_threshold == 0.7

    def test_out_of_range(self):
        with pytest.raises(ValidationError):
            ClusterParams(similarity_threshold=1.5)
        with pytest.raises(ValidationError):
            ClusterParams(similarity_threshold=-0.1)


class TestTwoPointParams:
    def test_defaults(self):
        p = TwoPointParams()
        assert p.exclude_duplicates is False
        assert p.full_output is False


class TestMDSParams:
    def test_defaults(self):
        p = MDSParams()
        assert p.dimensions == 3

    def test_valid_2d(self):
        p = MDSParams(dimensions=2)
        assert p.dimensions == 2

    def test_invalid_dimensions(self):
        with pytest.raises(ValidationError):
            MDSParams(dimensions=1)
        with pytest.raises(ValidationError):
            MDSParams(dimensions=4)


class TestQTLParams:
    def test_valid(self):
        p = QTLParams(model_type="interval_mapping", traits=["yield"])
        assert p.model_type == "interval_mapping"
        assert p.traits == ["yield"]

    def test_empty_traits_rejected(self):
        with pytest.raises(ValidationError):
            QTLParams(model_type="full", traits=[])


class TestPermutationParams:
    def test_defaults(self):
        p = PermutationParams()
        assert p.n_perms == 500

    def test_custom(self):
        p = PermutationParams(n_perms=1000)
        assert p.n_perms == 1000

    def test_zero_rejected(self):
        with pytest.raises(ValidationError):
            PermutationParams(n_perms=0)


class TestDatasetUpload:
    def test_valid_snploc(self):
        d = DatasetUpload(type="snploc")
        assert d.type == "snploc"

    def test_valid_qua(self):
        d = DatasetUpload(type="qua")
        assert d.type == "qua"

    def test_valid_loc(self):
        d = DatasetUpload(type="loc")
        assert d.type == "loc"

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            DatasetUpload(type="csv")


class TestMarkerSelectionRequest:
    def test_criteria_based(self):
        r = MarkerSelectionRequest(criteria={"chi_sig_max": 0.05})
        assert r.criteria == {"chi_sig_max": 0.05}

    def test_name_based(self):
        r = MarkerSelectionRequest(marker_names=["mkr1", "mkr2"])
        assert r.marker_names == ["mkr1", "mkr2"]

    def test_empty(self):
        r = MarkerSelectionRequest()
        assert r.criteria is None
        assert r.marker_names is None


class TestMarkerMoveRequest:
    def test_valid(self):
        r = MarkerMoveRequest(target_group="LG5")
        assert r.target_group == "LG5"

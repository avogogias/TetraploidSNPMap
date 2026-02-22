"""Tests for the Computation Service data models (Pydantic domain objects)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.models import (
    MarkerType,
    RatioCode,
    OrderedResultType,
    AlleleDosage,
    AlleleState,
    Allele,
    Marker,
    CMarker,
    LinkageGroup,
    OrderedResult,
    Cluster,
    Dendrogram,
    Trait,
    QTLResult,
    PermResult,
    AnovaTraitResult,
    AnovaResult,
    PhaseResult,
    LinkageMapGraph,
    Project,
)


class TestMarkerType:
    def test_enum_values(self):
        assert MarkerType.UNKNOWN == 0
        assert MarkerType.RFLP == 1
        assert MarkerType.AFLP == 2
        assert MarkerType.SSR == 3
        assert MarkerType.SNP == 4

    def test_enum_count(self):
        assert len(MarkerType) == 5


class TestRatioCode:
    def test_enum_values(self):
        assert RatioCode.UNKNOWN == 0
        assert RatioCode.R1_1 == 1
        assert RatioCode.R3_1 == 3


class TestOrderedResultType:
    def test_enum_values(self):
        assert OrderedResultType.ORT_TWOPOINT == 1
        assert OrderedResultType.ORT_MDS == 2
        assert OrderedResultType.ORT_PHASE == 5


class TestAlleleDosage:
    def test_valid_dosages(self):
        for d in [0, 1, 2, 3, 4, 9]:
            ad = AlleleDosage(dosage=d)
            assert ad.dosage == d

    def test_invalid_dosage(self):
        with pytest.raises(Exception):
            AlleleDosage(dosage=10)


class TestAlleleState:
    def test_valid_states(self):
        for s in [0, 1, 9]:
            a = AlleleState(state=s)
            assert a.state == s


class TestMarker:
    def test_basic_creation(self):
        m = Marker(name="SNP001")
        assert m.name == "SNP001"
        assert m.type == MarkerType.UNKNOWN

    def test_snp_marker(self):
        m = Marker(
            name="SNP001",
            type=MarkerType.SNP,
            parent_dosages=["2", "1"],
            chi=3.5,
            chisig=0.06,
            status="OK",
        )
        assert m.type == MarkerType.SNP
        assert m.parent_dosages == ["2", "1"]
        assert m.chi == 3.5
        assert m.status == "OK"

    def test_can_enable_ok_snp(self):
        m = Marker(name="M1", type=MarkerType.SNP, chisig=0.05, status="OK")
        assert m.can_enable() is True

    def test_can_enable_np_snp(self):
        m = Marker(name="M2", type=MarkerType.SNP, chisig=0.05, status="NP")
        assert m.can_enable() is False

    def test_can_enable_dr_snp(self):
        m = Marker(name="M3", type=MarkerType.SNP, chisig=0.05, status="DR")
        assert m.can_enable() is False

    def test_can_enable_low_chisig(self):
        m = Marker(name="M4", type=MarkerType.SNP, chisig=0.0001, status="OK")
        assert m.can_enable() is False

    def test_get_individual_count_empty(self):
        m = Marker(name="M1")
        assert m.get_individual_count() == 0


class TestCMarker:
    def test_wrapping(self):
        m = Marker(name="TestMkr")
        cm = CMarker(marker=m, checked=True, safe_name="mkr001")
        assert cm.checked is True
        assert cm.safe_name == "mkr001"
        assert cm.marker.name == "TestMkr"

    def test_safe_name_suffix(self):
        m = Marker(name="M1")
        cm = CMarker(marker=m, checked=True, safe_name="mkr042")
        assert cm.safe_name_suffix == 42

    def test_make_safe_name_snp(self):
        name = CMarker.make_safe_name(1, MarkerType.SNP)
        assert name == "mkr000001"

    def test_make_safe_name_nonsnp(self):
        name = CMarker.make_safe_name(1, MarkerType.RFLP)
        assert name == "mkr001"


class TestLinkageGroup:
    def test_creation(self):
        lg = LinkageGroup(name="LG1")
        assert lg.name == "LG1"
        assert lg.markers == []

    def test_with_markers(self):
        m1 = CMarker(marker=Marker(name="M1"), checked=True, safe_name="mkr001")
        m2 = CMarker(marker=Marker(name="M2"), checked=False, safe_name="mkr002")
        lg = LinkageGroup(name="LG1", markers=[m1, m2])
        assert len(lg.markers) == 2


class TestCluster:
    def test_creation(self):
        c = Cluster(groups=[])
        assert c.groups == []


class TestDendrogram:
    def test_creation(self):
        d = Dendrogram(newick="(A,B);")
        assert d.newick == "(A,B);"


class TestTrait:
    def test_creation(self):
        t = Trait(name="yield")
        assert t.name == "yield"
        assert t.positions == []
        assert t.lods == []

    def test_with_data(self):
        t = Trait(name="yield", positions=[0.0, 5.0, 10.0], lods=[0.5, 3.2, 1.1])
        assert len(t.positions) == 3
        assert len(t.lods) == 3


class TestOrderedResult:
    def test_creation(self):
        o = OrderedResult()
        assert hasattr(o, "linkage_group")
        assert hasattr(o, "result_type")


class TestProject:
    def test_creation(self):
        p = Project(name="Test Project")
        assert p.name == "Test Project"
        assert p.linkage_groups == []

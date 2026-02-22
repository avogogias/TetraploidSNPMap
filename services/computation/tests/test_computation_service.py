"""Tests for the Computation Service - config, health endpoint, and data models."""

import os
import pytest
from pathlib import Path

# Override env before importing
os.environ["TPM_SCRATCH_DIR"] = "/tmp/tpmap_test"
os.environ["TPM_BINARIES_DIR"] = "/tmp/tpmap_test_bin"
os.environ["TPM_R_SCRIPTS_DIR"] = "/tmp/tpmap_test_r"


class TestComputationConfig:
    """Test computation service configuration."""

    def test_default_settings(self):
        from app.config import Settings
        s = Settings()
        assert s.MAX_MARKERS == 8000
        assert s.MAX_INDIVIDUALS == 300
        assert s.MAX_PERMS == 500
        assert s.SUBPROCESS_TIMEOUT == 3600

    def test_get_binary_path(self):
        from app.config import Settings
        s = Settings()
        path = s.get_binary_path("SNPmatch_noimsl")
        assert path == Path(s.BINARIES_DIR) / "SNPmatch_noimsl"

    def test_get_r_script_path(self):
        from app.config import Settings
        s = Settings()
        path = s.get_r_script_path("General_estimation.R")
        assert path == Path(s.R_SCRIPTS_DIR) / "General_estimation.R"

    def test_get_r_env(self):
        from app.config import Settings
        s = Settings()
        env = s.get_r_env()
        assert "R_LIBS" in env
        assert "R_LIBS_USER" in env

    def test_binary_names_configured(self):
        from app.config import Settings
        s = Settings()
        assert s.BINARY_SNPMATCH == "SNPmatch_noimsl"
        assert s.BINARY_SNPCLUSTER == "SNPcluster_noimsl"
        assert s.BINARY_CHIMATRIX == "cluster_chimatrixonly"
        assert s.BINARY_SNPTWOPOINT == "SNPcexp_noimsl_dupcheck"
        assert s.BINARY_PHASE == "phasev6_noimsl"
        assert s.BINARY_SNPQTL == "SNP_QTL_newinput"
        assert s.BINARY_SNPQTLPERM == "SNP_QTLperm_noimsl"
        assert s.BINARY_SIMPLE_MODEL == "simple_model"
        assert s.BINARY_ANOVA == "anova"


class TestHealthEndpoint:
    """Test computation service health check."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        from httpx import AsyncClient, ASGITransport

        # Ensure scratch dir exists for health check
        os.makedirs("/tmp/tpmap_test", exist_ok=True)

        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "computation"
        assert "max_markers" in body
        assert body["max_markers"] == 8000
        assert "max_individuals" in body
        assert "r_available" in body
        assert "scratch_dir" in body


class TestDataModels:
    """Test computation domain data models."""

    def test_marker_type_enum(self):
        from app.data.models import MarkerType
        assert MarkerType.SNP == 4
        assert MarkerType.RFLP == 1
        assert MarkerType.AFLP == 2
        assert MarkerType.SSR == 3

    def test_ratio_code_enum(self):
        from app.data.models import RatioCode
        # RatioCode should have standard segregation ratios
        assert hasattr(RatioCode, "SxN") or len(list(RatioCode)) > 0

    def test_allele_dosage_model(self):
        from app.data.models import AlleleDosage
        d = AlleleDosage(dosage=2)
        assert d.dosage == 2

    def test_allele_dosage_unknown(self):
        from app.data.models import AlleleDosage
        d = AlleleDosage(dosage=9)
        assert d.dosage == 9

    def test_marker_model(self):
        from app.data.models import Marker
        m = Marker(name="TestMarker")
        assert m.name == "TestMarker"

    def test_cmarker_model(self):
        from app.data.models import CMarker, Marker
        m = Marker(name="Orig")
        cm = CMarker(marker=m, checked=True, safe_name="mkr001")
        assert cm.checked is True
        assert cm.safe_name == "mkr001"

    def test_linkage_group(self):
        from app.data.models import LinkageGroup
        lg = LinkageGroup(name="LG1")
        assert lg.name == "LG1"

    def test_ordered_result(self):
        from app.data.models import OrderedResult
        o = OrderedResult()
        assert hasattr(o, "linkage_group")

    def test_cluster_model(self):
        from app.data.models import Cluster
        c = Cluster()
        assert hasattr(c, "groups") or hasattr(c, "dendrogram")

    def test_trait_model(self):
        from app.data.models import Trait
        t = Trait(name="yield")
        assert t.name == "yield"

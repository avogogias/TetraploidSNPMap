"""Tests for the Computation Service configuration."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import Settings


class TestSettings:
    def test_limits(self):
        s = Settings()
        assert s.MAX_MARKERS == 8000
        assert s.MAX_INDIVIDUALS == 300
        assert s.MAX_PERMS == 500
        assert s.SUBPROCESS_TIMEOUT == 3600

    def test_binary_names(self):
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

    def test_get_binary_path(self):
        s = Settings()
        p = s.get_binary_path("SNPmatch_noimsl")
        assert p == Path(s.BINARIES_DIR) / "SNPmatch_noimsl"

    def test_get_r_script_path(self):
        s = Settings()
        p = s.get_r_script_path("General_estimation.R")
        assert p == Path(s.R_SCRIPTS_DIR) / "General_estimation.R"

    def test_get_r_env(self):
        s = Settings()
        env = s.get_r_env()
        assert "R_LIBS" in env
        assert "R_LIBS_USER" in env

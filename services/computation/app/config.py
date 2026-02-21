"""Configuration settings for the Computation Service.

Uses pydantic-settings to manage configuration via environment variables.
All paths and limits mirror the original Java Prefs.java configuration.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        SCRATCH_DIR: Temporary working directory for analysis jobs.
            Fortran executables and R scripts write their I/O files here.
        BINARIES_DIR: Path to the directory containing compiled Fortran executables.
        R_SCRIPTS_DIR: Path to the directory containing R analysis scripts.
        RSCRIPT_PATH: Full path to the Rscript executable.
        R_LIBS: Path to R library packages (maps to R_LIBS env var).
        R_LIBS_USER: Path to user R library packages (maps to R_LIBS_USER env var).
        REDIS_URL: Redis connection URL used as the Celery broker and result backend.
        MAX_MARKERS: Maximum number of loci (markers) allowed per dataset.
            Corresponds to LinkageGroup.verify() limit of 8000.
        MAX_INDIVIDUALS: Maximum number of individuals allowed per dataset.
            Corresponds to LinkageGroup.verify() limit of 300.
        MAX_PERMS: Maximum number of permutations for permutation testing.
        SUBPROCESS_TIMEOUT: Default timeout in seconds for Fortran/R subprocesses.
        MARKERNAME_MAXLEN: Maximum length for marker names.
        TRAITNAME_MAXLEN: Maximum length for trait names.
    """

    SCRATCH_DIR: str = "/tmp/tpmap"
    BINARIES_DIR: str = "/opt/tpmap/binaries"
    R_SCRIPTS_DIR: str = "/opt/tpmap/r-scripts"
    RSCRIPT_PATH: str = "/usr/bin/Rscript"
    R_LIBS: str = "/opt/tpmap/R/library"
    R_LIBS_USER: str = "/opt/tpmap/R/library"
    REDIS_URL: str = "redis://localhost:6379/0"
    MAX_MARKERS: int = 8000
    MAX_INDIVIDUALS: int = 300
    MAX_PERMS: int = 500
    SUBPROCESS_TIMEOUT: int = 3600
    MARKERNAME_MAXLEN: int = 20
    TRAITNAME_MAXLEN: int = 20

    # Fortran binary names (appended to BINARIES_DIR)
    BINARY_SNPMATCH: str = "SNPmatch_noimsl"
    BINARY_RECALC_CHISIG: str = "recalc_chisig"
    BINARY_SNPCLUSTER: str = "SNPcluster_noimsl"
    BINARY_CHIMATRIX: str = "cluster_chimatrixonly"
    BINARY_SNPTWOPOINT: str = "SNPcexp_noimsl_dupcheck"
    BINARY_PHASE: str = "phasev6_noimsl"
    BINARY_SNPQTL: str = "SNP_QTL_newinput"
    BINARY_READQTL: str = "Read_QTLdata"
    BINARY_SNPQTLPERM: str = "SNP_QTLperm_noimsl"
    BINARY_SIMPLE_MODEL: str = "simple_model"
    BINARY_SIMPLE_MODEL_ADDITIVE: str = "simple_model_additive"
    BINARY_FINDGENO: str = "findgeno"
    BINARY_CLUSTER: str = "cluster"
    BINARY_SIMMATCH: str = "simmatch"
    BINARY_ANOVA: str = "anova"
    BINARY_PERM: str = "perm"
    BINARY_TWOPOINT: str = "twopoint"
    BINARY_RIPPLE: str = "ripple"
    BINARY_SIMANNEAL: str = "simanneal"
    BINARY_QTL: str = "realoneparrecon"

    class Config:
        env_prefix = "TPM_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_binary_path(self, binary_name: str) -> Path:
        """Return the full path to a Fortran binary executable.

        Args:
            binary_name: The name of the binary (one of the BINARY_* settings).

        Returns:
            Full path to the binary executable.
        """
        return Path(self.BINARIES_DIR) / binary_name

    def get_r_script_path(self, script_name: str) -> Path:
        """Return the full path to an R script.

        Args:
            script_name: The filename of the R script (e.g., 'General_estimation.R').

        Returns:
            Full path to the R script.
        """
        return Path(self.R_SCRIPTS_DIR) / script_name

    def get_r_env(self) -> dict[str, str]:
        """Return environment variables required for R subprocess execution.

        Returns:
            Dictionary with R_LIBS and R_LIBS_USER set.
        """
        return {
            "R_LIBS": self.R_LIBS,
            "R_LIBS_USER": self.R_LIBS_USER,
        }


settings = Settings()

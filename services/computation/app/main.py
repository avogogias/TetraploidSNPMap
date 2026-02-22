"""FastAPI application entry point for the Computation Service.

This service wraps the Fortran executables and R scripts that form
the computational backend of TetraploidSNPMap, exposing them as
HTTP endpoints for the web frontend.
"""

import logging
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


def _verify_binary(name: str, path: Path) -> bool:
    """Check whether a Fortran binary exists and is executable.

    Args:
        name: Human-readable name of the binary for logging.
        path: Full filesystem path to the binary.

    Returns:
        True if the binary exists and is executable, False otherwise.
    """
    if not path.exists():
        logger.warning("Binary not found: %s at %s", name, path)
        return False
    if not os.access(path, os.X_OK):
        logger.warning("Binary not executable: %s at %s", name, path)
        return False
    logger.info("Binary OK: %s at %s", name, path)
    return True


def _verify_r_available() -> bool:
    """Check whether Rscript is available on the system.

    Returns:
        True if Rscript is found at the configured path, False otherwise.
    """
    rscript = Path(settings.RSCRIPT_PATH)
    if not rscript.exists():
        # Fall back to checking PATH
        if shutil.which("Rscript") is None:
            logger.warning(
                "Rscript not found at %s and not on PATH", settings.RSCRIPT_PATH
            )
            return False
    logger.info("Rscript OK: %s", settings.RSCRIPT_PATH)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler that runs startup and shutdown logic.

    On startup:
      - Creates the scratch directory if it does not exist.
      - Verifies that Fortran binaries are accessible.
      - Verifies that Rscript is available.

    These checks are non-fatal (warnings only) so the service can start
    even if some binaries are missing, allowing partial functionality
    and easier development/testing.
    """
    # Startup
    logger.info("Computation service starting up...")

    # Ensure scratch directory exists
    scratch = Path(settings.SCRATCH_DIR)
    scratch.mkdir(parents=True, exist_ok=True)
    logger.info("Scratch directory: %s", scratch)

    # Verify key Fortran binaries
    binaries_to_check = {
        "SNPmatch (FindSNPGeno)": settings.BINARY_SNPMATCH,
        "recalc_chisig": settings.BINARY_RECALC_CHISIG,
        "SNPcluster": settings.BINARY_SNPCLUSTER,
        "cluster_chimatrixonly": settings.BINARY_CHIMATRIX,
        "SNP TwoPoint": settings.BINARY_SNPTWOPOINT,
        "Phase": settings.BINARY_PHASE,
        "SNP QTL": settings.BINARY_SNPQTL,
        "Read QTL": settings.BINARY_READQTL,
        "SNP QTL Perm": settings.BINARY_SNPQTLPERM,
        "Simple Model": settings.BINARY_SIMPLE_MODEL,
    }

    available_count = 0
    for display_name, binary_name in binaries_to_check.items():
        binary_path = settings.get_binary_path(binary_name)
        if _verify_binary(display_name, binary_path):
            available_count += 1

    logger.info(
        "Fortran binaries: %d/%d available",
        available_count,
        len(binaries_to_check),
    )

    # Verify R availability
    _verify_r_available()

    # Verify R scripts directory
    r_scripts = Path(settings.R_SCRIPTS_DIR)
    if r_scripts.is_dir():
        scripts = list(r_scripts.glob("*.R"))
        logger.info("R scripts directory: %s (%d scripts)", r_scripts, len(scripts))
    else:
        logger.warning("R scripts directory not found: %s", r_scripts)

    logger.info("Computation service startup complete.")

    yield

    # Shutdown
    logger.info("Computation service shutting down.")


app = FastAPI(
    title="TetraploidSNPMap Computation Service",
    description=(
        "Wraps Fortran executables and R scripts for genetic linkage "
        "mapping analysis in tetraploid organisms. Provides endpoints "
        "for SNP genotype finding, clustering, two-point analysis, MDS "
        "ordering, phase analysis, QTL mapping, permutation testing, "
        "ANOVA, and linkage map generation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for web frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns basic service status including availability of external
    dependencies (Fortran binaries, R, scratch directory).

    Returns:
        Dictionary with service status information.
    """
    scratch_ok = Path(settings.SCRATCH_DIR).is_dir()
    r_ok = Path(settings.RSCRIPT_PATH).exists() or shutil.which("Rscript") is not None
    binaries_dir_ok = Path(settings.BINARIES_DIR).is_dir()

    return {
        "status": "healthy",
        "service": "computation",
        "scratch_dir": scratch_ok,
        "r_available": r_ok,
        "binaries_dir": binaries_dir_ok,
        "max_markers": settings.MAX_MARKERS,
        "max_individuals": settings.MAX_INDIVIDUALS,
    }

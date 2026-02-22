"""Celery worker for executing long-running analysis jobs.

This worker handles compute-intensive genetic analysis tasks including
clustering, two-point analysis, MDS ordering, phase estimation, QTL
analysis, and permutation testing. Each task wraps Fortran executables
or R scripts that perform the actual computation.
"""

import json
import os
import logging
import traceback
from datetime import datetime

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure

logger = logging.getLogger(__name__)

# Configure Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery("tpm_worker", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,       # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=86400,       # Results expire after 24 hours
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log when a task starts."""
    logger.info(f"Task {task_id} ({sender.name}) starting")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """Log when a task completes."""
    logger.info(f"Task {task_id} ({sender.name}) completed")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log when a task fails."""
    logger.error(f"Task {task_id} ({sender.name}) failed: {exception}")


@app.task(bind=True, name="analyses.run_clustering")
def run_clustering(self, project_id: str, dataset_id: str, params: dict) -> dict:
    """Run hierarchical clustering analysis on marker data.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset/linkage group identifier.
        params: Clustering parameters including similarity_threshold.

    Returns:
        Dictionary with cluster groups and dendrogram data.
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Initializing clustering"})

        from app.task_handlers import handle_clustering
        result = handle_clustering(project_id, dataset_id, params)

        return {
            "status": "COMPLETED",
            "analysis_type": "cluster",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Clustering failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "cluster",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.run_twopoint")
def run_twopoint(self, project_id: str, dataset_id: str, params: dict) -> dict:
    """Run two-point analysis for pairwise recombination frequency estimation.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset/linkage group identifier.
        params: Two-point parameters including exclude_duplicates, full_output.

    Returns:
        Dictionary with pairwise distances and ordered markers.
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Running two-point analysis"})

        from app.task_handlers import handle_twopoint
        result = handle_twopoint(project_id, dataset_id, params)

        return {
            "status": "COMPLETED",
            "analysis_type": "twopoint",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Two-point analysis failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "twopoint",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.run_mds")
def run_mds(self, project_id: str, dataset_id: str, twopoint_job_id: str, params: dict) -> dict:
    """Run multidimensional scaling for marker ordering.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset/linkage group identifier.
        twopoint_job_id: The ID of the preceding two-point analysis job.
        params: MDS parameters.

    Returns:
        Dictionary with ordered markers, distances, and 3D coordinates.
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Running MDS ordering"})

        from app.task_handlers import handle_mds
        result = handle_mds(project_id, dataset_id, twopoint_job_id, params)

        return {
            "status": "COMPLETED",
            "analysis_type": "mds",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"MDS analysis failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "mds",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.run_phase")
def run_phase(self, project_id: str, dataset_id: str, mds_job_id: str, twopoint_job_id: str) -> dict:
    """Run phase estimation analysis.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset/linkage group identifier.
        mds_job_id: The ID of the preceding MDS analysis job.
        twopoint_job_id: The ID of the preceding two-point analysis job.

    Returns:
        Dictionary with phase assignments for each marker.
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Running phase analysis"})

        from app.task_handlers import handle_phase
        result = handle_phase(project_id, dataset_id, mds_job_id, twopoint_job_id)

        return {
            "status": "COMPLETED",
            "analysis_type": "phase",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Phase analysis failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "phase",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.run_qtl")
def run_qtl(self, project_id: str, dataset_id: str, ordered_job_id: str, params: dict) -> dict:
    """Run QTL (Quantitative Trait Locus) analysis.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset identifier.
        ordered_job_id: The ID of the ordered result to use.
        params: QTL parameters including traits and model type.

    Returns:
        Dictionary with QTL results per trait (LOD scores, positions).
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Running QTL analysis"})

        from app.task_handlers import handle_qtl
        result = handle_qtl(project_id, dataset_id, ordered_job_id, params)

        return {
            "status": "COMPLETED",
            "analysis_type": "qtl",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"QTL analysis failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "qtl",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.run_permutation")
def run_permutation(self, project_id: str, dataset_id: str, ordered_job_id: str, params: dict) -> dict:
    """Run permutation testing for QTL significance thresholds.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset identifier.
        ordered_job_id: The ID of the ordered result.
        params: Permutation parameters including n_perms.

    Returns:
        Dictionary with permutation test results and significance thresholds.
    """
    try:
        n_perms = params.get("n_perms", 500)
        self.update_state(
            state="RUNNING",
            meta={"step": f"Running permutation test (0/{n_perms})"},
        )

        from app.task_handlers import handle_permutation
        result = handle_permutation(
            project_id, dataset_id, ordered_job_id, params,
            progress_callback=lambda current, total: self.update_state(
                state="RUNNING",
                meta={"step": f"Running permutation test ({current}/{total})"},
            ),
        )

        return {
            "status": "COMPLETED",
            "analysis_type": "permutation",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Permutation test failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "permutation",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.run_anova")
def run_anova(self, project_id: str, dataset_id: str, params: dict) -> dict:
    """Run Analysis of Variance on trait data.

    Args:
        project_id: The project identifier.
        dataset_id: The dataset identifier.
        params: ANOVA parameters including trait selection.

    Returns:
        Dictionary with ANOVA results per trait.
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Running ANOVA"})

        from app.task_handlers import handle_anova
        result = handle_anova(project_id, dataset_id, params)

        return {
            "status": "COMPLETED",
            "analysis_type": "anova",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"ANOVA failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "anova",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }


@app.task(bind=True, name="analyses.generate_linkage_map")
def generate_linkage_map(self, project_id: str, ordered_job_id: str, params: dict) -> dict:
    """Generate a linkage map from ordered analysis results.

    Args:
        project_id: The project identifier.
        ordered_job_id: The ID of the ordered result.
        params: Map generation parameters.

    Returns:
        Dictionary with linkage map data (groups, markers, positions).
    """
    try:
        self.update_state(state="RUNNING", meta={"step": "Generating linkage map"})

        from app.task_handlers import handle_linkage_map
        result = handle_linkage_map(project_id, ordered_job_id, params)

        return {
            "status": "COMPLETED",
            "analysis_type": "linkage_map",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Linkage map generation failed: {traceback.format_exc()}")
        return {
            "status": "FAILED",
            "analysis_type": "linkage_map",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }

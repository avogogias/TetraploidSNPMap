"""Task handler implementations that bridge Celery tasks to the computation service.

Each handler loads data from the project storage, invokes the appropriate
analysis functions from the computation service, and stores results back.
"""

import json
import os
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Project data is stored as JSON files on a shared volume
DATA_DIR = os.getenv("PROJECT_STORAGE_PATH", "/data/projects")
RESULTS_DIR = os.getenv("RESULTS_STORAGE_PATH", "/data/results")


def _load_project_data(project_id: str, dataset_id: str) -> dict:
    """Load dataset data from project storage."""
    data_path = Path(DATA_DIR) / project_id / "datasets" / f"{dataset_id}.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset {dataset_id} not found in project {project_id}")
    with open(data_path) as f:
        return json.load(f)


def _load_job_result(project_id: str, job_id: str) -> dict:
    """Load a previous analysis job's result."""
    result_path = Path(RESULTS_DIR) / project_id / f"{job_id}.json"
    if not result_path.exists():
        raise FileNotFoundError(f"Job result {job_id} not found")
    with open(result_path) as f:
        return json.load(f)


def _save_result(project_id: str, job_id: str, result: dict) -> None:
    """Save analysis result to storage."""
    result_dir = Path(RESULTS_DIR) / project_id
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / f"{job_id}.json"
    with open(result_path, "w") as f:
        json.dump(result, f)


def handle_clustering(project_id: str, dataset_id: str, params: dict) -> dict:
    """Handle clustering analysis task.

    Loads marker data, runs chi-square distance matrix computation
    followed by hierarchical clustering, and returns cluster groups
    with dendrogram data.
    """
    from app.computation.clustering import run_snp_cluster

    dataset = _load_project_data(project_id, dataset_id)
    similarity = params.get("similarity_threshold", 0.9)

    result = run_snp_cluster(dataset, similarity_threshold=similarity)
    return result


def handle_twopoint(project_id: str, dataset_id: str, params: dict) -> dict:
    """Handle two-point analysis task.

    Computes pairwise recombination frequencies between all selected
    markers using the Fortran SNPcexp program.
    """
    from app.computation.twopoint import run_twopoint_snp

    dataset = _load_project_data(project_id, dataset_id)
    exclude_dup = params.get("exclude_duplicates", False)
    full_output = params.get("full_output", False)

    result = run_twopoint_snp(
        dataset,
        exclude_duplicates=exclude_dup,
        full_output=full_output,
    )
    return result


def handle_mds(project_id: str, dataset_id: str, twopoint_job_id: str, params: dict) -> dict:
    """Handle MDS ordering task.

    Uses the R General_estimation script to perform multidimensional
    scaling on the pairwise distance matrix from two-point analysis.
    """
    from app.computation.mds import run_mds

    dataset = _load_project_data(project_id, dataset_id)
    twopoint_result = _load_job_result(project_id, twopoint_job_id)

    result = run_mds(dataset, twopoint_result, params)
    return result


def handle_phase(
    project_id: str,
    dataset_id: str,
    mds_job_id: str,
    twopoint_job_id: str,
) -> dict:
    """Handle phase estimation task.

    Runs the Fortran phasev6 program to determine marker phases
    based on MDS ordering and two-point pairwise data.
    """
    from app.computation.phase import run_phase

    dataset = _load_project_data(project_id, dataset_id)
    mds_result = _load_job_result(project_id, mds_job_id)
    twopoint_result = _load_job_result(project_id, twopoint_job_id)

    result = run_phase(dataset, mds_result, twopoint_result)
    return result


def handle_qtl(project_id: str, dataset_id: str, ordered_job_id: str, params: dict) -> dict:
    """Handle QTL analysis task.

    Runs the Fortran SNP_QTL program to map quantitative trait loci
    onto the ordered marker map.
    """
    from app.computation.qtl import run_snp_qtl

    dataset = _load_project_data(project_id, dataset_id)
    ordered_result = _load_job_result(project_id, ordered_job_id)

    # Load trait data
    trait_path = Path(DATA_DIR) / project_id / "traits" / f"{dataset_id}.json"
    if not trait_path.exists():
        raise FileNotFoundError("No trait data associated with this dataset")
    with open(trait_path) as f:
        trait_data = json.load(f)

    result = run_snp_qtl(dataset, ordered_result, trait_data, params)
    return result


def handle_permutation(
    project_id: str,
    dataset_id: str,
    ordered_job_id: str,
    params: dict,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """Handle permutation testing task.

    Runs multiple permutations of the QTL analysis to establish
    statistical significance thresholds.
    """
    from app.computation.permutation import run_snp_perm

    dataset = _load_project_data(project_id, dataset_id)
    ordered_result = _load_job_result(project_id, ordered_job_id)

    trait_path = Path(DATA_DIR) / project_id / "traits" / f"{dataset_id}.json"
    if not trait_path.exists():
        raise FileNotFoundError("No trait data associated with this dataset")
    with open(trait_path) as f:
        trait_data = json.load(f)

    n_perms = params.get("n_perms", 500)
    result = run_snp_perm(
        dataset, ordered_result, trait_data,
        n_perms=n_perms,
        progress_callback=progress_callback,
    )
    return result


def handle_anova(project_id: str, dataset_id: str, params: dict) -> dict:
    """Handle ANOVA task.

    Runs analysis of variance on trait data against marker genotypes.
    """
    from app.computation.anova import run_anova

    dataset = _load_project_data(project_id, dataset_id)

    trait_path = Path(DATA_DIR) / project_id / "traits" / f"{dataset_id}.json"
    if not trait_path.exists():
        raise FileNotFoundError("No trait data associated with this dataset")
    with open(trait_path) as f:
        trait_data = json.load(f)

    result = run_anova(dataset, trait_data, params)
    return result


def handle_linkage_map(project_id: str, ordered_job_id: str, params: dict) -> dict:
    """Handle linkage map generation task.

    Creates a visual linkage map representation from ordered marker data.
    """
    from app.computation.linkage_map import generate_linkage_map

    ordered_result = _load_job_result(project_id, ordered_job_id)
    result = generate_linkage_map(ordered_result, params)
    return result

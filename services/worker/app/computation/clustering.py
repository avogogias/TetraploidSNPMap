"""Clustering analysis - wraps Fortran SNPcluster and cluster_chimatrixonly programs.

The clustering pipeline:
1. Write marker data to input file (SNPloc format)
2. Run cluster_chimatrixonly to compute chi-square distance matrix
3. Run R fastcluster or the Fortran SNPcluster for hierarchical clustering
4. Parse dendrogram output and assign markers to linkage groups
"""

import os
import json
import tempfile
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BINARIES_DIR = os.getenv("BINARIES_DIR", "/app/binaries")
R_SCRIPTS_DIR = os.getenv("R_SCRIPTS_DIR", "/app/r-scripts")
RSCRIPT_PATH = os.getenv("RSCRIPT_PATH", "/usr/bin/Rscript")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_snp_cluster(dataset: dict, similarity_threshold: float = 0.9) -> dict:
    """Run SNP clustering analysis.

    Args:
        dataset: Dataset dictionary with markers data.
        similarity_threshold: Threshold for cutting the dendrogram (0.0-1.0).

    Returns:
        Dictionary with cluster groups and dendrogram structure.
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="cluster_")

    try:
        # Step 1: Write input files
        markers = [m for m in dataset.get("markers", []) if m.get("checked", True)]
        _write_cluster_input(markers, dataset.get("individual_count", 0), work_dir)

        # Step 2: Run chi-square distance matrix computation
        chimatrix_bin = os.path.join(BINARIES_DIR, "cluster_chimatrixonly")
        if os.path.exists(chimatrix_bin):
            _run_chimatrix(chimatrix_bin, work_dir)
        else:
            logger.warning("cluster_chimatrixonly binary not found, using Python fallback")
            _compute_chimatrix_python(markers, work_dir)

        # Step 3: Run R clustering script
        cluster_script = os.path.join(R_SCRIPTS_DIR, "cluster.R")
        if os.path.exists(cluster_script):
            _run_r_clustering(cluster_script, work_dir, similarity_threshold)
        else:
            logger.warning("cluster.R not found, using scipy fallback")
            _cluster_scipy_fallback(work_dir, similarity_threshold)

        # Step 4: Parse results
        result = _parse_cluster_results(work_dir, markers, similarity_threshold)
        return result

    finally:
        # Cleanup is optional; temp dir will be cleaned by OS
        pass


def _write_cluster_input(markers: list, individual_count: int, work_dir: str) -> None:
    """Write marker data in the format expected by the clustering programs."""
    input_path = os.path.join(work_dir, "cluster_input.dat")
    with open(input_path, "w") as f:
        f.write(f"{individual_count} {len(markers)}\n")
        for marker in markers:
            dosages = marker.get("dosages", [])
            line = marker["name"]
            for d in dosages:
                line += f" {d}"
            f.write(line + "\n")


def _run_chimatrix(binary_path: str, work_dir: str) -> None:
    """Execute the Fortran cluster_chimatrixonly program."""
    proc = subprocess.run(
        [binary_path],
        cwd=work_dir,
        input="cluster_input\n",
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"chimatrix failed: {proc.stderr}")


def _compute_chimatrix_python(markers: list, work_dir: str) -> None:
    """Python fallback for computing chi-square distance matrix."""
    import numpy as np

    n = len(markers)
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            d1 = markers[i].get("dosages", [])
            d2 = markers[j].get("dosages", [])
            if d1 and d2:
                shared = sum(1 for a, b in zip(d1, d2) if a == b and a != 9 and b != 9)
                total = sum(1 for a, b in zip(d1, d2) if a != 9 and b != 9)
                similarity = shared / total if total > 0 else 0
                dist_matrix[i][j] = 1 - similarity
                dist_matrix[j][i] = dist_matrix[i][j]

    output_path = os.path.join(work_dir, "distmatrix.txt")
    np.savetxt(output_path, dist_matrix, fmt="%.6f")


def _run_r_clustering(script_path: str, work_dir: str, threshold: float) -> None:
    """Execute the R clustering script."""
    r_libs = os.getenv("R_LIBS", "")
    env = os.environ.copy()
    env["R_LIBS"] = r_libs
    env["R_LIBS_USER"] = r_libs

    proc = subprocess.run(
        [RSCRIPT_PATH, "--vanilla", script_path, work_dir, str(threshold)],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"R clustering failed: {proc.stderr}")


def _cluster_scipy_fallback(work_dir: str, threshold: float) -> None:
    """Scipy fallback for hierarchical clustering."""
    import numpy as np
    from scipy.cluster.hierarchy import linkage, fcluster, to_tree
    from scipy.spatial.distance import squareform

    dist_path = os.path.join(work_dir, "distmatrix.txt")
    if not os.path.exists(dist_path):
        return

    dist_matrix = np.loadtxt(dist_path)
    condensed = squareform(dist_matrix)

    Z = linkage(condensed, method="average")
    clusters = fcluster(Z, t=1 - threshold, criterion="distance")

    # Save cluster assignments
    output_path = os.path.join(work_dir, "cluster_assignments.txt")
    np.savetxt(output_path, clusters, fmt="%d")

    # Save linkage matrix for dendrogram
    linkage_path = os.path.join(work_dir, "linkage_matrix.txt")
    np.savetxt(linkage_path, Z, fmt="%.6f")


def _parse_cluster_results(work_dir: str, markers: list, threshold: float) -> dict:
    """Parse clustering output files into result dictionary."""
    import numpy as np

    result = {"groups": [], "dendrogram": None, "similarity_threshold": threshold}

    assignments_path = os.path.join(work_dir, "cluster_assignments.txt")
    if os.path.exists(assignments_path):
        assignments = np.loadtxt(assignments_path, dtype=int)
        unique_clusters = sorted(set(assignments))

        for cluster_id in unique_clusters:
            group_markers = []
            for i, assignment in enumerate(assignments):
                if assignment == cluster_id and i < len(markers):
                    group_markers.append(markers[i])

            result["groups"].append({
                "name": f"Linkage Group {cluster_id}",
                "markers": group_markers,
                "marker_count": len(group_markers),
            })

    linkage_path = os.path.join(work_dir, "linkage_matrix.txt")
    if os.path.exists(linkage_path):
        Z = np.loadtxt(linkage_path)
        result["dendrogram"] = _linkage_to_dendrogram(Z, markers)

    return result


def _linkage_to_dendrogram(Z, markers: list) -> dict:
    """Convert scipy linkage matrix to nested dendrogram dictionary."""
    from scipy.cluster.hierarchy import to_tree

    import numpy as np

    root, node_list = to_tree(Z, rd=True)

    def _to_dict(node):
        if node.is_leaf():
            idx = node.id
            name = markers[idx]["name"] if idx < len(markers) else f"Marker_{idx}"
            return {"id": str(idx), "name": name, "distance": 0.0}
        return {
            "id": str(node.id),
            "distance": float(node.dist),
            "children": [_to_dict(node.left), _to_dict(node.right)],
        }

    return _to_dict(root)

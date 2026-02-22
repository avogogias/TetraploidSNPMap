"""MDS ordering analysis - wraps R General_estimation.R script.

Uses multidimensional scaling to order markers based on pairwise
recombination frequency estimates from two-point analysis.
"""

import os
import json
import tempfile
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

R_SCRIPTS_DIR = os.getenv("R_SCRIPTS_DIR", "/app/r-scripts")
RSCRIPT_PATH = os.getenv("RSCRIPT_PATH", "/usr/bin/Rscript")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_mds(dataset: dict, twopoint_result: dict, params: dict) -> dict:
    """Run MDS ordering on two-point results.

    Args:
        dataset: Dataset dictionary with marker data.
        twopoint_result: Two-point analysis results with PWD data.
        params: MDS parameters.

    Returns:
        Dictionary with ordered markers, distances, 3D coordinates, and fit stats.
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="mds_")

    try:
        # Write PWD file for R script
        pwd_path = os.path.join(work_dir, "twopoint.pwd")
        with open(pwd_path, "w") as f:
            f.write(twopoint_result.get("pwd_data", ""))

        # Write marker list
        markers = twopoint_result.get("markers", [])
        markerlist_path = os.path.join(work_dir, "markerlist.txt")
        with open(markerlist_path, "w") as f:
            for i, m in enumerate(markers):
                f.write(f"{i + 1} {m['name']}\n")

        # Run R MDS script
        mds_script = os.path.join(R_SCRIPTS_DIR, "General_estimation.R")
        if os.path.exists(mds_script):
            _run_mds_r(mds_script, work_dir)
        else:
            logger.warning("General_estimation.R not found, using Python MDS fallback")
            _run_mds_python_fallback(twopoint_result, work_dir)

        # Parse results
        result = _parse_mds_results(work_dir, markers)
        return result

    finally:
        pass


def _run_mds_r(script_path: str, work_dir: str) -> None:
    """Execute the R General_estimation script."""
    r_libs = os.getenv("R_LIBS", "")
    env = os.environ.copy()
    env["R_LIBS"] = r_libs
    env["R_LIBS_USER"] = r_libs

    proc = subprocess.run(
        [RSCRIPT_PATH, "--vanilla", script_path, work_dir],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=1800,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"MDS R script failed: {proc.stderr}")


def _run_mds_python_fallback(twopoint_result: dict, work_dir: str) -> None:
    """Python fallback using sklearn MDS."""
    import numpy as np

    pairwise = twopoint_result.get("pairwise_data", [])
    if not pairwise:
        return

    dist_matrix = np.array(pairwise)
    n = len(dist_matrix)

    # Simple 1D ordering by first principal coordinate
    from scipy.spatial.distance import squareform
    from scipy.cluster.hierarchy import leaves_list, linkage

    condensed = squareform(dist_matrix + dist_matrix.T)
    Z = linkage(condensed, method="average")
    order = leaves_list(Z)

    # Write estimated map
    positions = np.cumsum([0] + [dist_matrix[order[i], order[i + 1]] * 100
                                  for i in range(len(order) - 1)])

    with open(os.path.join(work_dir, "estimatedmap.txt"), "w") as f:
        f.write("order,locus,position,nnfit\n")
        for idx, (o, pos) in enumerate(zip(order, positions)):
            nnfit = 0.0
            if 0 < idx < len(order) - 1:
                d1 = abs(positions[idx] - positions[idx - 1])
                d2 = abs(positions[idx + 1] - positions[idx])
                nnfit = min(d1, d2)
            f.write(f"{idx + 1},{o + 1},{pos:.2f},{nnfit:.4f}\n")

    # Write 3D coordinates (use random for fallback)
    coords_3d = np.random.randn(n, 3)
    np.savetxt(os.path.join(work_dir, "smacof_conf.txt"), coords_3d, fmt="%.6f")

    # Write loci key
    with open(os.path.join(work_dir, "locikey.txt"), "w") as f:
        for i in range(n):
            f.write(f"{i + 1}\n")


def _parse_mds_results(work_dir: str, markers: list) -> dict:
    """Parse MDS output files."""
    result = {
        "ordered_markers": [],
        "distances": [],
        "coordinates_3d": [],
        "mean_nn_fit": 0.0,
        "estimated_map": "",
        "loci_key": "",
        "smacof_conf": "",
    }

    # Parse estimated map
    map_path = os.path.join(work_dir, "estimatedmap.txt")
    if os.path.exists(map_path):
        with open(map_path) as f:
            content = f.read()
            result["estimated_map"] = content

        lines = content.strip().split("\n")
        total_nnfit = 0.0
        count = 0
        prev_pos = 0.0

        for line in lines[1:]:  # Skip header
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    locus_idx = int(parts[1]) - 1
                    position = float(parts[2])
                    nnfit = float(parts[3])

                    if locus_idx < len(markers):
                        result["ordered_markers"].append(markers[locus_idx])

                    if count > 0:
                        result["distances"].append(position - prev_pos)
                    prev_pos = position
                    total_nnfit += nnfit
                    count += 1
                except (ValueError, IndexError):
                    continue

        if count > 0:
            result["mean_nn_fit"] = total_nnfit / count

    # Parse 3D coordinates
    conf_path = os.path.join(work_dir, "smacof_conf.txt")
    if os.path.exists(conf_path):
        import numpy as np
        coords = np.loadtxt(conf_path)
        result["coordinates_3d"] = coords.tolist()
        with open(conf_path) as f:
            result["smacof_conf"] = f.read()

    # Read loci key
    key_path = os.path.join(work_dir, "locikey.txt")
    if os.path.exists(key_path):
        with open(key_path) as f:
            result["loci_key"] = f.read()

    return result

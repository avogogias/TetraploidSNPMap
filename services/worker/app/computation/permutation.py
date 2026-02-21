"""Permutation testing - wraps Fortran SNP_QTLperm_noimsl program.

Performs permutation tests to establish significance thresholds
for QTL analysis results.
"""

import os
import tempfile
import subprocess
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

BINARIES_DIR = os.getenv("BINARIES_DIR", "/app/binaries")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_snp_perm(
    dataset: dict,
    ordered_result: dict,
    trait_data: dict,
    n_perms: int = 500,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """Run permutation testing for QTL significance.

    Args:
        dataset: Dataset with marker data.
        ordered_result: Ordered result from MDS/phase analysis.
        trait_data: Trait file data.
        n_perms: Number of permutations to run.
        progress_callback: Optional callback(current, total) for progress updates.

    Returns:
        Dictionary with permutation thresholds and distribution.
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="perm_")

    try:
        # Write input files (same as QTL)
        _write_perm_inputs(dataset, ordered_result, trait_data, n_perms, work_dir)

        binary = os.path.join(BINARIES_DIR, "SNP_QTLperm_noimsl")
        if os.path.exists(binary):
            _run_perm_binary(binary, work_dir, n_perms, progress_callback)
        else:
            logger.warning("SNP_QTLperm_noimsl binary not found")
            return {"thresholds": {}, "distribution": [], "n_perms": n_perms}

        # Parse results
        result = _parse_perm_results(work_dir, n_perms)
        return result

    finally:
        pass


def _write_perm_inputs(
    dataset: dict,
    ordered_result: dict,
    trait_data: dict,
    n_perms: int,
    work_dir: str,
) -> None:
    """Write permutation test input files."""
    # Write map
    map_path = os.path.join(work_dir, "perm_map.txt")
    with open(map_path, "w") as f:
        f.write(ordered_result.get("estimated_map", ""))

    # Write traits
    qua_path = os.path.join(work_dir, "perm_traits.qua")
    with open(qua_path, "w") as f:
        traits = trait_data.get("traits", [])
        individuals = trait_data.get("individuals", [])
        f.write(f"{len(individuals)} {len(traits)}\n")
        for trait in traits:
            f.write(f"{trait['name']}\n")
        for indiv in individuals:
            values = " ".join(str(v) for v in indiv.get("values", []))
            f.write(f"{values}\n")

    # Write number of permutations
    config_path = os.path.join(work_dir, "perm_config.txt")
    with open(config_path, "w") as f:
        f.write(f"{n_perms}\n")


def _run_perm_binary(
    binary: str,
    work_dir: str,
    n_perms: int,
    progress_callback: Optional[Callable],
) -> None:
    """Execute the permutation Fortran program."""
    proc = subprocess.Popen(
        [binary],
        cwd=work_dir,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    proc.stdin.write(f"perm\n{n_perms}\n")
    proc.stdin.close()

    # Read stdout for progress
    current = 0
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("perm"):
            current += 1
            if progress_callback and current % 10 == 0:
                progress_callback(current, n_perms)

    proc.wait(timeout=7200)

    if proc.returncode != 0:
        stderr = proc.stderr.read()
        if "forrtl: severe" in stderr:
            raise RuntimeError(f"Permutation Fortran error: {stderr}")


def _parse_perm_results(work_dir: str, n_perms: int) -> dict:
    """Parse permutation test output."""
    result = {
        "n_perms": n_perms,
        "thresholds": {},
        "distribution": [],
        "perm_text": "",
    }

    perm_out = os.path.join(work_dir, "perm.out")
    if os.path.exists(perm_out):
        with open(perm_out) as f:
            result["perm_text"] = f.read()

        # Parse LOD score distribution from permutations
        max_lods = []
        for line in result["perm_text"].strip().split("\n"):
            parts = line.split()
            if parts:
                try:
                    max_lods.append(float(parts[-1]))
                except ValueError:
                    continue

        if max_lods:
            max_lods.sort()
            result["distribution"] = max_lods

            # Calculate significance thresholds
            n = len(max_lods)
            result["thresholds"] = {
                "0.05": max_lods[int(0.95 * n)] if n > 20 else None,
                "0.01": max_lods[int(0.99 * n)] if n > 100 else None,
                "0.001": max_lods[int(0.999 * n)] if n > 1000 else None,
            }

    return result

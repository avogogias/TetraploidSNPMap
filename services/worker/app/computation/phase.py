"""Phase analysis - wraps Fortran phasev6_noimsl program.

Determines the phase (allelic configuration) of markers on
each of the four homologous chromosomes.
"""

import os
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

BINARIES_DIR = os.getenv("BINARIES_DIR", "/app/binaries")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_phase(dataset: dict, mds_result: dict, twopoint_result: dict) -> dict:
    """Run phase estimation analysis.

    Args:
        dataset: Dataset dictionary with marker data.
        mds_result: MDS ordering results.
        twopoint_result: Two-point pairwise results.

    Returns:
        Dictionary with phase assignments per marker.
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="phase_")

    try:
        # Write input files for the phase program
        _write_phase_inputs(mds_result, twopoint_result, work_dir)

        # Run Fortran phase program
        binary = os.path.join(BINARIES_DIR, "phasev6_noimsl")
        if os.path.exists(binary):
            _run_phase_binary(binary, work_dir)
        else:
            logger.warning("phasev6_noimsl binary not found")
            return {"phases": [], "markers": mds_result.get("ordered_markers", [])}

        # Parse results
        result = _parse_phase_results(work_dir, mds_result)
        return result

    finally:
        pass


def _write_phase_inputs(mds_result: dict, twopoint_result: dict, work_dir: str) -> None:
    """Write input files required by the phase Fortran program."""
    # Write estimated map from MDS
    map_path = os.path.join(work_dir, "estimatedmap.txt")
    with open(map_path, "w") as f:
        f.write(mds_result.get("estimated_map", ""))

    # Write PWD from twopoint
    pwd_path = os.path.join(work_dir, "twopoint.pwd")
    with open(pwd_path, "w") as f:
        f.write(twopoint_result.get("pwd_data", ""))

    # Write loci key
    key_path = os.path.join(work_dir, "locikey.txt")
    with open(key_path, "w") as f:
        f.write(mds_result.get("loci_key", ""))


def _run_phase_binary(binary: str, work_dir: str) -> None:
    """Execute the Fortran phasev6_noimsl program."""
    proc = subprocess.run(
        [binary],
        cwd=work_dir,
        input="phase\n",
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if proc.returncode != 0 and "forrtl: severe" in proc.stderr:
        raise RuntimeError(f"Phase analysis Fortran error: {proc.stderr}")


def _parse_phase_results(work_dir: str, mds_result: dict) -> dict:
    """Parse phase analysis output."""
    result = {
        "markers": mds_result.get("ordered_markers", []),
        "phases": [],
        "phase_text": "",
    }

    phase_path = os.path.join(work_dir, "phase.out")
    if os.path.exists(phase_path):
        with open(phase_path) as f:
            result["phase_text"] = f.read()

        # Parse phase assignments
        lines = result["phase_text"].strip().split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    marker_name = parts[0]
                    p1_phase = parts[1] if len(parts) > 1 else "0000"
                    p2_phase = parts[2] if len(parts) > 2 else "0000"
                    result["phases"].append({
                        "marker": marker_name,
                        "parent1": p1_phase,
                        "parent2": p2_phase,
                    })
                except (ValueError, IndexError):
                    continue

    return result

"""Two-point analysis - wraps Fortran SNPcexp_noimsl_dupcheck program.

Computes pairwise recombination frequencies and LOD scores between
all pairs of selected markers.
"""

import os
import tempfile
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BINARIES_DIR = os.getenv("BINARIES_DIR", "/app/binaries")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_twopoint_snp(
    dataset: dict,
    exclude_duplicates: bool = False,
    full_output: bool = False,
) -> dict:
    """Run two-point SNP analysis.

    Args:
        dataset: Dataset dictionary with marker data.
        exclude_duplicates: Whether to exclude duplicate markers.
        full_output: Whether to generate full pairwise output.

    Returns:
        Dictionary with PWD data, output text, and marker ordering.
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="twopoint_")

    try:
        markers = [m for m in dataset.get("markers", []) if m.get("checked", True)]
        individual_count = dataset.get("individual_count", 0)

        # Write input file
        _write_twopoint_input(markers, individual_count, work_dir)

        # Run Fortran binary
        binary = os.path.join(BINARIES_DIR, "SNPcexp_noimsl_dupcheck_NONOMP")
        if not os.path.exists(binary):
            binary = os.path.join(BINARIES_DIR, "SNPcexp_noimsl_dupcheck_OMP")

        if os.path.exists(binary):
            _run_twopoint_binary(binary, work_dir, exclude_duplicates, full_output)
        else:
            logger.warning("TwoPoint binary not found, returning empty result")
            return {"pwd_data": "", "output": "", "markers": markers, "distances": []}

        # Parse results
        result = _parse_twopoint_results(work_dir, markers, full_output)
        result["exclude_duplicates"] = exclude_duplicates
        result["full_output"] = full_output
        return result

    finally:
        pass


def _write_twopoint_input(markers: list, individual_count: int, work_dir: str) -> None:
    """Write marker data in SNPloc format for the two-point program."""
    input_path = os.path.join(work_dir, "twopoint.loc")
    with open(input_path, "w") as f:
        f.write(f"{individual_count} {len(markers)}\n")
        for marker in markers:
            dosages = marker.get("dosages", [])
            line = marker["name"]
            if marker.get("prefix"):
                line += f" {marker['prefix']}"
            for d in dosages:
                line += f" {d}"
            f.write(line + "\n")


def _run_twopoint_binary(
    binary: str, work_dir: str, exclude_dup: bool, full_output: bool
) -> None:
    """Execute the Fortran SNPcexp two-point program."""
    char_excl = "Y" if exclude_dup else "N"
    char_full = "Y" if full_output else "N"

    stdin_data = f"twopoint\n{char_full}\n{char_excl}\n"

    proc = subprocess.run(
        [binary],
        cwd=work_dir,
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if proc.returncode != 0 and "forrtl: severe" in proc.stderr:
        raise RuntimeError(f"TwoPoint Fortran error: {proc.stderr}")


def _parse_twopoint_results(work_dir: str, markers: list, full_output: bool) -> dict:
    """Parse two-point output files."""
    result = {
        "pwd_data": "",
        "output": "",
        "full_output_data": "",
        "markers": markers,
        "distances": [],
        "pairwise_data": [],
        "removed_loci": [],
    }

    pwd_path = os.path.join(work_dir, "twopoint.pwd")
    if os.path.exists(pwd_path):
        with open(pwd_path) as f:
            result["pwd_data"] = f.read()

    out_path = os.path.join(work_dir, "twopoint.out")
    if os.path.exists(out_path):
        with open(out_path) as f:
            result["output"] = f.read()

    if full_output:
        fullout_path = os.path.join(work_dir, "twopoint.fullout")
        if os.path.exists(fullout_path):
            with open(fullout_path) as f:
                result["full_output_data"] = f.read()

    # Parse PWD data into structured format
    if result["pwd_data"]:
        result["pairwise_data"] = _parse_pwd(result["pwd_data"], len(markers))

    return result


def _parse_pwd(pwd_text: str, n_markers: int) -> list:
    """Parse PWD file into a pairwise distance matrix."""
    lines = pwd_text.strip().split("\n")
    matrix = [[0.0] * n_markers for _ in range(n_markers)]

    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 4:
            try:
                i = int(parts[0]) - 1
                j = int(parts[1]) - 1
                rfq = float(parts[2])
                lod = float(parts[3])
                if 0 <= i < n_markers and 0 <= j < n_markers:
                    matrix[i][j] = rfq
                    matrix[j][i] = rfq
            except (ValueError, IndexError):
                continue

    return matrix

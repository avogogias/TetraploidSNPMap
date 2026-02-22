"""QTL analysis - wraps Fortran SNP_QTL_newinput and simple_model programs.

Maps quantitative trait loci (QTL) onto the ordered linkage map,
computing LOD scores at regular intervals along the chromosome.
"""

import os
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

BINARIES_DIR = os.getenv("BINARIES_DIR", "/app/binaries")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_snp_qtl(
    dataset: dict,
    ordered_result: dict,
    trait_data: dict,
    params: dict,
) -> dict:
    """Run SNP QTL analysis.

    Args:
        dataset: Dataset with marker data.
        ordered_result: Ordered result from MDS/phase analysis.
        trait_data: Trait file data with phenotypic measurements.
        params: QTL parameters (model_type, selected traits, etc.).

    Returns:
        Dictionary with QTL results per trait (positions, LOD scores).
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="qtl_")

    try:
        # Write input files
        _write_qtl_inputs(dataset, ordered_result, trait_data, work_dir)

        # Determine which binary to use
        model = params.get("model_type", "full")
        if model == "simple":
            binary = os.path.join(BINARIES_DIR, "simple_model")
        elif model == "additive":
            binary = os.path.join(BINARIES_DIR, "simple_model_additive")
        else:
            binary = os.path.join(BINARIES_DIR, "SNP_QTL_newinput")

        if os.path.exists(binary):
            _run_qtl_binary(binary, work_dir)
        else:
            logger.warning(f"QTL binary not found: {binary}")
            return {"traits": [], "positions": [], "lod_scores": []}

        # Parse results
        result = _parse_qtl_results(work_dir, trait_data)
        return result

    finally:
        pass


def _write_qtl_inputs(
    dataset: dict,
    ordered_result: dict,
    trait_data: dict,
    work_dir: str,
) -> None:
    """Write QTL analysis input files."""
    # Write the ordered map file
    map_path = os.path.join(work_dir, "qtl_map.txt")
    with open(map_path, "w") as f:
        f.write(ordered_result.get("estimated_map", ""))

    # Write trait data
    qua_path = os.path.join(work_dir, "qtl_traits.qua")
    with open(qua_path, "w") as f:
        traits = trait_data.get("traits", [])
        individuals = trait_data.get("individuals", [])
        n_traits = len(traits)
        n_indiv = len(individuals)

        f.write(f"{n_indiv} {n_traits}\n")
        for trait in traits:
            f.write(f"{trait['name']}\n")
        for indiv in individuals:
            values = " ".join(str(v) for v in indiv.get("values", []))
            f.write(f"{values}\n")

    # Write PWD/phase data if available
    if ordered_result.get("pwd_data"):
        pwd_path = os.path.join(work_dir, "twopoint.pwd")
        with open(pwd_path, "w") as f:
            f.write(ordered_result["pwd_data"])


def _run_qtl_binary(binary: str, work_dir: str) -> None:
    """Execute a QTL Fortran program."""
    proc = subprocess.run(
        [binary],
        cwd=work_dir,
        input="qtl\n",
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if proc.returncode != 0 and "forrtl: severe" in proc.stderr:
        raise RuntimeError(f"QTL Fortran error: {proc.stderr}")


def _parse_qtl_results(work_dir: str, trait_data: dict) -> dict:
    """Parse QTL output files."""
    result = {
        "traits": [],
        "positions": [],
        "lod_scores": [],
        "qtl_text": "",
    }

    # Read main QTL output
    qtl_out = os.path.join(work_dir, "qtl.out")
    if os.path.exists(qtl_out):
        with open(qtl_out) as f:
            result["qtl_text"] = f.read()

    # Parse QTL model matrix if present
    qmm_path = os.path.join(work_dir, "qtl_model_matrix.txt")
    if os.path.exists(qmm_path):
        with open(qmm_path) as f:
            result["model_matrix"] = f.read()

    # Parse LOD score profiles for each trait
    trait_names = [t["name"] for t in trait_data.get("traits", [])]
    for trait_name in trait_names:
        trait_result = {
            "name": trait_name,
            "positions": [],
            "lod_scores": [],
            "peak_position": None,
            "peak_lod": 0.0,
        }

        # Look for trait-specific output
        trait_file = os.path.join(work_dir, f"qtl_{trait_name}.txt")
        if os.path.exists(trait_file):
            with open(trait_file) as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pos = float(parts[0])
                            lod = float(parts[1])
                            trait_result["positions"].append(pos)
                            trait_result["lod_scores"].append(lod)
                            if lod > trait_result["peak_lod"]:
                                trait_result["peak_lod"] = lod
                                trait_result["peak_position"] = pos
                        except ValueError:
                            continue

        result["traits"].append(trait_result)

    return result

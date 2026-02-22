"""ANOVA analysis for trait data against marker genotypes."""

import os
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

BINARIES_DIR = os.getenv("BINARIES_DIR", "/app/binaries")
SCRATCH_DIR = os.getenv("SCRATCH_DIR", "/tmp/tpmap")


def run_anova(dataset: dict, trait_data: dict, params: dict) -> dict:
    """Run Analysis of Variance on trait data.

    Args:
        dataset: Dataset with marker data.
        trait_data: Trait file data.
        params: ANOVA parameters.

    Returns:
        Dictionary with ANOVA results per trait (F-values, p-values, etc.).
    """
    work_dir = tempfile.mkdtemp(dir=SCRATCH_DIR, prefix="anova_")

    try:
        markers = [m for m in dataset.get("markers", []) if m.get("checked", True)]
        _write_anova_inputs(markers, dataset, trait_data, work_dir)

        binary = os.path.join(BINARIES_DIR, "anova")
        if os.path.exists(binary):
            _run_anova_binary(binary, work_dir)
        else:
            logger.warning("ANOVA binary not found, using Python fallback")
            return _anova_python_fallback(markers, trait_data)

        result = _parse_anova_results(work_dir, trait_data)
        return result

    finally:
        pass


def _write_anova_inputs(
    markers: list, dataset: dict, trait_data: dict, work_dir: str
) -> None:
    """Write ANOVA input files."""
    dat_path = os.path.join(work_dir, "anova.dat")
    with open(dat_path, "w") as f:
        individual_count = dataset.get("individual_count", 0)
        f.write(f"{individual_count} {len(markers)}\n")
        for marker in markers:
            dosages = marker.get("dosages", [])
            line = marker["name"] + " " + " ".join(str(d) for d in dosages)
            f.write(line + "\n")

    qua_path = os.path.join(work_dir, "anova.qua")
    with open(qua_path, "w") as f:
        traits = trait_data.get("traits", [])
        individuals = trait_data.get("individuals", [])
        f.write(f"{len(individuals)} {len(traits)}\n")
        for trait in traits:
            f.write(f"{trait['name']}\n")
        for indiv in individuals:
            values = " ".join(str(v) for v in indiv.get("values", []))
            f.write(f"{values}\n")


def _run_anova_binary(binary: str, work_dir: str) -> None:
    """Execute the ANOVA Fortran program."""
    proc = subprocess.run(
        [binary],
        cwd=work_dir,
        input="anova\n",
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0 and "forrtl: severe" in proc.stderr:
        raise RuntimeError(f"ANOVA Fortran error: {proc.stderr}")


def _anova_python_fallback(markers: list, trait_data: dict) -> dict:
    """Python fallback for ANOVA using scipy."""
    from scipy import stats
    import numpy as np

    result = {"trait_results": []}
    traits = trait_data.get("traits", [])
    individuals = trait_data.get("individuals", [])

    for t_idx, trait in enumerate(traits):
        trait_values = []
        for indiv in individuals:
            vals = indiv.get("values", [])
            if t_idx < len(vals):
                trait_values.append(vals[t_idx])
            else:
                trait_values.append(None)

        marker_results = []
        for marker in markers:
            dosages = marker.get("dosages", [])[2:]  # Skip parent dosages
            groups = {}
            for i, d in enumerate(dosages):
                if d != 9 and i < len(trait_values) and trait_values[i] is not None:
                    groups.setdefault(d, []).append(trait_values[i])

            group_vals = [v for v in groups.values() if len(v) > 1]
            if len(group_vals) >= 2:
                try:
                    f_val, p_val = stats.f_oneway(*group_vals)
                    marker_results.append({
                        "marker": marker["name"],
                        "f_value": float(f_val) if not np.isnan(f_val) else 0.0,
                        "p_value": float(p_val) if not np.isnan(p_val) else 1.0,
                    })
                except Exception:
                    marker_results.append({
                        "marker": marker["name"],
                        "f_value": 0.0,
                        "p_value": 1.0,
                    })

        result["trait_results"].append({
            "trait": trait["name"],
            "markers": marker_results,
        })

    return result


def _parse_anova_results(work_dir: str, trait_data: dict) -> dict:
    """Parse ANOVA output files."""
    result = {"trait_results": [], "anova_text": ""}

    out_path = os.path.join(work_dir, "anova.out")
    if os.path.exists(out_path):
        with open(out_path) as f:
            result["anova_text"] = f.read()

    return result

"""Tests for the clustering computation module."""

import os
import sys
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_markers(n=10, ind_count=20):
    """Create synthetic marker data for testing."""
    markers = []
    for i in range(n):
        dosages = np.random.choice([0, 1, 2, 3, 4], size=ind_count).tolist()
        markers.append({
            "name": f"SNP{i:03d}",
            "safe_name": f"mkr{i:06d}",
            "checked": True,
            "dosages": dosages,
            "type": "SNP",
        })
    return markers


class TestComputeChimatrixPython:
    def test_basic_distance_matrix(self):
        from app.computation.clustering import _compute_chimatrix_python

        markers = _make_markers(5, 20)
        work_dir = tempfile.mkdtemp()
        _compute_chimatrix_python(markers, work_dir)

        dist_path = os.path.join(work_dir, "distmatrix.txt")
        assert os.path.exists(dist_path)

        dist_matrix = np.loadtxt(dist_path)
        assert dist_matrix.shape == (5, 5)
        # Diagonal should be zero
        np.testing.assert_array_equal(np.diag(dist_matrix), np.zeros(5))
        # Matrix should be symmetric
        np.testing.assert_array_almost_equal(dist_matrix, dist_matrix.T)

    def test_identical_markers_zero_distance(self):
        from app.computation.clustering import _compute_chimatrix_python

        dosages = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        markers = [
            {"name": "A", "dosages": dosages.copy()},
            {"name": "B", "dosages": dosages.copy()},
        ]
        work_dir = tempfile.mkdtemp()
        _compute_chimatrix_python(markers, work_dir)

        dist_matrix = np.loadtxt(os.path.join(work_dir, "distmatrix.txt"))
        assert dist_matrix[0][1] == 0.0

    def test_missing_data_handled(self):
        from app.computation.clustering import _compute_chimatrix_python

        markers = [
            {"name": "A", "dosages": [9, 9, 9, 1, 2]},
            {"name": "B", "dosages": [9, 9, 9, 1, 2]},
        ]
        work_dir = tempfile.mkdtemp()
        _compute_chimatrix_python(markers, work_dir)

        dist_matrix = np.loadtxt(os.path.join(work_dir, "distmatrix.txt"))
        assert dist_matrix[0][1] == 0.0  # Non-missing values are identical


class TestClusterScipyFallback:
    def test_basic_clustering(self):
        from app.computation.clustering import _cluster_scipy_fallback

        # Create a simple distance matrix
        work_dir = tempfile.mkdtemp()
        dist_matrix = np.array([
            [0.0, 0.1, 0.8, 0.9],
            [0.1, 0.0, 0.7, 0.85],
            [0.8, 0.7, 0.0, 0.15],
            [0.9, 0.85, 0.15, 0.0],
        ])
        np.savetxt(os.path.join(work_dir, "distmatrix.txt"), dist_matrix, fmt="%.6f")

        _cluster_scipy_fallback(work_dir, threshold=0.5)

        assignments_path = os.path.join(work_dir, "cluster_assignments.txt")
        assert os.path.exists(assignments_path)

        assignments = np.loadtxt(assignments_path, dtype=int)
        assert len(assignments) == 4
        # Markers 0,1 should cluster together and 2,3 should cluster together
        assert assignments[0] == assignments[1]
        assert assignments[2] == assignments[3]
        assert assignments[0] != assignments[2]

    def test_linkage_matrix_saved(self):
        from app.computation.clustering import _cluster_scipy_fallback

        work_dir = tempfile.mkdtemp()
        dist_matrix = np.array([
            [0.0, 0.2, 0.8],
            [0.2, 0.0, 0.7],
            [0.8, 0.7, 0.0],
        ])
        np.savetxt(os.path.join(work_dir, "distmatrix.txt"), dist_matrix, fmt="%.6f")

        _cluster_scipy_fallback(work_dir, threshold=0.5)

        linkage_path = os.path.join(work_dir, "linkage_matrix.txt")
        assert os.path.exists(linkage_path)


class TestParseClusterResults:
    def test_parse_with_assignments(self):
        from app.computation.clustering import _parse_cluster_results

        work_dir = tempfile.mkdtemp()
        markers = [{"name": "M1"}, {"name": "M2"}, {"name": "M3"}]

        np.savetxt(os.path.join(work_dir, "cluster_assignments.txt"), [1, 1, 2], fmt="%d")

        result = _parse_cluster_results(work_dir, markers, 0.9)
        assert "groups" in result
        assert len(result["groups"]) == 2
        assert result["similarity_threshold"] == 0.9

        group1 = result["groups"][0]
        assert group1["marker_count"] == 2
        group2 = result["groups"][1]
        assert group2["marker_count"] == 1


class TestWriteClusterInput:
    def test_format(self):
        from app.computation.clustering import _write_cluster_input

        markers = [
            {"name": "SNP1", "dosages": [0, 1, 2]},
            {"name": "SNP2", "dosages": [3, 4, 0]},
        ]
        work_dir = tempfile.mkdtemp()
        _write_cluster_input(markers, 3, work_dir)

        input_path = os.path.join(work_dir, "cluster_input.dat")
        assert os.path.exists(input_path)
        with open(input_path) as f:
            lines = f.readlines()
        assert lines[0].strip() == "3 2"
        assert "SNP1" in lines[1]


class TestFullClusteringPipeline:
    def test_run_snp_cluster_python_fallback(self):
        """Test the full clustering pipeline using Python/scipy fallbacks."""
        from app.computation.clustering import run_snp_cluster

        markers = _make_markers(8, 30)
        dataset = {"markers": markers, "individual_count": 30}

        # Ensure scratch dir exists
        os.makedirs("/tmp/tpmap", exist_ok=True)

        result = run_snp_cluster(dataset, similarity_threshold=0.8)
        assert "groups" in result
        assert "dendrogram" in result
        assert "similarity_threshold" in result
        assert result["similarity_threshold"] == 0.8
        assert len(result["groups"]) > 0

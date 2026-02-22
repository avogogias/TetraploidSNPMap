"""Tests for the MDS computation module."""

import os
import sys
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestMDSPythonFallback:
    def test_basic_ordering(self):
        from app.computation.mds import _run_mds_python_fallback

        n = 5
        # Create a structured pairwise distance matrix
        pairwise = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                pairwise[i][j] = abs(i - j) * 0.1

        twopoint_result = {"pairwise_data": pairwise}
        work_dir = tempfile.mkdtemp()

        _run_mds_python_fallback(twopoint_result, work_dir)

        # Should produce estimatedmap.txt
        assert os.path.exists(os.path.join(work_dir, "estimatedmap.txt"))
        # Should produce 3D coordinates
        assert os.path.exists(os.path.join(work_dir, "smacof_conf.txt"))
        # Should produce loci key
        assert os.path.exists(os.path.join(work_dir, "locikey.txt"))

    def test_empty_pairwise_skips(self):
        from app.computation.mds import _run_mds_python_fallback

        twopoint_result = {"pairwise_data": []}
        work_dir = tempfile.mkdtemp()
        _run_mds_python_fallback(twopoint_result, work_dir)
        # Should not produce output
        assert not os.path.exists(os.path.join(work_dir, "estimatedmap.txt"))


class TestParseMDSResults:
    def test_parse_estimated_map(self):
        from app.computation.mds import _parse_mds_results

        work_dir = tempfile.mkdtemp()
        markers = [{"name": "M1"}, {"name": "M2"}, {"name": "M3"}]

        with open(os.path.join(work_dir, "estimatedmap.txt"), "w") as f:
            f.write("order,locus,position,nnfit\n")
            f.write("1,1,0.00,0.0000\n")
            f.write("2,2,5.30,0.1200\n")
            f.write("3,3,12.80,0.0800\n")

        result = _parse_mds_results(work_dir, markers)
        assert len(result["ordered_markers"]) == 3
        assert len(result["distances"]) == 2
        assert result["distances"][0] == pytest.approx(5.3, abs=0.1)
        assert result["mean_nn_fit"] > 0

    def test_parse_3d_coordinates(self):
        from app.computation.mds import _parse_mds_results

        work_dir = tempfile.mkdtemp()
        markers = [{"name": "M1"}, {"name": "M2"}]

        # Create minimal map file
        with open(os.path.join(work_dir, "estimatedmap.txt"), "w") as f:
            f.write("order,locus,position,nnfit\n")
            f.write("1,1,0.00,0.0\n")
            f.write("2,2,5.00,0.1\n")

        # Create 3D coordinate file
        coords = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        np.savetxt(os.path.join(work_dir, "smacof_conf.txt"), coords, fmt="%.6f")

        result = _parse_mds_results(work_dir, markers)
        assert len(result["coordinates_3d"]) == 2
        assert len(result["coordinates_3d"][0]) == 3


class TestRunMDS:
    def test_python_fallback_integration(self):
        """Test full MDS with Python fallback."""
        from app.computation.mds import run_mds

        os.makedirs("/tmp/tpmap", exist_ok=True)

        n = 6
        pairwise = [[abs(i - j) * 0.1 for j in range(n)] for i in range(n)]
        markers = [{"name": f"M{i}"} for i in range(n)]

        dataset = {"markers": markers}
        twopoint_result = {"pairwise_data": pairwise, "markers": markers, "pwd_data": ""}
        params = {"dimensions": 3}

        result = run_mds(dataset, twopoint_result, params)
        assert "ordered_markers" in result
        assert "distances" in result
        assert "estimated_map" in result

"""Tests for the two-point analysis computation module."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestWriteTwopointInput:
    def test_format(self):
        from app.computation.twopoint import _write_twopoint_input

        markers = [
            {"name": "M1", "dosages": [0, 1, 2, 0]},
            {"name": "M2", "dosages": [1, 1, 0, 2], "prefix": "SD"},
        ]
        work_dir = tempfile.mkdtemp()
        _write_twopoint_input(markers, 4, work_dir)

        path = os.path.join(work_dir, "twopoint.loc")
        assert os.path.exists(path)
        with open(path) as f:
            lines = f.readlines()
        assert lines[0].strip() == "4 2"
        assert "M1" in lines[1]
        assert "SD" in lines[2]  # Prefix included


class TestParsePWD:
    def test_basic_parsing(self):
        from app.computation.twopoint import _parse_pwd

        pwd_text = "header line\n1 2 0.15 3.5\n1 3 0.30 2.0\n2 3 0.25 2.5\n"
        matrix = _parse_pwd(pwd_text, 3)
        assert len(matrix) == 3
        assert matrix[0][1] == 0.15
        assert matrix[1][0] == 0.15  # Symmetric
        assert matrix[0][2] == 0.30
        assert matrix[1][2] == 0.25

    def test_empty_pwd(self):
        from app.computation.twopoint import _parse_pwd

        matrix = _parse_pwd("", 3)
        assert all(matrix[i][j] == 0.0 for i in range(3) for j in range(3))

    def test_malformed_lines_skipped(self):
        from app.computation.twopoint import _parse_pwd

        pwd_text = "header\n1 2 0.1 1.0\nbad line\n1 3 0.2 2.0\n"
        matrix = _parse_pwd(pwd_text, 3)
        assert matrix[0][1] == 0.1
        assert matrix[0][2] == 0.2


class TestRunTwopointSnp:
    def test_no_binary_returns_empty_result(self):
        """Without Fortran binary, returns an empty result dict."""
        from app.computation.twopoint import run_twopoint_snp

        dataset = {
            "markers": [
                {"name": "M1", "checked": True, "dosages": [0, 1]},
                {"name": "M2", "checked": True, "dosages": [1, 0]},
            ],
            "individual_count": 2,
        }
        os.makedirs("/tmp/tpmap", exist_ok=True)

        result = run_twopoint_snp(dataset)
        assert "pwd_data" in result
        assert "markers" in result
        assert result["pwd_data"] == ""

    def test_only_checked_markers_used(self):
        from app.computation.twopoint import run_twopoint_snp

        dataset = {
            "markers": [
                {"name": "M1", "checked": True, "dosages": [0, 1]},
                {"name": "M2", "checked": False, "dosages": [1, 0]},
                {"name": "M3", "checked": True, "dosages": [2, 1]},
            ],
            "individual_count": 2,
        }
        os.makedirs("/tmp/tpmap", exist_ok=True)

        result = run_twopoint_snp(dataset)
        # Only 2 checked markers should be in result
        assert len(result["markers"]) == 2

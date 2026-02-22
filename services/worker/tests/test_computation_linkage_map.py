"""Tests for the linkage map generation module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestGenerateLinkageMap:
    def test_basic_map(self):
        from app.computation.linkage_map import generate_linkage_map

        ordered_result = {
            "ordered_markers": [
                {"name": "M1", "safe_name": "mkr001"},
                {"name": "M2", "safe_name": "mkr002"},
                {"name": "M3", "safe_name": "mkr003"},
            ],
            "distances": [5.0, 10.0],
        }
        result = generate_linkage_map(ordered_result, {})

        assert len(result["groups"]) == 1
        group = result["groups"][0]
        assert group["name"] == "Linkage Group 1"
        assert len(group["markers"]) == 3

        # Check cumulative positions
        assert group["markers"][0]["position"] == 0.0
        assert group["markers"][1]["position"] == 5.0
        assert group["markers"][2]["position"] == 15.0

        assert result["total_distance"] == 15.0

    def test_empty_markers(self):
        from app.computation.linkage_map import generate_linkage_map

        result = generate_linkage_map({"ordered_markers": [], "distances": []}, {})
        assert result["groups"] == []
        assert result["total_distance"] == 0.0

    def test_single_marker(self):
        from app.computation.linkage_map import generate_linkage_map

        result = generate_linkage_map(
            {"ordered_markers": [{"name": "Alone"}], "distances": []}, {}
        )
        assert len(result["groups"]) == 1
        assert result["groups"][0]["markers"][0]["position"] == 0.0
        assert result["total_distance"] == 0.0

    def test_negative_distances_become_absolute(self):
        from app.computation.linkage_map import generate_linkage_map

        result = generate_linkage_map(
            {
                "ordered_markers": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
                "distances": [-3.0, 7.0],
            },
            {},
        )
        positions = [m["position"] for m in result["groups"][0]["markers"]]
        assert positions == [0.0, 3.0, 10.0]

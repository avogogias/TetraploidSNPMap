"""Tests for the ANOVA computation module."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAnovaPythonFallback:
    def test_basic_anova(self):
        from app.computation.anova import _anova_python_fallback

        markers = [
            {
                "name": "M1",
                "dosages": [0, 0, 0, 1, 1, 2, 2, 2],  # first 2 are parents
            },
        ]
        trait_data = {
            "traits": [{"name": "yield"}],
            "individuals": [
                {"values": [v]} for v in
                [10.0, 12.0, 11.0, 20.0, 22.0, 30.0]
            ],
        }

        result = _anova_python_fallback(markers, trait_data)
        assert "trait_results" in result
        assert len(result["trait_results"]) == 1
        assert result["trait_results"][0]["trait"] == "yield"

    def test_multiple_traits(self):
        from app.computation.anova import _anova_python_fallback

        markers = [
            {"name": "M1", "dosages": [0, 0, 1, 1, 2, 2]},
        ]
        trait_data = {
            "traits": [{"name": "height"}, {"name": "weight"}],
            "individuals": [
                {"values": [10.0, 50.0]},
                {"values": [12.0, 55.0]},
                {"values": [20.0, 70.0]},
                {"values": [22.0, 72.0]},
            ],
        }

        result = _anova_python_fallback(markers, trait_data)
        assert len(result["trait_results"]) == 2
        trait_names = [r["trait"] for r in result["trait_results"]]
        assert "height" in trait_names
        assert "weight" in trait_names

    def test_empty_markers(self):
        from app.computation.anova import _anova_python_fallback

        result = _anova_python_fallback(
            [],
            {"traits": [{"name": "t1"}], "individuals": []},
        )
        assert len(result["trait_results"]) == 1
        assert result["trait_results"][0]["markers"] == []


class TestRunAnova:
    def test_no_binary_uses_fallback(self):
        from app.computation.anova import run_anova

        os.makedirs("/tmp/tpmap", exist_ok=True)

        dataset = {
            "markers": [
                {"name": "M1", "checked": True, "dosages": [0, 0, 1, 1, 2, 2]},
            ],
            "individual_count": 6,
        }
        trait_data = {
            "traits": [{"name": "yield"}],
            "individuals": [
                {"values": [10.0]},
                {"values": [12.0]},
                {"values": [20.0]},
                {"values": [22.0]},
            ],
        }

        result = run_anova(dataset, trait_data, {})
        assert "trait_results" in result

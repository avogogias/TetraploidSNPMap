"""Tests for the task handler bridge functions."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def project_dir(tmp_path):
    """Create a temp project directory structure."""
    data_dir = tmp_path / "data"
    results_dir = tmp_path / "results"
    data_dir.mkdir()
    results_dir.mkdir()

    # Patch environment
    os.environ["PROJECT_STORAGE_PATH"] = str(data_dir)
    os.environ["RESULTS_STORAGE_PATH"] = str(results_dir)

    return {"data_dir": data_dir, "results_dir": results_dir}


class TestLoadProjectData:
    def test_load_existing_dataset(self, project_dir):
        # Reimport after patching env
        from importlib import reload
        import app.task_handlers as th
        reload(th)

        data_dir = project_dir["data_dir"]
        project_path = data_dir / "proj1" / "datasets"
        project_path.mkdir(parents=True)

        dataset_data = {
            "markers": [{"name": "M1", "checked": True, "dosages": [0, 1]}],
            "individual_count": 2,
        }
        with open(project_path / "ds1.json", "w") as f:
            json.dump(dataset_data, f)

        result = th._load_project_data("proj1", "ds1")
        assert result["markers"][0]["name"] == "M1"

    def test_load_missing_dataset_raises(self, project_dir):
        from importlib import reload
        import app.task_handlers as th
        reload(th)

        with pytest.raises(FileNotFoundError, match="not found"):
            th._load_project_data("proj1", "nonexistent")


class TestLoadJobResult:
    def test_load_existing_result(self, project_dir):
        from importlib import reload
        import app.task_handlers as th
        reload(th)

        results_dir = project_dir["results_dir"]
        (results_dir / "proj1").mkdir()
        result_data = {"status": "COMPLETED", "groups": []}
        with open(results_dir / "proj1" / "job1.json", "w") as f:
            json.dump(result_data, f)

        result = th._load_job_result("proj1", "job1")
        assert result["status"] == "COMPLETED"

    def test_load_missing_result_raises(self, project_dir):
        from importlib import reload
        import app.task_handlers as th
        reload(th)

        with pytest.raises(FileNotFoundError, match="not found"):
            th._load_job_result("proj1", "nonexistent")


class TestSaveResult:
    def test_save_and_load(self, project_dir):
        from importlib import reload
        import app.task_handlers as th
        reload(th)

        result = {"status": "COMPLETED", "data": [1, 2, 3]}
        th._save_result("proj1", "job42", result)

        loaded = th._load_job_result("proj1", "job42")
        assert loaded["status"] == "COMPLETED"
        assert loaded["data"] == [1, 2, 3]

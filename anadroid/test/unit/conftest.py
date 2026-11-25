import pytest


@pytest.fixture(autouse=True)
def run_in_tmp_dir(tmp_path, monkeypatch):
    """Unit tests write logs and results in the current directory. Keep them out of the repository."""
    monkeypatch.chdir(tmp_path)

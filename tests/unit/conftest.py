import pytest

from anadroid import Config


@pytest.fixture(autouse=True)
def isolate_test(tmp_path, monkeypatch):
    """Unit tests write logs and results in the current directory. Keep them out of the repository.
    Config values set by one test must not reach the next test."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Config, "RUNTIME_OVERRIDES", {})

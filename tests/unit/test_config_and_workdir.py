import json
import os

import pytest

from anadroid import Config
from anadroid.main import build_parser, apply_workdir


@pytest.fixture
def clean_config(monkeypatch, tmp_path):
    monkeypatch.setattr(Config, "USER_CONFIG_FILE", None)
    monkeypatch.delenv("PYANADROID_CONFIG", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def write_config(path, tests_per_app):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"tests": {"tests_per_app": tests_per_app}}, f)
    return str(path)


def test_default_config_is_the_packaged_file(clean_config):
    assert Config.get_config_file() == Config.CONFIG_FILE
    assert "tests_per_app" in Config.get_general_config("tests")


def test_user_config_dir_is_used(clean_config, tmp_path):
    path = write_config(tmp_path / "xdg" / "pyanadroid" / "general_config.json", 11)
    assert Config.get_config_file() == path
    assert Config.get_general_config("tests")["tests_per_app"] == 11


def test_config_in_the_current_directory_has_priority_over_the_user_dir(clean_config, tmp_path):
    write_config(tmp_path / "xdg" / "pyanadroid" / "general_config.json", 11)
    write_config(tmp_path / "general_config.json", 12)  # the tests run in tmp_path
    assert Config.get_general_config("tests")["tests_per_app"] == 12


def test_explicit_config_file_has_the_top_priority(clean_config, tmp_path, monkeypatch):
    write_config(tmp_path / "general_config.json", 12)
    env_path = write_config(tmp_path / "env" / "c.json", 13)
    monkeypatch.setenv("PYANADROID_CONFIG", env_path)
    assert Config.get_general_config("tests")["tests_per_app"] == 13
    Config.set_config_file(write_config(tmp_path / "cli" / "c.json", 14))
    assert Config.get_general_config("tests")["tests_per_app"] == 14


def test_missing_explicit_config_file_is_an_error(clean_config, tmp_path):
    with pytest.raises(FileNotFoundError):
        Config.set_config_file(str(tmp_path / "missing.json"))


def test_workdir_gets_logs_and_results_and_keeps_input_paths(tmp_path):
    projects = tmp_path / "projects"
    projects.mkdir()
    args = build_parser().parse_args(["-d", "projects", "-apk", "a.apk", "-td", "my_tests",
                                      "--workdir", str(tmp_path / "work" / "run1")])
    apply_workdir(args)
    assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path / "work" / "run1")
    assert args.diretory == str(tmp_path / "projects")
    assert args.application_packages == [str(tmp_path / "a.apk")]
    assert args.tests_dir == str(tmp_path / "my_tests")


def test_no_workdir_changes_nothing(tmp_path):
    args = build_parser().parse_args(["-d", "projects"])
    apply_workdir(args)
    assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path) and args.diretory == "projects"

import hashlib
import os
import zipfile

import pytest

from anadroid.main import build_parser
from anadroid.utils import ExternalTools
from anadroid.utils.ExternalTools import find_tool_path, download_tool, find_pmd, TOOLS


@pytest.fixture
def tools_dir(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    monkeypatch.setenv("PYANADROID_TOOLS_DIR", str(cache))
    for name in TOOLS:
        monkeypatch.delenv(ExternalTools.get_env_var_name(name), raising=False)
    return cache


def test_manifest_entries_are_complete():
    for name, tool in TOOLS.items():
        assert tool["file"] and tool["url"].startswith("https://") and len(tool["sha256"]) == 64, name


def test_environment_variable_has_priority(tools_dir, monkeypatch):
    monkeypatch.setenv("PYANADROID_JINST", "/custom/jInst.jar")
    assert find_tool_path("jinst") == "/custom/jInst.jar"


def test_downloaded_tool_has_priority_over_the_bundled_file(tools_dir):
    bundled = find_tool_path("jinst")
    assert bundled.endswith(os.path.join("resources", "jars", "jInst.jar"))
    tools_dir.mkdir()
    (tools_dir / "jInst.jar").write_text("x")
    assert find_tool_path("jinst") == str(tools_dir / "jInst.jar")


def test_download_checks_the_checksum(tools_dir, tmp_path, monkeypatch):
    source = tmp_path / "source.jar"
    source.write_bytes(b"tool content")
    tool = {"file": "my.jar", "url": source.as_uri(), "sha256": hashlib.sha256(b"tool content").hexdigest()}
    monkeypatch.setitem(TOOLS, "mytool", tool)
    assert download_tool("mytool") == str(tools_dir / "my.jar")
    assert (tools_dir / "my.jar").read_bytes() == b"tool content"

    monkeypatch.setitem(TOOLS, "badtool", dict(tool, file="bad.jar", sha256="0" * 64))
    with pytest.raises(ValueError):
        download_tool("badtool")
    assert not (tools_dir / "bad.jar").exists()


def test_archive_tools_are_extracted(tools_dir, tmp_path, monkeypatch):
    archive = tmp_path / "pmd.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("pmd-bin-7.9.0/bin/pmd", "#!/bin/sh\n")
    monkeypatch.setitem(TOOLS, "pmd", {"file": "pmd-bin-7.9.0/bin/pmd", "url": archive.as_uri(), "archive": True,
                                         "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()})
    path = download_tool("pmd")
    assert path == str(tools_dir / "pmd-bin-7.9.0" / "bin" / "pmd") and os.access(path, os.X_OK)


def test_pmd_comes_from_pmd_home_or_the_path(tools_dir, monkeypatch):
    monkeypatch.delenv("PMD_HOME", raising=False)
    monkeypatch.setattr(ExternalTools.shutil, "which", lambda name: None)
    assert find_pmd() == "pmd"
    monkeypatch.setattr(ExternalTools.shutil, "which", lambda name: "/usr/bin/pmd")
    assert find_pmd() == "/usr/bin/pmd"
    monkeypatch.setenv("PMD_HOME", "/opt/pmd")
    assert find_pmd() == os.path.join("/opt/pmd", "bin", "pmd")


def test_cli_has_a_setup_flag():
    assert build_parser().parse_args(["--setup"]).setup is True

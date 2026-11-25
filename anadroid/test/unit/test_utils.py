import os
import subprocess
import sys

from anadroid.utils import Utils
from anadroid.utils.Utils import execute_shell_command


def test_container_command_does_not_run_on_host(monkeypatch):
    started = []
    real_popen = subprocess.Popen

    def fake_popen(command, *args, **kwargs):
        started.append(command)
        return real_popen("true", *args, **kwargs)

    monkeypatch.setenv("ANDROID_HOME", "/sdk")
    monkeypatch.setattr(Utils.subprocess, "Popen", fake_popen)
    execute_shell_command("echo hello", in_container=True, container_id="c1")
    assert len(started) == 1
    assert started[0].startswith("docker exec c1")


def test_container_wrapper_works_without_android_home(monkeypatch):
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    wrapper = Utils.DockerCommandWrapper("c1")
    assert wrapper._replace_paths("ls /tmp/x") == "ls /tmp/x"


def test_timeout_keeps_partial_output():
    res = execute_shell_command("echo started; sleep 5", timeout=1)
    assert res.return_code != 0
    assert "started" in res.output


def test_import_does_not_create_results_dir(tmp_path):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([repo_root] + sys.path))
    subprocess.run([sys.executable, "-c", "import anadroid.Anadroid"], cwd=tmp_path, env=env, check=True,
                   capture_output=True)
    assert not (tmp_path / "anadroid_results").exists()

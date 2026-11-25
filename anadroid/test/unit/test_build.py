from types import SimpleNamespace

import pytest

from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK, INSTRUMENTER
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.build import GradleBuilder as gradle_builder_module
from anadroid.build.GradleBuilder import GradleBuilder
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE
from anadroid.utils import JavaVersionManager as java_version_manager
from anadroid.utils.JavaVersionManager import get_gradle_matching_version
from anadroid.utils.Utils import COMMAND_RESULT


@pytest.mark.parametrize("gradle_version,java_version", [
    (None, 17),
    ("4.10.1", 8),
    ("5.6.4", 11),
    ("7.2", 11),
    ("7.3.3", 17),
    ("8.4", 17),
    ("8.5", 21),
    ("8.10.2", 21),
    ("9.0", 21),
])
def test_java_version_for_gradle_version(gradle_version, java_version):
    assert get_gradle_matching_version(gradle_version) == java_version


def test_sign_apks_reads_the_command_result(monkeypatch, tmp_path):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    builder = GradleBuilder(None, MockedDevice(), str(tmp_path), None)
    builder.proj = SimpleNamespace(proj_dir=str(tmp_path), results_dir=str(tmp_path),
                                   get_apks=lambda build_type=None: ["app-release.apk"])
    monkeypatch.setattr(gradle_builder_module, "sign_apk", lambda apk: COMMAND_RESULT(0, "", ""))
    assert builder.sign_apks(BUILD_TYPE.RELEASE) is True


def test_just_analyze_processes_each_project_one_time(monkeypatch, tmp_path):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    anadroid = AnaDroid(str(tmp_path), results_dir=str(tmp_path), profiler=PROFILER.NONE,
                        testing_framework=TESTING_FRAMEWORK.NONE, device=MockedDevice(),
                        instrumenter=INSTRUMENTER.NONE, instrumentation_type=INSTRUMENTATION_TYPE.MANIFEST,
                        load_projects=False)
    anadroid.app_projects_ut = ["/projs/a", "/projs/b", "/projs/c"]
    processed = []
    monkeypatch.setattr(anadroid, "build_app_project", lambda proj, **kwargs: processed.append(proj))
    monkeypatch.setattr(anadroid.device, "install_apks", lambda *args, **kwargs: [])
    anadroid.just_analyze()
    assert processed == ["/projs/a", "/projs/b", "/projs/c"]


def test_find_java_home_reads_the_release_file(monkeypatch, tmp_path):
    jdk8 = tmp_path / "jdk-a"
    jdk17 = tmp_path / "jdk-b" / "Contents" / "Home"
    jdk8.mkdir()
    jdk17.mkdir(parents=True)
    (jdk8 / "release").write_text('JAVA_VERSION="1.8.0_442"\n')
    (jdk17 / "release").write_text('IMPLEMENTOR="x"\nJAVA_VERSION="17.0.4.1"\n')
    monkeypatch.delenv("JAVA_HOME_17", raising=False)
    monkeypatch.setattr(java_version_manager, "JAVA_SEARCH_GLOBS", [str(tmp_path / "*")])
    assert java_version_manager.find_java_home(8) == str(jdk8)
    assert java_version_manager.find_java_home(17) == str(jdk17)
    assert java_version_manager.find_java_home(21) is None
    assert f'export JAVA_HOME="{jdk17}"' in java_version_manager.get_change_java_version_cmd(17)
    assert java_version_manager.get_change_java_version_cmd(21) == ""


def test_find_java_home_prefers_the_environment_variable(monkeypatch):
    monkeypatch.setenv("JAVA_HOME_17", "/custom/jdk17")
    assert java_version_manager.find_java_home(17) == "/custom/jdk17"


def test_gradle_retry_keeps_the_lint_option(monkeypatch, tmp_path):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    builder = GradleBuilder(None, MockedDevice(), str(tmp_path), None)
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    builder.proj = SimpleNamespace(proj_dir=str(tmp_path), results_dir=str(results_dir), has_gradle_wrapper=lambda: True)
    commands = []

    def fake_shell(cmd, **kwargs):
        commands.append(cmd)
        return COMMAND_RESULT(0, "try editing the distributionUrl", "")

    monkeypatch.setattr(gradle_builder_module, "execute_shell_command", fake_shell)
    monkeypatch.setattr(gradle_builder_module, "solve_known_error", lambda *args, **kwargs: None)
    assert builder.exec_with_gradlew(tries=1, skip_lint=True) is False
    assert len(commands) == 2
    assert all("-x lint" in c and "gtimeout" not in c for c in commands)

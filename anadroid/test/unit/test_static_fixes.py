import os
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK, INSTRUMENTER
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.application.Dependency import BuildDependency, DependencyType
from anadroid.build import GracleBuildErrorSolver as solver
from anadroid.build import GradleBuilder as gradle_builder_module
from anadroid.build.GracleBuildErrorSolver import KNOWN_ERROR, solve_known_error, update_gradle_wrapper_version
from anadroid.build.GradleBuilder import GradleBuilder, gen_dependency_string, set_transitive_names
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrumentation.ManifestInstrumenter import AndroidManifestInstrumenter, ANDROID_NS
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE
from anadroid.utils import Utils
from anadroid.utils.JavaVersionManager import get_java_version
from anadroid.utils.Utils import DockerCommandWrapper, COMMAND_RESULT


def make_anadroid(monkeypatch, tmp_path, **kwargs):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    return AnaDroid(str(tmp_path), results_dir=str(tmp_path), profiler=PROFILER.NONE,
                    testing_framework=TESTING_FRAMEWORK.NONE, device=MockedDevice(),
                    instrumenter=INSTRUMENTER.NONE, instrumentation_type=INSTRUMENTATION_TYPE.MANIFEST,
                    load_projects=False, **kwargs)


def make_builder(monkeypatch, tmp_path, plugin_version="8.5.0"):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    proj = SimpleNamespace(proj_dir=str(tmp_path), results_dir=str(results_dir), modules={},
                           get_gradle_plugin=lambda: plugin_version)
    return GradleBuilder(proj, MockedDevice(), str(tmp_path), None)


# --- recover option ---

def test_recover_reads_the_projects_of_the_previous_run(monkeypatch, tmp_path):
    anadroid = make_anadroid(monkeypatch, tmp_path)
    logs = tmp_path / "logs"
    logs.mkdir(exist_ok=True)
    previous = logs / "2020-01-01-10-00-00.log"
    previous.write_text("[Info] 2020-01-01-10-00-01: Processing app Mint in /projs/Mint in space\n"
                        "[Info] 2020-01-01-10-00-02: Processing app b in /projs/b\n")
    os.utime(previous, (1, 1))
    Utils.logi("a message of the current run")  # creates the log file of the current run
    assert anadroid.get_projs_from_last_run() == ["/projs/Mint in space", "/projs/b"]


# --- gradle error rules ---

def test_wrapper_version_update(tmp_path):
    props = tmp_path / "gradle-wrapper.properties"
    props.write_text("distributionUrl=https\\://services.gradle.org/distributions/gradle-6.5-bin.zip\n")
    update_gradle_wrapper_version(str(props), "8.7-all")
    assert "gradle-8.7-all.zip" in props.read_text()
    update_gradle_wrapper_version(str(props), None)
    assert "gradle-8.7-all.zip" in props.read_text()


def test_wrapper_error_without_wrapper_file_does_not_crash(tmp_path):
    proj = SimpleNamespace(proj_dir=str(tmp_path), root_build_file=str(tmp_path / "build.gradle"))
    (tmp_path / "build.gradle").write_text("")
    solve_known_error(proj, KNOWN_ERROR.WRAPPER_ERROR,
                      "Minimum supported Gradle version is 8.7. Current version is 8.0. try editing the distributionUrl")


def test_missing_platform_rule_reads_the_version_from_the_error(monkeypatch, tmp_path):
    downloaded = []
    monkeypatch.setattr(solver, "SDKManager",
                        lambda: SimpleNamespace(download_platform=lambda v: downloaded.append(v)))
    proj = SimpleNamespace(proj_dir=str(tmp_path))
    solve_known_error(proj, KNOWN_ERROR.NO_TARGET_PLATFORM, "failed to find target with hash string 'android-34' in: /sdk")
    assert downloaded == ["34"]


def test_min_sdk_rule_raises_the_min_sdk(tmp_path):
    build_file = tmp_path / "build.gradle"
    build_file.write_text("android {\n defaultConfig {\n  minSdkVersion 16\n }\n}\n")
    proj = SimpleNamespace(proj_dir=str(tmp_path), get_build_files=lambda: [str(build_file)])
    solve_known_error(proj, KNOWN_ERROR.MIN_SDK_ERROR,
                      "Manifest merger failed : uses-sdk:minSdkVersion 16 cannot be smaller than version 21 "
                      "declared in library [androidx.core:core:1.9.0]")
    assert "minSdkVersion 21" in build_file.read_text()


# --- gradle builder ---

def test_dependency_strings():
    set_transitive_names("8.0.0")
    assert gen_dependency_string(BuildDependency("g:a", version="1.0")) == "implementation 'g:a:1.0'"
    assert gen_dependency_string(BuildDependency("g:a")) == "implementation 'g:a'"
    assert gen_dependency_string(BuildDependency("g:p", dep_type=DependencyType.CLASSPATH, version="2")) == "classpath 'g:p:2'"
    assert gen_dependency_string(BuildDependency("lib", dep_type=DependencyType.LOCAL_MODULE)) == "implementation project(':lib')"
    set_transitive_names("2.0.0")
    assert gradle_builder_module.ANDROID_TEST_TRANSITIVE == "androidTestCompile"
    set_transitive_names("8.0.0")


def test_failed_build_is_not_a_success_when_retry_is_off(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path)
    builder.regist_error_build("build")
    builder.retry_on_fail = False
    assert builder.was_attempted_to_build_before() is True
    assert builder.build() is False


def test_last_build_status_is_read_from_the_results_dir(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path)
    builder.regist_successful_build("build")
    os.remove(os.path.join(builder.proj.proj_dir, "gradle_builder_buildStatus.json"))
    assert builder.was_last_build_successful() is True


def test_plugin_is_added_to_a_plugins_block_with_parentheses(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path)
    builder.instrumenter = SimpleNamespace(needs_build_plugin=lambda: True, get_build_plugins=lambda: ["my-plugin"])
    build_file = tmp_path / "build.gradle"
    build_file.write_text("plugins {\n    id('com.android.application')\n}\nandroid {\n}\n")
    builder._GradleBuilder__add_plugins(str(build_file))
    content = build_file.read_text()
    assert "id('com.android.application')" in content and "id 'my-plugin'" in content


def test_local_properties_has_no_ndk_path_when_the_ndk_is_absent(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path)
    assert "ndk" not in builder.build_local_properties_file()
    (tmp_path / "ndk-bundle").mkdir()
    assert "ndk.dir" in builder.build_local_properties_file()


# --- utils ---

def test_container_command_keeps_quotes(monkeypatch):
    commands = []
    monkeypatch.setattr(Utils, "execute_shell_command", lambda cmd, **kwargs: commands.append(cmd) or COMMAND_RESULT(0, "", ""))
    DockerCommandWrapper("c1").execute('echo "a b" > /x/out.txt')
    assert commands == ["""docker exec c1 sh -c 'echo "a b" > /x/out.txt'"""]


def test_sign_apk_command_does_not_need_bash(monkeypatch):
    commands = []
    monkeypatch.setattr(Utils, "get_apksigner_bin", lambda: "apksigner")
    monkeypatch.setattr(Utils, "execute_shell_command", lambda cmd, **kwargs: commands.append(cmd) or COMMAND_RESULT(0, "", ""))
    Utils.sign_apk("/x/app.apk")
    assert "<<<" not in commands[0] and "--ks-pass pass:" in commands[0]


@pytest.mark.parametrize("text,version", [
    ('openjdk version "1.8.0_442"', 8),
    ('openjdk version "11.0.26" 2025-01-21', 11),
    ('openjdk version "17.0.11" 2024-04-16', 17),
    ('java version "21.0.1.8" 2023-10-17 LTS', 21),
    ("17", 17),
    (8, 8),
])
def test_java_version_parsing(text, version):
    assert get_java_version(text) == version


def test_semantic_version_with_one_number():
    assert DefaultSemanticVersion("8").major == 8
    assert DefaultSemanticVersion("").major == 0


# --- analyzers and instrumentation ---

def test_pmd_reports_a_missing_binary(tmp_path):
    project = SimpleNamespace(proj_dir=str(tmp_path), proj_name="p", modules={"app": None})
    with pytest.raises(FileNotFoundError):
        PMDAnalysis(bin_path=str(tmp_path / "no_pmd")).analyze_project(project, output_dir=str(tmp_path))


MANIFEST = ('<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
            'xmlns:tools="http://schemas.android.com/tools" package="a.b">'
            '<application android:label="x" tools:ignore="AllowBackup"/></manifest>')


def test_manifest_gets_profileable_and_debuggable(tmp_path):
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(MANIFEST)
    device = SimpleNamespace(get_device_sdk_version=lambda: 33)
    instrumenter = AndroidManifestInstrumenter(SimpleNamespace(device=device))
    instrumenter._AndroidManifestInstrumenter__make_app_debuggable_and_profileable(str(manifest), True)
    application = ET.parse(str(manifest)).getroot().find("application")
    assert application.find("profileable").get(f"{{{ANDROID_NS}}}shell") == "true"
    assert application.get(f"{{{ANDROID_NS}}}debuggable") == "true"
    assert "xmlns:tools" in manifest.read_text()


def test_build_tools_come_from_the_newest_version(monkeypatch, tmp_path):
    for version in ("25.0.2", "9.0.0", "37.0.0", "36.1.0"):
        tool_dir = tmp_path / "build-tools" / version
        tool_dir.mkdir(parents=True)
        (tool_dir / "apksigner").write_text("")
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    assert Utils.find_build_tool("apksigner") == str(tmp_path / "build-tools" / "37.0.0" / "apksigner")
    assert Utils.get_apksigner_bin() == str(tmp_path / "build-tools" / "37.0.0" / "apksigner")
    assert Utils.find_build_tool("aapt") is None

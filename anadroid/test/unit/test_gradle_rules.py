from types import SimpleNamespace

import pytest

from anadroid.application.AndroidProject import find_gradle_plugin_version
from anadroid.build import GradleBuilder as gradle_builder_module
from anadroid.build.GracleBuildErrorSolver import get_adequate_gradle_version, is_known_error, KNOWN_ERROR
from anadroid.build.GradleBuilder import GradleBuilder, replace_sdk_version, set_transitive_names
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.device.MockedDevice import MockedDevice


@pytest.mark.parametrize("content,version", [
    ("classpath 'com.android.tools.build:gradle:4.1.3'", "4.1.3"),
    ('classpath("com.android.tools.build:gradle:7.4.2")', "7.4.2"),
    ("plugins {\n id 'com.android.application' version '8.1.0' apply false\n}", "8.1.0"),
    ('plugins {\n id("com.android.library") version "8.5.2" apply false\n}', "8.5.2"),
    ("plugins {\n alias(libs.plugins.android.application) apply false\n}", None),
])
def test_find_gradle_plugin_version_in_build_file(tmp_path, content, version):
    build_file = tmp_path / "build.gradle"
    build_file.write_text(content)
    assert find_gradle_plugin_version(str(tmp_path), str(build_file)) == version


def test_find_gradle_plugin_version_in_version_catalog(tmp_path):
    build_file = tmp_path / "build.gradle.kts"
    build_file.write_text("plugins {\n alias(libs.plugins.android.application) apply false\n}")
    (tmp_path / "gradle").mkdir()
    (tmp_path / "gradle" / "libs.versions.toml").write_text(
        '[versions]\nkotlin = "2.0.0"\nagp = "8.7.3"\n'
        '[plugins]\nandroid-application = { id = "com.android.application", version.ref = "agp" }\n')
    assert find_gradle_plugin_version(str(tmp_path), str(build_file)) == "8.7.3"


@pytest.mark.parametrize("plugin_version,gradle_version", [
    ("3.6.4", "5.6.4-all"),
    ("4.1.3", "6.5-all"),
    ("4.2.2", "6.7.1-all"),
    ("7.0.4", "7.0-all"),
    ("7.4.2", "7.5-all"),
    ("8.0.0", "8.0-all"),
    ("8.5.2", "8.7-all"),
    ("8.13.0", "8.13-all"),
    ("9.0.0", "9.1.0-all"),
    ("9.5.0", "9.6.0-all"),
])
def test_gradle_version_for_plugin_version(plugin_version, gradle_version):
    assert get_adequate_gradle_version(plugin_version) == gradle_version


def test_semantic_version_order():
    assert DefaultSemanticVersion("8.10.2") > DefaultSemanticVersion("8.4")
    assert DefaultSemanticVersion("7.0") == DefaultSemanticVersion("7.0.0")


def test_known_error_detection():
    assert is_known_error("Minimum supported Gradle version is 8.7. Current version is 8.0. "
                          "If using the gradle wrapper, try editing the distributionUrl") == KNOWN_ERROR.WRAPPER_ERROR
    assert is_known_error("BUILD SUCCESSFUL in 3s") is None


@pytest.mark.parametrize("line,expected", [
    ("minSdkVersion 33", "minSdkVersion 28"),
    ("minSdkVersion(33)", "minSdkVersion(28)"),
    ("minSdk 33", "minSdk 28"),
    ("minSdk = 33", "minSdk = 28"),
    ("minSdkVersion rootProject.ext.minSdk", "minSdkVersion rootProject.ext.minSdk"),
])
def test_replace_sdk_version(line, expected):
    assert replace_sdk_version(line, "min", 28) == expected


def test_transitive_names_follow_the_current_project():
    set_transitive_names("2.3.0")
    assert gradle_builder_module.TRANSITIVE == "compile"
    set_transitive_names("8.1.0")
    assert gradle_builder_module.TRANSITIVE == "implementation"


def make_builder(monkeypatch, tmp_path, plugin_version):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    proj = SimpleNamespace(proj_dir=str(tmp_path), results_dir=str(tmp_path), get_gradle_plugin=lambda: plugin_version)
    return GradleBuilder(proj, MockedDevice(), str(tmp_path), None)


BUILD_FILE = "android {\n    defaultConfig {\n        minSdk 33\n        targetSdk 35\n    }\n}\n"


def test_new_plugin_gets_lint_block_and_no_dex_options(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path, "8.5.0")
    build_file = tmp_path / "build.gradle"
    build_file.write_text(BUILD_FILE)
    builder._GradleBuilder__add_or_update_dexoptions(str(build_file))
    builder._GradleBuilder__add_or_update_lintoptions(str(build_file))
    content = build_file.read_text()
    assert "dexOptions" not in content
    assert "lintOptions" not in content
    assert "lint {" in content and "abortOnError false" in content


def test_old_plugin_keeps_dex_and_lint_options(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path, "3.6.4")
    build_file = tmp_path / "build.gradle"
    build_file.write_text(BUILD_FILE)
    builder._GradleBuilder__add_or_update_dexoptions(str(build_file))
    builder._GradleBuilder__add_or_update_lintoptions(str(build_file))
    content = build_file.read_text()
    assert "dexOptions {" in content and "lintOptions {" in content


def test_sdk_versions_adapt_to_the_device_with_the_new_dsl(monkeypatch, tmp_path):
    builder = make_builder(monkeypatch, tmp_path, "8.5.0")
    build_file = tmp_path / "build.gradle"
    build_file.write_text(BUILD_FILE)
    assert builder.needs_min_sdk_upgrade(str(build_file)) is True
    assert builder.adapt_target_sdk_upgrade(str(build_file)) is True
    content = build_file.read_text()
    assert "minSdk 28" in content and "targetSdk 28" in content

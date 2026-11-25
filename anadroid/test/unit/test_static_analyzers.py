from types import SimpleNamespace

from anadroid.analysis.pre_build_analysis import PMDAnalysis as pmd_module
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.utils.Utils import COMMAND_RESULT

LINT_REPORT = """<?xml version="1.0" encoding="UTF-8"?>
<issues format="6" by="lint 8.0.0">
    <issue id="DrawAllocation" severity="Warning" message="m1" category="Performance">
        <location file="app/src/main/java/com/example/MainView.java" line="10"/>
    </issue>
    <issue id="DrawAllocation" severity="Warning" message="m2" category="Performance">
        <location file="app/src/androidTest/java/com/example/MainViewTest.java" line="20"/>
    </issue>
</issues>
"""


def test_lint_ignores_issues_in_test_sources(tmp_path):
    report = tmp_path / "lint-results-debug.xml"
    report.write_text(LINT_REPORT)
    analyzer = LintAnalysis()
    assert [i.file for i in analyzer.get_issues(str(report))] == ["app/src/main/java/com/example/MainView.java"]
    assert len(analyzer.get_issues(str(report), ignore_tests=False)) == 2


def test_pmd_continues_after_a_module_that_is_already_processed(monkeypatch, tmp_path):
    commands = []
    monkeypatch.setattr(pmd_module, "execute_shell_command",
                        lambda cmd, **kwargs: commands.append(cmd) or COMMAND_RESULT(0, "", ""))
    project = SimpleNamespace(proj_dir=str(tmp_path), proj_name="p", modules={"app": None, "lib": None})
    (tmp_path / "app_pmd_analysis.json").write_text("{}")
    PMDAnalysis().analyze_project(project, retry=False, output_dir=str(tmp_path))
    assert len(commands) == 1
    assert "lib_pmd_analysis.json" in commands[0]

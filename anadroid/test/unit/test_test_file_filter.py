import json

import pytest

from anadroid.analysis.StaticAnalyzer import is_test_file
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.DetektAnalysis import DetektAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis

MAIN_FILE = "app/src/main/java/com/latest/contest/AttestationHelper.java"
TEST_FILE = "app/src/test/java/com/latest/contest/AttestationHelperTest.java"


@pytest.mark.parametrize("path,expected", [
    (MAIN_FILE, False),
    ("app/src/main/java/com/example/testing/Fastest.kt", False),
    ("app/src/main/res/layout/activity_test.xml", False),
    ("/home/tester/projects/app/src/main/java/A.java", False),
    (TEST_FILE, True),
    ("app/src/androidTest/java/com/example/A.kt", True),
    ("app/src/testDebug/java/com/example/A.kt", True),
    ("app/src/androidTestFree/java/com/example/A.kt", True),
    ("app/src/sharedTest/java/com/example/A.kt", True),
    ("app\\src\\test\\java\\A.java", True),
    ("app/src/main/java/com/example/ExampleInstrumentedTest.java", True),
    ("app/src/main/java/com/example/ExampleUnitTest.kt", True),
    (None, False),
    ("", False),
])
def test_is_test_file(path, expected):
    assert is_test_file(path) is expected


def files_of(issues):
    return sorted(i.file for i in issues)


def test_pmd_keeps_main_files_with_test_in_the_path(tmp_path):
    report = tmp_path / "app_pmd_analysis.json"
    violation = {"rule": "AvoidArrayLoops", "beginline": 1, "begincolumn": 1}
    report.write_text(json.dumps({"files": [{"filename": MAIN_FILE, "violations": [violation]},
                                            {"filename": TEST_FILE, "violations": [violation]}]}))
    assert files_of(PMDAnalysis().get_issues(str(report))) == [MAIN_FILE]
    assert len(PMDAnalysis().get_issues(str(report), ignore_tests=False)) == 2


def test_lint_keeps_main_files_with_test_in_the_path(tmp_path):
    report = tmp_path / "lint-results.xml"
    report.write_text(f'''<issues>
<issue id="DrawAllocation" severity="Warning" message="m1" category="Performance"><location file="{MAIN_FILE}" line="1"/></issue>
<issue id="DrawAllocation" severity="Warning" message="m2" category="Performance"><location file="{TEST_FILE}" line="2"/></issue>
</issues>''')
    assert files_of(LintAnalysis().get_issues(str(report))) == [MAIN_FILE]


def test_detekt_ignores_variant_test_source_sets(tmp_path):
    report = tmp_path / "detekt_analysis.xml"
    error = '<error line="1" column="1" severity="warning" message="m" source="detekt.SpreadOperator"/>'
    report.write_text(f'''<checkstyle version="4.3">
<file name="/p/{MAIN_FILE}">{error}</file>
<file name="/p/app/src/testDebug/java/A.kt">{error}</file>
</checkstyle>''')
    assert files_of(DetektAnalysis().get_issues(str(report))) == [f"/p/{MAIN_FILE}"]


def test_adoctor_keeps_main_files_with_test_in_the_path(tmp_path):
    report = tmp_path / "adoctor.csv"
    report.write_text(f"File,Class,SL\n{MAIN_FILE},A,1\n{TEST_FILE},B,1\n")
    issues = ADoctorAnalysis().get_issues(str(report))
    assert {i.file for i in issues} == {MAIN_FILE}


def test_ecoandroid_filter_reads_the_file_text(tmp_path):
    analyzer = EcoAndroidAnalysis()
    issue_id = next(iter(analyzer.identifiable_issues))
    report_dir = tmp_path / "ecoandroid_out"
    report_dir.mkdir()

    def problem(path):
        return (f'<problem><file>file://$PROJECT_DIR$/{path}</file><line>3</line>'
                f'<problem_class id="{issue_id}">x</problem_class><description>d</description></problem>')

    (report_dir / f"{issue_id}.xml").write_text(f"<problems>{problem(MAIN_FILE)}{problem(TEST_FILE)}</problems>")
    assert files_of(analyzer.get_issues(str(report_dir))) == [MAIN_FILE]

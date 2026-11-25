from types import SimpleNamespace

import pytest

from anadroid import Anadroid as anadroid_module
from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK, INSTRUMENTER
from anadroid.analysis.pre_build_analysis import create_pre_build_analyzers, PRE_BUILD_ANALYZERS
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE
from anadroid.main import build_parser


def make_anadroid(monkeypatch, tmp_path, **kwargs):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    return AnaDroid(str(tmp_path), results_dir=str(tmp_path), profiler=PROFILER.NONE,
                    testing_framework=TESTING_FRAMEWORK.NONE, device=MockedDevice(),
                    instrumenter=INSTRUMENTER.NONE, instrumentation_type=INSTRUMENTATION_TYPE.MANIFEST,
                    load_projects=False, **kwargs)


def test_create_analyzers_from_names():
    analyzers = create_pre_build_analyzers(["pmd", "lint"])
    assert [type(a) for a in analyzers] == [PMDAnalysis, LintAnalysis]


def test_all_registered_analyzers_can_be_imported():
    assert len(create_pre_build_analyzers(PRE_BUILD_ANALYZERS.keys())) == len(PRE_BUILD_ANALYZERS)


def test_unknown_analyzer_name_is_an_error():
    with pytest.raises(ValueError):
        create_pre_build_analyzers(["not_a_tool"])


def test_cli_selects_analyzers_and_jobs():
    args = build_parser().parse_args(["-sa", "-sat", "pmd", "lint", "-j", "2"])
    assert args.static_analyzers == ["pmd", "lint"]
    assert args.jobs == 2
    assert build_parser().parse_args([]).static_analyzers == ["scc"]


def test_anadroid_uses_the_selected_analyzers(monkeypatch, tmp_path):
    anadroid = make_anadroid(monkeypatch, tmp_path, pre_build_analyzers=["pmd"])
    assert [type(a) for a in anadroid.pre_build_analyzers.inner_analyzers] == [PMDAnalysis]


def test_static_analysis_in_parallel_keeps_the_project_order(monkeypatch, tmp_path):
    anadroid = make_anadroid(monkeypatch, tmp_path)
    anadroid.app_projects_ut = [f"/projs/p{i}" for i in range(6)]
    monkeypatch.setattr(anadroid_module, "AndroidProject",
                        lambda projname, projdir, **kwargs: SimpleNamespace(results_dir=f"res/{projname}"))
    analyzed = []
    anadroid.pre_build_analyzers = SimpleNamespace(
        analyze_project=lambda proj, **kwargs: analyzed.append(proj.results_dir))
    assert anadroid.just_static_analyze(jobs=3) == [f"res/p{i}" for i in range(6)]
    assert sorted(analyzed) == [f"res/p{i}" for i in range(6)]

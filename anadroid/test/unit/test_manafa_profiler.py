import json
from types import SimpleNamespace

from anadroid.profiler.ManafaProfiler import ManafaProfiler


def make_profiler(tmp_path, **trace_attribute):
    """ManafaProfiler with a fake E-manafa object. `trace_attribute` is the attribute with the method trace file:
    trace_out_file in AMEManafa, hunter_out_file in HunterEManafa."""
    files = {}
    for name in ("bts", "pft", "trace", "consumptions"):
        files[name] = tmp_path / f"{name}.log"
        files[name].write_text(name)
    attribute_name = next(iter(trace_attribute))
    manafa = SimpleNamespace(bts_out_file=str(files["bts"]), pft_out_file=str(files["pft"]),
                             app_consumptions_log=str(files["consumptions"]),
                             save_final_report=lambda **kwargs: None, clean=lambda: None,
                             **{attribute_name: str(files["trace"])})
    profiler = ManafaProfiler.__new__(ManafaProfiler)
    profiler.manafa = manafa
    profiler.test_index_file = "tests_index.json"
    return profiler


def pull_and_read_index(profiler, tmp_path):
    target_dir = tmp_path / "out"
    target_dir.mkdir()
    profiler.pull_results(0, str(target_dir))
    assert (target_dir / "trace.log").exists()
    return json.loads((target_dir / "tests_index.json").read_text())["0"]


def test_pull_results_with_activity_manager_traces(tmp_path):
    assert len(pull_and_read_index(make_profiler(tmp_path, trace_out_file=True), tmp_path)) == 4


def test_pull_results_with_hunter_traces(tmp_path):
    assert len(pull_and_read_index(make_profiler(tmp_path, hunter_out_file=True), tmp_path)) == 4

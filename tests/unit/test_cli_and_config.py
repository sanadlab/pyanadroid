import json

from anadroid import Config
from anadroid.Types import ANALYZER
from anadroid.main import build_parser


def test_post_execution_analyzer_option_accepts_analyzer_names():
    args = build_parser().parse_args(["-pa", ANALYZER.MANAFA_ANALYZER.value])
    assert ANALYZER(args.post_execution_analyzers) == ANALYZER.MANAFA_ANALYZER


def test_device_serial_accepts_text():
    args = build_parser().parse_args(["-ds", "emulator-5554"])
    assert args.device_serial == "emulator-5554"


def test_set_general_config_does_not_change_the_file(tmp_path):
    cfg_file = tmp_path / "general_config.json"
    cfg_file.write_text(json.dumps({"tests": {"tests_per_app": 1}}))
    Config.set_general_config("tests", "tests_per_app", 7, cfg_file=str(cfg_file))
    assert Config.get_general_config("tests", cfg_file=str(cfg_file))["tests_per_app"] == 7
    assert json.loads(cfg_file.read_text())["tests"]["tests_per_app"] == 1

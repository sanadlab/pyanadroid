from anadroid.main import build_parser
from anadroid.utils import Utils


def read_log():
    with open(Utils.get_log_file()) as f:
        return f.read()


def test_debug_messages_go_to_the_file_but_not_to_the_console(monkeypatch, capsys):
    monkeypatch.setattr(Utils, "VERBOSE", False)
    Utils.logd("debug detail")
    Utils.logi("info detail")
    console = capsys.readouterr().out
    assert "debug detail" not in console and "info detail" in console
    assert "[Debug]" in read_log() and "debug detail" in read_log()


def test_verbose_mode_shows_debug_messages(monkeypatch, capsys):
    Utils.set_verbose(True)
    Utils.logd("debug detail")
    Utils.set_verbose(False)
    assert "debug detail" in capsys.readouterr().out


def test_failed_command_message_has_the_command_and_the_return_code(capsys):
    res = Utils.execute_shell_command("echo problem 1>&2; exit 3")
    assert res.validate() is False
    console = capsys.readouterr().out
    assert "exit 3" in console and "return code 3" in console and "problem" in console


def test_cli_has_a_verbose_flag():
    assert build_parser().parse_args(["-v"]).verbose is True
    assert build_parser().parse_args([]).verbose is False

import argparse
import os
import inspect

from anadroid.Anadroid import AnaDroid
from anadroid.Config import set_general_config, set_config_file
from anadroid.Types import TESTING_FRAMEWORK, PROFILER, ANALYZER, INSTRUMENTER, BUILDER
from anadroid.analysis.pre_build_analysis import PRE_BUILD_ANALYZERS
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.device.Device import set_device_conn, has_connected_device
from anadroid.device.DeviceState import DeviceState
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE
from anadroid.utils.ExternalTools import setup_tools
from anadroid.utils.Utils import set_verbose, logi, get_log_file


def init_pyanadroid_from_args(args):
    needs_dynamic_execution = not (args.buildonly or args.justanalyze or args.device or args.staticanalyze)
    return AnaDroid(arg1=args.diretory if (len(args.package_names) + len(args.application_packages) == 0) else args,
                    testing_framework=TESTING_FRAMEWORK(args.testingframework if needs_dynamic_execution else TESTING_FRAMEWORK.NONE),
                    device=MockedDevice() if not needs_dynamic_execution and not has_connected_device() else None,
                    profiler=PROFILER(args.profiler if needs_dynamic_execution else PROFILER.NONE),
                    build_type=BUILD_TYPE(args.buildtype),
                    instrumenter=INSTRUMENTER(args.instrumenter),
                    instrumentation_type=INSTRUMENTATION_TYPE(args.instrumentationtype),
                    analyzer=ANALYZER(args.post_execution_analyzers),
                    tests_dir=args.tests_dir,
                    rebuild_apps=args.rebuild,
                    reinstrument=args.reinstrument,
                    recover_from_last_run=args.recover,
                    test_cmd=args.command,
                    load_projects=not args.run_only and args.device is None,
                    lazy_load=args.device is not None,
                    builder=args.builder,
                    pre_build_analyzers=args.static_analyzers
                    )


def process_general_config(args_obj):
    n_times = args_obj.n_times if args_obj.n_times != 0 else 0
    if n_times != 0:
        set_general_config('tests', 'tests_per_app', n_times)


def count_positional_args(func):
    sig = inspect.signature(func)
    positional_args = [param for param in sig.parameters.values()
                       if param.default == inspect.Parameter.empty
                       and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
    return len(positional_args)


def exec_device_cmd(anad, cmd: str):
    device_methods = list(filter(lambda x: '__' not in x, dir(anad.device)))
    has_arg = len(cmd.split(" ")) > 1
    action = cmd.split(" ")[0]
    if action.strip() == 'list':
        action_explanation = list(map(lambda x:
                                      f'-> {x}: ' + getattr(anad.device, x).__doc__.replace("\n", " ")
                                      if getattr(anad.device, x).__doc__ is not None else f'-> {x}', device_methods))
        res = "List of available actions:\n" + "\n".join(action_explanation)
        print(res)
        return res
    try:
        action_m = getattr(anad.device, action)
    except:
        raise Exception(f"Unable to find {action} action")
    if not callable(action_m):
        if isinstance(action_m, DeviceState):
            if has_arg:
                action_m = getattr(anad.device.device_state, cmd.split(" ")[1].strip())
                return str(action_m)
            else:
                print("please provide a valid action for device state")
        else:
            return str(action_m)
    min_action_args = count_positional_args(action_m)
    hasnt_enough_arg = callable(action_m) and min_action_args > len(cmd.split(" ")[1:])
    if hasnt_enough_arg:
        raise Exception(f"Not enough args for {action} action. Expecting {min_action_args} args")
    res = action_m if not callable(action_m) else (action_m(*cmd.split(" ")[1:]) if has_arg else action_m())
    return res


def get_device_cmd_help_text():
    return """device <Action> perform device commands"""


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--testingframework", default=TESTING_FRAMEWORK.MONKEY.value, type=str,
                        help="testing framework to exercise app(s)", choices=[e.value for e in TESTING_FRAMEWORK])
    parser.add_argument("-p", "--profiler", default=PROFILER.MANAFA.value, type=str,
                        help="energy profiler", choices=[e.value for e in PROFILER])
    parser.add_argument("-b", "--buildtype", default=BUILD_TYPE.DEBUG.value, type=str,
                        help="app build type", choices=[e.value for e in BUILD_TYPE])
    parser.add_argument("-i", "--instrumenter", default=INSTRUMENTER.MANIFEST.value, type=str,
                        help="Source code instrumenter", choices=[e.value for e in INSTRUMENTER])
    parser.add_argument("-it", "--instrumentationtype", default=INSTRUMENTATION_TYPE.MANIFEST.value,
                        type=str, help="instrumentation type", choices=[e.value for e in INSTRUMENTATION_TYPE])
    parser.add_argument("-pa", "--post_execution_analyzers", default=ANALYZER.MANAFA_ANALYZER.value, type=str,
                        help="results analyzer",
                        choices=[e.value for e in ANALYZER])
    parser.add_argument("-d", "--diretory", default="demoProjects", type=str, help="app(s)' folder")
    parser.add_argument("-dev", "--device", default=None, type=str,
                        help="device <Action>. performs device class commands")
    parser.add_argument("-bo", "--buildonly", help="just build apps", action='store_true')
    parser.add_argument("-record", "--record", help="record test", action='store_true', default=False)
    parser.add_argument("-run", "--run_only", help="run only (skip build and instrumentation phase)",
                        action='store_true')
    parser.add_argument("-rb", "--rebuild", help="rebuild apps", action='store_true')
    parser.add_argument("-ri", "--reinstrument", help="reinstrument app", action='store_true')
    parser.add_argument("-ja", "--justanalyze", help="just analyze apps", action='store_true')
    parser.add_argument("-sa", "--staticanalyze", help="statically analyze apps", action='store_true')
    parser.add_argument("-sc", "--setconnection", help="set connection to device and exit",
                        choices=["USB", "WIFI"])
    parser.add_argument("-ds", "--device_serial", help="device serial id", type=str, default=None)
    parser.add_argument("-td", "--tests_dir", help="tests directory", type=str, default=None)
    parser.add_argument("-n", "--package_names", help="package(s) of already installed apps",
                        nargs='+', default=[])
    parser.add_argument("-apk", "--application_packages", help="path of apk(s) to process",
                        nargs='+', default=[])
    parser.add_argument("-rec", "--recover", help="recover progress of the previous run",
                        action='store_true')
    parser.add_argument("-cmd", "--command", help="test command", type=str, default=None)
    parser.add_argument("-nt", "--n_times", help="times to repeat test (overrides config)",
                        type=int, default=0)
    parser.add_argument("-bd", "--builder", help="builder to use", type=str, default=BUILDER.ANADROID_GRADLE_BUILDER.value,
                        choices=[e.value for e in BUILDER])
    parser.add_argument("-sat", "--static_analyzers", help="static analyzers to run before the build",
                        nargs='+', default=["scc"], choices=list(PRE_BUILD_ANALYZERS))
    parser.add_argument("-j", "--jobs", help="number of projects to analyze at the same time (with -sa)",
                        type=int, default=1)
    parser.add_argument("--config", help="general config file (JSON) to use in place of the default file",
                        type=str, default=None)
    parser.add_argument("--workdir", help="directory for the logs and the results (default: current directory)",
                        type=str, default=None)
    parser.add_argument("--setup", help="download the external tools (jars, PMD) and exit", action='store_true')
    parser.add_argument("-v", "--verbose", help="show debug messages (commands and their results)",
                        action='store_true')
    return parser


def apply_workdir(args):
    """makes the working directory the current directory. Logs and results are written there.
    The input paths of the command line stay relative to the directory where the command started."""
    if args.workdir is None:
        return
    args.diretory = os.path.abspath(args.diretory)
    args.tests_dir = os.path.abspath(args.tests_dir) if args.tests_dir is not None else None
    args.application_packages = [os.path.abspath(apk) for apk in args.application_packages]
    args.config = os.path.abspath(args.config) if args.config is not None else None
    os.makedirs(args.workdir, exist_ok=True)
    os.chdir(args.workdir)


def main():
    args = build_parser().parse_args()
    apply_workdir(args)
    if args.config is not None:
        set_config_file(args.config)
    set_verbose(args.verbose)
    logi(f"Log file of this run: {get_log_file()}")
    if args.setup:
        setup_tools()
        exit(0)
    process_general_config(args)
    if args.setconnection:
        set_device_conn(args.setconnection, device_id=args.device_serial)
        exit(0)
    anadroid = init_pyanadroid_from_args(args)
    if args.device:
        res = exec_device_cmd(anadroid, args.device)
        print(res)
    elif args.staticanalyze:
        anadroid.just_static_analyze(jobs=args.jobs)
    elif args.buildonly:
        anadroid.just_build_apps()
    elif args.justanalyze:
        anadroid.just_analyze()
    elif args.record:
        anadroid.record_test(args.tests_dir)
    elif args.run_only:
        anadroid.exec_command()
    else:
        anadroid.default_workflow()


if __name__ == '__main__':
    main()

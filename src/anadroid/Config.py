import json
import os

from anadroid.Types import TESTING_APPROACH, TESTING_FRAMEWORK, BUILD_SYSTEM, PROFILER, INSTRUMENTER, ANALYZER
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_general_config_dir, loge, logd

GENERAL_CONFIG_FILE_NAME = "general_config.json"
RESOURCES_CONFIG_DIR = get_general_config_dir()
# default config file, in the package
CONFIG_FILE = os.path.join(RESOURCES_CONFIG_DIR, GENERAL_CONFIG_FILE_NAME)
# config file given by the user (e.g. with --config)
USER_CONFIG_FILE = None


def set_config_file(path):
    """sets the config file to use in the current process."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config file {path} not found")
    global USER_CONFIG_FILE
    USER_CONFIG_FILE = path


def get_config_file():
    """returns the config file to use. The first file that exists in this order:
    1. the file given with --config, or in the environment variable PYANADROID_CONFIG;
    2. general_config.json in the current directory;
    3. general_config.json in the user config directory (~/.config/pyanadroid);
    4. the default file of the package.
    """
    user_config_dir = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config"),
                                   "pyanadroid")
    candidates = [USER_CONFIG_FILE, os.environ.get("PYANADROID_CONFIG"), GENERAL_CONFIG_FILE_NAME,
                  os.path.join(user_config_dir, GENERAL_CONFIG_FILE_NAME)]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return CONFIG_FILE


# values set at run time (e.g. from the command line). They apply to the current process only.
RUNTIME_OVERRIDES = {}


def get_general_config(cfg_type, cfg_file=None, default_value={}):
    cfg_file = cfg_file if cfg_file is not None else get_config_file()
    if not os.path.exists(cfg_file):
        loge(f"Config file {cfg_file} not found. Using the default value for '{cfg_type}'")
        return default_value
    with open(cfg_file, 'r') as jj:
        cfg = json.load(jj)
    if cfg_type not in cfg:
        logd(f"No '{cfg_type}' section in config file {cfg_file}. Using the default value")
        return default_value
    return {**cfg[cfg_type], **RUNTIME_OVERRIDES.get(cfg_type, {})}


def set_general_config(cfg_type, cfg_key, cfg_value,  cfg_file=None):
    """Overrides a config value for the current process. Does not change the config file."""
    cfg_file = cfg_file if cfg_file is not None else get_config_file()
    with open(cfg_file, 'r') as jj:
        cfg = json.load(jj)
    if cfg_type not in cfg:
        raise Exception(f"invalid config type {cfg_type}")
    RUNTIME_OVERRIDES.setdefault(cfg_type, {})[cfg_key] = cfg_value


SUPPORTED_TESTING_APPROACHES = {
    TESTING_APPROACH.WHITEBOX
}

SUPPORTED_TESTING_FRAMEWORKS = {
    TESTING_FRAMEWORK.MONKEY,
    TESTING_FRAMEWORK.RERAN,
    TESTING_FRAMEWORK.APP_CRAWLER,
    TESTING_FRAMEWORK.MONKEY_RUNNER,
    TESTING_FRAMEWORK.JUNIT,
    TESTING_FRAMEWORK.DROIDBOT,
    TESTING_FRAMEWORK.CUSTOM,
    TESTING_FRAMEWORK.NONE
}

SUPPORTED_BUILDING_SYSTEMS = {
    BUILD_SYSTEM.GRADLE
}

SUPPORTED_PROFILERS = {
    PROFILER.TREPN,
    PROFILER.MANAFA,
    PROFILER.GREENSCALER,
    PROFILER.NONE
}

SUPPORTED_INSTRUMENTERS = {
    INSTRUMENTER.JINST,
    INSTRUMENTER.NONE,
    INSTRUMENTER.MANIFEST
}

SUPPORTED_ANALYZERS = {
    ANALYZER.OLD_ANADROID_ANALYZER,
    ANALYZER.MANAFA_ANALYZER
}

SUPPORTED_INSTRUMENTATION_TYPES = {
    INSTRUMENTATION_TYPE.TEST,
    INSTRUMENTATION_TYPE.ANNOTATION,
    INSTRUMENTATION_TYPE.METHOD,
    INSTRUMENTATION_TYPE.MANIFEST,
}

SUPPORTED_SUITES = {
    PROFILER.TREPN: [INSTRUMENTATION_TYPE.TEST, INSTRUMENTATION_TYPE.METHOD],
    PROFILER.MANAFA: [INSTRUMENTATION_TYPE.ANNOTATION, INSTRUMENTATION_TYPE.MANIFEST],
    PROFILER.GREENSCALER: [INSTRUMENTATION_TYPE.ANNOTATION],
    PROFILER.NONE: [INSTRUMENTATION_TYPE.NONE, INSTRUMENTATION_TYPE.ANNOTATION, INSTRUMENTATION_TYPE.MANIFEST, INSTRUMENTATION_TYPE.METHOD, INSTRUMENTATION_TYPE.TEST]
}
import json
import os

from anadroid.Types import TESTING_APPROACH, TESTING_FRAMEWORK, BUILD_SYSTEM, PROFILER, INSTRUMENTER, ANALYZER
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_general_config_dir, loge, logd

GENERAL_CONFIG_FILE_NAME = "general_config.json"
RESOURCES_CONFIG_DIR = get_general_config_dir()
CONFIG_FILE = os.path.join(RESOURCES_CONFIG_DIR, GENERAL_CONFIG_FILE_NAME) \
    if not os.path.exists(GENERAL_CONFIG_FILE_NAME) else GENERAL_CONFIG_FILE_NAME


# values set at run time (e.g. from the command line). They apply to the current process only.
RUNTIME_OVERRIDES = {}


def get_general_config(cfg_type, cfg_file=CONFIG_FILE, default_value={}):
    if not os.path.exists(cfg_file):
        loge(f"Config file {cfg_file} not found. Using the default value for '{cfg_type}'")
        return default_value
    with open(cfg_file, 'r') as jj:
        cfg = json.load(jj)
    if cfg_type not in cfg:
        logd(f"No '{cfg_type}' section in config file {cfg_file}. Using the default value")
        return default_value
    return {**cfg[cfg_type], **RUNTIME_OVERRIDES.get(cfg_type, {})}


def set_general_config(cfg_type, cfg_key, cfg_value,  cfg_file=CONFIG_FILE):
    """Overrides a config value for the current process. Does not change the config file."""
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
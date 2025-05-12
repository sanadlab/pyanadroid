import os
import re
from shutil import copy

from textops import grep

from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge

# /Applications/IntelliJ\ IDEA\ CE.app/Contents/bin/inspect.sh  /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/ /Users/rar9993/repos/EcoAndroid/eco_ide/EcoAndroid/Project_Default.xml /Users/rar9993/repos/EcoAndroid/eco_ide/EcoAndroid/out  -d /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/app -v2

DEFAULT_PATH_JAR = os.path.join(get_resources_dir(), 'jars' ,"customLintFatima.jar")

class XALintAnalysis(LintAnalysis):
    def __init__(self, analyzers_cfg_file=None, jar_path=DEFAULT_PATH_JAR):
        super().__init__(analyzers_cfg_file, performance_only=False)
        self.name = 'xaL'
        self.jar_path = jar_path
        self.exec_cmd = ''
        self.setup()
        self.identifiable_issues.update({
           "NoLowMemoryResolver": KnownStaticPerformanceIssues.NO_LOW_MEMORY_RESOLVER,
            "InvalidatewithoutRect": KnownStaticPerformanceIssues.INVALIDATE_WITHOUT_RECT,
            "UnsupportedHardwareAcceleration": KnownStaticPerformanceIssues.UNSUPPORTED_HARDWARE_ACCELERATION,
            "HeavyAsyncTask": KnownStaticPerformanceIssues.HEAVY_ASYNC_TASK,
            "HeavyServiceStart": KnownStaticPerformanceIssues.HEAVY_SERVICE_START,
            "HeavyBroadcastReceiver": KnownStaticPerformanceIssues.HEAVY_BROADCAST_RECEIVER,
            "VacuousBackgroundService": KnownStaticPerformanceIssues.VACUOUS_BACKGROUND_SERVICE,
            "LifecycleContainment": KnownStaticPerformanceIssues.LIFECYCLE_CONTAINMENT,
            "EarlyResourceBinding": KnownStaticPerformanceIssues.EARLY_RESOURCE_BINDING,
            "ImmortalityBug": KnownStaticPerformanceIssues.IMMORTALITY_BUG,

        })

    def setup(self, **kwargs):
        target_location = os.path.join(os.path.expanduser("~"), ".android", 'lint')
        if not os.path.exists(target_location):
            os.makedirs(target_location)
        copy(self.jar_path, target_location)

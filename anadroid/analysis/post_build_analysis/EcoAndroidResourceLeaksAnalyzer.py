import os
import platform

from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.utils.Utils import execute_shell_command, get_resources_dir

# java -jar build/libs/EcoAndroidResourceLeak.jar "/Users/rar9993/Library/Android/sdk/platforms" "/Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/app/build/outputs/apk/debug/app-debug.apk" "standalone_out"

DEFAULT_OUTPUT_DIRNAME = "ecoandroid_analysis_output/"
DEFAULT_PATH_JAR = os.path.join(get_resources_dir(), 'jars', "EcoAndroidResourceLeak.jar")
DEFAULT_SDK_PATH = "/Users/rar9993/Library/Android/sdk/platforms"

class EcoAndroidResourceLeaksAnalysis(ExecutionResultsAnalyzer):
    def __init__(self, analyzers_cfg_file=None, jar_path=DEFAULT_PATH_JAR,
                 default_output_dir=DEFAULT_OUTPUT_DIRNAME, sdk_path=DEFAULT_SDK_PATH):
        super().__init__(analyzers_cfg_file)
        self.jar_path = jar_path
        self.sdk_path = sdk_path
        self.default_output_dir = default_output_dir
        self.exec_cmd = f"java -jar {jar_path} "

    def setup(self, **kwargs):
       pass

    def validate_test(self, app, arg1, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    def validate_filters(self):
        pass

    def clean(self):
        pass

    def get_val_for_filter(self, filter_name, add_data=None):
        pass

    def analyze_app(self, project, **kwargs):
        cmd = f"{self.exec_cmd} {project.proj_dir} {output_filepath} {search_pattern_code}"
        print(cmd)

    def analyze_test(self, app, test_id, **kwargs):
        pass

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        pass


import os

from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer
from anadroid.analysis.metrics.Issues import Issue, KnownStaticPerformanceIssues
from anadroid.application.Application import App
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, logi

# java -jar build/libs/EcoAndroidResourceLeak.jar "/Users/rar9993/Library/Android/sdk/platforms" "/Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/app/build/outputs/apk/debug/app-debug.apk" "standalone_out"

DEFAULT_OUTPUT_DIRNAME = "ecoandroid_resource_leaks/"
DEFAULT_PATH_JAR = os.path.join(get_resources_dir(), 'jars', "EcoAndroidResourceLeak.jar")
DEFAULT_SDK_PATH = "~/Library/Android/sdk/platforms"

class EcoAndroidResourceLeaksAnalysis(ExecutionResultsAnalyzer):
    def __init__(self, analyzers_cfg_file=None, jar_path=DEFAULT_PATH_JAR,
                 default_output_dir=DEFAULT_OUTPUT_DIRNAME, sdk_path=DEFAULT_SDK_PATH):
        super().__init__(analyzers_cfg_file)
        self.jar_path = jar_path
        self.sdk_path = sdk_path
        self.default_output_dir = default_output_dir
        self.exec_cmd = f"source ~/.zshrc ; j17 ; java -jar {jar_path}"
        self.identifiable_issues = {
            "CURSOR": KnownStaticPerformanceIssues.UNCLOSED_CLOSEABLE,
            "WAKELOCK": KnownStaticPerformanceIssues.WAKE_LOCK,
            "SQLITEDB": KnownStaticPerformanceIssues.UNCLOSED_CLOSEABLE,
            "CAMERA": KnownStaticPerformanceIssues.CAMERA_LEAK,
        }

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

    def analyze_app(self, app: App, **kwargs):
        retry = kwargs.get("retry", False)
        res_folder = os.path.join(app.local_res, DEFAULT_OUTPUT_DIRNAME)
        res_folder_prefix = os.path.join(res_folder, app.package_name)
        if not os.path.exists(res_folder):
            print(f"Creating directory {res_folder}")
            os.mkdir(res_folder)
        if not retry and len(list(filter(lambda x: x.endswith(".csv"), os.listdir(res_folder)))) > 0:
            logi(f"Skipping analysis for {app.package_name}. Already processed by EcoAndroid Resorce Leaks Analysis")
            return
        analyse_cmd = f"{self.exec_cmd} {self.sdk_path} {app.apk}  {res_folder_prefix}"
        print(analyse_cmd)
        res = execute_shell_command(analyse_cmd)
        res.validate()

    def analyze_test(self, app, test_id, **kwargs):
        pass

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        pass

    def get_issues(self, output_dir):
        #ignore_pkgs = ['androidx', 'app_key', 'android.support', 'com.android', 'com.google', 'dalvik', 'org.apache', 'kotlinx', 'kotlin.', 'java', 'javax', 'org.jetbrains']
        if not os.path.exists(output_dir):
            print(f"Error: {output_dir} does not exist.")
            return None
        issues = []
        # Iterate over XML files in the output directory
        for root_dir, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith("_all.csv"):  # Ensure we're processing only csv files
                    file_path = os.path.join(root_dir, file)
                    print(file_path)
                    #issue_id = file.split("_")[-1].replace(".csv", "")
                    #print(f"Pro", issue_id)
                    with open(file_path, 'r') as f:
                        #next(f)
                        header = next(f)
                        rl_index = 5 if 'setupTime' in header else 4
                        for line in f:
                            if len(line.split(",")) < 5:
                                continue
                            issue_id = line.split(",")[rl_index]
                            #if line.strip() == "" or any(pkg in line for pkg in ignore_pkgs):
                               #print(f"Ignoring line: {line.strip()}")
                            #   continue
                            #if issue_id not in self.identifiable_issues:
                            #    continue
                            #if 'src' in file_path and ('test' in file_path or 'androidTest' in file_path or "InstrumentedTest" in file_path) and ignore_tests:
                            #    continue
                            #print(line)
                            if issue_id in self.identifiable_issues:
                                issue = Issue(self.identifiable_issues[issue_id],
                                    i_class=line.split(",")[rl_index-1],
                                    description=issue_id,
                                    detection_tool_name="EcoAndroid_RL")
                            #print(line.strip())
                                if issue in issues:
                                    continue
                                issues.append(issue)
        return issues
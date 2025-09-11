
import os

from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer
from anadroid.analysis.metrics.Issues import Issue, KnownStaticPerformanceIssues
from anadroid.application.Application import App
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, logi

# java -jar build/libs/EcoAndroidResourceLeak.jar "/Users/rar9993/Library/Android/sdk/platforms" "/Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/app/build/outputs/apk/debug/app-debug.apk" "standalone_out"

DEFAULT_OUTPUT_DIRNAME = "droidlens_analysis_output/"
DEFAULT_CLASSPATH = os.path.join(get_resources_dir(), 'jars','libs', "jFuzzyLogic.jar")
DEFAULT_PATH_JAR = os.path.join(get_resources_dir(), 'jars', "droidlens-1.0-jar-with-dependencies.jar")
DEFAULT_SDK_PATH = "~/Library/Android/sdk/platforms"

class DroidLensAnalysis(ExecutionResultsAnalyzer):
    def __init__(self, analyzers_cfg_file=None, jar_path=DEFAULT_PATH_JAR,
                 default_output_dir=DEFAULT_OUTPUT_DIRNAME, sdk_path=DEFAULT_SDK_PATH, cp_path=DEFAULT_CLASSPATH):
        super().__init__(analyzers_cfg_file)
        self.jar_path = jar_path
        self.sdk_path = sdk_path
        self.cp_path = cp_path
        self.default_output_dir = default_output_dir
        self.exec_cmd = f"source ~/.zshrc ; j8 ; java -cp {cp_path}:{jar_path} doridlens.Main"
        self.identifiable_issues = {
            #"ARGB8888": KnownStaticPerformanceIssues.BITMAP_FORMAT_USAGE,
            "BLOB": KnownStaticPerformanceIssues.BLOB_CLASS,
            "BLOB_NO_FUZZY": KnownStaticPerformanceIssues.BLOB_CLASS,
            "CC": KnownStaticPerformanceIssues.COMPLEX_CLASS,
            "CC_NO_FUZZY": KnownStaticPerformanceIssues.COMPLEX_CLASS,
            "HMU": KnownStaticPerformanceIssues.HASHMAP_USAGE,
            "HAS": KnownStaticPerformanceIssues.HEAVY_ASYNC_TASK,
            "HAS_NO_FUZZY": KnownStaticPerformanceIssues.HEAVY_ASYNC_TASK,
            "HBR": KnownStaticPerformanceIssues.HEAVY_BROADCAST_RECEIVER,
            "HBR_NO_FUZZY": KnownStaticPerformanceIssues.HEAVY_BROADCAST_RECEIVER,
            "HSS": KnownStaticPerformanceIssues.HEAVY_SERVICE_START,
            "HSS_NO_FUZZY": KnownStaticPerformanceIssues.HEAVY_SERVICE_START,
            "IGS": KnownStaticPerformanceIssues.INTERNAL_GETTER_SETTER,
            "IOD": KnownStaticPerformanceIssues.DRAW_ALLOCATION,
            "IWR": KnownStaticPerformanceIssues.INVALIDATE_WITHOUT_RECT,
            "LIC": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "LM": KnownStaticPerformanceIssues.LONG_METHOD,
            "MIM": KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD,
            "NLMR": KnownStaticPerformanceIssues.NO_LOW_MEMORY_RESOLVER,
            "UIO": KnownStaticPerformanceIssues.UI_OVERDRAW,
            "SAK": KnownStaticPerformanceIssues.SWISS_ARMY_KNIFE,
            #"THI": KnownStaticPerformanceIssues.
            "UCS": KnownStaticPerformanceIssues.UNSUITED_LRU_CACHE_SIZE,
            "UHA": KnownStaticPerformanceIssues.UNSUPPORTED_HARDWARE_ACCELERATION,
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
        package_only = kwargs.get('package_only', True)
        retry = kwargs.get("retry", False)
        res_folder = os.path.join(app.local_res, DEFAULT_OUTPUT_DIRNAME)
        res_folder_prefix = os.path.join(res_folder, app.package_name)
        if not os.path.exists(res_folder):
            print(f"Creating directory {res_folder}")
            os.makedirs(res_folder)
        if not retry and len(list(filter(lambda x: x.endswith(".csv"), os.listdir(res_folder)))) > 0:
            logi(f"Skipping analysis for {app.package_name}. Already processed by DroidLens")
            return
        analyse_cmd = (f"{self.exec_cmd} analyse -a {self.sdk_path} -db neo4j -p {app.package_name} -n {app.name}"
                       f" -u UNSAFE -omp {str(package_only).lower()} {app.apk}")
        print(analyse_cmd)
        res = execute_shell_command(analyse_cmd)
        res.validate()
        query_cmd = f"{self.exec_cmd} query -db neo4j -d true -r NONFUZZY -c {res_folder_prefix}"
        res = execute_shell_command(query_cmd)
        print(res)
        query_cmd = f"{self.exec_cmd} query -db neo4j -d true -r ALLAP -c {res_folder_prefix}"
        res = execute_shell_command(query_cmd)
        print(res)
        res.validate()
        print(query_cmd)

    def analyze_test(self, app, test_id, **kwargs):
        pass

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        pass

    def get_issues(self, output_dir, ignore_tests=True):
        ignore_pkgs = ['androidx', 'app_key', 'android.support', 'com.android', 'com.google', 'dalvik', 'org.apache', 'kotlinx', 'kotlin.', 'java', 'javax', 'org.jetbrains']
        if not os.path.exists(output_dir):
            print(f"Error: {output_dir} does not exist.")
            return None
        issues = []
        # Iterate over XML files in the output directory
        for root_dir, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".csv"):  # Ensure we're processing only csv files
                    file_path = os.path.join(root_dir, file)
                    issue_id = file.split("_")[-1].replace(".csv", "")
                    #print(f"Pro", issue_id)
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.strip() == "" or any(pkg in line for pkg in ignore_pkgs):
                               #print(f"Ignoring line: {line.strip()}")
                               continue
                            if issue_id not in self.identifiable_issues:
                                continue
                            #if 'src' in file_path and (
                            #        'test' in file_path or 'androidTest' in file_path or "InstrumentedTest" in file_path) and ignore_tests:
                            #    continue
                            issue = Issue(self.identifiable_issues[
                                issue_id] if issue_id in self.identifiable_issues else issue_id,
                                i_class=line.strip().split("$")[0],
                                detection_tool_name="DroidLens")
                            #print(line.strip())
                            if issue in issues:
                                continue
                            issues.append(issue)
        return issues
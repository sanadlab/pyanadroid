import os
import csv
from textops import lcount, cat

from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.JavaRetry import change_java_version_cmd
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, logs

# /Applications/IntelliJ\ IDEA\ CE.app/Contents/bin/inspect.sh  /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/ /Users/rar9993/repos/EcoAndroid/eco_ide/EcoAndroid/Project_Default.xml /Users/rar9993/repos/EcoAndroid/eco_ide/EcoAndroid/out  -d /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/app -v2

DEFAULT_OUTPUT_DIRNAME = "adoctor_output"
DEFAULT_OUTPUT_FILENAME = "adoctor.csv"
DEFAULT_PATH_JAR = os.path.join(get_resources_dir(), 'jars' ,"aDoctor-1.0-SNAPSHOT-jar-with-dependencies.jar")
DEFAULT_MAIN_CLASS = "it.unisa.aDoctor.process.RunAndroidSmellDetection"
DEFAULT_SEARCH_PATTERN = "111111111111111"

class ADoctorAnalysis(StaticAnalyzer):
    def __init__(self, analyzers_cfg_file=None, default_output_dir=DEFAULT_OUTPUT_DIRNAME,
                 jar_path=DEFAULT_PATH_JAR, main_class=DEFAULT_MAIN_CLASS):
        super().__init__(analyzers_cfg_file)
        self.default_output_dir = default_output_dir
        self.exec_cmd = f"java -cp {jar_path} {main_class} "
        self.identifiable_issues = {
            "SL": KnownStaticPerformanceIssues.SLOW_FOR_LOOP,
            "DW": KnownStaticPerformanceIssues.WAKE_LOCK,
            "IGS": KnownStaticPerformanceIssues.INTERNAL_GETTER_SETTER,
            "MIM": KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD,
            "NLMR": KnownStaticPerformanceIssues.NO_LOW_MEMORY_RESOLVER,
            "LIC": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "IDS": KnownStaticPerformanceIssues.HASHMAP_USAGE,
            "UC": KnownStaticPerformanceIssues.UNCLOSED_CLOSEABLE,
            "LT": KnownStaticPerformanceIssues.LEAKING_THREAD,
            "DTWC": KnownStaticPerformanceIssues.DATA_TRANSMISSION_WITHOUT_COMPRESSION,
            "RAM": KnownStaticPerformanceIssues.RIGID_ALARM_MANAGER,
            "ISQLQ": KnownStaticPerformanceIssues.INEFFICIENT_SQL_QUERY,
            "IDFP": KnownStaticPerformanceIssues.INEFFICIENT_DATA_FORMAT_AND_PARSER,
            "DR": KnownStaticPerformanceIssues.DEBUGGABLE_RELEASE,
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

    import csv

    def get_issues(self, results_output_file):
        """Parses the ADoctor results output file and returns a list of reported issues."""
        if not os.path.exists(results_output_file):
            loge(f"Results file not found: {results_output_file}")
            return []

        issues_list = []

        with open(results_output_file, "r") as file:
            reader = csv.reader(file)
            headers = next(reader)  # Read the first row as headers

            if headers[0] != "File":
                loge("Invalid file format: Missing expected 'Class' header")
                return []

            for row in reader:
                filepath = row[0]
                class_name = row[1]
                issues_detected = [
                    self.identifiable_issues[headers[i]]
                    for i in range(2, len(headers))
                    if headers[i] in self.identifiable_issues and int(row[i]) > 0
                ]
                for iss in issues_detected:
                    issues_list.append(Issue(iss, i_class=class_name, file=filepath, detection_tool_name="aDoctor"))
        return issues_list

    def analyze_project(self, project, **kwargs):
        retry = kwargs.get("retry", True)
        search_pattern_code = kwargs.get("search_pattern_code", DEFAULT_SEARCH_PATTERN)
        output_dir = kwargs.get("output_dir",  getattr(project, 'results_dir', self.default_output_dir))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_filepath = os.path.join(output_dir, DEFAULT_OUTPUT_FILENAME)
        if os.path.exists(output_filepath) and not retry and self.validate_success(None, output_filepath):
            logs(f"Skipping project {project.proj_name}. Already processed by ADoctor")
            return
        extra_cmd = change_java_version_cmd(8)
        cmd = f"{extra_cmd} {self.exec_cmd} {project.proj_dir} {output_filepath} {search_pattern_code}"
        print(cmd)
        res = execute_shell_command(cmd, timeout=200)
        self.validate_success(res, output_filepath)

    def validate_success(self, res, expected_output_file):
        if not os.path.exists(expected_output_file) and (res is None or res.return_code != 0):
            loge(f"Error executing Adoctor analysis. Check the logs for more information")
            print(res)
            return False
        logs(f"Adoctor analysis executed successfully")
        return True

import json
import os
import re

from textops import grepci, cat, lcount

from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, logs

# java -jar build/libs/DAAP-1.0.jar /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp ALL | grep 'Issue,'

DEFAULT_OUTPUT_DIRNAME = "daap_output"
DEFAULT_OUTPUT_FILENAME = "daap_analysis.json"
DEFAULT_PATH_JAR = os.path.join(get_resources_dir(), 'jars' ,"DAAP-1.0.jar")
DEFAULT_SEARCH_PATTERN = "ALL"

class DAAPAnalysis(StaticAnalyzer):
    def __init__(self, analyzers_cfg_file=None, default_output_dir=DEFAULT_OUTPUT_DIRNAME,
                 jar_path=DEFAULT_PATH_JAR):
        super().__init__(analyzers_cfg_file)
        self.default_output_dir = default_output_dir
        self.exec_cmd = f"java -jar {jar_path} "
        self.identifiable_issues = {
            "Slow For Loop": KnownStaticPerformanceIssues.SLOW_FOR_LOOP,
            "Durable Wake Lock": KnownStaticPerformanceIssues.WAKE_LOCK,
            "Internal Getter Setter": KnownStaticPerformanceIssues.INTERNAL_GETTER_SETTER,
            "Method Ignoring Method": KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD,
            "Low Memory": KnownStaticPerformanceIssues.NO_LOW_MEMORY_RESOLVER,
            "Leaking Inner Class": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "Inefficient Data Structure": KnownStaticPerformanceIssues.HASHMAP_USAGE,
            "Overdrawn Pixel": KnownStaticPerformanceIssues.UI_OVERDRAW,
            "Unclosed Closeable": KnownStaticPerformanceIssues.UNCLOSED_CLOSEABLE,
            "Leaking Thread": KnownStaticPerformanceIssues.LEAKING_THREAD,
            "Rigid Alarm Manager": KnownStaticPerformanceIssues.RIGID_ALARM_MANAGER,
            "Inefficient Data Format and Parser": KnownStaticPerformanceIssues.INEFFICIENT_DATA_FORMAT_AND_PARSER,
            "Debuggable Release": KnownStaticPerformanceIssues.DEBUGGABLE_RELEASE,
            "Nested Layout": KnownStaticPerformanceIssues.NESTED_WEIGHT,
            "Config Changes": KnownStaticPerformanceIssues.CONFIG_CHANGES,
            "Dropped Data": KnownStaticPerformanceIssues.DROPPED_DATA,
            "Collection of Bitmaps": KnownStaticPerformanceIssues.COLLECTION_OF_BITMAPS,
            "Collection of Views": KnownStaticPerformanceIssues.COLLECTION_OF_VIEWS,
            "Static Bitmap": KnownStaticPerformanceIssues.STATIC_BITMAP,
            "Static View": KnownStaticPerformanceIssues.STATIC_VIEW,
            "Static Context": KnownStaticPerformanceIssues.STATIC_CONTEXT,
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

    def analyze_project(self, project, **kwargs):
        retry = kwargs.get("retry", True)
        search_pattern_code = kwargs.get("search_pattern_code", DEFAULT_SEARCH_PATTERN)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', self.default_output_dir))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for module in project.modules:
            module_path = os.path.join(project.proj_dir, module)
            output_filepath = os.path.join(output_dir, f"{module}_{DEFAULT_OUTPUT_FILENAME}")
            if os.path.exists(output_filepath) and not retry and self.validate_success(None, output_filepath):
                logs(f"Skipping module {project.proj_name}.{module} . Already processed by DAAP")
                return
            #cmd = f"{self.exec_cmd} {module_path} {search_pattern_code} |  grep 'Issue,'  > {output_filepath}"
            cmd = f"{self.exec_cmd} {module_path} {search_pattern_code} "
            print(cmd)
            res = execute_shell_command(cmd, timeout=150)
            self.parse_write_output(res, output_filepath)
            self.validate_success(res, output_filepath)

    def validate_success(self, res, expected_output_file=None):
        if not os.path.exists(expected_output_file) and (res is None or res.return_code != 0):
            loge(f"Error executing DAAP analysis. Check the logs for more information")
            print(res)
            return False
        line_count =  expected_output_file | cat() | lcount()
        if line_count > 0:
            logs(f"DAAP analysis executed successfully")
        else:
            loge(f"Error executing DAAP analysis. Empty file")
            return False
        return True

    def parse_write_output(self, res, output_filepath):
        if res is not None and res.return_code == 0:
            find_dict = parse_detected_issues(res.output)
            #print([x for x in find_dict.keys() if len(find_dict[x]) > 0])
            with open(output_filepath, 'w') as f:
                json.dump(find_dict, f, indent=1)

    def get_issues(self, results_file):
        issues = []
        try:
            with open(results_file, "r") as file:
                issues_data = json.load(file)
            module_name = os.path.basename(results_file).replace(f"_{DEFAULT_OUTPUT_FILENAME}", "")
            for issue_type, files in issues_data.items():
                if files:  # Only store issues that have associated file paths
                    for file in files:
                        if issue_type in self.identifiable_issues:
                            issues.append(Issue(self.identifiable_issues[issue_type],
                                                file=os.path.join(module_name, file), detection_tool_name="DAAP"))
            logs(f"Found {len(issues)} issues in {results_file}")
            return issues

        except (FileNotFoundError, json.JSONDecodeError) as e:
            loge(f"Error reading issues file: {results_file} {e}")
            return issues

def parse_detected_issues(output):
    """
    Parses anti-pattern detection output into a dictionary of issues with associated file paths

    Args:
        output (str): Raw output from detection tool

    Returns:
        dict: {issue_name: [list_of_paths]}
    """
    pattern = r'Detecting: (.*?)\n(.*?)(?=\n\nDetecting: |\Z)'
    sections = re.findall(pattern, output, re.DOTALL)
    issue_map = {}
    for issue, content in sections:
        # Extract all file paths in section
        paths = re.findall(r'Path: (.*?)\n', content)
        # Remove duplicate paths while preserving order
        seen = set()
        unique_paths = [p for p in paths if not (p in seen or seen.add(p))]
        issue_map[issue.strip()] = unique_paths

    return issue_map







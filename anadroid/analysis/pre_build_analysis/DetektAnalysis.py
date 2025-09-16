import os
import re
import shutil
import xml.etree.ElementTree as ET
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, mega_find, logs, logw, logi, \
    find_source_root_dynamically


class DetektAnalysis(StaticAnalyzer):
    def __init__(self, analyzers_cfg_file=None, performance_only=True, default_output_format='xml', **kwargs):
        super().__init__(analyzers_cfg_file)
        self.name = 'Detekt'
        self.performance_only = performance_only
        self.default_output_format = default_output_format
        self.identifiable_issues = {
            "ArrayPrimitive": KnownStaticPerformanceIssues.ARRAY_PRIMITIVE,
            "CouldBeSequence": KnownStaticPerformanceIssues.COULD_BE_SEQUENCE,
            "ForEachOnRange": KnownStaticPerformanceIssues.FOR_EACH_ON_RANGE,
            "SpreadOperator": KnownStaticPerformanceIssues.SPREAD_OPERATOR,
            "UnnecessaryPartOfBinaryExpression": KnownStaticPerformanceIssues.UNNECESSARY_PART_OF_BINARY_EXPRESSION,
            "UnnecessaryTypeCasting": KnownStaticPerformanceIssues.UNNECESSARY_TYPE_CASTING,
        }

    def setup(self, **kwargs):
        exec_detekt = execute_shell_command("detekt --version")
        if exec_detekt.return_code != 0:
            raise EnvironmentError(
                f"Detekt not found in the host machine")

        logi("Detekt setup is valid.")

    def analyze_project(self, project, **kwargs):
        """
        Executes the Detekt analysis pipeline.
        Args:
            project: The project object to analyze.
        """

        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', project.proj_dir))

        source_path = find_source_root_dynamically(project.proj_dir)
        output_file_name = f"detekt_analysis.{self.default_output_format}"
        output_file_path = os.path.join(output_dir, output_file_name)
        retry = kwargs.get("retry", True)
        if os.path.exists(output_file_path) and not retry and self.validate_success(None, output_file_path):
            logs(f"Skipping app. Already processed by Detekt")
            return

        if source_path is None or not os.path.exists(source_path):
            loge(f"Source path not found for project at {project.proj_dir}. Cannot run Detekt.")
            return

        d_command = [
            "detekt",
            "--input", source_path,
            "-r", f"{self.default_output_format}:{output_file_path}"
        ]


        logi("Detekt: Running analysis. This may take a while...")
        cmd_str = " ".join(f'"{c}"' if " " in c else c for c in d_command)
        print(cmd_str)
        res_analyze = execute_shell_command(cmd_str)

        self.validate_success(res_analyze, output_file_path)

    def get_issues(self, results_file: str, ignore_tests: bool = True):
        """
        Parses a Detekt XML report (checkstyle format) and transforms findings
        into a list of Issue objects.
        """
        issues = []
        if not os.path.exists(results_file):
            loge(f"Detekt results file not found at {results_file}")
            return issues

        try:
            tree = ET.parse(results_file)
            root = tree.getroot()
        except ET.ParseError:
            loge(f"Error parsing Detekt XML report: {results_file}")
            return issues

        # Map Detekt's string severities to a common format (e.g., High, Medium, Low)
        severity_map = {
            'error': 'High',
            'warning': 'Medium',
            'info': 'Low',
            'ignore': 'Info'  # Or however you want to handle 'ignore'
        }

        # The Detekt XML structure is <file> -> <error>
        for file_element in root.findall("file"):
            filepath = file_element.get("name")

            # Centralized check for test files to skip all errors within them if needed
            if ignore_tests and filepath and ('/test/' in filepath or '/androidTest/' in filepath):
                continue

            for error_element in file_element.findall("error"):
                issue_id = error_element.get("source").split(".")[-1]

                # This performance_only filter is preserved from your original code
                if self.performance_only and issue_id not in self.identifiable_issues:
                    continue

                # Derive category from the issue ID (e.g., 'style' from 'detekt.style.MagicNumber')
                try:
                    category = issue_id.split('.')[1]
                except IndexError:
                    category = 'unknown'

                line = error_element.get("line")
                detekt_severity = error_element.get("severity", "ignore").lower()

                issue_inst = Issue(
                    issue_type=self.identifiable_issues.get(issue_id, issue_id),
                    category=category,
                    severity=severity_map.get(detekt_severity, "Medium"),  # Default to Medium if unknown
                    description=error_element.get("message"),
                    file=filepath,
                    line=int(line) if line and line.isdigit() else None,
                    detection_tool_name=self.name
                )

                if issue_inst not in issues:
                    issues.append(issue_inst)
        print(issues)
        return issues

    def validate_success(self, res, expected_output_file):
        """Checks if the analysis was successful based on the presence of the results file."""
        if not os.path.exists(expected_output_file) and (res is None or res.return_code != 0):
            loge(f"Error executing Detekt analysis. Check the logs for more information")
            print(res)
            return False
        if not os.path.exists(expected_output_file):
            loge(f"Error executing Detekt analysis. Output file not found.")
            logw(res.output)
            logw(res.errors)
            return False
        if res:
            logs(f"Detekt analysis executed successfully. Results at {expected_output_file}")
        return True

    # --- Stub implementations for the rest of the interface ---
    def validate_test(self, app, arg1, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    def clean(self):
        pass

    def get_val_for_filter(self, filter_name, add_data=None):
        pass

    def setup_project(self, project, **kwargs):
        pass

    def pick_task(self, proj, default_task='lintDebug', **kwargs):
        pass

    def validate_filters(self):
        """Validates if the filters are set correctly."""
        return True
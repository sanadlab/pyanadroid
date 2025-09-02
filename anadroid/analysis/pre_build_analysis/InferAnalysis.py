import os
import shutil
import json  # Used for parsing Infer's output
from shutil import copy
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import Issue
from anadroid.utils.Utils import execute_shell_command, loge, logs, logw, logi

# Default build task for Infer to capture. 'assemble' is a good choice.
DEFAULT_GRADLE_TASK = 'assembleDebug'


class InferAnalyzer(StaticAnalyzer):
    """
    Implements the StaticAnalyzer interface to run Facebook's Infer.
    Infer works in two main phases:
    1. Capture: It hooks into a build command (like './gradlew assembleDebug') to create a model of the project.
    2. Analyze: It runs its analysis algorithms on the captured model.
    """

    def __init__(self, analyzers_cfg_file=None, performance_only=True, uses_gradlew=True,
                 default_task=DEFAULT_GRADLE_TASK, **kwargs):
        super().__init__(analyzers_cfg_file)
        self.name = 'Infer'
        self.exec_cmd = 'infer'  # Relies on 'infer' being in the system's PATH
        self.use_gradlew = uses_gradlew  # Infer wraps the gradlew command
        self.default_task = default_task
        self.performance_only = performance_only
        self.flags = ["--loop-hoisting", "--inefficient-keyset-iterator", "--starvation" "--cost"]
        self.identifiable_issues = {

        }
        # Mapping of Infer bug types to your framework's known issues.
        # This list can be expanded based on Infer's documentation.
        # See: https://fbinfer.com/docs/all-issue-types


    def setup(self, **kwargs):
        """
        Validates that the 'infer' command is available on the system.
        """
        if not shutil.which(self.exec_cmd):
            raise EnvironmentError(
                f"'{self.exec_cmd}' command not found. Please install Facebook Infer and ensure it is in your PATH.")
        logi("Infer installation found.")

    def analyze_project(self, project, **kwargs):
        """
        Executes the full infer analysis pipeline: clean, capture, and analyze.
        Args:
            project: The project object to analyze.
        """
        build_task = kwargs.get("exec_task", self.default_task)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', project.proj_dir))
        infer_out_dir_name = "infer-out"
        infer_out_path = os.path.join(project.proj_dir, infer_out_dir_name)
        gradlew_path = os.path.join(project.proj_dir, 'gradlew')

        # 1. Clean up previous results
        if os.path.exists(infer_out_path):
            logi(f"Removing existing Infer output directory: {infer_out_path}")
            shutil.rmtree(infer_out_path)

        logi(f"Analyzing project '{project.proj_name}' with Infer")

        # 2. Run './gradlew clean' (highly recommended for a clean capture)
        clean_cmd = f"cd {project.proj_dir}; chmod +x gradlew; {gradlew_path} clean"
        logi("Infer Step 1/3: Cleaning project")
        res_clean = execute_shell_command(clean_cmd)
        if not res_clean.validate():
            loge("Gradle clean failed. Aborting Infer analysis.")
            logw(res_clean.errors)
            return

        # 3. Run 'infer capture'
        # Infer wraps the build command to capture compilation data.
        capture_cmd = (f"cd {project.proj_dir}; "
                       f"{self.exec_cmd} capture --out {infer_out_dir_name}  --keep-going -- "
                       f"{gradlew_path} {build_task} " + " ".join(self.flags))
        logi("Infer Step 2/3: Capturing build. This may take a while...")
        res_capture = execute_shell_command(capture_cmd, timeout=600)  # Increased timeout for build
        print(res_capture)
        if not res_capture.validate():
            loge("Infer capture phase failed.")
            logw(res_capture.errors)
            return

        # 4. Run 'infer analyze'
        analyze_cmd = f"cd {project.proj_dir}; {self.exec_cmd} analyze --out {infer_out_dir_name}"
        logi("Infer Step 3/3: Analyzing captured data.")
        res_analyze = execute_shell_command(analyze_cmd, timeout=300)
        if not res_analyze.validate():
            loge("Infer analyze phase failed.")
            logw(res_analyze.errors)
            return
        print(res_analyze)
        # 5. Copy results to the designated output directory
        json_report_path = os.path.join(infer_out_path, "report.json")
        txt_report_path = os.path.join(infer_out_path, "report.txt")

        if os.path.exists(json_report_path):
            final_json_path = os.path.join(output_dir, "infer_report.json")
            final_txt_path = os.path.join(output_dir, "infer_report.txt")
            logi(f"Copying results to {output_dir}")
            copy(json_report_path, final_json_path)
            if os.path.exists(txt_report_path):
                copy(txt_report_path, final_txt_path)
            self.validate_success(res_analyze, final_json_path)
        else:
            loge("Infer analysis finished, but no report.json was found.")

    def get_issues(self, results_file, ignore_tests=True):
        """
        Parses an infer 'report.json' file and transforms the findings into a list of Issue objects.
        Args:
            results_file (str): Path to the 'report.json' file.
            ignore_tests (bool): If True, issues found in test files will be ignored.

        Returns:
            list: A list of Issue objects.
        """
        issues = []
        if not os.path.exists(results_file):
            loge(f"Infer results file not found at {results_file}")
            return issues

        with open(results_file, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                loge(f"Error decoding JSON from {results_file}")
                return issues

        for bug in data:
            issue_id = bug.get("bug_type")

            # Apply performance-only filter if enabled
            if self.performance_only and issue_id not in self.identifiable_issues:
                continue

            filepath = bug.get("file")
            # Apply test file filter
            if ignore_tests and filepath and ('/test/' in filepath or '/androidTest/' in filepath):
                continue

            issue_inst = Issue(
                issue_type=self.identifiable_issues.get(issue_id, issue_id),
                category=bug.get("bug_type_hum"),
                severity=bug.get("severity"),
                description=bug.get("qualifier"),
                file=filepath,
                line=bug.get("line"),
                detection_tool_name=self.name
            )

            if issue_inst not in issues:
                issues.append(issue_inst)

        return issues

    def validate_success(self, res, expected_output_file):
        """Checks if the analysis was successful based on the presence of the results file."""
        if not os.path.exists(expected_output_file):
            loge(f"Error executing Infer analysis. Output file not found.")
            return False
        logs(f"Infer analysis executed successfully. Results at {expected_output_file}")
        return True

    # The following methods are part of the interface but are not essential
    # for the core functionality of running Infer. They can be implemented
    # as needed or left as stubs.
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

    def setup_project(self, project, **kwargs):
        pass

    def pick_task(self, proj, default_task='lintDebug', **kwargs):
        pass

    def generate_local_properties(self, project_dir):
        # This is a generic helper, not specific to Infer, but useful.
        cmd = f"echo \"sdk.dir=$ANDROID_HOME\" > {os.path.join(project_dir, 'local.properties')}"
        execute_shell_command(cmd)
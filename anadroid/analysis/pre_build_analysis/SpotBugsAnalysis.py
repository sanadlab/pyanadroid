import os
import re
import xml.etree.ElementTree as ET
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, mega_find, logs, logw, logi

# Default build task required by SpotBugs to get .class files.
DEFAULT_GRADLE_TASK = 'assembleDebug'

class SpotBugsAnalyzer(StaticAnalyzer):
    """
    Implements the StaticAnalyzer interface to run SpotBugs.
    SpotBugs analyzes compiled Java bytecode (.class files). This process involves:
    1. Building the project to generate the bytecode.
    2. Running the SpotBugs command-line tool against the compiled classes.
    3. Parsing the XML output to identify issues.
    """

    def __init__(self, analyzers_cfg_file=None, performance_only=True, uses_gradlew=True,
                 default_task=DEFAULT_GRADLE_TASK, **kwargs):
        super().__init__(analyzers_cfg_file)
        self.name = 'SpotBugs'
        self.spotbugs_home = os.environ.get("SPOTBUGS_HOME", '$HOME/spotbugs/spotbugs-4.9.3')
        self.android_sdk_root = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        self.use_gradlew = uses_gradlew
        self.default_task = default_task
        self.performance_only = performance_only
        self.plugin_path = kwargs.get("spotbugs_plugin_path", None)

        # Mapping of SpotBugs bug codes to your framework's known issues.
        # See: https://spotbugs.readthedocs.io/en/latest/bugDetections.html


    def setup(self, **kwargs):
        """Validates that SpotBugs and Android SDK environment variables are set."""
        if not self.spotbugs_home:
            raise EnvironmentError(
                "SPOTBUGS_HOME environment variable not set. Please point it to your SpotBugs installation.")
        if not self.android_sdk_root:
            raise EnvironmentError(
                "ANDROID_HOME or ANDROID_SDK_ROOT environment variable not set. Please point it to your Android SDK.")

        executable = self._get_spotbugs_executable()
        if not os.path.exists(executable):
            raise FileNotFoundError(
                f"SpotBugs executable not found at '{executable}'. Check your SPOTBUGS_HOME installation.")

        logi("SpotBugs setup is valid.")

    def _get_spotbugs_executable(self):
        """Returns the path to the SpotBugs executable, accounting for OS differences."""
        executable = os.path.join(self.spotbugs_home, "bin", "spotbugs")
        if os.name == 'nt':
            executable += ".bat"
        return executable

    def _find_compile_sdk_version(self, project_dir):
        """Parses build.gradle to find the compileSdkVersion."""
        build_gradle_path = os.path.join(project_dir, "app", "build.gradle")
        if not os.path.exists(build_gradle_path):
            build_gradle_path = os.path.join(project_dir, "app", "build.gradle.kts")

        if os.path.exists(build_gradle_path):
            try:
                with open(build_gradle_path, 'r') as f:
                    content = f.read()
                    match = re.search(r'compileSdk(?:Version)?\s*=?\s*(\d+)', content)
                    if match:
                        return match.group(1)
            except Exception as e:
                logw(f"Could not read compile SDK version: {e}")
        return "33"  # Return a reasonable default

    def analyze_project(self, project, **kwargs):
        """
        Executes the SpotBugs analysis pipeline.
        Args:
            project: The project object to analyze.
        """
        build_task = kwargs.get("exec_task", self.default_task)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', project.proj_dir))
        gradlew_path = os.path.join(project.proj_dir, 'gradlew')

        # 1. Build the project to ensure .class files are available
        logi("SpotBugs Step 1/2: Building project to generate bytecode")
        build_cmd = f"cd {project.proj_dir}; chmod +x gradlew; {gradlew_path} {build_task}"
        res_build = execute_shell_command(build_cmd, timeout=300)
        if not res_build.validate():
            loge(f"Gradle build failed for project {project.proj_name}. SpotBugs cannot run.")
            logw(res_build.errors)
            return

        # 2. Find necessary paths for SpotBugs analysis
        sdk_version = self._find_compile_sdk_version(project.proj_dir)
        android_jar_path = os.path.join(self.android_sdk_root, "platforms", f"android-{sdk_version}", "android.jar")
        classes_path = os.path.join(project.proj_dir, "app", "build", "intermediates", "javac",
                                    build_task.replace("assemble", ""), "classes")
        source_path = os.path.join(project.proj_dir, "app", "src", "main", "java")

        if not os.path.exists(classes_path):
            loge(f"Compiled classes directory not found at {classes_path}. Aborting SpotBugs.")
            return
        if not os.path.exists(android_jar_path):
            loge(f"Android SDK JAR not found at {android_jar_path}. Make sure SDK {sdk_version} is installed.")
            return

        # 3. Construct and run the SpotBugs command
        output_file_name = "spotbugs_report.xml"
        output_file_path = os.path.join(output_dir, output_file_name)

        spotbugs_command = [
            self._get_spotbugs_executable(),
            "-textui",
            "-xml:withMessages",  # XML output with detailed messages
            "-output", output_file_path,
            "-effort:max",
            "-auxclasspath", android_jar_path,
            "-sourcepath", source_path,
            classes_path  # The directory to analyze
        ]

        if self.plugin_path and os.path.exists(self.plugin_path):
            logi(f"Using SpotBugs plugin: {self.plugin_path}")
            spotbugs_command.extend(["-pluginList", self.plugin_path])

        logi("SpotBugs Step 2/2: Running analysis. This may take a few minutes...")
        cmd_str = " ".join(f'"{c}"' if " " in c else c for c in spotbugs_command)
        res_analyze = execute_shell_command(cmd_str)

        self.validate_success(res_analyze, output_file_path)

    def get_issues(self, results_file, ignore_tests=True):
        """
        Parses a SpotBugs XML report and transforms findings into a list of Issue objects.
        """
        issues = []
        if not os.path.exists(results_file):
            loge(f"SpotBugs results file not found at {results_file}")
            return issues

        try:
            tree = ET.parse(results_file)
            root = tree.getroot()
        except ET.ParseError:
            loge(f"Error parsing SpotBugs XML report: {results_file}")
            return issues

        for bug_instance in root.findall("BugInstance"):
            issue_id = bug_instance.get("type")

            if self.performance_only and issue_id not in self.identifiable_issues:
                continue

            # Find the primary source line to check for test files
            source_line_info = bug_instance.find("SourceLine")
            if source_line_info is not None:
                filepath = source_line_info.get("sourcepath")
                line = source_line_info.get("start")  # SpotBugs uses 'start' for line number
                if ignore_tests and filepath and ('/test/' in filepath or '/androidTest/' in filepath):
                    continue

                issue_inst = Issue(
                    issue_type=self.identifiable_issues.get(issue_id, issue_id),
                    category=bug_instance.get("category"),
                    severity=bug_instance.get("priority"),  # SpotBugs uses priority (1=High, 2=Medium, 3=Low)
                    description=bug_instance.find("LongMessage").text,
                    file=filepath,
                    line=int(line) if line else None,
                    detection_tool_name=self.name
                )

                if issue_inst not in issues:
                    issues.append(issue_inst)

        return issues

    def validate_success(self, res, expected_output_file):
        """Checks if the analysis was successful based on the presence of the results file."""
        if not os.path.exists(expected_output_file):
            loge(f"Error executing SpotBugs analysis. Output file not found.")
            logw(res.output)
            logw(res.errors)
            return False
        logs(f"SpotBugs analysis executed successfully. Results at {expected_output_file}")
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
        # This is a stub. SpotBugs does not have specific filters like some other tools.
        return True
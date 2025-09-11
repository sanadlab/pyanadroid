import os
import re
import xml.etree.ElementTree as ET
from os.path import expanduser

from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, mega_find, logs, logw, logi, \
    DockerCommandWrapper, find_source_root_dynamically

# Default build task required by SpotBugs to get .class files.
DEFAULT_GRADLE_TASK = 'compileDebugSources'

class SpotBugsAnalysis(StaticAnalyzer):
    """
    Implements the StaticAnalyzer interface to run SpotBugs.
    SpotBugs analyzes compiled Java bytecode (.class files). This process involves:
    1. Building the project to generate the bytecode.
    2. Running the SpotBugs command-line tool against the compiled classes.
    3. Parsing the XML output to identify issues.
    """

    def __init__(self, analyzers_cfg_file=None, performance_only=True, uses_gradlew=True,
                 default_task=DEFAULT_GRADLE_TASK, **kwargs):
        super().__init__(analyzers_cfg_file, **kwargs)
        self.name = 'SpotBugs'
        self.spotbugs_home = os.environ.get("SPOTBUGS_HOME", '$HOME/spotbugs/spotbugs-4.9.3')
        self.android_sdk_root = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        self.use_gradlew = uses_gradlew
        self.default_task = default_task
        self.performance_only = performance_only
        self.plugin_path = kwargs.get("spotbugs_plugin_path", None)
        self.identifiable_issues = {
            "HSC_HUGE_SHARED_STRING_CONSTANT": KnownStaticPerformanceIssues.HUGE_SHARED_STRING_CONSTANT,
            "DMI_BLOCKING_METHODS_ON_URL": KnownStaticPerformanceIssues.BLOCKING_METHODS_ON_URL,
            "DMI_COLLECTION_OF_URLS": KnownStaticPerformanceIssues.BLOCKING_METHODS_ON_URL,
            "DM_STRING_CTOR": KnownStaticPerformanceIssues.STRING_INSTANTIATION,
            "DM_STRING_VOID_CTOR": KnownStaticPerformanceIssues.STRING_INSTANTIATION,
            "DM_STRING_TOSTRING": KnownStaticPerformanceIssues.STRING_TO_STRING,
            "DM_GC": KnownStaticPerformanceIssues.EXPLICIT_GC,
            "DM_BOOLEAN_CTOR": KnownStaticPerformanceIssues.USE_VALUE_OF,
            "DM_NUMBER_CTOR": KnownStaticPerformanceIssues.USE_VALUE_OF,
            "DM_FP_NUMBER_CTOR": KnownStaticPerformanceIssues.USE_VALUE_OF,
            "DM_BOXED_PRIMITIVE_TOSTRING": KnownStaticPerformanceIssues.BOXED_PRIMITIVE_TO_STRING,
            "DM_BOXED_PRIMITIVE_FOR_PARSING": KnownStaticPerformanceIssues.BOXED_PRIMITIVE_FOR_PARSING,
            "DM_BOXED_PRIMITIVE_FOR_COMPARE": KnownStaticPerformanceIssues.BOXED_PRIMITIVE_FOR_COMPARE,
            "BX_UNBOXED_AND_COERCED_FOR_TERNARY_OPERATOR": KnownStaticPerformanceIssues.UNBOXED_AND_COERCED_FOR_TERNARY_OPERATOR,
            "BX_UNBOXING_IMMEDIATELY_REBOXED": KnownStaticPerformanceIssues.UNBOXING_IMMEDIATELY_REBOXED,
            "BX_BOXING_IMMEDIATELY_UNBOXED": KnownStaticPerformanceIssues.BOXING_IMMEDIATELY_UNBOXED,
            "BX_BOXING_IMMEDIATELY_UNBOXED_TO_PERFORM_COERCION": KnownStaticPerformanceIssues.BOXING_IMMEDIATELY_UNBOXED_TO_PERFORM_COERCION,
            "DM_NEW_FOR_GETCLASS": KnownStaticPerformanceIssues.NEW_FOR_GETCLASS,
            "DM_NEXTINT_VIA_NEXTDOUBLE": KnownStaticPerformanceIssues.NEXTINT_VIA_NEXTDOUBLE,
            "SS_SHOULD_BE_STATIC": KnownStaticPerformanceIssues.FIELD_SHOULD_BE_STATIC,
            "UUF_UNUSED_FIELD": KnownStaticPerformanceIssues.UNUSED_FIELD,
            "URF_UNREAD_FIELD": KnownStaticPerformanceIssues.UNREAD_FIELD,
            "SIC_INNER_SHOULD_BE_STATIC": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "SIC_INNER_SHOULD_BE_STATIC_NEEDS_THIS": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "SIC_INNER_SHOULD_BE_STATIC_ANONYMOUS": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "UPM_UNCALLED_PRIVATE_METHOD": KnownStaticPerformanceIssues.UNCALLED_PRIVATE_METHOD,
            "SBSC_USE_STRINGBUFFER_CONCATENATION": KnownStaticPerformanceIssues.STRINGBUFFER_CONCATENATION,
            "IIL_ELEMENTS_GET_LENGTH_IN_LOOP": KnownStaticPerformanceIssues.HEAVY_LENGTH_IN_LOOP,
            "IIL_PREPARE_STATEMENT_IN_LOOP": KnownStaticPerformanceIssues.PREPARE_STATEMENT_IN_LOOP,
            "IIL_PATTERN_COMPILE_IN_LOOP": KnownStaticPerformanceIssues.PATTERN_COMPILE_IN_LOOP,
            "IIL_PATTERN_COMPILE_IN_LOOP_INDIRECT": KnownStaticPerformanceIssues.PATTERN_COMPILE_IN_LOOP,
            "IIO_INEFFICIENT_INDEX_OF": KnownStaticPerformanceIssues.USE_INDEX_OF_CHAR,
            "IIO_INEFFICIENT_LAST_INDEX_OF": KnownStaticPerformanceIssues.USE_INDEX_OF_CHAR_LAST,
            "ITA_INEFFICIENT_TO_ARRAY": KnownStaticPerformanceIssues.INEFFICIENT_TO_ARRAY,
            "WMI_WRONG_MAP_ITERATOR": KnownStaticPerformanceIssues.INEFFICIENT_MAP_ITERATOR,
            "UM_UNNECESSARY_MATH": KnownStaticPerformanceIssues.UNNECESSARY_MATH,
            "IMA_INEFFICIENT_MEMBER_ACCESS": KnownStaticPerformanceIssues.INEFFICIENT_MEMBER_ACCESS,
        }

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
        return "35"  # Return a reasonable default

    def analyze_project(self, project, **kwargs):
        """
        Executes the SpotBugs analysis pipeline.
        Args:
            project: The project object to analyze.
        """
        build_task = kwargs.get("exec_task", self.default_task)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', project.proj_dir))
        gradlew_path = os.path.join(project.proj_dir, 'gradlew')
        replace_paths = [
            "~" + os.sep + os.path.relpath(project.proj_dir, expanduser("~")) + os.sep,
            os.path.relpath(project.proj_dir, expanduser("~")) + os.sep,
            os.path.relpath(output_dir, os.path.curdir) + os.sep,
            os.path.abspath(os.path.dirname(project.proj_dir)) + os.sep,
            os.path.basename(os.path.dirname(project.proj_dir)) + os.sep,

            "~" + os.sep + os.path.relpath(output_dir, expanduser("~")) + os.sep,
            os.path.relpath(output_dir, expanduser("~")) + os.sep,
            os.path.relpath(output_dir, os.path.curdir) + os.sep,
            os.path.abspath(output_dir) + os.sep,
            os.path.basename(output_dir) + os.sep,

        ]

        if self.should_run_in_container:
            DockerCommandWrapper(self.container_id, paths_to_truncate=replace_paths).push(project.proj_dir)

        # 1. Build the project to ensure .class files are available
        logi("SpotBugs Step 1/2: Building project to generate bytecode")
        build_cmd = f"cd {project.proj_dir}; chmod +x gradlew; ./gradlew {build_task}"
        res_build = execute_shell_command(build_cmd, timeout=300, in_container=self.should_run_in_container,
                                              container_id=self.container_id,
                                              replace_paths=replace_paths)
        if not res_build.validate():
            loge(f"Gradle build failed for project {project.proj_name}. SpotBugs cannot run.")
            logw(res_build.errors)
            return

        # 2. Find necessary paths for SpotBugs analysis
        sdk_version = self._find_compile_sdk_version(project.proj_dir)
        android_jar_path = os.path.join(self.android_sdk_root, "platforms", f"android-{sdk_version}", "android.jar")

        possible_class_paths = mega_find(os.path.join(project.proj_dir, "app", "build", "intermediates", "javac"),
                                        pattern="classes", type_file='d', maxdepth=3)
        classes_path = os.path.join(project.proj_dir, "app", "build", "intermediates", "javac",
                                    build_task.replace("assemble", ""), "classes") \
            if len(possible_class_paths) == 0 else possible_class_paths[0]
        source_path = find_source_root_dynamically(project.proj_dir)

        if not os.path.exists(classes_path) and not self.should_run_in_container:
            loge(f"Compiled classes directory not found at {classes_path}. Aborting SpotBugs.")
            return
        if not os.path.exists(android_jar_path):
            loge(f"Android SDK JAR not found at {android_jar_path}. Make sure SDK {sdk_version} is installed.")
            return

        # 3. Construct and run the SpotBugs command
        output_file_name = f"{project.proj_name}_spotbugs_report.xml"
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
        res_analyze = execute_shell_command(cmd_str, in_container=self.should_run_in_container,
                                              container_id=self.container_id,
                                              replace_paths=replace_paths)

        if self.should_run_in_container:
            DockerCommandWrapper(self.container_id, paths_to_truncate=replace_paths).pull(output_file_path)

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
            print(issue_id)
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
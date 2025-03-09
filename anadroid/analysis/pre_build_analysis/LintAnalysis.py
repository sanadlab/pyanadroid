import datetime
import os
import re
import time
from shutil import copy
import xml.etree.ElementTree as ET
from textops import grep

from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.build.GradleBuilder import GradleBuilder
from anadroid.utils.JavaRetry import JavaRetry
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, mega_find, logs, logw, logi

LINT_PERFORMANCE_XML_FILE = os.path.join(get_resources_dir(), 'lint.xml')
LINT_OPTIONS = [
    #"--offline",
    "--no-daemon",
    "--continue",
    "-Pandroid.lint.abortOnError=false",
    "-Pandroid.lint.ignoreTestSources=true",
    "-Pandroid.lint.checkDependencies=true",
    "-Dorg.gradle.jvmargs=-Xmx8g",
]

DEFAULT_GRADLE_TASK = 'lintDebug'

LINT_FAILED_FILE = 'lint_failed.txt'

class LintAnalysis(StaticAnalyzer):
    def __init__(self, analyzers_cfg_file=None, performance_only=True, uses_gradlew=True,
                 default_task=DEFAULT_GRADLE_TASK, **kwargs):
        super().__init__(analyzers_cfg_file)
        self.name = 'Lint'
        self.exec_cmd = ''
        self.performance_only = performance_only
        self.use_gradlew = uses_gradlew
        self.default_task = default_task
        self.identifiable_issues = {
            "AnimatorKeep" : KnownStaticPerformanceIssues.ANIMATOR_KEEP,
            "AnnotationProcessorOnCompilePath": KnownStaticPerformanceIssues.ANNOTATION_PROCESSOR_ON_COMPILE_PATH,
            "DevModeObsolete": KnownStaticPerformanceIssues.DEV_MODE_OBSOLETE,
            "DisableBaselineAlignment": KnownStaticPerformanceIssues.DISABLE_BASELINE_ALIGNMENT,
            "DrawAllocation": KnownStaticPerformanceIssues.DRAW_ALLOCATION,
            "DuplicateDivider": KnownStaticPerformanceIssues.DUPLICATE_DIVIDER,
            "AssertionSideEffect": KnownStaticPerformanceIssues.ASSERTION_SIDE_EFFECT,
            "DuplicateStrings": KnownStaticPerformanceIssues.DUPLICATE_STRINGS,
            "ExpensiveAssertion": KnownStaticPerformanceIssues.EXPENSIVE_ASSERTION,
            "LaunchActivityFromNotification": KnownStaticPerformanceIssues.LAUNCH_ACTIVITY_FROM_NOTIFICATION,
            "HandlerLeak": KnownStaticPerformanceIssues.LEAKING_HANDLER,
            "InefficientWeight": KnownStaticPerformanceIssues.INEFFICIENT_WEIGHT,
            "LifecycleAnnotationProcessorWithJava8": KnownStaticPerformanceIssues.LIFECYCLE_ANNOTATION_PROCESSOR_WITH_JAVA8,
            "LogConditional": KnownStaticPerformanceIssues.LOG_CONDITIONAL,
            "MergeRootFrame": KnownStaticPerformanceIssues.MERGE_ROOT_FRAME,
            "NestedWeights": KnownStaticPerformanceIssues.INEFFICIENT_WEIGHT,
            "NotificationTrampoline": KnownStaticPerformanceIssues.NOTIFICATION_TRAMPOLINE,
            "NotifyDataSetChanged": KnownStaticPerformanceIssues.NOTIFY_DATA_SET_CHANGED,
            "ObsoleteLayoutParam": KnownStaticPerformanceIssues.OBSOLETE_LAYOUT_PARAM,
            "ObsoleteSdkInt": KnownStaticPerformanceIssues.OBSOLETE_SDK_INT,
            "Overdraw": KnownStaticPerformanceIssues.UI_OVERDRAW,
            "Recycle": KnownStaticPerformanceIssues.RECYCLE,
            "RedundantNamespace": KnownStaticPerformanceIssues.REDUNDANT_NAMESPACE,
            "StaticFieldLeak": KnownStaticPerformanceIssues.STATIC_FIELD_LEAK,
            "StringFormatTrivial": KnownStaticPerformanceIssues.STRING_FORMAT_TRIVIAL,
            "SyntheticAccessor": KnownStaticPerformanceIssues.LEAKING_INNER_CLASS,
            "TooDeepLayout": KnownStaticPerformanceIssues.TOO_DEEP_LAYOUT,
            "TooManyViews": KnownStaticPerformanceIssues.TOO_MANY_VIEWS,
            "UnusedIds": KnownStaticPerformanceIssues.UNUSED_IDS,
            "UnusedNamespace": KnownStaticPerformanceIssues.UNUSED_NAMESPACE,
            "UnusedResources": KnownStaticPerformanceIssues.UNUSED_RESOURCES,
            "UsableSpace": KnownStaticPerformanceIssues.USABLE_SPACE,
            "UseCompoundDrawables": KnownStaticPerformanceIssues.USE_COMPOUND_DRAWABLES,
            "UseOfBundledGooglePlayServices": KnownStaticPerformanceIssues.USE_OF_BUNDLED_GOOGLE_PLAY_SERVICES,
            "UseSparseArrays": KnownStaticPerformanceIssues.HASHMAP_USAGE,
            "UseValueOf": KnownStaticPerformanceIssues.USE_VALUE_OF,
            "UselessLeaf": KnownStaticPerformanceIssues.USELESS_LEAF,
            "UselessParent": KnownStaticPerformanceIssues.USELESS_PARENT,
            "VectorPath": KnownStaticPerformanceIssues.VECTOR_PATH,
            "ViewHolder": KnownStaticPerformanceIssues.VIEW_HOLDER,
            "Wakelock": KnownStaticPerformanceIssues.WAKE_LOCK,
            "WakelockTimeout": KnownStaticPerformanceIssues.WAKELOCK_TIMEOUT,
            "WearableBindListener": KnownStaticPerformanceIssues.WEARABLE_BIND_LISTENER,
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

    def setup_project(self, project, **kwargs):
        pb = GradleBuilder(project, device=None, resources_dir=get_resources_dir(), instrumenter=None)
        res = pb.exec_with_gradlew(target_task='tasks', skip_lint=True)
        print(res)
        exit(0)

    def pick_task(self, proj, default_task='lintDebug', **kwargs):
        cmd = f"cd {proj.proj_dir}; chmod +x gradlew; ./gradlew tasks"
        res = execute_shell_command(cmd)
        print(res)
        lint_tasks = grep(res.output, 'lint')
        print(lint_tasks)
        # TODO

    def analyze_project(self, project, **kwargs):
        exec_task = kwargs.get("default_task", 'lintDebug')
        self.generate_local_properties(project.proj_dir)
        if self.performance_only:
            copy(LINT_PERFORMANCE_XML_FILE, project.proj_dir)
        retry = kwargs.get("retry", True)
        gradlew_path = os.path.join(project.proj_dir, 'gradlew')
        cmd = f"cd {project.proj_dir}; chmod +x gradlew; {gradlew_path} {exec_task} " + " ".join(LINT_OPTIONS)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', project.proj_dir))
        lt_files = mega_find(project.proj_dir, pattern="lint*result*.xml", maxdepth=5, type_file='f')
        print(lt_files)
        if len(lt_files) > 0 and not retry:
            logs(f"Skipping project {project.proj_name}. Already processed by Lint")
            return
        lint_failed_file = os.path.join(project.proj_dir, LINT_FAILED_FILE)
        if not retry and os.path.exists(lint_failed_file):
            logs(f"Skipping project {project.proj_name}. Lint failed in previous executions")
            return
        logi("Analyzing project" + project.proj_name)
        res = execute_shell_command(cmd,timeout=150)
        if exec_task == self.default_task and res.return_code != 0:
            logw(f"Error executing {exec_task} analysis. Trying with default task")
            self.analyze_project(project, retry=False, default_task='lint')
        java_retryer = JavaRetry()
        if res.return_code != 0:
            java_version = re.search("requires Java ([0-9]+) to run", str(res.errors))
            if java_version:
                java_version = int(java_version.group(1))
                target_java = 8
                if java_version > target_java:
                    target_java = 17
                loge(f"Java version {java_version} is not supported by lint. using Java {target_java}")
                execute_shell_command(f"source ~/.zshrc ; j{target_java}")
                res = execute_shell_command(cmd, timeout=300)
            else:
                retry, extra_cmd = java_retryer.change_java_retry((res.output + res.errors).lower())
                while retry:
                    print(extra_cmd + cmd)
                    res = execute_shell_command(extra_cmd + cmd, timeout=300)
                    retry, extra_cmd = java_retryer.change_java_retry((res.output + res.errors).lower())

        res_file = grep(res.output, ' report to (.*).xml')
        if res_file:
            res_file = res_file[0]
            res_file = res_file.split(' ')[-1].strip()
            res_file = res_file.replace('file://', '')
            res_file = res_file.replace('file:', '').replace(' ', '').replace('\n', '')
            copy(res_file,  output_dir)
            self.validate_success(res, os.path.join(output_dir, res_file))
        else:
            res = mega_find(project.proj_dir, pattern="lint*results*.xml", maxdepth=5, type_file='f')
            if len(res) > 0:
                res_file = res[0]
                copy(res_file, output_dir)
                self.validate_success(res, os.path.join(output_dir, res_file))
            else:
                loge("No lint results found")
                with open(lint_failed_file, 'w') as f:
                    f.write(f"{time.time()} {exec_task} failed")

    def validate_success(self, res, expected_output_file):
        if not os.path.exists(expected_output_file) and res.return_code != 0:
            loge(f"Error executing lint analysis. Check the logs for more information")
            print(res)
            return False
        logs(f"lint analysis executed successfully")
        return True

    def generate_local_properties(self, project_dir):
        cmd = f"echo \"sdk.dir=$ANDROID_HOME\" > {os.path.join(project_dir, 'local.properties')}"
        res = execute_shell_command(cmd)

    def get_issues(self, results_file):
        issues = []
        # Iterate over XML files in the lint results directory
        tree = ET.parse(results_file)
        root = tree.getroot()
        # Parse XML structure
        for issue in root.findall("issue"):
            issue_id = issue.get("id")
            category = issue.get("category")
            if self.performance_only and (issue_id not in self.identifiable_issues.keys() or category is None
                                          or category != 'Performance'):
                continue
            severity = issue.get("severity")
            message = issue.get("message")

            priority = issue.get("priority")
            summary = issue.get("summary")
            explanation = issue.get("explanation")
            # Extract affected file paths
            locations = [(loc.get("file", None), loc.get('line', None)) for loc in issue.findall("location")]
            for loc in locations:
                issues.append(Issue(issue_id, category, severity, message,
                                    file=loc[0], line=loc[1], detection_tool_name=self.name))

        return issues


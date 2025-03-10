import json
import os
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, logs

DEFAULT_OUTPUT_DIRNAME = "daap_output"
DEFAULT_OUTPUT_FILENAME = "pmd_analysis"
DEFAULT_RULESET = "category/java/performance.xml"
DEFAULT_PATH_EXEC = os.path.join(get_resources_dir(), 'bin' , 'pmd-bin-7.9.0', 'bin', "pmd")
DEFAULT_SEARCH_PATTERN = "check"
DEFAULT_OUTPUT_FORMAT = "json"

# /Users/rar9993/repos/pyanadroid/anadroid/resources/bin/pmd-bin-7.9.0/bin/pmd  check -d ../pyanadroid/demoProjects/SampleApp/app/src/main/java -R rulesets/java/quickstart.xml -f json

class PMDAnalysis(StaticAnalyzer):
    def __init__(self, analyzers_cfg_file=None, default_output_dir=DEFAULT_OUTPUT_DIRNAME,
                 bin_path=DEFAULT_PATH_EXEC):
        super().__init__(analyzers_cfg_file)
        self.default_output_dir = default_output_dir
        self.exec_cmd = f"{bin_path} "
        self.identifiable_issues = {
            "AppendCharacterWithChar": KnownStaticPerformanceIssues.APPEND_CHARACTER_WITH_CHAR,
            "AvoidArrayLoops": KnownStaticPerformanceIssues.AVOID_ARRAY_LOOPS,
            "AvoidCalendarDateCreation": KnownStaticPerformanceIssues.AVOID_CALENDAR_DATE_CREATION,
            "AvoidFileStream": KnownStaticPerformanceIssues.AVOID_FILE_STREAM,
            "AvoidInstantiatingObjectsInLoops": KnownStaticPerformanceIssues.AVOID_INSTANTIATING_OBJECTS_IN_LOOPS,
            "BigIntegerInstantiation": KnownStaticPerformanceIssues.BIG_INTEGER_INSTANTIATION,
            "ConsecutiveAppendsShouldReuse": KnownStaticPerformanceIssues.CONSECUTIVE_APPENDS_SHOULD_REUSE,
            "ConsecutiveLiteralAppends": KnownStaticPerformanceIssues.CONSECUTIVE_LITERAL_APPENDS,
            "InefficientEmptyStringCheck": KnownStaticPerformanceIssues.INEFFICIENT_EMPTY_STRING_CHECK,
            "InefficientStringBuffering": KnownStaticPerformanceIssues.INEFFICIENT_STRING_BUFFERING,
            "InsufficientStringBufferDeclaration": KnownStaticPerformanceIssues.INSUFFICIENT_STRING_BUFFER_DECLARATION,
            "OptimizableToArrayCall": KnownStaticPerformanceIssues.OPTIMIZABLE_TO_ARRAY_CALL,
            "RedundantFieldInitializer": KnownStaticPerformanceIssues.REDUNDANT_FIELD_INITIALIZER,
            "StringInstantiation" : KnownStaticPerformanceIssues.STRING_INSTANTIATION,
            "StringToString": KnownStaticPerformanceIssues.STRING_TO_STRING,
            "TooFewBranchesForSwitch": KnownStaticPerformanceIssues.TOO_FEW_BRANCHES_FOR_SWITCH,
            "UseArrayListInsteadOfVector": KnownStaticPerformanceIssues.USE_ARRAY_LIST_INSTEAD_OF_VECTOR,
            "UseArraysAsList": KnownStaticPerformanceIssues.USE_ARRAYS_AS_LIST,
            "UseIndexOfChar":  KnownStaticPerformanceIssues.USE_INDEX_OF_CHAR,
            "UseIOStreamsWithApacheCommonsFileItem": KnownStaticPerformanceIssues.USE_IO_STREAMS_WITH_APACHE_COMMONS_FILE_ITEM,
            "UselessStringValueOf": KnownStaticPerformanceIssues.USELESS_STRING_VALUE_OF,
            "UseStringBufferForStringAppends": KnownStaticPerformanceIssues.USE_STRING_BUFFER_FOR_STRING_APPENDS,
            "UseStringBufferLength": KnownStaticPerformanceIssues.USE_STRING_BUFFER_LENGTH,
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
        search_pattern_code = kwargs.get("search_pattern_code", DEFAULT_SEARCH_PATTERN)
        ruleset = kwargs.get("ruleset", DEFAULT_RULESET)
        retry = kwargs.get("retry", True)
        output_format = kwargs.get("output_format", DEFAULT_OUTPUT_FORMAT)
        output_filename = kwargs.get("output_filename", DEFAULT_OUTPUT_FILENAME)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', self.default_output_dir))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for module in project.modules:
            module_path = os.path.join(project.proj_dir, module)
            output_filepath = os.path.join(output_dir, f"{module}_{output_filename}.{output_format}")
            if os.path.exists(output_filepath) and not retry:
                logs(f"Skipping module {project.proj_name}.{module}. Already processed by PMD")
                return
            cmd = f"{self.exec_cmd} {search_pattern_code} -d {module_path} -R {ruleset} -f {output_format} -r {output_filepath}"
            print(cmd)
            res = execute_shell_command(cmd,timeout=300)
            self.validate_success(res, output_filepath)

    def validate_success(self, res, expected_output_file):
        if not os.path.exists(expected_output_file) and res.return_code != 0:
            loge(f"Error executing PMD analysis. Check the logs for more information")
            print(res)
            return False
        logs(f"PMD analysis executed successfully")
        return True

    def get_issues(self, results_file):
        """Parses a PMD JSON results file and extracts violations information."""
        try:
            with open(results_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            issues = []
            #module_name = os.path.basename(results_file).replace(f"_{DEFAULT_OUTPUT_FILENAME}", "")
            for file_entry in data.get("files", []):
                filename = file_entry.get("filename")
                for violation in file_entry.get("violations", []):
                    issues.append(Issue(
                        self.identifiable_issues.get(violation.get("rule"), violation.get("rule")),
                        file=filename,
                        detection_tool_name="PMD",
                        line=violation.get("beginline", None),
                        column=violation.get("begincolumn", None),
                    ))

        except Exception as e:
            print(f"Error parsing PMD results: {e}")
            return []

        return issues





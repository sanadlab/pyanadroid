import os

from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.utils.Utils import execute_shell_command, log_to_file, logi

DEFAULT_FILENAME = "scc.json"


class SCCAnalyzer(StaticAnalyzer):
    """Implements AbstractAnalyzer interface to allow to calculate app code results using scc tool.
    """
    def __init__(self):
        super(SCCAnalyzer, self).__init__()
        self.bin_cmd = "scc"

    def setup(self, **kwargs):
        pass

    def analyze_project(self, project, **kwargs):
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', project.proj_dir))
        output_log_file = kwargs.get("output_log_file") if 'output_log_file' in kwargs else DEFAULT_FILENAME
        input_dir = project.proj_dir
        cmd = f"{self.bin_cmd} {input_dir} -f json"
        logi(f"Analyzing project {project.proj_dir} with SCC (output file: {output_log_file})")
        res = execute_shell_command(cmd,timeout=60)
        if res.validate(Exception(f"Unable to analyze sources with {self.bin_cmd}")):
            log_to_file(res.output, os.path.join(output_dir, output_log_file), mode='w')

    def show_results(self, app_list):
        pass

    def clean(self):
        pass

    def get_val_for_filter(self, filter_name, add_data=None):
        return super().get_val_for_filter(filter_name, add_data)

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        pass

    def analyze_test(self, app, test_id, **kwargs):
        pass

    def validate_test(self, app, arg1, **kwargs):
        return True

    def validate_filters(self):
        return super().validate_filters()
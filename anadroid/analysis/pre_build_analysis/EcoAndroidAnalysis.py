import os
import platform
from anadroid.analysis.StaticAnalyzer import StaticAnalyzer
from anadroid.analysis.metrics.Issues import KnownStaticPerformanceIssues, Issue
from anadroid.utils.Utils import execute_shell_command, get_resources_dir, loge, logs
import xml.etree.ElementTree as ET


# /Applications/IntelliJ\ IDEA\ CE.app/Contents/bin/inspect.sh  /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/ /Users/rar9993/repos/EcoAndroid/eco_ide/EcoAndroid/Project_Default.xml /Users/rar9993/repos/EcoAndroid/eco_ide/EcoAndroid/out  -d /Users/rar9993/repos/pyanadroid/demoProjects/SampleApp/app -v2

#

def infer_ecoandroid_cmd():
    # check if mac os or linux or windows
    if os.name == "posix":
        # check if mac os
        if platform.system() == "Darwin":
            return "/Applications/IntelliJ\ IDEA\ CE.app/Contents/bin/inspect.sh"
        else:
            return "idea.sh inspect"
    else:
        return "idea64.exe inspect"


DEFAULT_PROFILE_PATH = os.path.join(get_resources_dir() ,"Project_Default.xml")
DEFAULT_OUTPUT_DIRNAME = "ecoandroid_analysis_output"


class EcoAndroidAnalysis(StaticAnalyzer):
    def __init__(self, analyzers_cfg_file=None, default_profile_path=DEFAULT_PROFILE_PATH, default_output_dir=DEFAULT_OUTPUT_DIRNAME):
        super().__init__(analyzers_cfg_file)
        self.default_profile_path = default_profile_path
        self.default_output_dir = default_output_dir
        self.identifiable_issues = {
            "CheckLayoutSize": KnownStaticPerformanceIssues.CHECK_LAYOUT_SIZE,
            "CheckMetadata": KnownStaticPerformanceIssues.CHECK_METADATA,
            "CheckNetwork": KnownStaticPerformanceIssues.CHECK_NETWORK,
            "DirtyRendering": KnownStaticPerformanceIssues.CHECK_LAYOUT_SIZE,
            "DynamicWaitTime": KnownStaticPerformanceIssues.DYNAMIC_WAIT_TIME,
            "GZIPCompression": KnownStaticPerformanceIssues.DATA_TRANSMISSION_WITHOUT_COMPRESSION,
            "InfoWarningFCM": KnownStaticPerformanceIssues.INFO_WARNING_FCM,
            "PassiveProviderLocation": KnownStaticPerformanceIssues.PASSIVE_PROVIDER_LOCATION,
            "SSLSessionCaching": KnownStaticPerformanceIssues.SSL_SESSION_CACHING,
            "URLCaching": KnownStaticPerformanceIssues.URL_CACHING,

        }

    def setup(self, **kwargs):
        expected_exec_file = infer_ecoandroid_cmd()
        if not os.path.exists(expected_exec_file):
            raise Exception(f"Expected executable file not found: {expected_exec_file}")

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
        profile_path = kwargs.get("profile_path", self.default_profile_path)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', self.default_output_dir))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for module in project.modules:
            print("Analyzing module: ", module)
            module_path = os.path.join(project.proj_dir, module)
            module_out_dir = os.path.join(output_dir, f"ecoandroid_{module}")
            if os.path.exists(module_out_dir) and not retry:
                logs(f"Skipping module {project.proj_name}.{module}. Already processed by EcoAndroid")
                return
            if not os.path.exists(module_out_dir):
                os.makedirs(module_out_dir)
            else:
                # cleanup the directory, otherwise the tool will append to file and xml file will not have a single root
                for root_dir, _, files in os.walk(module_out_dir):
                    for file in files:
                        os.remove(os.path.join(root_dir, file))
            timeout = 300
            cmd = f"gtimeout {timeout} {infer_ecoandroid_cmd()} {project.proj_dir} " f"{profile_path} {module_out_dir} -d {module_path} -v2"
            print(cmd)
            res = execute_shell_command(cmd, timeout=timeout)
            self.validate_success(res, module_out_dir)

    def validate_success(self, res, expected_output_file):
        if not os.path.exists(expected_output_file) and res.return_code != 0:
            loge(f"Error executing ecoandroid analysis. Check the logs for more information")
            print(res)
            return False
        logs(f"ecoandroid analysis executed successfully")
        return True

    def get_issues(self, output_dir):
        issues = []
        found_issues_id = set()
        # Iterate over XML files in the output directory
        for root_dir, _, files in os.walk(output_dir):
            for file in files:
                #print(file)
                if file.endswith(".xml"):  # Ensure we're processing only XML files
                    file_path = os.path.join(root_dir, file)
                    try:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        # Parse XML structure
                        for issue in root.findall("issue"):
                            issue_id = issue.get("id", None)
                            if issue_id is None:
                                continue
                            if issue_id in found_issues_id:
                                continue
                            found_issues_id.add(issue_id)
                            issue_type = issue.get("category", None)
                            file_path = issue.get("file", None)
                            line = issue.get("line", None)
                            desc = issue.get("description", None)
                            # TODO other fields
                            issues.append(
                                Issue(self.identifiable_issues[issue_id] if issue_id in self.identifiable_issues else issue_id,
                                      file=file_path,
                                      line=line,
                                      detection_tool_name="EcoAndroid",
                                      description=desc)
                            )
                    except Exception as e:
                        loge(f"Error parsing file {file_path}: {e}")

        return issues

import multiprocessing
import os
import platform
import shutil
import time

from textops import cat

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

ANDROID_HOME = os.environ.get("ANDROID_HOME", None)

eco_lock = multiprocessing.Lock()

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
        self.ignorable_issues = {
            "SpellCheckingInspection",
            "CanBeFinal",
            "CatchMayIgnoreException",
            "Deprecation",
            "DuplicateThrows",
            "EmptyMethod",
            "FieldMayBeFinal",
            "GrazieInspection",
            "NullableProblems",
            "RedundantCast",
            "UNUSED_IMPORT",
            "UnnecessaryToStringCall",
            "XmlUnusedNamespaceDeclaration",
            "unused",
            "UnusedSymbol",
            "RedundantThrows",
            "JavadocDeclaration",
            "RawUseOfParameterizedType",
            "UnusedAssignment",
            'UNCHECKED_WARNING',
            'JavadocReference',
            'JavadocLinkAsPlainText',
            'XmlHighlighting',
            'HasPlatformType',
            'FoldInitializerAndIfToElvis',
            'GradlePackageVersionRange',
            "DanglingJavadoc",
            "Convert2Lambda",
            "GrUnnecessarySemicolon",
            "AndroidDomInspection"
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
        remove_local_props = kwargs.get("remove_local_props", True) # TODO
        remove_idea_fldr = kwargs.get("remove_idea_fldr", True)  # TODO
        profile_path = kwargs.get("profile_path", self.default_profile_path)
        output_dir = kwargs.get("output_dir", getattr(project, 'results_dir', self.default_output_dir))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if remove_idea_fldr and os.path.exists(os.path.join(project.proj_dir, ".idea")):
            shutil.rmtree(os.path.join(project.proj_dir, ".idea"))
        if remove_local_props and os.path.exists(os.path.join(project.proj_dir, "local.properties")):
            os.remove(os.path.join(project.proj_dir, "local.properties"))
        for module in project.modules:
            print("Analyzing module: ", module)
            module_path = os.path.join(project.proj_dir, module)
            module_out_dir = os.path.join(output_dir, f"ecoandroid_{module}")
            possible_log_file = os.path.join(module_out_dir, "ecoandroid.log")
            possible_check_string = str(cat(possible_log_file) ) if os.path.exists(possible_log_file) else None
            if os.path.exists(module_out_dir) and len(os.listdir(module_out_dir)) > 0 and self.executed_correctly(possible_check_string) and not retry:
                logs(f"Skipping module {project.proj_name}.{module}. Already processed by EcoAndroid")
                return
            if not os.path.exists(module_out_dir):
                os.makedirs(module_out_dir)
            else:
                # cleanup the directory, otherwise the tool will append to file and xml file will not have a single root
                for root_dir, _, files in os.walk(module_out_dir):
                    for file in files:
                        if file.endswith(".xml"):
                            os.remove(os.path.join(root_dir, file))
            timeout = 300
            #log_file = os.path.join(module_out_dir, "ecoandroid.log")
            cmd = f"gtimeout {timeout} {infer_ecoandroid_cmd()} {project.proj_dir} " f"{profile_path} {module_out_dir} -d {module_path} -v2"
            print(cmd)
            with eco_lock:
                time.sleep(2)
                res = execute_shell_command(cmd, timeout=timeout)
                time.sleep(2)
            self.validate_success(res, module_out_dir)

    def executed_correctly(self, str_to_check):
        if str_to_check is None:
            return True
        if "nly one instance" in str_to_check:
            return False
        return True

    def validate_success(self, res, expected_output_dir):
        if not os.path.exists(expected_output_dir) and res.return_code != 0:
            loge(f"Error executing ecoandroid analysis. Check the logs for more information")
            print(res)
            return False
        out_str = res.output + res.errors
        log_file = os.path.join(expected_output_dir, "ecoandroid.log")
        with open(log_file, 'w') as f:
            f.write(out_str)
        print(out_str)
        if not self.executed_correctly(out_str):
            loge(f"Error executing ecoandroid analysis. Check the logs for more information")
            # print(out_str)
            return
        logs(f"ecoandroid analysis executed successfully")
        fi_to_touch = os.path.join(expected_output_dir, 'done.ok')
        #print("touching grass", fi_to_touch)
        execute_shell_command(f"touch {fi_to_touch}")
        return True

    def get_issues(self, output_dir, ignore_tests=True):
        issues = []
        # Iterate over XML files in the output directory
        for root_dir, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".xml"):  # Ensure we're processing only XML files
                    file_path = os.path.join(root_dir, file)
                    try:
                        tree = ET.parse(file_path)
                        for issue in tree.iter():
                            #print(issue.tag)
                            if issue.tag != "problem":
                                continue
                            method_id = None
                            class_id = None
                            issue_id = issue.get("id", None)
                            if issue_id is None:
                                prob_class = issue.find("problem_class")
                                if prob_class is None:
                                    continue
                                issue_id = prob_class.get('id', None)
                                if issue_id is None:
                                    continue
                            if issue_id not in self.identifiable_issues and issue_id in self.ignorable_issues:
                                continue
                            file_path = issue.find("file", None)
                            if 'src' in file_path and (
                                    'test' in file_path or 'androidTest' in file_path or "InstrumentedTest" in file_path) and ignore_tests:
                                continue
                            line = issue.find("line", None)
                            desc = issue.find("description", None)
                            entry_type = issue.find("entry_point", None)
                            if entry_type is not None:
                                if entry_type.get("TYPE").strip() == "method":
                                    method_def = entry_type.get("FQNAME")
                                    method_id = method_def.split("(")[0].split(" ")[-1]
                                    class_id = method_def.split("(")[0].split(" ")[0]
                                    #print(f"Method: {method_id}, Class: {class_id}")
                            issue = Issue(self.identifiable_issues[issue_id] if issue_id in self.identifiable_issues else issue_id,
                                      file=file_path.text.replace("file://$PROJECT_DIR$" + os.sep, "")  if file_path is not None else None,
                                      line=line.text if line is not None else None,
                                      method=method_id,
                                      i_class=class_id,
                                      detection_tool_name="EcoAndroid",
                                      description=desc.text if desc is not None else None)
                            if issue not in issues:
                                print(issue)
                                issues.append(issue)
                    except Exception as e:
                        loge(f"Error parsing file {file_path}: {e}")

        return issues

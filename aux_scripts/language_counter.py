import ast
import csv
import json
import os
from functools import reduce
from os import listdir
from subprocess import Popen, PIPE, TimeoutExpired
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pylab import *

from textops import find, cat

from anadroid.analysis.post_build_analysis.DroidLensAnalyzer import DroidLensAnalysis
from anadroid.analysis.post_build_analysis.EcoAndroidResourceLeaksAnalyzer import EcoAndroidResourceLeaksAnalysis
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.ChimeraAnalysis import ChimeraAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.DetektAnalysis import DetektAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.InferAnalysis import InferAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.analysis.pre_build_analysis.SpotBugsAnalysis import SpotBugsAnalysis
from anadroid.analysis.pre_build_analysis.XALintAnalysis import XALintAnalysis

EXCLUDED_LANGS = {'gitignore', 'Markdown', 'License', 'JSON', 'YAML', 'Prolog', 'C Header', 'Batch', 'Properties File'}
INCLUDED_LANGS = {'Java', 'Python', 'Dart', 'TypeScript', 'JavaScript', 'C', 'C++', 'Kotlin', 'Rust',  'Gradle', 'XML'}



TO_EXCLUDE = {
    "UnusedIds",
    "UnusedResources",
    "ViewTag",
    "InternalGetterSetter",
    "DroppedData",
    "VectorPath",
    "MemberIgnoringMethod"
}

ISSUE_CATEGORY_MAPPING = {
    "SlowForLoop": ["Suboptimal Algorithm"],
    "DrawAllocation": ["Resource Management"],
    "Recycle": ["Resource Management", "API Misuse"],
    "WakeLock": ["Concurrency", "Resource Management"],
    "WakelockTimeout": ["Resource Management"],
    "ViewHolder": ["Suboptimal Algorithm", "Resource Management"],
    "ObsoleteLayoutParam": ["Resource Management", "Code Smell"],
    "BLOBClass": ["Code Smell"],
    "SwissArmyKnife": ["Code Smell"],
    "Longmethod": ["Code Smell"],
    "ComplexClass": ["Code Smell"],
    "InternalGetterSetter": ["Obsolete Solution"],
    "MemberIgnoringMethod": ["Suboptimal Algorithm"],
    "NoLowMemoryResolver": ["Resource Management"],
    "LeakingInnerClass": ["Code Smell"],
    "UnsuitedLRUCacheSize": ["Resource Management"],
    "HashmapUsage": ["Data Manipulation", "Obsolete Solution"],
    "Overdraw": ["Resource Management"],
    "UIOverdraw": ["Resource Management"],
    "InvalidatewithoutRect": ["Unnecessary Computation"],
    "UnsupportedHardwareAcceleration": ["Suboptimal Algorithm"],
    "HeavyAsyncTask": ["Concurrency", "Suboptimal Algorithm"],
    "HeavyServiceStart": ["Suboptimal Algorithm"],
    "HeavyBroadcastReceiver": ["Suboptimal Algorithm"],
    "BitmapFormatUsage": ["Resource Management"],
    "UnclosedCloseable": ["Resource Management"],
    "CameraLeak": ["Resource Management"],
    "MediaLeak": ["Resource Management"],
    "LeakingThread": ["Resource Management"],
    "LeakingHandler": ["Resource Management"],
    "DataTransmissionWithoutCompression": ["RPC/IPC", "Suboptimal Algorithm"],
    "VacuousBackgroundService": ["Resource Management"],
    "LifecycleContainment": ["Resource Management"],
    "EarlyResourceBinding": ["Resource Management"],
    "ImmortalityBug": ["Resource Management"],
    "RigidAlarmManager": ["Suboptimal Algorithm"],
    "InefficientSQLQuery": ["Data Access", "RPC/IPC"],
    "DebuggableRelease": ["Resource Management"],
    "InefficientDataFormatAndParser": ["Data Access", "Suboptimal Algorithm"],
    "MemoizationChance": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "DynamicWaitTime": ["Suboptimal Algorithm", "RPC/IPC"],
    "InfoWarningFCM": ["Obsolete Solution"],
    "PassiveProviderLocation": ["Resource Management"],
    "SSLSessionCaching": ["RPC/IPC"],
    "URLCaching": ["RPC/IPC", "Unnecessary Computation"],
    "CheckLayoutSize": ["Resource Management", "Unnecessary Computation"],
    "CheckMetadata": ["Unnecessary Computation"],
    "CheckNetwork": ["RPC/IPC"],
    "DirtyRendering": ["Unnecessary Computation"],
    "ExcessiveLoopCallsDetector": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "NestedWeight": ["Resource Management", "Suboptimal Algorithm"],
    "ConfigChanges": ["Resource Management"],
    "DroppedData": ["Resource Management"],
    "CollectionOfBitmaps": ["Resource Management"],
    "CollectionOfViews": ["Resource Management"],
    "StaticBitmap": ["Code Smell"],
    "StaticContext": ["Code Smell"],
    "StaticView": ["Code Smell"],
    "StaticFieldLeak": ["Code Smell"],
    "UselessStringValueOf": ["Data Manipulation", "Unnecessary Computation"],
    "AppendCharacterWithChar": ["Data Manipulation", "Suboptimal Algorithm"],
    "AvoidArrayLoops": ["Data Manipulation", "Obsolete Solution"],
    "AvoidCalendarDateCreation": ["Obsolete Solution", "Unnecessary Computation"],
    "AvoidFileStream": ["Data Access", "Obsolete Solution"],
    "AvoidInstantiatingObjectsInLoops": ["Unnecessary Computation"],
    "BigIntegerInstantiation": ["Data Manipulation", "Unnecessary Computation"],
    "ConsecutiveAppendsShouldReuse": ["Data Manipulation", "Code Smell"],
    "ConsecutiveLiteralAppends": ["Data Manipulation", "Code Smell"],
    "InefficientEmptyStringCheck": ["Data Manipulation", "Suboptimal Algorithm"],
    "InefficientStringBuffering": ["Data Manipulation"],
    "InsufficientStringBufferDeclaration": ["Data Manipulation"],
    "OptimizableToArrayCall": ["Data Manipulation", "Suboptimal Algorithm"],
    "RedundantFieldInitializer": ["Code Smell"],
    "StringInstantiation": ["Data Manipulation", "Unnecessary Computation"],
    "StringToString": ["Data Manipulation", "Unnecessary Computation"],
    "TooFewBranchesForSwitch": ["Code Smell"],
    "UseArrayListInsteadOfVector": ["Obsolete Solution", "Data Manipulation"],
    "UseArraysAsList": ["Obsolete Solution", "Data Manipulation"],
    "UseIndexOfChar": ["Data Manipulation", "Suboptimal Algorithm"],
    "UseIOStreamsWithApacheCommonsFileItem": ["Data Access", "API Misuse"],
    "UseStringBufferForStringAppends": ["Data Manipulation"],
    "UseStringBufferLength": ["Data Manipulation", "Suboptimal Algorithm"],
    "AddEmptyString": ["Data Manipulation", "Unnecessary Computation"],
    "UselessParent": ["Resource Management"],
    "UselessLeaf": ["Resource Management"],
    "AnimatorKeep": ["Resource Management"],
    "ObsoleteSdkInt": ["Obsolete Solution", "Code Smell"],
    "DuplicateDivider": ["Obsolete Solution", "Code Smell"],
    "UseValueOf": ["Data Manipulation", "Unnecessary Computation"],
    "UnpackedNativeCode": ["Build Optimization"],
    "UnusedResources": ["Resource Management"],
    "UnusedIds": ["Resource Management", "Code Smell"],
    "InefficientWeight": ["Resource Management", "Suboptimal Algorithm"],
    "DisableBaselineAlignment": ["Resource Management", "Suboptimal Algorithm"],
    "MergeRootFrame": ["Resource Management"],
    "DevModeObsolete": ["Build Optimization", "Obsolete Solution"],
    "LifecycleAnnotationProcessorWithJava8": ["Build Optimization", "Obsolete Solution"],
    "AnnotationProcessorOnCompilePath": ["Build Optimization"],
    "LogConditional": ["Code Smell"],
    "WearableBindListener": ["Obsolete Solution"],
    "UsableSpace": ["Data Access", "Obsolete Solution"],
    "VectorPath": ["Resource Management"],
    "UnusedNamespace": ["Resource Management", "Code Smell"],
    "RedundantNamespace": ["Resource Management", "Code Smell"],
    "ViewTag": ["Obsolete Solution"],
    "TooManyViews": ["Resource Management", "Suboptimal Algorithm"],
    "TooDeepLayout": ["Resource Management", "Suboptimal Algorithm"],
    "UseCompoundDrawables": ["Resource Management", "Suboptimal Algorithm"],
    "UseOfBundledGooglePlayServices": ["Build Optimization"],
    "StringFormatTrivial": ["Data Manipulation", "Unnecessary Computation"],
    "AssertionSideEffect": ["Unnecessary Computation", "Code Smell"],
    "DuplicateStrings": ["Resource Management", "Code Smell"],
    "ExpensiveAssertion": ["Unnecessary Computation", "Code Smell"],
    "LaunchActivityFromNotification": ["Code Smell"],
    "NotificationTrampoline": ["Obsolete Solution"],
    "AutoboxingStateCreation": ["Data Manipulation"],
    "AutoboxingStateValueProperty": ["Data Manipulation", "Unnecessary Computation"],
    "FrequentlyChangedStateReadInComposition": ["Unnecessary Computation"],
    "KaptUsageInsteadOfKsp": ["Build Optimization", "Obsolete Solution"],
    "NotifyDataSetChanged": ["Suboptimal Algorithm", "Obsolete Solution"],
    "UnnecessaryArrayInit": ["Data Manipulation", "Unnecessary Computation"],
    "SyntheticAccessor": ["Suboptimal Algorithm"],
    "UseOfNonLambdaOffsetOverload": ["Unnecessary Computation"],
    "InefficientKeySetIterator": ["Data Manipulation", "Suboptimal Algorithm"],
    "InvariantCall": ["Unnecessary Computation"],
    "IPCOnUIThread": ["Suboptimal Algorithm", "RPC/IPC"],
    "RegexOpOnUIThread": ["Unnecessary Computation"],
    "ExpensiveExecutionTime": ["Suboptimal Algorithm"],
    "HugeSharedStringConstant": ["Data Manipulation"],
    "BlockingMethodsOnURL": ["RPC/IPC"],
    "ExplicitGarbageCollection": ["Suboptimal Algorithm", "Code Smell"],
    "BoxedPrimitiveToString": ["Data Manipulation", "Unnecessary Computation"],
    "BoxedPrimitiveForParsing": ["Data Manipulation", "Unnecessary Computation"],
    "BoxedPrimitiveForCompare": ["Data Manipulation", "Unnecessary Computation"],
    "UnboxedAndCorecedForTernaryOperator": ["Data Manipulation"],
    "UnboxingImmediatelyReboxed": ["Data Manipulation", "Unnecessary Computation"],
    "BoxingImmediatelyUnboxed": ["Data Manipulation", "Unnecessary Computation"],
    "BoxingImmediatelyUnboxedToPerformCoercion": ["Data Manipulation", "Unnecessary Computation"],
    "NewForGetClass": ["Unnecessary Computation"],
    "NextIntViaNextDouble": ["Suboptimal Algorithm"],
    "UnusedField": ["Code Smell", "Unnecessary Computation"],
    "UnreadField": ["Code Smell"],
    "UncalledPrivateMethod": ["Code Smell"],
    "UseStringBufferConcatenation": ["Data Manipulation", "Suboptimal Algorithm"],
    "ElementsGetLengthInLoop": ["Data Access", "Unnecessary Computation"],
    "PrepareStatementInLoop": ["Data Access", "Unnecessary Computation"],
    "PatternCompileInLoop": ["Unnecessary Computation"],
    "InefficientLastIndexOf": ["Data Manipulation", "Suboptimal Algorithm"],
    "UnnecessaryMath": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "BloatedSynchronizedBlock": ["Concurrency"],
    "DubiousListCollection": ["Data Manipulation", "Suboptimal Algorithm"],
    "DubiousSetofCollections": ["Data Manipulation", "Suboptimal Algorithm"],
    "ContainsOnCollectedStream": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "AvoidSizeOnCollectedStream": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "UseFindFirst": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "ExecutorNotShuttingDown": ["Resource Management"],
    "DoubleBufferCopy": ["Data Access", "Suboptimal Algorithm"],
    "ListIndexIterating": ["Suboptimal Algorithm"],
    "LocalSynchronizedCollection": ["Concurrency", "Unnecessary Computation"],
    "RunFinalization": ["Code Smell", "API Misuse"],
    "InstanceBasedThreadLocal": ["Concurrency"],
    "PossibleMemoryBloat": ["Resource Management"],
    "TailRecursion": ["Suboptimal Algorithm"],
    "UseEnumCollections": ["Data Manipulation", "Obsolete Solution"],
    "ArrayPrimitive": ["Data Manipulation"],
    "CouldBeSequence": ["Suboptimal Algorithm"],
    "SpreadOperator": ["Data Manipulation"],
    "UnnecessaryPartOfBinaryExpression": ["Code Smell"],
    "UnnecessaryTypeCasting": ["Code Smell", "Unnecessary Computation"],
    "LogToStringParameter": ["Unnecessary Computation", "API Misuse"],
    "LogAppendedStringInFormat": ["Data Manipulation", "API Misuse"],
    "UseSingletonList": ["Suboptimal Algorithm", "API Misuse"],
    "CallingSizeOnSubContainer": ["Unnecessary Computation"],
    "ContainsKeyBeforeGet": ["Suboptimal Algorithm"],
    "GetBeforeRemove": ["Suboptimal Algorithm"],
    "NeedlessInstanceRetrieval": ["Unnecessary Computation"],
    "NeedlessMemberCollectionSynchronization": ["Unnecessary Computation", "Concurrency"],
    "OptionalPrimitiveVariantPreferred": ["Data Manipulation", "Suboptimal Algorithm"],
    "OptionalIssuesUsesImmediateExecution": ["Unnecessary Computation"],
    "PreSizeCollections": ["Suboptimal Algorithm"],
    "SubOptimalCollectionSizing": ["Suboptimal Algorithm"],
    "StaticArrayCreatedInMethod": ["Unnecessary Computation"],
    "SubOptimalExpressionOrder": ["Suboptimal Algorithm"],
    "SQLInLoop": ["Data Access", "Suboptimal Algorithm"],
    "ContainsBeforeAdd": ["Unnecessary Computation"],
    "ContainsBeforeRemove": ["Unnecessary Computation"],
    "UseAddAll": ["Suboptimal Algorithm"],
    "UnjitableMethod": ["Code Smell"],
    "ForEachOnRange": ["Suboptimal Algorithm"]
}

LIGHTWEIGHT_TOOLS = {
    "adoctor",
    "daap",
    "detekt",
    "pmd"
}

def load_tp_rates(filename='issue_level_annotated_stats.json'):
    tp_rates = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            for issue_name, stats in data.items():
                tp_rates[issue_name] = float(stats.get('precision', 0.0))
    return tp_rates

TP_RATES = load_tp_rates()

def load_tps(tp_file='llm_gen_datasets/vibe_and_similar_issues_annotated.csv'):
    tps = []
    if os.path.exists(tp_file):
        with open(tp_file, 'r') as tp_f:
            for line in tp_f.readlines():
                if 'real_true_positi' in line:
                    parts = line.strip().split(';')
                    if len(parts) >= 4:
                        tool = parts[0].strip()
                        issue = parts[1].strip()
                        proj = parts[2].strip().replace('/NONE_TRANSFORMED_','')
                        file = parts[3].strip().replace('/NONE_TRANSFORMED_','')
                        tps.append( (issue, tool, proj, file) )
    return tps

TRUE_POSITIVES = load_tps()

def get_project_root_dir(proj_path):
    """infers Android project root directory."""
    has_gradle_right_next = mega_find(proj_path, pattern="build.gradle", maxdepth=4, type_file='f')
    if len(has_gradle_right_next) > 0:
        top_gradle_file = min(has_gradle_right_next, key=len)
        return os.path.dirname(top_gradle_file)
    return None


def is_android_project(dirpath):
    """determines if a given directory is an Android Project.
    looks for settings.gradle files.
    Args:
        dirpath: path of the directory.

    Returns:
        bool: True if file is in diretory, False otherwise.
    """
    return any([f for f in listdir(dirpath) if '.gradle' in f])

def get_proj_name(file_location):
    if 'AndroidStudio' in file_location:
        return file_location.split('AndroidStudio')[1].split(os.sep)[1]
    elif 'similar_' in file_location:
        print(file_location)
        return file_location.split('similar_')[1].split(os.sep)[1]
    elif 'native_apps' in file_location:
        return file_location.split('native_apps')[1].split(os.sep)[1]
    return file_location



def merge_duplicate_issues(issues_list, skip_possible_duplicates=True):
    print('initial total issues', len(issues_list))
    merged_dict = {}
    for i, reg in enumerate(sorted(issues_list, key=lambda x: len(x.get_issue_location()), reverse=True)):
        #issue_key = reg['issue'].get_simple_name() + reg['prev_commit_hash'] + reg['commit_hash'] + str(getattr(reg['issue'], 'file', ''))
        issue_key = (str(getattr(reg.issue_type, 'value', reg.issue_type))  + ( get_proj_name(str(getattr(reg, 'file', ''))))
                     + str(getattr(reg, 'file', '')).split("/")[-1] )
        if skip_possible_duplicates and issue_key in merged_dict:
            #print('skipping', reg['issue_name'], 'on', reg['repo_dir'])
            # keep the longest location
            line = '' if 'line' not in reg.get_issue_location() else reg.get_issue_location().split("|")[-1]
            mg_line = '' if 'line' not in merged_dict[issue_key][-1].get_issue_location() else merged_dict[issue_key][-1].get_issue_location().split("|")[-1]
            line_number = int(line) if line.strip().isdigit() else -1
            mg_line_number = int(mg_line) if mg_line.strip().isdigit() else -1
            if len(reg.get_issue_location().split('.')[-1]) > len(merged_dict[issue_key][-1].get_issue_location().split('.')[-1]) and mg_line_number > -1:
            #if len(reg['issue_location']) > len(merged_dict[issue_key]['issue_location']):
                merged_dict[issue_key].pop()
                merged_dict[issue_key] = [reg]
            elif line_number > mg_line_number:
                merged_dict[issue_key].append(reg)
                continue
            else:
                continue
        elif not skip_possible_duplicates:
            issue_key += reg.detection_tool_name + str(getattr(reg, 'file', ''))
        merged_dict[issue_key] = merged_dict.get(issue_key, []) + [reg]
    return reduce(lambda a, b: a + b, merged_dict.values(), [])

def load_projects(dirpath):
    """loads Android Projects from a directory containing one or more projects."""
    return_projs = []
    if is_android_project(dirpath):
        potential_projects = [dirpath]
    else:
        potential_projects = list(
            filter(lambda x: os.path.isdir(os.path.join(dirpath, x)), os.listdir(dirpath)))
    for maybe_proj in potential_projects:
        path_dir = os.path.join(dirpath, maybe_proj)
        proj_fldr = get_project_root_dir(path_dir)
        if proj_fldr is not None:
            return_projs.append(proj_fldr)
        else:
            children_dirs = list(filter(lambda x: os.path.isdir(os.path.join(path_dir, x)), os.listdir(path_dir)))
            for child in children_dirs:
                child_path_dir = os.path.join(path_dir, child)
                proj_fldr = get_project_root_dir(child_path_dir)
                if proj_fldr is not None:
                    return_projs.append(proj_fldr)
    return return_projs


def build_scc_json_for_all_projs(dirpath):
    projs = load_projects(dirpath)
    print(f"total projs: {len(projs)}")
    for pdir in projs:
        res, o, e = execute_shell_command(f"scc {pdir} -f json > {os.path.join(pdir,'scc.json')}")


def execute_shell_command(cmd, args=[], timeout=None):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print(command)
    proc = Popen(command, stdout=PIPE, stderr=PIPE,shell=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except TimeoutExpired as e:
        print("command " + cmd + " timed out")
        out = e.stdout if e.stdout is not None else out
        err = e.stderr if e.stderr is not None else err
        proc.kill()
        proc.returncode = 1
    return proc.returncode, out.decode("utf-8"), err.decode('utf-8')


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


class LanguageStats(object):
    def __init__(self):
        self.language_info = {}
        self.proj_info = {}
        self.parsed_files = set()
        self.pure_native = {
            "Java": [],
            "Java+C": [],
            "Kotlin": [],
            "Kotlin+C":[],
            "mix": [],
            "C": [],
        }
        self.cross = {
            "JavaScript": [],
            "Dart": [],
            "Java": [],
            "Kotlin": [],
            "C": [],
        }

    def add_language_info(self, proj_path, lang_info):
        #print(lang_info)
        if 'Name' not in lang_info or lang_info['Name'] in EXCLUDED_LANGS or lang_info['Name'] not in INCLUDED_LANGS:
            return
        if lang_info['Name'] in self.language_info:
            # update stats
            self.language_info[lang_info['Name']] = {
                'proj_count': 1 + self.language_info[lang_info['Name']]['proj_count'],
                'total_loc': lang_info['Code'] + self.language_info[lang_info['Name']]['total_loc'],
                'total_cc': lang_info['Complexity'] + self.language_info[lang_info['Name']]['total_cc'],
                'total_files': lang_info['Count'] + self.language_info[lang_info['Name']]['total_files'],
                'proj_files': self.language_info[lang_info['Name']]['proj_files'] + [proj_path]
            }
        else:
            # new entry
            self.language_info[lang_info['Name']] = {
                'proj_count': 1,
                'total_loc': lang_info['Code'],
                'total_cc': lang_info['Complexity'],
                'total_files': lang_info['Count'],
                'proj_files': [proj_path]
            }
        # add unique stats


    def run_scc(self, proj_path, proj_results_dir):
        if not os.path.exists(proj_path):
            print("proj path does not exist")
            if 'TRANSFORMED' in str(proj_path):
                proj_path = os.path.dirname(proj_path)
                if not os.path.exists(proj_path):
                    print("proj path does not exist")
                    return
        scc_file = os.path.join(proj_results_dir, 'scc.json')
        if os.path.exists(scc_file):
            return
        cmd = f"scc {proj_path} -f json > {scc_file}"
        print(cmd)
        res = execute_shell_command(cmd, timeout=200)

    def parse_repo(self, filepath):
        proj_path = self.solve_project_dir(str(cat(filepath)))
        print(proj_path)
        if proj_path is None:
            return
        proj_results_dir = os.path.join(os.path.dirname(filepath))
        scc_file = os.path.join(proj_results_dir, 'scc.json')
        if not os.path.exists(scc_file):
            self.run_scc(proj_path, proj_results_dir)
            if not os.path.exists(scc_file):
                return
        with open(scc_file, 'r') as jj:
            info = json.load(jj)
        if not os.path.exists(proj_path):
            if 'TRANSFORMED' in str(proj_path):
                proj_path = os.path.dirname(proj_path)
                if not os.path.exists(proj_path):
                    print("proj path does not exist")
                    return
            else:
                print("proj path does not exist")
                return
        is_native = self.check_native(proj_path, info)
        for lang_info in info:
            self.add_language_info(proj_path, lang_info)
            self.parsed_files.add(filepath)
        #issues = []
        issues = merge_duplicate_issues(self.load_project_issues(proj_results_dir))
        #print(len(issues))
        #print(issues)
        self.proj_info[proj_path] = {
            'lang_info': info,
            'is_native': is_native,
            'is_on_play_store': self.check_store(proj_path),
            'last_app_update': self.get_last_update(proj_path),
            'last_app_update_year': datetime.datetime.fromtimestamp(self.get_last_update(proj_path)/1000).year,
            'app_category': self.get_app_category(proj_path),
            'issues': issues,
            'tp_issues': [x for x in TRUE_POSITIVES if proj_path in  x[2] or x[2] in proj_path]
        }

    def load_project_issues(self, proj_results_dir):
        issues_list = []
        adoctor_file = os.path.join(proj_results_dir, 'adoctor.csv')
        if os.path.exists(adoctor_file):
            # print("adoctor")
            issues_list = issues_list + ADoctorAnalysis().get_issues(adoctor_file)
        pmd_files = mega_find(proj_results_dir, pattern="*pmd_analysis.json", type_file='f', maxdepth=2)
        if len(pmd_files) > 0:
            for pmd_file in pmd_files:
                issues_list = issues_list + PMDAnalysis().get_issues(pmd_file)
        daap_files = mega_find(proj_results_dir, pattern="*daap_analysis.json", type_file='f', maxdepth=2)
        if len(daap_files) > 0:
            for daap_file in daap_files:
                issues_list = issues_list + DAAPAnalysis().get_issues(daap_file)
        eco_android_dirs = mega_find(proj_results_dir, pattern="*ecoandroid*", type_file='d', maxdepth=2)
        if len(eco_android_dirs) > 0:
            print(eco_android_dirs)
            for eco_dir in eco_android_dirs:
                if 'resource_leaks' in eco_dir:
                    issues_list = issues_list + list(
                        filter(lambda x: x not in issues_list, EcoAndroidResourceLeaksAnalysis().get_issues(eco_dir)))
                else:
                    issues_list = issues_list + list(
                        filter(lambda x: x not in issues_list, EcoAndroidAnalysis().get_issues(eco_dir)))
        lint_results = mega_find(proj_results_dir, pattern="*lint*.xml", type_file='f', maxdepth=2)
        if len(lint_results) > 0:
            lint_issues = set()
            for lint_file in lint_results:
                try:
                    lint_issues.update(LintAnalysis().get_issues(lint_file))
                    lint_issues.update(XALintAnalysis().get_issues(lint_file, ignore_lint_issues=True))
                    lint_issues.update(ChimeraAnalysis().get_issues(lint_file, ignore_lint_issues=True))
                except:
                    pass
            issues_list = issues_list + list(lint_issues)
        detekt_results = mega_find(proj_results_dir, pattern="*detekt_analysis.xml", type_file='f', maxdepth=2)
        if len(detekt_results) > 0:
            for detekt_file in detekt_results:
                issues_list = issues_list + DetektAnalysis().get_issues(detekt_file)
        spotbugs_results = mega_find(proj_results_dir, pattern="*spotbugs*.xml", type_file='f', maxdepth=2)
        if len(spotbugs_results) > 0:
            for spotbugs_file in spotbugs_results:
                issues_list = issues_list + SpotBugsAnalysis().get_issues(spotbugs_file)
        infer_results = mega_find(proj_results_dir, pattern="*infer_report.json", type_file='f', maxdepth=2)
        if len(infer_results) > 0:
            for infer_file in infer_results:
                issues_list = issues_list + InferAnalysis().get_issues(infer_file)
        droidlens_results = mega_find(proj_results_dir, pattern="*droidlens*", type_file='d', maxdepth=2)
        if len(droidlens_results) > 0:
            for droidlens_dir in droidlens_results:
                issues_list = issues_list + list(
                    filter(lambda x: x not in issues_list, DroidLensAnalysis().get_issues(droidlens_dir)))
        print(f"Loaded {len(issues_list)} issues from {proj_results_dir}")
        return issues_list


    def check_store(self, project_path):
        store_file = os.path.join(project_path, 'is_on_play_store.log')
        if not os.path.exists(store_file):
            return False
        return  'true' in str(cat(store_file)).lower()

    def get_last_update(self, project_path):
        if not os.path.exists(project_path):
            if 'TRANSFORMED' in str(project_path):
                project_path = os.path.dirname(project_path)
                if not os.path.exists(project_path):
                    print("proj path does not exist")
                    return 0
        last_up_file = os.path.join(project_path, 'lastUpdate.log')
        print(last_up_file)
        if not os.path.exists(last_up_file):
            return 0
        text = str(cat(last_up_file))
        #print(last_up_file)
        #print(text)
        return int(text)

    def get_app_category(self, project_path):
        categ_file = os.path.join(project_path, 'categories.log')
        #print(categ_file)
        if not os.path.exists(categ_file):
            return []
        text = str(cat(categ_file))
        #print(text)
        if ']' not in text:
            return [ text.replace("'", "").replace("[", '') ]
        else:
            #print(f"-{text}-")
            return ast.literal_eval(text)


    def check_native(self,filepath, info):
        has_java = any([x for x in info if x['Name'] == 'Java'])
        has_kotlin = any([x for x in info if x['Name'] == 'Kotlin'])
        has_js = any([x for x in info if x['Name'] in ['JavaScript', 'TypeScript']])
        has_dart = any([x for x in info if x['Name'] == 'Dart'])
        has_cpp = any([x for x in info if x['Name'] in ['C', 'C++']])
        is_cross = has_js or has_dart
        is_native = has_java or has_kotlin and not is_cross
        if is_native:
            pure_java = has_java and not has_kotlin
            pure_kt = has_kotlin and not has_java
            if pure_java:
                self.pure_native['Java'] = self.pure_native['Java'] + [filepath]
                if has_cpp:
                    self.pure_native['Java+C'] = self.pure_native['Java+C']  + [filepath]
            elif pure_kt:
                self.pure_native['Kotlin'] = self.pure_native['Kotlin']  + [filepath]
                if has_cpp:
                    self.pure_native['Kotlin+C'] = self.pure_native['Kotlin+C']  + [filepath]
            else:
                self.pure_native['mix'] = self.pure_native['mix'] + [filepath]
            if has_cpp:
                self.pure_native['C'] = self.pure_native['C']  + [filepath]
        elif is_cross:
            if has_dart:
                self.cross['Dart'] = self.cross['Dart']  + [filepath]
            elif has_js:
                self.cross['JavaScript'] = self.cross['JavaScript']  + [filepath]

        return is_native


    def get_last_commit(self, directory_path, lookup_filename_pattern='*_commit_data.csv'):
        # Find all files matching the pattern in the directory and its subdirectories
        if directory_path is None or not os.path.exists(directory_path):
            if 'TRANSFORMED' in str(directory_path):
                directory_path = os.path.dirname(directory_path)
                print(directory_path)
                if not os.path.exists(directory_path):
                    print(f"{directory_path} does not exist")
                    return None
            else:
                print(f"{directory_path} does not exist")
                return None
        file_list = mega_find(directory_path, pattern=lookup_filename_pattern, type_file='f')
        print(directory_path, file_list)
        # Sort the files by modification time (most recent first)
        file_list.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        # Return the most recent file
        if len(file_list) > 0:
            target_file  = file_list[0]
            # read index 1 from csv
            with open(target_file, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=";")
                next(reader)
                for row in reader:
                    if len(row) > 1:
                        return row[0]
        else:
            return None

    def solve_project_dir(self, proj_dir):
        if os.path.exists(proj_dir):
            return proj_dir
        proj_path = proj_dir
        if "FORMED" in proj_dir:
            proj_path = os.path.dirname(proj_dir)
            if os.path.exists(proj_path):
                return proj_path
        if 'native_apps' in proj_dir:
            proj_path = proj_dir.replace('native_apps', 'cross_platform_apps')
            if not os.path.exists(proj_path):
                proj_path = proj_path.replace('cross_platform_apps', 'unknown')
                if not os.path.exists(proj_path):
                    print(proj_path, "nao existe")
                    return None
        elif 'cross_platform_apps' in proj_dir:
            proj_path = proj_dir.replace('cross_platform_apps', 'native_apps')
            if not os.path.exists(proj_path):
                proj_path = proj_path.replace('native_apps', 'unknown')
                if not os.path.exists(proj_path):
                    print(proj_path, "nao existe")
                    return None
        elif 'unknown' in proj_dir:
            proj_path = proj_dir.replace('unknown', 'native_apps')
            if not os.path.exists(proj_path):
                proj_path = proj_path.replace('native_apps', 'cross_platform_apps')
                if not os.path.exists(proj_path):
                    print(proj_path, "nao existe")
                    return None
        return proj_path

    def search_and_parse_files_in_dir(self, directory_path, expected_filename="project_path.txt", only_last_commit=True, avoid_pattern='randomxzy.pattern'):
        file_list = mega_find(directory_path, pattern=expected_filename, type_file='f')
        #print(file_list)
        for filepath in file_list:
            if avoid_pattern in filepath:
                continue
            if only_last_commit and len(file_list) > 1:
                proj_dir = self.solve_project_dir(str(cat(filepath)))
                #last_commit = self.get_last_commit(proj_dir)
                #print(filepath)
                #if (proj_dir is None or (last_commit is None or last_commit not in filepath)) and (proj_dir is None or 'unknown' not in proj_dir):
                #    print('siga')
                #    continue
            self.parse_repo(filepath)


    def merge_duplicate_issues(issues_list, skip_possible_duplicates=True):
        print('initial total issues', len(issues_list))
        merged_dict = {}
        for i, reg in enumerate(issues_list):
            # issue_key = reg['issue'].get_simple_name() + reg['prev_commit_hash'] + reg['commit_hash'] + str(getattr(reg['issue'], 'file', ''))
            issue_key = reg['issue_name'] + reg['repo_dir'] + reg['file'] + (
                reg['tool'] if not skip_possible_duplicates else '')
            if skip_possible_duplicates and issue_key in merged_dict:
                # print('skipping', reg['issue_name'], 'on', reg['repo_dir'])
                # keep the longest location
                # ine = '' if 'line' not in reg['issue_location'] else reg['issue_location'].split("|")[-1]
                # mg_line = '' if 'line' not in merged_dict[issue_key]['issue_location'] else merged_dict[issue_key]['issue_location'].split("|")[-1]
                # if line != '' and mg_line != '' and 'line' in merged_dict[issue_key]['issue_location']:
                #    issue_key += f"|line:{line}"
                # elif len(reg['issue_location']) > len(merged_dict[issue_key]['issue_location']):
                if len(reg['issue_location']) > len(merged_dict[issue_key]['issue_location']):
                    merged_dict[issue_key] = reg
                else:
                    continue
            merged_dict[issue_key] = reg
        return list(merged_dict.values())

    def gen_langs_boxplots_loc_per_proj(self):
        fig1, en_box = plt.subplots()
        resdic = {}
        print(json.dumps(self.language_info, indent=1))
        for lang, val in self.language_info.items():
            print(lang, val)
            if lang not in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']:
                continue
            projs_with_lang = val['proj_files']
            new_l = []
            for proj in projs_with_lang:
                res_langs = list(filter(lambda x: x['Name'] == lang, self.proj_info[proj]['lang_info']))
                print(res_langs)
                if len(res_langs) == 0:
                    continue
                res_langs = res_langs[0]
                if 'Code' not in res_langs:
                    continue
                new_l = new_l + ([res_langs['Code']] )
                #print(res_langs)
                print("------")
            resdic[lang] = new_l
        total_loc = sum([sum(resdic[lang]) for lang in resdic.keys()])
        #resdic['all'] = [sum(resdic[lang]) for lang in resdic.keys()]
        print(resdic)
        print(total_loc)
        #print(self.proj_info)
        total_issues = sum([len(self.proj_info[proj]['issues']) for proj in self.proj_info.keys()])
        #print(total_issues)
        bp_dict = en_box.boxplot(x=list(resdic.values()),
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=8)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(resdic.keys()))
        plt.setp(xtickNames, rotation=45, fontsize=12)
        plt.suptitle("All Projects' LoC")
        plt.show()

    def gen_langs_boxplots_apd(self, only_lightweight_tools=True):
        fig1, en_box = plt.subplots()
        resdic = {}
        mdic = {}
        tpmdic = {}
        tpresdic = {}
        #print(json.dumps(self.language_info, indent=1))
        print(len(self.proj_info))
        for proj in self.proj_info.keys():
            lang_infos = self.proj_info[proj]['lang_info']
            total_loc = 0
            for lang_info in lang_infos:
                lang = lang_info['Name']
                if lang not in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']:
                    continue
                if 'Code' not in lang_info:
                    continue
                total_loc += lang_info['Code']
                #print(self.proj_info[proj]['issues'])
                #print('sapo')
            if only_lightweight_tools:
                #tp_list = [x[1] for x in self.proj_info[proj]['tp_issues'] if x[0].strip().lower() in LIGHTWEIGHT_TOOLS]
                issue_list = [x for x in self.proj_info[proj]['issues'] if getattr(x, 'detection_tool_name', '').lower() in LIGHTWEIGHT_TOOLS]
            else:
                issue_list = self.proj_info[proj]['issues']
                #tp_list = self.proj_info[proj]['tp_issues']
            resdic[proj] = len(issue_list) / (total_loc / 1000) if total_loc > 0 else 0
            density  = 0
            for x in set([str(getattr(x.issue_type, 'value', x.issue_type)) for x in issue_list]):
                density += TP_RATES.get(x, 1) * len([y for y in issue_list if str(getattr(y.issue_type, 'value', y.issue_type)) == x])
            print("density", proj, density)
            tpresdic[proj] = density / (total_loc / 1000) if total_loc > 0 else 0
        print("projetos:", len(resdic))
        for res in resdic.keys():
            if 'AndroidStudioProj' in res:
                mdic['DVibeProjs'] = mdic.get('DVibeProjs', []) + [resdic[res]]
                tpmdic['DVibeProjs'] = tpmdic.get('DVibeProjs', []) + [tpresdic[res]]
            elif 'similar_' in res:
                mdic['DSimProjs'] = mdic.get('DSimProjs', []) + [resdic[res]]
                tpmdic['DSimProjs'] = tpmdic.get('DSimProjs', []) + [tpresdic[res]]
                #mdic['DOpenProjs'] = mdic.get('DOpenProjs', []) + [resdic[res]]
                #tpmdic['DOpenProjs'] = tpmdic.get('DOpenProjs', []) + [tpresdic[res]]
            else:
                mdic['DOpenProjs'] = mdic.get('DOpenProjs', []) + [resdic[res]]
                tpmdic['DOpenProjs'] = tpmdic.get('DOpenProjs', []) + [tpresdic[res]]

        #print(mdic)
        #print(tpmdic)
        #print(tpmdic.values())
        #exit(0)

        #print(self.proj_info)
        #print(total_issues)'
        bp_dict = en_box.boxplot(x=list(mdic.values()),
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            widths=0.5
                            )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=7)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['red',  'lightblue', 'darkkhaki' ]
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])
        xtickNames = plt.setp(en_box, xticklabels=list(mdic.keys()))
        plt.setp(xtickNames, rotation=45, fontsize=8)
        plt.legend(handles=[
            plt.Line2D([0], [0], color='red', lw=4, label='DVibeProjs'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='DSimProjs'),
            plt.Line2D([0], [0], color='lightblue', lw=4, label='DOpenProjs'),

        ])
        plt.suptitle("Datasets' APDs")
        en_box.set_ylabel("APD")
        plt.show()

        # tp
        fig1, en_box = plt.subplots()
        bp_dict = en_box.boxplot(x=list(tpmdic.values()),
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 widths=0.5
                                 )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            text(x, y, '%.2f' % y, fontsize=8)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['red', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])
        #xtickNames = plt.setp(en_box, xticklabels=list(tpmdic.keys()))
        #plt.setp(xtickNames, rotation=45, fontsize=8)
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='DVibeProjs'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='DSimProjs'),

        ])
        plt.suptitle("Datasets' APDs")
        en_box.set_ylabel("APD")
        plt.show()

    def gen_projs_capd(self, only_lightweight_tools=False):
        fig1, en_box = plt.subplots()
        categs = set(z for z in ISSUE_CATEGORY_MAPPING.values() for z in z)
        empt_categs = {k: 0 for k in categs}
        cats_set = {k: {} for k in categs}
        tp_cats_set = {k: {} for k in categs}
        for proj in self.proj_info.keys():
            lang_infos = self.proj_info[proj]['lang_info']
            total_loc = 0
            for lang_info in lang_infos:
                lang = lang_info['Name']
                if lang not in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']:
                    continue
                if 'Code' not in lang_info:
                    continue
                total_loc += lang_info['Code']
                #print(self.proj_info[proj]['issues'])
                #print('sapo')
            proj_cats = empt_categs.copy()
            tp_proj_cats = empt_categs.copy()
            for iss in self.proj_info[proj]['issues']:
                tool_name = getattr(iss, 'detection_tool_name', '')
                if only_lightweight_tools and tool_name.lower() not in LIGHTWEIGHT_TOOLS:
                    continue
                issue_categs = ISSUE_CATEGORY_MAPPING.get(getattr(iss.issue_type, 'value', iss.issue_type), [])
                for categ in issue_categs:
                    proj_cats[categ] += 1
            for iss in self.proj_info[proj]['tp_issues']:
                print(iss)
                issue_categs = ISSUE_CATEGORY_MAPPING.get(iss[1].strip(), [])
                for categ in issue_categs:
                    tp_proj_cats[categ] += 1
            if 'AndroidStudioProj' in proj:
                for categ, ct in proj_cats.items():
                    vb = cats_set[categ].get('DVibeProjs', [])
                    tpvb = tp_cats_set[categ].get('DVibeProjs', [])
                    tpvb.append( tp_proj_cats.get(categ) / (total_loc / 1000) if total_loc > 0 else 0)
                    vb.append( ct / (total_loc / 1000) if total_loc > 0 else 0)
                    cats_set[categ]['DVibeProjs'] = vb
                    tp_cats_set[categ]['DVibeProjs'] = tpvb
            elif 'similar_' in proj:
                for categ, ct in proj_cats.items():
                    #print('janine', total_loc,tp_proj_cats.get(categ) )
                    vb = cats_set[categ].get('DSimProjs', [])
                    xb = cats_set[categ].get('DOpenProjs', [])
                    tpvb = tp_cats_set[categ].get('DSimProjs', [])
                    tpxb = tp_cats_set[categ].get('DOpenProjs', [])
                    tpvb.append(tp_proj_cats.get(categ) / (total_loc / 1000) if total_loc > 0 else 0)
                    tpxb.append(tp_proj_cats.get(categ) / (total_loc / 1000) if total_loc > 0 else 0)
                    vb.append(ct / (total_loc / 1000) if total_loc > 0 else 0)
                    xb.append(ct / (total_loc / 1000) if total_loc > 0 else 0)
                    cats_set[categ]['DSimProjs'] = vb
                    cats_set[categ]['DOpenProjs'] = xb
                    tp_cats_set[categ]['DSimProjs'] = tpvb
                    tp_cats_set[categ]['DOpenProjs'] = tpxb
                    #print(tp_proj_cats.get(categ) / (total_loc / 1000) if total_loc > 0 else 0,tpvb)
            else:
                for categ, ct in proj_cats.items():
                    xb = cats_set.get('DOpenProjs', [])
                    tpxb = tp_cats_set[categ].get('DOpenProjs', [])
                    tpxb.append(ct / (total_loc / 1000) if total_loc > 0 else 0)
                    xb.append(ct / (total_loc / 1000) if total_loc > 0 else 0)
                    cats_set[categ]['DOpenProjs'] = xb
                    tp_cats_set[categ]['DOpenProjs'] = tpxb
            # plot as histogram average of each of the 3 datasets per category contained in cats_set (3 bars per category)

        print(tp_cats_set)
        # ---- plotting part: 3 bars per category ----
        categories = sorted({x:v for x,v in cats_set.items() if sum(cats_set[x].get('DVibeProjs', [])) >= 0
                             and sum(tp_cats_set[x].get('DVibeProjs', [])) > 0 }.keys())
        x = np.arange(len(categories))  # x positions

        vibe_means = []
        similar_means = []
        open_means = []

        # compute means per category
        for cat in categories:
            vibe_vals = cats_set[cat].get('DVibeProjs', [])
            similar_vals = cats_set[cat].get('DSimProjs', [])
            open_vals = cats_set[cat].get('DOpenProjs', [])
            vibe_means.append(np.mean(vibe_vals) if vibe_vals else 0)
            similar_means.append(np.mean(similar_vals) if similar_vals else 0)
            open_means.append(np.mean(open_vals) if open_vals else 0)

        # draw all bars once
        width = 0.25  # width of each bar
        en_box.bar(x - width, vibe_means, width, label='DVibeProjs', color='red')
        en_box.bar(x, similar_means, width, label='DSimProjs', color='darkkhaki')
        en_box.bar(x + width, open_means, width, label='DOpenProjs', color='lightblue')

        en_box.set_xticks(x)
        en_box.set_xticklabels(categories, rotation=25, ha='right',fontsize=8)
        # label bars:
        for bar in en_box.patches:
            height = bar.get_height()
            en_box.annotate('%.3f' % height,
                            xy=(bar.get_x() + bar.get_width() / 2, min(0, .75 * height)),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            rotation=90,
                            ha='center', va='bottom', fontsize=6)
        en_box.set_ylabel('CAPD')
        en_box.set_title('Average category density per project type')
        en_box.legend()
        fig1.tight_layout()
        plt.show()

        vibe_means = []
        similar_means = []
        open_means = []

        # compute means per category
        for cat in categories:
            vibe_vals = cats_set[cat].get('DVibeProjs', [])
            similar_vals = cats_set[cat].get('DSimProjs', [])
            open_vals = cats_set[cat].get('DOpenProjs', [])
            vibe_means.append(np.mean(vibe_vals) if vibe_vals else 0)
            similar_means.append(np.mean(similar_vals) if similar_vals else 0)
            open_means.append(np.mean(open_vals) if open_vals else 0)

        # draw all bars once
        width = 0.25  # width of each bar
        en_box.bar(x - width, vibe_means, width, label='DVibeProjs')
        en_box.bar(x, similar_means, width, label='DSimProjs')
        en_box.bar(x + width, open_means, width, label='DOpenProjs')

        en_box.set_xticks(x)
        en_box.set_xticklabels(categories, rotation=45, ha='right', fontsize=6)
        # label bars:
        for bar in en_box.patches:
            height = bar.get_height()
            en_box.annotate('%.3f' % height,
                            xy=(bar.get_x() + bar.get_width() / 2, min(0, .75 * height)),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            rotation=90,
                            ha='center', va='bottom', fontsize=6)
        en_box.set_ylabel('CAPD')
        en_box.set_title('Average category density per project type (True Positives')
        en_box.legend()
        fig1.tight_layout()
        plt.show()

        fig1, en_box = plt.subplots()
        # do the same for the true positives now

        vibe_means = []
        similar_means = []

        # compute means per category
        for cat in categories:
            vibe_vals = tp_cats_set[cat].get('DVibeProjs', [])
            similar_vals = tp_cats_set[cat].get('DSimProjs', [])
            vibe_means.append(np.mean(vibe_vals) if vibe_vals else 0)
            similar_means.append(np.mean(similar_vals) if similar_vals else 0)

        # draw all bars once
        width = 0.25  # width of each bar
        en_box.bar(x + width, vibe_means, width, label='DVibeProjs', color='red')
        en_box.bar(x, similar_means, width, label='DSimProjs', color='darkkhaki')
        #en_box.bar(x + width, open_means, width, label='DOpenProjs')

        en_box.set_xticks(x)
        en_box.set_xticklabels(categories, rotation=30, ha='right')
        # label bars:
        for bar in en_box.patches:
            height = bar.get_height()
            en_box.annotate('%.3f' % height,
                            xy=(bar.get_x() + bar.get_width() / 2, min(0, .75 * height)),
                            xytext=(0, 2),  # 3 points vertical offset
                            textcoords="offset points",
                            rotation=90,
                            ha='center', va='bottom', fontsize=6)
        en_box.set_ylabel('CAPD')
        en_box.set_title('Average category density per project type')
        en_box.legend()
        fig1.tight_layout()
        plt.show()

    def gen_langs_boxplots_sfp(self, only_lightweight_tools=False):
        fig1, en_box = plt.subplots()
        resdic = {}
        tpresdic = {}
        tpm_dic = {}
        mdic = {}
        # print(json.dumps(self.language_info, indent=1))
        for proj in self.proj_info.keys():
            lang_infos = self.proj_info[proj]['lang_info']
            total_files = 0
            for lang_info in lang_infos:
                lang = lang_info['Name']
                if lang not in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']:
                    continue
                if 'Count' not in lang_info:
                    continue
                total_files += lang_info['Count']
            file_set = set()
            tp_file_set = set()
            for iss in self.proj_info[proj]['issues']:
                tool_name = getattr(iss, 'detection_tool_name', '')
                if only_lightweight_tools and tool_name.lower() not in LIGHTWEIGHT_TOOLS:
                    continue
                iss_file = getattr(iss, 'file', None)
                if iss_file is not None:
                    file_set.add(iss_file)
            for iss in self.proj_info[proj]['tp_issues']:
                tool_name = iss[0]
                if only_lightweight_tools and tool_name.lower() not in LIGHTWEIGHT_TOOLS:
                    continue
                iss_file = iss[2]
                if iss_file is not None:
                    tp_file_set.add(iss_file)
            if total_files < len(file_set) or total_files < len(tp_file_set):
                print(file_set)
                print(tp_file_set)
                print(total_files)
                exit(0)
            resdic[proj] = (total_files - len(file_set)) / total_files if total_files > 0 else 0
            tp_density = (len(file_set) * np.average(list(TP_RATES.values())))
            tpresdic[proj] = (total_files - tp_density) / total_files if total_files > 0 else 0
        for res in resdic.keys():
            if 'AndroidStudioProj' in res:
                mdic['DVibeProjs'] = mdic.get('DVibeProjs', []) + [resdic[res]]
                tpm_dic['DVibeProjs'] = tpm_dic.get('DVibeProjs', []) + [tpresdic[res]]
            elif 'similar_' in res:
                mdic['DSimProjs'] = mdic.get('DSimProjs', []) + [resdic[res]]
                tpm_dic['DSimProjs'] = tpm_dic.get('DSimProjs', []) + [tpresdic[res]]
                mdic['DOpenProjs'] = mdic.get('DOpenProjs', []) + [resdic[res]]
                #tpm_dic['DOpenProjs'] = tpm_dic.get('DOpenProjs', []) + [tpresdic[res]]
            else:
                mdic['DOpenProjs'] = mdic.get('DOpenProjs', []) + [resdic[res]]
                tpm_dic['DOpenProjs'] = tpm_dic.get('DOpenProjs', []) + [tpresdic[res]]
        # print(self.proj_info)
        # print(total_issues)'
        #print(mdic)
        #print(tpm_dic)

        bp_dict = en_box.boxplot(x=list(mdic.values()),
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 widths=0.5
                                 )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['red',  'lightblue', 'darkkhaki' ]
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])
        #xtickNames = plt.setp(en_box, xticklabels=list(mdic.keys()))
        #plt.setp(xtickNames, rotation=45, fontsize=6)
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='DVibeProjs'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='DSimProjs'),
            plt.Line2D([0], [0], color='red', lw=4, label='DOpenProjs'),

        ])
        plt.suptitle("Datasets' SFP")
        en_box.set_ylabel("SFP")
        plt.show()

        #tp
        fig1, en_box = plt.subplots()
        bp_dict = en_box.boxplot(x=list(tpm_dic.values()),
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 widths=0.5
                                 )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['red', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])
        #xtickNames = plt.setp(en_box, xticklabels=list(tpm_dic.keys()))
        #plt.setp(xtickNames, rotation=45, fontsize=6)
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='DVibeProjs'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='DSimProjs'),


        ])
        plt.suptitle("Datasets' SFP")
        en_box.set_ylabel("SFP")
        plt.show()

    def gen_langs_boxplots_loc_per_file(self):
        fig1, en_box = plt.subplots()
        resdic = {}
        #print(self.language_info)
        for lang, val in self.language_info.items():
            print(lang, val)
            if lang not in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']:
                continue
            projs_with_lang = val['proj_files']
            new_l = []
            for proj in projs_with_lang:
                res_langs = list(filter(lambda x: x['Name'] == lang, self.proj_info[proj]['lang_info']))
                print(res_langs)
                if len(res_langs) == 0:
                    continue
                res_langs = res_langs[0]
                if 'Code' not in res_langs:
                    continue
                new_l = new_l + ([res_langs['Code'] / res_langs['Count']])
                # print(res_langs)
                print("------")
            resdic[lang] = new_l
        total_loc = sum([sum(resdic[lang]) for lang in resdic.keys()])
        # resdic['all'] = [sum(resdic[lang]) for lang in resdic.keys()]
        print(resdic)
        print(total_loc)
        # print(self.proj_info)
        #total_issues = sum([len(self.proj_info[proj]['issues']) for proj in self.proj_info.keys()])
        # print(total_issues)
        bp_dict = en_box.boxplot(x=list(resdic.values()),
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=8)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(resdic.keys()))
        plt.setp(xtickNames, rotation=45, fontsize=6)
        plt.suptitle("All Projects' LoC")
        plt.show()



    x='''
    bp_dict = plt.boxplot(the_list, self.language_info.keys(),  patch_artist=True)
    i = 0
    for line in bp_dict['medians']:
        x, y = line.get_xydata()[1]  # top of median line
        xx, yy = line.get_xydata()[0]
        text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
        # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
        i = i + 1

    # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['boxes']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])

    xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
    plt.setp(xtickNames, rotation=90, fontsize=5)
    plt.show()'''

    def gen_langs_boxplots_cc(self):
        fig1, en_box = plt.subplots()
        resdic = {}
        for lang, val in self.language_info.items():
            #print(val)
            projs_with_lang = val['proj_files']
            new_l = []
            for proj in projs_with_lang:
                res_langs = list(filter(lambda x: x['Name'] == lang, self.proj_info[proj]['lang_info']))
                if len(res_langs) == 0:
                    continue
                res_langs = res_langs[0]
                if 'Complexity' not in res_langs:
                    continue
                new_l = new_l + [res_langs['Complexity']]
                #print(res_langs)
                print("------")
            resdic[lang] = new_l

        bp_dict = en_box.boxplot(x=list(resdic.values()),
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(resdic.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' CC")
        plt.show()


    def gen_langs_boxplots_total_files(self):
        fig1, en_box = plt.subplots()
        the_list = [list(map(lambda z: z['Count'], x)) for x in
                    map(lambda t: t['proj_files'], self.language_info.values())]

        bp_dict = en_box.boxplot(x=the_list,
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=12)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' #Files")
        plt.show()

    def gen_stats(self):
        print(json.dumps(self.language_info, indent=1))

    def plot_language_histogram(self):
        langs = list(self.language_info.keys())
        proj_counts = [self.language_info[lang]['proj_count'] for lang in langs]
        plt.figure(figsize=(10, 6))
        plt.bar(langs, proj_counts, color='skyblue')
        plt.xlabel('Programming Languages')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per Language' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        # label histogram
        for i in range(len(proj_counts)):
            if proj_counts[i] > 0:
                plt.text(i, proj_counts[i], str(proj_counts[i]), ha='center', va='bottom')
        plt.tight_layout()
        plt.show()



    def gen_langs_pure_histogram(self, discriminate_play=True):
        if not discriminate_play:
            langs = [x for x in self.pure_native.keys()] + [x for x in self.cross.keys()]
            proj_counts = [len(self.pure_native[lang]) for lang in self.pure_native.keys()] + [len(self.cross[lang]) for lang in self.cross.keys()]
        else:
            langs = []
            proj_counts = []
            for l, projs in self.pure_native.items():
                play_c = len([x for x in projs if self.proj_info[x]['is_on_play_store']])
                langs.append(l)
                proj_counts.append(len(self.pure_native[l]))
                langs.append(l+'_play')
                proj_counts.append(play_c)
            for l, projs in self.cross.items():
                play_c = len([x for x in projs if self.proj_info[x]['is_on_play_store']])
                langs.append(l)
                proj_counts.append(len(self.cross[l]))
                langs.append(l + '_play')
                proj_counts.append(play_c)
        #proj_counts = [self.language_info[lang]['proj_count'] for lang in langs]
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(langs, proj_counts)
        colors = ['lightblue', 'darkkhaki']
        i = 1
        for bar in bar_dict:
            i = i + 1
            bar.set_facecolor(colors[i % len(colors)])
        plt.xlabel('Pure  Projects')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects containing only one language' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        # put labels on each bar
        for i in range(len(proj_counts)):
            if proj_counts[i] > 0:
                plt.text(i, proj_counts[i], str(proj_counts[i]), ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

    def gen_cross_play_histogram(self):
        langs = ['native', 'native_play', 'cross', 'cross_play']
        proj_counts = [
            len([x for x in self.proj_info.values() if x['is_native']]),
            len([x for x in self.proj_info.values() if x['is_native'] and x['is_on_play_store']]),
            len([x for x in self.proj_info.values() if not x['is_native']]),
            len([x for x in self.proj_info.values() if not x['is_native'] and x['is_on_play_store']]),
        ]
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(langs, proj_counts)
        colors = ['lightblue', 'darkkhaki']
        i = 1
        for bar in bar_dict:
            i = i + 1
            bar.set_facecolor(colors[i % len(colors)])
        plt.xlabel('Pure  Projects')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects containing only one language' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        # put labels on each bar
        for i in range(len(proj_counts)):
            if proj_counts[i] > 0:
                plt.text(i, proj_counts[i], str(proj_counts[i]), ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_age(self):
        """generates a histogram of the age of the apps."""
        age_years = {}
        #age_years = set([datetime.datetime.fromtimestamp(x['last_app_update']/1000).year for x in self.proj_info.values()])
        for proj in self.proj_info.values():
            year = proj['last_app_update_year']
            if year == 1970:
                continue
            age_years[year] = age_years[year] + 1 if year in age_years else 1

        #proj_counts = [len([x for x in self.proj_info.values() if datetime.datetime.fromtimestamp(x['last_app_update']/1000).year == y]) for y in age_years]
        plt.figure(figsize=(10, 6))
        plt.bar(age_years.keys(), age_years.values(), color='skyblue')
        for i in age_years.keys():
            plt.text(i, age_years[i], str(age_years[i]), ha='center', va='bottom')
        plt.xlabel('Years')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per Year (Last Update)' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(list(age_years.keys()), rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_age_play(self):
        """generates a histogram of the age of the apps."""
        age_years = {}
        #age_years = set([datetime.datetime.fromtimestamp(x['last_app_update']/1000).year for x in self.proj_info.values()])
        for proj in self.proj_info.values():
            year = proj['last_app_update_year']
            print(year)
            if year == 1970:
                continue
            if proj['is_on_play_store']:
                key = f"{year}_play"
                age_years[key] = age_years[key] + 1 if key in age_years else 1
            age_years[str(year)] = age_years[str(year)] + 1 if str(year) in age_years else 1
        for f in list(age_years.keys()):
            if 'play' not in f and f"{f}_play" not in age_years:
                age_years[f + '_play'] = 0
        age_years = {k: v for k, v in sorted(age_years.items())}
        #proj_counts = [len([x for x in self.proj_info.values() if datetime.datetime.fromtimestamp(x['last_app_update']/1000).year == y]) for y in age_years]
        plt.figure(figsize=(10, 6))
        colors = ['lightblue', 'darkkhaki']
        bar_dict = plt.bar(age_years.keys(), age_years.values())
        for i in age_years.keys():
            plt.text(i, age_years[i], str(age_years[i]), ha='center', va='bottom')
        i = 1
        for bar in bar_dict:
            i = i + 1
            bar.set_facecolor(colors[i % len(colors)])

        plt.xlabel('Years')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per Year')
        plt.xticks(list(age_years.keys()), rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def get_plot_projs_per_category(self):
        # generate histogram of number of total projs per app category
        # get all categories
        categories = {}
        for proj, proj_d in self.proj_info.items():
            categ = proj_d['app_category']
            if categ is None or len(categ) == 0:
                continue
            for cat in categ:
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(proj)
        # count the number of distinct projs per category
        categories_count = {}
        for cat, projs in categories.items():
            categories_count[cat] = len(projs)
        # sort the categories_count dictionary by value
        categories_count = dict(sorted(categories_count.items(), key=lambda item: item[1]))
        # plot the categories_count dictionary
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(categories_count.keys(), categories_count.values())
        for i in categories_count.keys():
            plt.text(i, categories_count[i], str(categories_count[i]), ha='center', va='bottom')
        plt.xlabel('App Categories')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per App Category' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()


    def gen_pie_categories(self):
        # generate a pie chart of number of total projs per app category
        # get all categories
        categories = {}
        for proj, proj_d in self.proj_info.items():
            categ = proj_d['app_category']
            if categ is None or len(categ) == 0:
                continue
            for cat in categ:
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(proj)
        # count the number of distinct projs per category
        categories_count = {}
        for cat, projs in categories.items():
            categories_count[cat] = len(projs)
        # sort the categories_count dictionary by value
        categories_count = dict(sorted(categories_count.items(), key=lambda item: item[1]))
        # plot the categories_count dictionary
        plt.figure(figsize=(10, 6))
        plt.pie(categories_count.values(), labels=categories_count.keys(), autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title('Number of Projects per App Category' + f" (Total Projects: {len(self.proj_info)})")
        plt.tight_layout()
        plt.show()



    def get_plot_issues_per_category(self):
        # generate a histogram of number of total of distinct issues per app category
        # get all categories
        categories = {}
        for proj, proj_d in self.proj_info.items():
            categ = proj_d['app_category']
            if categ is None or len(categ) == 0:
                continue
            for cat in categ:
                if cat not in categories:
                    categories[cat] = []
            for issue in proj_d['issues']:
                if issue is None or issue.issue_type is None:
                    continue
                issue_name = getattr(issue.issue_type, 'value', issue.issue_type).strip().lower()
                if issue_name.lower() == 'syntaxerror':
                    continue
                for cat in categ:
                    categories[cat].append(issue_name)
        # count the number of distinct issues per category
        categories_count = {}
        for cat, issues in categories.items():
            categories_count[cat] = len(issues)
        # sort the categories_count dictionary by value
        categories_count = dict(sorted(categories_count.items(), key=lambda item: item[1]))
        # plot the categories_count dictionary
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(categories_count.keys(), categories_count.values())
        for i in categories_count.keys():
            plt.text(i, categories_count[i], str(categories_count[i]), ha='center', va='bottom')
        plt.xlabel('App Categories')
        plt.ylabel('Number of Distinct Issues')
        plt.title('Number of Distinct Issues per App Category' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()




    def gen_plot_apps_loc_per_model(self):
        # generate a boxplot of the number of lines of code per model (if the projdir contains gpt or gemini)
        loc_per_model = {}
        #print(self.proj_info)
        for proj, proj_d in self.proj_info.items():
            print(proj)
            if 'gpt' in proj.lower():
                model = 'GPT-4o'
            else:
                model = 'Gemini_Pro_2.5'
            loc = sum([x['Code'] for x in proj_d['lang_info'] if x['Name'] in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']])
            if model not in loc_per_model:
                loc_per_model[model] = []
            loc_per_model[model].append(loc)
        plt.figure(figsize=(10, 6))
        # start y axis at 0
        plt.ylim(0, max([max(x) for x in loc_per_model.values()]) * 1.1)
        boxes = plt.boxplot(loc_per_model.values(), patch_artist=True,
                            labels=loc_per_model.keys(), widths=0.6)
        # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in boxes['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])
        # add labels
        for i in range(len(loc_per_model.keys())):
            plt.text(i + 1, boxes['medians'][i].get_ydata()[0],
                     str(float(boxes['medians'][i].get_ydata()[0])), ha='center', va='bottom', fontsize=8, rotation=45, zorder=100)
        plt.ylabel('LoC')
        plt.title('Number of Lines of Code per Model' + f" (Total Projects: {len(self.proj_info)})")
        #plt.xticks(rotation=45, ha='right')
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='GPT4o'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='Gemini_Pro_2')
        ])
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_loc_per_dataset(self):
        # generate a boxplot of the number of lines of code per model (if the projdir contains gpt or gemini)
        loc_per_model = {}
        #print(self.proj_info)
        for proj, proj_d in self.proj_info.items():
            print(proj)
            if 'ndroidstudiopro' in proj.lower():
                    model = 'DVibeProjs'
            elif 'similar_' in proj.lower():
                model = 'DSimProjs'
            else:
                model = 'DOpenProjs'

            loc = sum([x['Code'] for x in proj_d['lang_info'] if x['Name'] in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']]) / 1000
            if model not in loc_per_model:
                loc_per_model[model] = []
            loc_per_model[model].append(loc)
        plt.figure(figsize=(10, 6))
        # start y axis at 0
        plt.ylim(0, max([max(x) for x in loc_per_model.values()]) * 1.1)
        boxes = plt.boxplot(loc_per_model.values(), patch_artist=True,
                            labels=loc_per_model.keys(), widths=0.6)
        # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in boxes['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])
        # add labels
        for i in range(len(loc_per_model.keys())):
            plt.text(i + 1, boxes['medians'][i].get_ydata()[0],
                     str(float(boxes['medians'][i].get_ydata()[0])), ha='center', va='bottom', fontsize=8, rotation=45, zorder=100)
        plt.ylabel('KLoC')
        plt.title('Number of Lines of Code per Dataset' + f" (Total Projects: {len(self.proj_info)})")
        #plt.xticks(rotation=45, ha='right')
        plt.legend(handles=[
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='DOpenProjs'),
            plt.Line2D([0], [0], color='lightblue', lw=4, label='DSimProjs'),
            plt.Line2D([0], [0], color='red', lw=4, label='DVibeProjs'),
        ])
        plt.tight_layout()
        plt.show()

    # issues
    def gen_plot_apps_issues(self):
        #all_issues = set()
        issues_dict = {}
        for proj, proj_d in self.proj_info.items():
            for issue in proj_d['issues']:
                if issue is None or issue.issue_type is None:
                    continue
                #all_issues.add(issue.issue_type)
                issue_name = getattr(issue.issue_type, 'value', issue.issue_type).strip().lower()
                orig_name = issue_name
                if issue_name.lower() == 'syntaxerror':
                    continue
                print(proj, issue_name)
                if 'ndroidstudiopro' in proj.lower():
                    issue_name = issue_name + '_vibe'
                elif 'similar_' in proj.lower():
                    issue_name = issue_name + '_similar'
                else:
                    continue
                issues_dict[issue_name] = issues_dict.get(issue_name, set()).union({proj})
        print('jasus')
        print(issues_dict)
        # sort the issues_dict alphabetically
        #issues_dict = dict(sorted(issues_dict.items(), key=lambda item: item[0]))
        #colors = ['lightblue', 'darkkhaki']

        issues_dict = dict(sorted(issues_dict.items(), key=lambda item: item[0]))
        colors = ['lightblue', 'darkkhaki']
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(issues_dict.keys(), [len(x) for x in issues_dict.values()])
        # change x axis labels to remove '_vibe' and '_similar'

        for i in issues_dict.keys():
            plt.text(i, len(issues_dict[i]), str(len(issues_dict[i])), ha='center', va='bottom', rotation=90)
        i = 0
        for bar, issue_name in zip(bar_dict, issues_dict.keys()):
            if '_vibe' in issue_name:
                bar.set_facecolor('lightblue')
            elif '_similar' in issue_name:
                bar.set_facecolor('darkkhaki')
        plt.xlabel('PAPs')
        plt.ylabel('#Projects')
        plt.title('Project count per PAP')
        # Modify x-axis labels to remove '_vibe' and '_similar'
        cleaned_labels = [label.replace('_vibe', '').replace('_similar', '') for label in issues_dict.keys()]
        plt.xticks(ticks=range(len(cleaned_labels)), labels=cleaned_labels, rotation=45, ha='right', fontsize=6)
        # add legend for the colors
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='vibe dataset'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='similar dataset')
        ])
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_issues_occurrences(self, only_lightweight_tools=False):
        #all_issues = set()
        issues_dict = {}
        for proj, proj_d in self.proj_info.items():
            for issue in proj_d['issues']:
                if issue is None or issue.issue_type is None:
                    continue
                #all_issues.add(issue.issue_type)
                issue_name = getattr(issue.issue_type, 'value', issue.issue_type).strip()
                if issue_name.lower() == 'syntaxerror' or issue_name in TO_EXCLUDE:
                    continue
                tool_name = getattr(issue, 'detection_tool_name', '')
                if only_lightweight_tools and tool_name.lower() not in LIGHTWEIGHT_TOOLS:
                    continue
                issue_name = issue_name.lower()
                if 'ndroidstudiopro' in proj.lower():
                    issue_name = issue_name + '_vibe'
                elif 'similar_' in proj.lower():
                    issue_name = issue_name + '_similar'
                else:
                    issue_name = issue_name + '_open'
                issues_dict[issue_name] = issues_dict.get(issue_name, 0) + 1

                '''if 'gpt' in proj.lower():
                    issue_name = issue_name + '_gpt'
                else:
                    issue_name = issue_name + '_gemini'
                if issue_name not in issues_dict:
                    # issues_dict[issue_name ] = set()
                    if issue_name + '_gpt' not in issues_dict:
                        issues_dict[orig_name + '_gpt'] = set()
                    if issue_name + '_gemini' not in issues_dict:
                        issues_dict[orig_name + '_gemini'] = set()'''

        # Cap bar heights and prepare data for plotting
        plt.figure(figsize=(10, 6))
        plt.ylim(0, 300)

        # Group issues by their prefix and suffix
        grouped_issues = {}
        suffixes = ['_vibe', '_similar', '_open']  # Add other suffixes if needed
        for issue_name, count in issues_dict.items():
            prefix = issue_name.split('_')[0]  # Extract the prefix
            suffix = next((s for s in suffixes if issue_name.endswith(s)), None)
            if suffix:
                if prefix not in grouped_issues:
                    grouped_issues[prefix] = {s: 0 for s in suffixes}
                grouped_issues[prefix][suffix] += count

        # Prepare data for stacked bar plot
        x_labels = list(grouped_issues.keys())
        bar_positions = range(len(x_labels))
        bar_heights = {suffix: [min(grouped_issues[prefix][suffix], 300) for prefix in x_labels] for suffix in suffixes}
        original_heights = {suffix: [grouped_issues[prefix][suffix] for prefix in x_labels] for suffix in suffixes}

        # Plot stacked bars
        colors = ['red', 'darkkhaki', 'lightblue']  # Colors for each suffix
        bottom = [0] * len(x_labels)  # Initialize bottom for stacking
        for i, suffix in enumerate(suffixes):
            bars = plt.bar(bar_positions, bar_heights[suffix], bottom=bottom, color=colors[i], label=suffix)
            # Add labels for each segment
            for bar, height, btm, original_height in zip(bars, bar_heights[suffix], bottom, original_heights[suffix]):
                if height > 0:
                    label = str(original_height) if original_height > 300 else str(height)
                    plt.text(bar.get_x() + bar.get_width() / 2, min(btm + min(height, 300) / 4, 300), label,
                             ha='center', va='center', fontsize=6, rotation=90, zorder=100 )
            bottom = [sum(x) for x in zip(bottom, bar_heights[suffix])]  # Update bottom for next stack


        # Add labels and legend
        plt.xlabel('PAPs')
        plt.ylabel('# Occurrences')
        #plt.title('# Occurrences per PAP')
        plt.xticks(bar_positions, x_labels, rotation=30, ha='right', fontsize=9)
        #plt.legend(title='Issue Variants', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='open dataset'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='similar dataset'),
            plt.Line2D([0], [0], color='red', lw=4, label='vibe dataset')
        ])
        plt.tight_layout()
        plt.show()

    def gen_manual_proj_histogram(self):
        di = {
        "FlappyBird": 29,
        "GPTFlappyBird": 12,
        "GPTGame2048": 23,
        "GPTPhotoGallery": 7,
        "GPTScientificCalculator": 14,
        "GPTToDoNotes": 16,
        "GPTWeather": 4,
        "GalleryApp": 6,
        "ScientificCalculator": 11,
        "ToDoNotes": 8,
        "WeatherApp": 11,
        "game2048": 30,
        "FlappyBird_tp": 23,
        "GPTFlappyBird_tp": 10,
        "GPTGame2048_tp": 20,
        "GPTPhotoGallery_tp": 5,
        "GPTScientificCalculator_tp": 14,
        "GPTToDoNotes_tp": 9,
        "GPTWeather_tp": 3,
        "GalleryApp_tp": 3,
        "ScientificCalculator_tp": 10,
        "ToDoNotes_tp": 6,
        "WeatherApp_tp": 10,
        "game2048_tp": 27
        }
        plt.figure(figsize=(10, 6))
        # sort the issues_dict alphabetically
        di = dict(sorted(di.items(), key=lambda item: item[0]))
        bar_dict = plt.bar(di.keys(), di.values())
        for i in di.keys():
            plt.text(i, di[i], str(di[i]), ha='center', va='bottom')
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bar in bar_dict:
            bar.set_facecolor(colors[i % len(colors)])
            i = i + 1
        plt.xlabel('Projects')
        plt.ylabel('Number of Projects')
        plt.title('Number of Issues per Project ' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        plt.legend(handles=[
            plt.Line2D([0], [0], color='lightblue', lw=4, label='Detected Instances'),
            plt.Line2D([0], [0], color='darkkhaki', lw=4, label='True Positives')
        ])
        plt.tight_layout()
        plt.show()

    def gen_manual_issue_tp_histogram(self):
        di = {
        "AppendCharacterWithChar": 7,
        "AvoidFileStream": 5,
        "AvoidInstantiatingObjectsInLoops": 9,
        "DataTransmissionWithoutCompression": 5,
        "DrawAllocation": 2,
        "DroppedData": 14,
        "InefficientWeight": 1,
        "LeakingInnerClass": 4,
        "LeakingThread": 2,
        "LogConditional": 7,
        "MemberIgnoringMethod": 17,
        "MergeRootFrame": 1,
        "NoLowMemoryResolver": 13,
        "Overdraw": 2,
        "RedundantFieldInitializer": 9,
        "SlowForLoop": 5,
        "SyntheticAccessor": 58,
        "TooFewBranchesForSwitch": 1,
        "UnclosedCloseable": 1,
        "UnusedIds": 1,
        "UnusedResources": 7,
        "AppendCharacterWithChar_tp": 7,
        "AvoidFileStream_tp": 5,
        "DataTransmissionWithoutCompression_tp": 0,
        "MergeRootFrame_tp": 1,
        "AvoidInstantiatingObjectsInLoops_tp": 8,
        "SlowForLoop_tp": 0,
        "DrawAllocation_tp": 1,
        "DroppedData_tp": 14,
        "InefficientWeight_tp": 1,
        "LeakingInnerClass_tp": 1,
        "UnclosedCloseable_tp": 0,
        "LeakingThread_tp": 2,
        "LogConditional_tp": 7,
        "MemberIgnoringMethod_tp": 4,
        "NoLowMemoryResolver_tp": 13,
        "Overdraw_tp": 2,
        "RedundantFieldInitializer_tp": 9,
        "SyntheticAccessor_tp": 57,
        "TooFewBranchesForSwitch_tp": 1,
        "UnusedIds_tp": 1,
        "UnusedResources_tp": 7
        }
        plt.figure(figsize=(10, 6))
        # sort the issues_dict alphabetically
        di = dict(sorted(di.items(), key=lambda item: item[0]))
        bar_dict = plt.bar(di.keys(), di.values())
        for i in di.keys():
            plt.text(i, di[i], str(di[i]), ha='center', va='bottom')
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bar in bar_dict:
            bar.set_facecolor(colors[i % len(colors)])
            i = i + 1
        plt.xlabel('Issues')
        plt.ylabel('Number of Issues')
        plt.title('Unique occurrences of Issues ' + f" (Total Projects: {len(self.proj_info)})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def gen_plot_app_play_issues(self):
        # plot a box plot displaying on median how many distinct issues there are in play store apps vs non store apps
        play_store_issues = []
        non_play_store_issues = []

        for proj, proj_d in self.proj_info.items():
            distinct_issues = len(set([getattr(issue.issue_type, 'value', issue.issue_type).strip().lower() for issue in proj_d['issues'] if issue and issue.issue_type]))
            if proj_d['is_on_play_store']:
                play_store_issues.append(distinct_issues)
            else:
                non_play_store_issues.append(distinct_issues)

        data = [play_store_issues, non_play_store_issues]
        plt.figure(figsize=(10, 6))
        boxes = plt.boxplot(data, patch_artist=True, labels=['Play Store Apps', 'Non-Play Store Apps'])
        # plot median on each box
        for i in range(len(data)):
            plt.text(i + 1, boxes['medians'][i].get_ydata()[0],
                     str(int(boxes['medians'][i].get_ydata()[0])), ha='center', va='bottom')
        plt.ylabel('Number of Distinct Issues')
        plt.title('Median Number of Distinct Issues in Play Store Apps vs Non-Play Store Apps')
        plt.show()


    def gen_plot_app_play_issues_occurrences_critical(self):
        # plot a box plot displaying on median how many issues there are in play store apps vs non store apps
        play_store_issues = []
        non_play_store_issues = []
        for proj, proj_d in self.proj_info.items():
            issues = [x for x in proj_d['issues'] if is_critical_issue(getattr(x.issue_type, 'value', x.issue_type ))]
            issue_c = len(issues)
            if proj_d['is_on_play_store']:
                play_store_issues.append(issue_c)
            else:
                non_play_store_issues.append(issue_c)

        data = [play_store_issues, non_play_store_issues]
        plt.figure(figsize=(10, 6))
        boxes = plt.boxplot(data, patch_artist=True, labels=['Play Store Apps', 'Non-Play Store Apps'])
        # plot median on each box
        for i in range(len(data)):
            plt.text(i + 1, boxes['medians'][i].get_ydata()[0],
                     str(int(boxes['medians'][i].get_ydata()[0])), ha='center', va='bottom')
        plt.ylabel('Number of Distinct Critical Issues')
        plt.title('Median Number of occurences of critical Issues in Play Store Apps vs Non-Play Store Apps')
        plt.show()


    def gen_plot_app_play_issues_occurrences(self):
        # plot a box plot displaying on median how many issues there are in play store apps vs non store apps
        play_store_issues = []
        non_play_store_issues = []
        for proj, proj_d in self.proj_info.items():
            issue_c = len(proj_d['issues'])
            if proj_d['is_on_play_store']:
                play_store_issues.append(issue_c)
            else:
                non_play_store_issues.append(issue_c)

        data = [play_store_issues, non_play_store_issues]
        plt.figure(figsize=(10, 6))
        boxes = plt.boxplot(data, patch_artist=True, labels=['Play Store Apps', 'Non-Play Store Apps'])
        for i in range(len(data)):
            plt.text(i + 1, boxes['medians'][i].get_ydata()[0],
                     str(int(boxes['medians'][i].get_ydata()[0])), ha='center', va='bottom')
        plt.ylabel('#occurrence of Issues')
        plt.title('Median Number of Issues in Play Store Apps vs Non-Play Store Apps')
        plt.show()


    def gen_plot_issues_per_year(self):
        issues_per_year = {}
        for proj, proj_d in self.proj_info.items():
            year = proj_d['last_app_update_year']
            if year == 1970:
                continue
            distinct_issues = len(set([getattr(issue.issue_type, 'value', issue.issue_type).strip().lower() for issue in proj_d['issues'] if issue and issue.issue_type]))
            if year in issues_per_year:
                issues_per_year[year].append(distinct_issues)
            else:
                issues_per_year[year] = [distinct_issues]

        years = sorted(issues_per_year.keys())

        plt.figure(figsize=(10, 6))
        boxes = plt.boxplot([issues_per_year[y] for y in years], patch_artist=True, tick_labels=years)
        # plot median on each box
        for i in range(len(years)):
            plt.text(i + 1, boxes['medians'][i].get_ydata()[0],
                     str(int(boxes['medians'][i].get_ydata()[0])), ha='center', va='bottom')
        plt.xlabel('Year')
        plt.ylabel('Number of Distinct Issues')
        plt.title('Number of Distinct Issues per Year of Last Update')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def gen_issues_per_tool(self):
        # plot a histogram of the number of issues detected by each tool
        issues_per_tool = {}
        for proj, proj_d in self.proj_info.items():
            for issue in proj_d['issues']:
                if issue is None or issue.issue_type is None:
                    continue
                issue_tool = issue.detection_tool_name
                if issue_tool is None:
                    continue
                if issue_tool not in issues_per_tool:
                    issues_per_tool[issue_tool] = 0
                issues_per_tool[issue_tool] += 1
        # sort the issues_per_tool dictionary by value
        issues_per_tool = dict(sorted(issues_per_tool.items(), key=lambda item: item[1]))
        # plot the issues_per_tool dictionary
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(issues_per_tool.keys(), issues_per_tool.values())
        for i in issues_per_tool.keys():
            plt.text(i, issues_per_tool[i], str(issues_per_tool[i]), ha='center', va='bottom')
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bar in bar_dict:
            bar.set_facecolor(colors[i % len(colors)])
            i = i + 1
        plt.xlabel('Tools')
        plt.ylabel('Number of Issues')
        plt.title('Number of Issues per Tool')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def plot_agg_categories(self):
        fig1, en_box = plt.subplots()
        resdic = {}
        # convert categories of ISSUE_CATEGORY_MAPPING into a set
        categs = set(z for z in ISSUE_CATEGORY_MAPPING.values() for z in z)
        empt_categs = {k:0 for k in categs}
        empt_categs_set = {k: set() for k in categs}
        mdic = {'DVibeProjs': empt_categs.copy(), 'DSimProjs': empt_categs.copy(), 'DOpenProjs': empt_categs.copy()}
        proj_count_dic = {'DVibeProjs': empt_categs_set.copy(), 'DSimProjs': empt_categs_set.copy(), 'DOpenProjs': empt_categs_set.copy()}
        # print(json.dumps(self.language_info, indent=1))
        for proj in self.proj_info.keys():
            lang_infos = self.proj_info[proj]['lang_info']
            total_loc = 0
            for lang_info in lang_infos:
                lang = lang_info['Name']
                if lang not in ['Java', 'Kotlin', 'Groovy', 'XML', 'Gradle']:
                    continue
                if 'Code' not in lang_info:
                    continue
                total_loc += lang_info['Code']
                # print(self.proj_info[proj]['issues'])
                # print('sapo')
            cat_set = set()
            for iss in self.proj_info[proj]['issues']:
                issue_categs = ISSUE_CATEGORY_MAPPING.get(getattr(iss.issue_type, 'value', iss.issue_type), [])
                for categ in issue_categs:
                    if 'AndroidStudioProj' in proj:
                        mdic['DVibeProjs'][categ] = mdic['DVibeProjs'].get(categ, 0) + 1
                        proj_count_dic['DVibeProjs'][categ] = proj_count_dic['DVibeProjs'].get(categ, set()).union({proj})
                    elif 'similar_' in proj:
                        proj_count_dic['DSimProjs'][categ] = proj_count_dic['DSimProjs'].get(categ, set()).union({proj})
                        mdic['DSimProjs'][categ] = mdic['DSimProjs'].get(categ, 0) + 1
                        proj_count_dic['DOpenProjs'][categ] = proj_count_dic['DOpenProjs'].get(categ, set()).union({proj})
                        mdic['DOpenProjs'][categ] = mdic['DOpenProjs'].get(categ, 0) + 1
                    else:
                        proj_count_dic['DOpenProjs'][categ] = proj_count_dic['DOpenProjs'].get(categ, set()).union({proj})
                        mdic['DOpenProjs'][categ] = mdic['DOpenProjs'].get(categ, 0) + 1

        # sort categs of mdic alphabetically
        mdic = {k: dict(sorted(v.items(), key=lambda item: item[0])) for k, v in mdic.items()}
        proj_count_dic = {k: dict(sorted(v.items(), key=lambda item: item[0])) for k, v in proj_count_dic.items()}
        for k in proj_count_dic.keys():
            ct_list = []
            pc_list = []
            for cat in proj_count_dic[k].keys():
                print('projcount', k, cat, len(proj_count_dic[k][cat]))
                print('issue_count', k, cat, mdic[k][cat])
                pc_list.append(len(proj_count_dic[k][cat]))
                ct_list.append(mdic[k][cat])
            print(pc_list)
            print(ct_list)
            print('---')

def main(lookup_dir):
    #lookup_dir = "/Users/ruirua/repos/pyAnaDroid/demoProjects"
    #build_scc_json_for_all_projs(lookup_dir)
    ls = LanguageStats()
    ls.search_and_parse_files_in_dir(lookup_dir, only_last_commit=True, avoid_pattern='anadroid_bef_22_results')
    #ls.gen_pie_categories()
    #ls.gen_stats()
    #print(json.dumps(ls.language_info, indent=1))
    #ls.plot_language_histogram()
    #ls.gen_langs_boxplots_loc_per_proj()
    #ls.gen_manual_proj_histogram()
    #ls.gen_plot_apps_loc_per_model()
    #ls.gen_plot_apps_loc_per_dataset()
    #exit(0)
    only_light = True
    #ls.gen_langs_boxplots_apd(only_lightweight_tools=only_light)
    #ls.gen_projs_capd(only_lightweight_tools=only_light)
    #ls.gen_langs_boxplots_sfp(only_lightweight_tools=only_light)
    #ls.gen_plot_apps_issues()
    #ls.plot_agg_categories()
    ls.gen_plot_apps_issues_occurrences(only_lightweight_tools=only_light)
    exit(0)
    ls.gen_langs_boxplots_loc_per_file()
    #return

    ls.gen_manual_proj_histogram()
    ls.gen_manual_issue_tp_histogram()
    ls.gen_langs_boxplots_cc()
    ls.gen_langs_boxplots_total_files()
    '''ls.gen_langs_pure_histogram()
    ls.gen_cross_play_histogram()
    ls.get_plot_projs_per_category()
    ls.get_plot_issues_per_category()
    '''
    #ls.gen_issues_per_tool()

    #ls.gen_plot_app_play_issues_occurrences_critical()
    #ls.gen_plot_apps_age_play()
    #ls.gen_plot_apps_age()
    #ls.gen_plot_apps_issues()
    #ls.gen_plot_apps_issues()
    #ls.gen_plot_apps_issues_occurrences()


    #ls.gen_plot_app_play_issues()
    #ls.gen_plot_app_play_issues_occurrences()
    #ls.gen_plot_issues_per_year()
    #plot_true_positives()

def plot_true_positives(filepath="classified_regressions.csv"):
    # get true positives
    if not os.path.exists(filepath):
        print("file not found", filepath)
        return
    tps = {}
    with open(filepath, 'r') as jj:
        reader = csv.reader(jj, delimiter=';')
        next(reader)
        for row in reader:
            issue_name = row[0].strip().lower()
            is_tp = row[-1].strip().lower() == 'true_positive'
            if is_tp:
                tps[issue_name] = tps[issue_name] + 1 if issue_name in tps else 1
        #info = json.load(jj)
    #print(tps)
    plt.bar(tps.keys(), tps.values(), color='skyblue')
    plt.xlabel('Issues')
    plt.ylabel('Number of TPs')
    plt.title('Number of TPs per issue')
    for i, issue in enumerate(tps.keys()):
        plt.text(i, tps[issue], str(tps[issue]), ha='center', va='bottom')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


def is_critical_issue(issue_name):
    if issue_name is None:
        return False
    issue_id = issue_name.strip().lower()
    critical_issues = ['wakelock', 'drawallocation', 'uioverdraw', 'viewholder', 'nestedweight']
    return issue_id in critical_issues


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("error. provide input dir")
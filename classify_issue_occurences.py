import csv
import os.path
import time
import traceback
from functools import reduce

import tiktoken
from dotenv import dotenv_values
from anadroid.utils.Utils import execute_shell_command, loge, logs, logi
from together import Together
from openai import OpenAI
from google import genai
# Set the base URL for Together AI

#client = Together(api_key=API_KEY)
client = genai.Client(api_key=dotenv_values('.env')['GOOGLE_AI_STUDIO_API_KEY'])
TOKEN_LIMIT = 8192
DEFAULT_ISSUE_FILE_EXTENSIONS='-- "*.java" "*.kt" "*.xml" "*.kts" "*.gradle"'
MODEL = 'gemini-2.0-flash' #'gemini-2.5-flash-lite'

# gemini-2.5-flash-preview-09-2025 \ gemini-2.0-flash

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

ISSUE_PRIORITY_RANK = (
    "CameraLeak",
    "MediaLeak",
    "Overdraw",
    "DrawAllocation",
    "WakeLock",
    "WakelockTimeout",
    "InefficientDataFormatAndParser",
    "InvalidateWithoutRect",
    "UnsupportedHardwareAcceleration",
    "NestedWeight",
    "HashmapUsage",
    "BitmapFormatUsage",
    "InefficientDataFormatAndParser",
    "DataTransmissionWithoutCompression",
    "SSLSessionCaching",
    "URLCaching",
    "CheckLayoutSize",
    "CheckMetadata",
    "CheckNetwork",
    "CollectionOfBitmaps",
    "CollectionOfViews",
    "InefficientSQLQuery",
    "SlowForLoop",
    "VacuousBackgroundService",
    "ImmortalityBug",
    "RigidAlarmManager",
    "BitmapFormatUsage",
    "UnsuitedLRUCacheSize",
    "UnclosedCloseable",
    "HeavyBroadcastReceiver",
    "HeavyServiceStart",
    "HeavyAsyncTask",
    "PassiveProviderLocation",
    "LeakingThread",
    "LeakingHandler",
    "LeakingInnerClass",
    "StaticBitmap",
    "StaticContext",
    "StaticView",
    "CollectionOfBitmaps",
    "CollectionOfViews",
    "InvalidatewithoutRect",
    "SwissArmyKnife",
    "ComplexClass",
    "Longmethod",
    "BLOBClass",
    "NestedWeight",
    "TooManyViews",
    "TooDeepLayout",
    "Overdraw",
    "UnsupportedHardwareAcceleration",
    "Recycle",
    "UnsuitedLRUCacheSize",
    "StaticFieldLeak",
    "EarlyResourceBinding",
    "LifecycleContainment",
    "MemoizationChance",
    "SyntheticAccessor"
    "DynamicWaitTime",
    "InfoWarningFCM",
    "DirtyRendering",
    "ConfigChanges",
    "DebuggableRelease",
    "RedundantFieldInitializer",
    "NoLowMemoryResolver",
    "MemberIgnoringMethod",
    "InternalGetterSetter",
    'DroppedData',
    'TooFewBranchesForSwitch',
)

TO_EXCLUDE = {
    #"UnusedIds",
    #"UnusedResources",
    "ViewTag",
    "InternalGetterSetter",
    #"DroppedData",
    #"VectorPath",
}

def send_to_llm(msg, max_tokens=None, model=MODEL):
    if isinstance(client, Together):
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            #model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": msg}, {"role": "assistant", "content": "option: "}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    elif isinstance(client, OpenAI):
        response =  client.responses.create(
            model="gpt-4o",
            input=msg,
            max_tokens=max_tokens
        )
        return response.output_text
    elif isinstance(client, genai.Client):
        try:
            time.sleep(4)
            response = client.models.generate_content(
                model=model,
                contents=msg,
                config={
                    #"max_output_tokens": max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                    #"temperature": temperature,
                },
            )
        except Exception as e:
            loge(f"Error sending to LLM: {e}")
            time.sleep(10)
            response = client.models.generate_content(
                model=MODEL,
                contents=msg,
                config={
                    # "max_output_tokens": max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                },
            )
        return response.text
    else:
        raise Exception("Invalid client")



def get_issue_file(repo_dir, curr_commit, file):
    check_info = f"-f {curr_commit}" if curr_commit.strip() != '' else ''
    file_cmd = f'cd {repo_dir} ; git checkout {check_info} > /dev/null 2>&1 ; find . -type f -name {os.path.basename(file)} | head -1'
    print("file comd", file_cmd)

    try:
        file_find = execute_shell_command(file_cmd)
        file_find.validate(Exception("Error finding issue file"))
    except:
        if file is not None and file != '':
            file_cmd =  f'find . -type f -name {os.path.basename(file)} | head -1'
            file_find = execute_shell_command(file_cmd)
            file_find.validate()
        else:
            return None
    return file_find.output.strip() if file_find.output.strip() != "" else None
    #print(file_find)

def get_file_content(repo_dir, curr_commit, file, def_null_value="No info available"):
    issue_file = get_issue_file(repo_dir, curr_commit, file)
    if issue_file is None:
        return def_null_value
    print(issue_file)
    cont_cmd = f'git -C {repo_dir} show {curr_commit}:{issue_file.strip()}'\
        if curr_commit.strip() != '' else f'cat {os.path.join(repo_dir, issue_file.strip())}'
    print(cont_cmd)
    try:
        file_content_res = execute_shell_command(cont_cmd)
        file_content_res.validate(Exception("Error getting file content"))
    except:
        return def_null_value
    #ret_file_code = file_content_res.return_code
    file_content = file_content_res.output
    if file_content.strip() == "":
        file_content = def_null_value
    return file_content

def merge_duplicate_issues(issues_list, skip_possible_duplicates=True):
    print('initial total issues', len(issues_list))
    merged_dict = {}
    for i, reg in enumerate(sorted(issues_list, key=lambda x: len(x['issue_location']), reverse=True)):
        #issue_key = reg['issue'].get_simple_name() + reg['prev_commit_hash'] + reg['commit_hash'] + str(getattr(reg['issue'], 'file', ''))
        issue_key = reg['issue_name'] + reg['repo_dir'] + reg['file'].split("/")[-1]
        if skip_possible_duplicates and issue_key in merged_dict:
            #print('skipping', reg['issue_name'], 'on', reg['repo_dir'])
            # keep the longest location
            line = '' if 'line' not in reg['issue_location'] else reg['issue_location'].split("|")[-1]
            mg_line = '' if 'line' not in merged_dict[issue_key][-1]['issue_location'] else merged_dict[issue_key][-1]['issue_location'].split("|")[-1]
            line_number = int(line) if line.strip().isdigit() else -1
            mg_line_number = int(mg_line) if mg_line.strip().isdigit() else -1
            if line_number > mg_line_number:
                merged_dict[issue_key].append(reg)
                continue
            elif len(reg['issue_location'].split('.')[-1]) > len(merged_dict[issue_key][-1]['issue_location'].split('.')[-1]) or mg_line_number > -1:
            #if len(reg['issue_location']) > len(merged_dict[issue_key]['issue_location']):
                merged_dict[issue_key].pop()
                merged_dict[issue_key].append(reg)
            else:
                continue
        elif not skip_possible_duplicates:
            issue_key += reg['tool']
        merged_dict[issue_key] = merged_dict.get(issue_key, []) + [reg]
    x = reduce(lambda a, b: a + b, merged_dict.values(), [])
    return x



def explain_why(file_content, issue_spec, location, model, is_false_positive=True):
    fp_question = f"""
                Explain why this performance issue cannot be identified in this file and what could have caused it to be a false positive raised by a static analysis tool.
            """
    tp_question = f"""
                Explain why this performance issue is present in this file.
            """
    if is_false_positive:
        question = fp_question
    else:
        question = tp_question
    # code_diff_res = get_code_diff(repo_dir, curr_commit, issue, extensions=issue.get_file_extensions())
    prompt = f"""
            Given the specification of a statically identified issue previously identified on this Android project:
            Issue Name {issue_spec['issue_name']}
            {"Class/Method/Line : " + location}
            Issue specification: {issue_spec['description']}
            Invalid if: {issue_spec.get('possible_void', 'No info available') if issue_spec.get('possible_void', 'No info available').strip() != '' else 'No info available'}
            ##############
            File content: 
            {file_content}
            ##############
            {question}
        """
    try:
        res = send_to_llm(prompt, model=model)
        return res.replace(';', '').replace('\n', '#-#').strip()
    except Exception as e:
        traceback.print_exc()
        time.sleep(2)
        loge(f"Error sending to LLM: {e}")
    return "Error"

def validate_issue(issue_spec, repo_dir, file, location, curr_commit='', llm_model=MODEL, exp=True):
    explanation = ''
    question = f"""
        I want to know if this specific statically detectable performance issue exists in the previous file.
        Respond with only one of the following options,  without any additional explanations: 
            "Uncertain" - If it is not possible to evaluate if the issue exists solely based on the provided information. 
            It might require analysis of other project files.
            "Not present" - If the issue is definitely not present in the provided file content.
            "Exists" - If the issue is definitely present in the provided file content.
    """
    print(issue_spec)
    file_content = get_file_content(repo_dir, curr_commit, file)
    if file_content == "No info available":
        return "Error", "Could not retrieve file content"
    prompt = f"""
        Given the specification of a statically identified issue previously identified on this Android project:
        Issue Name {issue_spec['issue_name']}
        {"Class/Method/Line : " + location}
        Issue specification: {issue_spec['description']}
        Invalid if: {issue_spec.get('possible_void', 'No info available') if issue_spec.get('possible_void', 'No info available').strip() != '' else 'No info available'}
        ##############
        File content: 
        {file_content}
        ##############
        {question}
    """
    print(prompt)
    try:
        res = send_to_llm(prompt, max_tokens=8, model=llm_model)
        print(res)
    except Exception as e:
        traceback.print_exc()
        time.sleep(2)
        loge(f"Error sending to LLM: {e}")
        try:
            res = send_to_llm(prompt, max_tokens=8, model=llm_model)
        except Exception as e:
            time.sleep(2)
            loge(f"Error sending to LLM: {e}")
            res = 'Error'

    if 'not' not in res.lower() and 'uncertain' not in res.lower():
        final_label = "True_Positive"
        #logs("A true positive!", res.lower())
        # write_to_file(f"{issue_name}_true_positives.txt", answer.lower())
    elif res.lower() == 'uncertain':
        final_label = "Uncertain"
    elif 'not' in res.lower():
        final_label = "False_Positive"
    else:
        final_label = "Error"
        return final_label, res

    if not exp:
        return final_label, explanation

    explanation = explain_why(file_content, issue_spec, location, llm_model, is_false_positive=(final_label!="True_Positive"))
    return final_label, explanation

def load_issues_csv(csv_file):
    issues = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            if len(row) < 5:
                continue
            iss_name = row[0].strip()
            if iss_name in TO_EXCLUDE:
                continue
            if iss_name is None or iss_name in ['', "Issue"]:
                print("Could not parse issue", row)
                continue
            repo_dir = row[2].strip().replace("/NONE_TRANSFORMED_", "")
            v = {
                'issue_name': iss_name,
                'tool': row[1].strip(),
                'repo_dir': repo_dir,
                'file': row[3].strip().replace("/NONE_TRANSFORMED_",""),
                'issue_location': row[4].strip().replace("/NONE_TRANSFORMED_",""),
                }
            issues.append(v)
    return issues

def gen_label_key(f1, f2, f3, f4):
    return '-'.join([f1, f2, f3, f4])

def load_labels(filename="classified_issues.csv"):
    labels = {}
    if not os.path.exists(filename):
        return labels
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], issue_name)
            #  gen_label_key(issue_name, reg['repo_dir'], reg['file'], '')
            key = gen_label_key(row[0], row[2], row[3],'')
            labels[key] = {
                'issue_name': row[0],
                'tool': row[1],
                'repo_dir': row[2],
                'file': row[3],
                'issue_location': row[4],
                'llm_label': row[-1]
            }
    return labels


def save_label(issue_dict,  final_label, explanation, file_path="classified_issues.csv"):
    with open(file_path, 'a+') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([issue_dict['issue_name'], issue_dict['tool'], issue_dict['repo_dir'],
                         issue_dict['file'], issue_dict['issue_location'],
                         final_label.strip().replace("\n", ""), explanation.strip().replace("\n", "")])


def get_corresponding_spec(issue, issue_spec):
    issue_id = issue
    if issue_id in issue_spec:
        return issue_spec[issue_id]
    elif issue_id == "UselessStringValueOf":
        return issue_spec["UseValueOf"]
    return None


def load_issue_specification_list(filename="performance_issues_list.csv"):
    issues = {}
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)
        for i, row in enumerate(reader):
            issue_name = row[0].strip()
            if issue_name.strip() == '' or len(row) < 16:
                continue
            issues[issue_name] = {
                'description': row[18],
                'sample': row[19],
                'expected_fix': row[20],
                'file_extensions': row[21].strip().split(','),
                'severity': row[22],
                'example_1': row[23].strip(),
                'example_2': row[24].strip(),
                'possible_void': row[25],
                'issue_name': issue_name
            }
    return issues


def write_to_file(filename, content):
    with open(filename, 'a+') as file:
        file.write(content + "\n------\n")
    print(f"Content written to {filename}")

def print_stats(issues_list, lim_per_issue=100000):
    issue_count = {}
    repo_count = {}
    issue_categ = {}
    for reg in issues_list:
        #print(reg)
        repo_dir = reg['repo_dir']
        if 'AndroidStudioProjects' in repo_dir: #  'AndroidStudioProjects' not in repo_dir:
            continue
        issue_name = reg['issue_name'].strip()
        issue_count[issue_name] = issue_count.get(issue_name, 0) + 1
        repo_count[repo_dir] = repo_count.get(repo_dir, 0) + 1
        issue_categories = ISSUE_CATEGORY_MAPPING.get(issue_name, [])
        for cat in issue_categories:
            issue_categ[cat] = issue_categ.get(cat, 0) + 1

    sorted_issues = sorted(issue_count.items(), key=lambda x: x[1], reverse=True)
    for iss, count in sorted_issues:
        print(f"{iss}: {count}")

    issue_curr_count = {}
    # write issues to file
    with open("annotation_candidates_issues.csv", 'w') as file:
        for reg in issues_list:
            issue_name = reg['issue_name']
            if issue_curr_count.get(issue_name, 0) >= lim_per_issue:
                continue
            file.write(f"{reg['tool']};{issue_name};{reg['repo_dir']};{reg['file']};unlabeled\n")
            issue_curr_count[issue_name] = issue_curr_count.get(issue_name, 0) + 1
            # DAAP;CollectionOfBitmaps;/Users/rar9993/repos/research/fdroid_apps/native_apps/android-anuto;file:/src/main/java/ch/logixisland/anuto/game/objects/Sprite.java;real_false_positive

    print("distinct issues:", len(issue_count))
    for repo, count in repo_count.items():
        print(f"{repo}: {count}")

    print("distinct categs:", len(issue_categ))
    #for cat, count in issue_categ.items():
    #    print(f"{cat}: {count}")


def evaluate_issues(csv_regressions_file, ignore_file_removed=True, lim_per_issue=1000):
    issue_spec = load_issue_specification_list()
    print("loaded issue specification")
    issues_list = merge_duplicate_issues(load_issues_csv(csv_regressions_file))
    print("filtered issue list", len(issues_list))
    print_stats(issues_list, lim_per_issue=lim_per_issue)
    exit(0)
    #print(was_code_moved())
    prev_labels = load_labels()
    size = len(issues_list)
    per_issue_count = {}
    sorted_issue_list = sorted(issues_list, key=lambda x: ISSUE_PRIORITY_RANK.index(x['issue_name']) if x['issue_name'] in ISSUE_PRIORITY_RANK else 0)
    for i, reg in enumerate(sorted_issue_list):
        logi(f"issue {i+1} of {size}")
        issue_name = reg['issue_name']
        reg_key = gen_label_key(issue_name, reg['repo_dir'], reg['file'], '')
        if per_issue_count.get(issue_name, 0) >= lim_per_issue:
            print("Issue reached the limit of classifications")
            continue
        if reg_key in prev_labels:
            print("Already classified")
            per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1
            continue
        print('-----')
        corrresponding_spec = get_corresponding_spec(issue_name, issue_spec)
        if corrresponding_spec is None:
            loge(f"Could not find the specification for issue {reg['issue_name']}")
            continue
        answer, explanation = validate_issue(corrresponding_spec, reg['repo_dir'], reg['file'], reg['issue_location'])
        print("Issue:", issue_name, "Final label: ", answer, "Explanation: ", explanation)
        if "Error" not in answer:
            per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1
            save_label(reg, answer, explanation)


if __name__ == '__main__':
    csv_filename = "llm_gen_datasets/similar_found_issues.csv" # "sample_issues.csv"
    issue_lim = 100
    evaluate_issues(csv_filename, lim_per_issue=issue_lim)
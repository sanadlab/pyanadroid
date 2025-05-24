import csv
import os.path
import time
import traceback
import tiktoken
from dotenv import dotenv_values
from anadroid.analysis.metrics.Issues import issue_from_string
from anadroid.utils.Utils import execute_shell_command, loge, logs, logi
from together import Together
from openai import OpenAI

# Set the base URL for Together AI
API_KEY=dotenv_values('.env')['TOGETHER_AI_API_KEY']
client = Together(api_key=API_KEY)
TOKEN_LIMIT = 8192
DEFAULT_ISSUE_FILE_EXTENSIONS='-- "*.java" "*.kt" "*.xml" "*.kts" "*.gradle"'

ISSUE_PRIORITY_RANK = (
    "WakeLock",
    "WakelockTimeout",
    "CameraLeak",
    "MediaLeak",
    "UIOverdraw",
    "DrawAllocation",
    "InefficientDataFormatAndParser",
    "InvalidatewithoutRect",
    "UnsupportedHardwareAcceleration",
    "NestedWeight",
    "HashmapUsage",
    "BitmapFormatUsage",
    "InefficientDataFormatAndParser",
    "SSLSessionCaching",
    "URLCaching",
    "CheckLayoutSize",
    "CheckMetadata",
    "CheckNetwork",
    "CollectionOfBitmaps",
    "CollectionOfViews",
    "InefficientSQLQuery",
    "DataTransmissionWithoutCompression",
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
    "DynamicWaitTime",
    "InfoWarningFCM",
    "DirtyRendering",
    "ConfigChanges",
    "DebuggableRelease",
    "RedundantFieldInitializer",
     "NoLowMemoryResolver",
    "MemberIgnoringMethod",
    "InternalGetterSetter",

)


def get_issue_rank(issue):
    val = ISSUE_PRIORITY_RANK.index(issue.get_simple_name().strip()) \
        if issue.get_simple_name().strip() in ISSUE_PRIORITY_RANK else len(ISSUE_PRIORITY_RANK)
    return val

def get_token_count(texto, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(texto)
    return len(tokens)


def truncate_text_to_fit(text, model="gpt-4", max_new_tokens=384, max_tokens_limit=TOKEN_LIMIT):
    """Truncate the input text to ensure the total tokens stay within the model's limit."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    # Calculate max allowed input tokens
    max_input_tokens = max_tokens_limit - max_new_tokens

    # If input exceeds limit, truncate
    if len(tokens) > max_input_tokens:
        tokens = tokens[:max_input_tokens]  # Keep only allowed tokens

    return encoding.decode(tokens)  # Convert back to string



def send_to_llm(msg, max_tokens=None):
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
    else:
        raise Exception("Invalid client")

def was_code_moved(repo_dir, curr_commit, issue):
    def_null_value = "No info available"
    question = """
        I want to know if the issue was: 
            Completely removed from the place where it was found.
            Moved to another method/class/file.
            Kept without being fixed
        Answer with only one word from the following options: "Removed", "Moved", or "Kept", without any additional explanations"""
    code_diff_res = get_code_diff(repo_dir, curr_commit, issue, def_null_value, extensions=issue.get_file_extensions())
    #if code_diff_res.strip() == "" or code_diff_res == def_null_value:
    file_content = get_file_content(repo_dir, curr_commit, issue, def_null_value)
    #else:
    #    file_content = def_null_value
    ret_file_code = -1
    #print('file', issue.file)
    if code_diff_res.strip() == "" and (issue.file is None or ret_file_code != 0):
        loge("No diff and no file content")
        return "Unknown"
    prompt = f"""
        Given the following statically detectable issue previously identified on this Android project:
        Issue Name: {issue.get_simple_name()}
        {"Detected on previous Class/Method/Line: " + issue.get_issue_location()}
        Issue specification: {issue.description}
        Git diff between current commit and the previous one: {code_diff_res}
        Current file content: 
        {file_content}
        {question}
    """
    res = "Unknown"
    submitted_file_content = True
    submitted_git_diff = True
    #print(prompt)
    try:
        res = send_to_llm(prompt, max_tokens=8)
    except Exception as e:
        time.sleep(1)
        loge(f"Error sending to LLM: {e}")
        prompt = f"""
               Given the following statically detectable issue previously identified on this Android project:
               Issue Name: {issue.get_simple_name()}
               {"Original file: " + issue.file if issue.file is not None else ""}
               {"Detected on previous Class/Method/Line: " + issue.get_issue_location()}
               Issue specification: {issue.description}
               Git diff between the previous commit and the current commit: {code_diff_res}
               {question}
           """
        submitted_file_content = False
        print("total token count", get_token_count(prompt))
        try:
            res = send_to_llm(prompt, max_tokens=8)
        except Exception as e:
            time.sleep(1)
            loge(f"Error sending to LLM: {e}")
            print("total token count", get_token_count(prompt))
            prompt = f"""
                    Given the following statically detectable issue previously identified on this Android project:
                    Issue Name: {issue.get_simple_name()}
                    {"Original file: " + issue.file if issue.file is not None else ""}
                    {"Detected on previous Class/Method/Line: " + issue.get_issue_location()}
                    Issue specification: {issue.description}
                    Current file content: 
                    {file_content}
                    {question}
                """
            submitted_file_content = True
            submitted_git_diff = False
            try:
                res = send_to_llm(truncate_text_to_fit(prompt), max_tokens=8)
            except:
                res = "Unknown"
                submitted_file_content = False
                submitted_git_diff = False
    return res.strip(), submitted_git_diff, submitted_file_content

def get_code_diff(repo_dir, curr_commit, issue, def_null_value="No info available", optimize_token_count=True,
                  extensions=None):
    code_diff_target_extensions = '-- ' + ' '.join(list(map(lambda x: f'\"{x}\"', extensions.split(" ")))).replace("\"\"", "") if extensions is not None else DEFAULT_ISSUE_FILE_EXTENSIONS
    #print('extensoes', code_diff_target_extensions)
    issue_file = get_issue_file(repo_dir, curr_commit, issue)
    print('issue file', issue_file)
    if issue_file is not None and issue_file.strip() != '':
        diff_cmd = f"cd {repo_dir} ; git checkout -f {curr_commit}; git diff HEAD^ {'-- ' + issue_file}"
    else:
        # TODO code_diff_target_extensions
        diff_cmd = f"cd {repo_dir} ; git checkout -f {curr_commit}; git diff HEAD^ {code_diff_target_extensions}"
    print("performing", diff_cmd)
    code_diff_res = execute_shell_command(diff_cmd)
    code_diff_res.validate()
    #print(code_diff_res)
    #print(issue)
    diff_output = code_diff_res.output if code_diff_res.output.strip() != "" else def_null_value
    if optimize_token_count and get_token_count(diff_output) > TOKEN_LIMIT:
        diff_output = def_null_value
    return diff_output

def get_issue_file(repo_dir, curr_commit, issue):
    if issue.file is None:
        return None
    file_cmd = f'cd {repo_dir} ; git checkout -f {curr_commit} > /dev/null 2>&1 ; find . -type f -name {os.path.basename(issue.file)} | head -1'
    #print("file comd", file_cmd)
    file_find = execute_shell_command(file_cmd)
    file_find.validate()
    return file_find.output.strip() if file_find.output.strip() != "" else None
    #print(file_find)

def get_file_content(repo_dir, curr_commit, issue, def_null_value="No info available"):
    issue_file = get_issue_file(repo_dir, curr_commit, issue)
    if issue_file is None:
        return def_null_value
    cont_cmd = f'cd {repo_dir} && git show {curr_commit}:{issue_file.strip()}'
    #print(cont_cmd)
    file_content_res = execute_shell_command(cont_cmd)
    file_content_res.validate()
    #ret_file_code = file_content_res.return_code
    file_content = file_content_res.output
    if file_content.strip() == "":
        file_content = def_null_value
    return file_content

def merge_duplicate_issues_on_regressions(regression_list, skip_possible_duplicates=True):
    print('initial total regressions', len(regression_list))
    merged_regressions= []
    merged_regressions_dict = {}
    for i, reg in enumerate(regression_list):
        '''is_equal = lambda a,b : (a['issue'].get_simple_name() == b['issue'].get_simple_name() and a['repo_dir'] == b['repo_dir']
                                 and a['prev_commit_hash'] == b['prev_commit_hash'] and a['commit_hash'] == b['commit_hash'])

        equiv_issues = [r for r in regression_list if is_equal(r, reg)
                        and (r['issue'].get_issue_location() == reg['issue'].get_issue_location()
                             or (getattr(r['issue'], 'file', '') is not None and getattr(reg['issue'], 'file', '') is not None
                                and os.path.basename(getattr(r['issue'], 'file', '')) == os.path.basename(getattr(reg['issue'], 'file', ''))))
                        and r['issue'].detection_tool_name != reg['issue'].detection_tool_name
                        ]'''
        issue_key = reg['issue'].get_simple_name() + reg['prev_commit_hash'] + reg['commit_hash'] + str(getattr(reg['issue'], 'file', ''))
        if issue_key in merged_regressions_dict and reg['issue'].is_less_descriptive(merged_regressions_dict[issue_key]):
            print('skipping', reg['issue'].get_simple_name(), 'on', reg['repo_dir'], 'commit', reg['commit_hash'])
            continue
        merged_regressions_dict[issue_key] = reg
        '''
        if any(equiv_issues) and skip_possible_duplicates:
            if reg['issue'].is_less_descriptive(equiv_issues[0]['issue']) or not reg['issue'].is_more_descriptive(equiv_issues[0]['issue']):
                print('skipping', reg['issue'].get_simple_name(), 'on', reg['repo_dir'], 'commit', reg['commit_hash'])
                equiv_merged_issues = [r for r in merged_regressions if
                                is_equal(r, reg) and r['issue'].detection_tool_name != reg['issue'].detection_tool_name]
                if not any(equiv_merged_issues):
                    merged_regressions.append(reg)
                #merged_regressions.append(reg)
                continue
            else:
                continue
        merged_regressions.append(reg)
    return merged_regressions'''
    return list(merged_regressions_dict.values())

def followed_correct_solution(issue, expected_fix, repo_dir, curr_commit):
    def_null_value = "No info available"
    question = f"""
        I want to know if this specific issue was fixed according to the expected fix.
        Respond with only one of the following options: "Fixed" or "Not fixed", without any additional explanations
    """
    code_diff_res = get_code_diff(repo_dir, curr_commit, issue, def_null_value, extensions=issue.get_file_extensions())
    #code_diff_res = get_code_diff(repo_dir, curr_commit, issue, extensions=issue.get_file_extensions())
    file_content = get_file_content(repo_dir, curr_commit, issue)
    prompt = f"""
        Given the following statically identified issue previously identified on this Android project:
        {"Class/Method/Line : " + issue.get_issue_location()}
        Issue specification: {issue.description}
        Expected fix: {expected_fix}
        Git diff between the current commit and the previous commit: {code_diff_res}
         Current file content: 
        {file_content}
        {question}
    """
    submitted_file_content = True
    submitted_git_diff = True
    #print(prompt)
    try:
        res = send_to_llm(prompt, max_tokens=8)
    except Exception as e:
        traceback.print_exc()
        time.sleep(2)
        loge(f"Error sending to LLM: {e}")
        prompt = f"""
                Given the following statically identified issue previously identified on an Android project:
                {"Original file: " + issue.file if issue.file is not None else ""}
                {"Class/Method/Line : " + issue.get_issue_location()}
                Issue specification: {issue.description}
                Expected fix: {expected_fix}
                Git diff between the current commit and the previous commit: {code_diff_res}
                {question}
            """
        submitted_file_content = False
        try:
            res = send_to_llm(prompt, max_tokens=8)
        except Exception as e:
            time.sleep(2)
            loge(f"Error sending to LLM: {e}")
            prompt = f"""
                    Given the following statically identified issue previously identified on an Android project:
                    {"Original file: " + issue.file if issue.file is not None else ""}
                    {"Class/Method/Line : " + issue.get_issue_location()}
                    Issue specification: {issue.description}
                    Expected fix: {expected_fix}
                     Current file content: 
                    {file_content}
                    {question}
                """
            submitted_file_content = True
            submitted_git_diff = False
            try:
                res = send_to_llm(truncate_text_to_fit(prompt), max_tokens=8)
            except:
                return "Unknown", False, False
    return res.strip(), submitted_git_diff, submitted_file_content


def load_regressions_csv(csv_file="regressions.csv"):
    regressions = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            v = {
                    'repo_dir': row[0],
                    'prev_commit_hash': row[1],
                    'commit_hash': row[2],
                    'commit_message': row[3],
                    'issue': issue_from_string(row[4]),
                    'classification': row[5],
                }
            regressions.append(v)
            #print(v)
    return regressions

def load_classified_regressions_csv(csv_file="classified_regressions.csv"):
    regressions = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            v = {
                    'issue_name': issue_from_string(row[4]),
                    'classification': row[5],
                }
            regressions.append(v)
            #print(v)
    return regressions

def gen_label_key(repo_dir, prev_commit_hash, commit_hash, issue_name):
    return '-'.join([repo_dir, prev_commit_hash, commit_hash, issue_name])

def load_labels(filename="classified_regressions.csv"):
    labels = {}
    if not os.path.exists(filename):
        return labels
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], issue_name)
            key = gen_label_key(row[1], row[3], row[4], row[0])
            labels[key] = {
                'issue_name': row[0],
                'repo_dir': row[1],
                'issue_location': row[2],
                'prev_commit_hash': row[3],
                'fix_commit_hash': row[4],
                'commit_message': row[5],
                'sub_git_diff': row[6],
                'sub_file_ctnt': row[7],
                'pre_label': row[8],
                'llm_label': row[9]
            }
    return labels


def save_label(repo_dir, prev_commit_hash, commit_hash, issue, commit_msg, manual_label, final_label,
               file_path="classified_regressions.csv"):
    with open(file_path, 'a+') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([issue.get_simple_name(), repo_dir,
                         issue.get_issue_location() , prev_commit_hash,
                         commit_hash, commit_msg, manual_label, final_label])

def new_save_label(repo_dir, prev_commit_hash, commit_hash, issue, commit_msg, manual_label, final_label,
               file_path="new_classified_regressions.csv", had_git_diff="Unknown", had_file_content="Unknown"):
    with open(file_path, 'a+') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([issue.get_simple_name(), repo_dir,
                         issue.get_issue_location() , prev_commit_hash,
                         commit_hash, commit_msg, had_git_diff, had_file_content, manual_label, final_label])

def get_corresponding_spec(issue, issue_spec):
    issue_id = issue.get_simple_name()
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
            print(i)
            issue_name = row[0].strip()
            if issue_name.strip() == '' or len(row) < 16:
                continue
            issues[issue_name] = {
                'description': row[14],
                'sample': row[15],
                'expected_fix': row[16],
                'file_extensions': row[17].strip().split(','),
                'severity': row[18],
                'example_1': row[19].strip(),
                'example_2': row[20].strip(),
            }
    return issues


def evaluate_true_positives(csv_regressions_file, ignore_file_removed=True, lim_per_issue=1000):
    order_label = [ 'def_removal', 'prob_removal', 'prob_move', 'file_removed']
    issue_spec = load_issue_specification_list()
    print("loaded issue specification")

    regressions = merge_duplicate_issues_on_regressions(load_regressions_csv(csv_regressions_file))
    regressions = sorted(
        regressions,
        key=lambda x: (order_label.index(x['classification']), get_issue_rank(x['issue']))
    )
    print("sorted regressions", len(regressions))
    if ignore_file_removed:
        regressions = [r for r in regressions if r['classification'] != 'file_removed']
    print("filtered regressions", len(regressions))
    #print(was_code_moved())
    size = len(regressions)
    print("Regressions to classify: ", size)
    prev_labels = load_labels()
    per_issue_count = {}
    for i, reg in enumerate(regressions):
        logi(f"regression {i+1} of {size}")
        curr_manual_label = reg['classification']
        issue_name = reg['issue'].get_simple_name()
        reg_key = gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], issue_name)
        if per_issue_count.get(issue_name, 0) >= lim_per_issue:
            print("Issue reached the limit of classifications")
            continue
        if reg_key in prev_labels:
            print("Already classified")
            per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1
            continue
        print('-----')
        #print(curr_manual_label)
        final_label = "Possible_True_Positive"
        corrresponding_spec = get_corresponding_spec(reg['issue'], issue_spec)
        if corrresponding_spec is None:
            loge(f"Could not find the specification for issue {reg['issue'].get_simple_name()}")
            continue
        reg['issue'].description = corrresponding_spec['description']
        reg['issue'].file_extensions = corrresponding_spec['file_extensions']
        #print(reg['issue'].get_file_extensions())
        moved_label, sub_git_diff, sub_file_ctnt = was_code_moved(reg['repo_dir'], reg['commit_hash'], reg['issue']).lower()
        print("was code moved? ", moved_label, curr_manual_label)
        if 'removed' in moved_label:
            #print('Checking if the issue was fixed...')
            rec_fix, sub_git_diff, sub_file_ctnt = followed_correct_solution(reg['issue'], corrresponding_spec['expected_fix'], reg['repo_dir'], reg['commit_hash'])
            #print("was issue fixed according to solution? ", rec_fix, corrresponding_spec['expected_fix'])
            if 'not' not in rec_fix.lower():
                final_label = "True_Positive"
                logs("A true positive!")
        elif moved_label == 'Unknown':
            final_label = "Unknown"
        else:
            final_label = "Possible_False_Positive"
        print("Issue:", reg['issue'].get_simple_name(), "Final label: ", final_label)
        save_label(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], reg['issue'],
                   reg['commit_message'], curr_manual_label, final_label)
        per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1


def reevaluate_true_positives(csv_regressions_file, ignore_file_removed=True, lim_per_issue=1000):
    order_label = [ 'def_removal', 'prob_removal', 'prob_move', 'file_removed']
    issue_spec = load_issue_specification_list()
    print("loaded issue specification")
    regressions = merge_duplicate_issues_on_regressions(load_classified_regressions_csv(csv_regressions_file))
    regressions = sorted(
        regressions,
        key=lambda x: (order_label.index(x['classification']), get_issue_rank(x['issue']))
    )
    print("sorted regressions", len(regressions))
    if ignore_file_removed:
        regressions = [r for r in regressions if r['classification'] != 'file_removed']
    print("filtered regressions", len(regressions))
    #print(was_code_moved())
    size = len(regressions)
    print("Regressions to classify: ", size)
    prev_labels = load_labels()
    per_issue_count = {}
    for i, reg in enumerate(regressions):
        logi(f"regression {i+1} of {size}")
        curr_manual_label = reg['classification']
        issue_name = reg['issue'].get_simple_name()
        reg_key = gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], issue_name)
        if per_issue_count.get(issue_name, 0) >= lim_per_issue:
            print("Issue reached the limit of classifications")
            continue
        if reg_key in prev_labels:
            print("Already classified")
            per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1
            continue
        print('-----')
        #print(curr_manual_label)
        final_label = "Possible_True_Positive"
        corrresponding_spec = get_corresponding_spec(reg['issue'], issue_spec)
        if corrresponding_spec is None:
            loge(f"Could not find the specification for issue {reg['issue'].get_simple_name()}")
            continue
        reg['issue'].description = corrresponding_spec['description']
        reg['issue'].file_extensions = corrresponding_spec['file_extensions']
        #print(reg['issue'].get_file_extensions())
        moved_label, git_diff, file_ct = was_code_moved(reg['repo_dir'], reg['commit_hash'], reg['issue']).lower()
        print("was code moved? ", moved_label, curr_manual_label)
        if 'removed' in moved_label:
            #print('Checking if the issue was fixed...')
            rec_fix, sub_git_diff, sub_file_ctnt = followed_correct_solution(reg['issue'],
                                                                             corrresponding_spec['expected_fix'],
                                                                             reg['repo_dir'], reg['commit_hash'])

            #print("was issue fixed according to solution? ", rec_fix, corrresponding_spec['expected_fix'])
            if 'not' not in rec_fix.lower():
                final_label = "True_Positive"
                logs("A true positive!")
        elif moved_label == 'Unknown':
            final_label = "Unknown"
        else:
            final_label = "Possible_False_Positive"
        print("Issue:", reg['issue'].get_simple_name(), "Final label: ", final_label)
        save_label(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], reg['issue'],
                   reg['commit_message'], curr_manual_label, final_label)
        per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1


def augmentate_true_positives_dateset(csv_filename='regressions.csv', lim_per_issue=1000):
    order_label = ['def_removal', 'prob_removal', 'prob_move', 'file_removed']
    issue_spec = load_issue_specification_list()
    print("loaded issue specification")
    regressions = merge_duplicate_issues_on_regressions(load_regressions_csv(csv_filename))
    regressions = sorted(
        regressions,
        key=lambda x: (order_label.index(x['classification']), get_issue_rank(x['issue']))
    )
    print("sorted regressions", len(regressions))
    print("filtered regressions", len(regressions))
    # print(was_code_moved())
    size = len(regressions)
    print("Regressions to classify: ", size)
    prev_labels = load_labels(filename="new_classified_regressions.csv")
    per_issue_count = {}
    for i, reg in enumerate(regressions):
        logi(f"regression {i + 1} of {size}")
        curr_manual_label = reg['classification']
        issue_name = reg['issue'].get_simple_name()
        reg_key = gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], issue_name)
        if per_issue_count.get(issue_name, 0) >= lim_per_issue:
            print(f"Issue {issue_name}, reached the limit of classifications {lim_per_issue}")
            continue
        if reg_key in prev_labels:
            print("Already classified")
            if prev_labels[reg_key]['llm_label'] == 'True_Positive':
                per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1
            continue
        print('-----')
        # print(curr_manual_label)
        final_label = "Possible_True_Positive"
        corrresponding_spec = get_corresponding_spec(reg['issue'], issue_spec)
        if corrresponding_spec is None:
            loge(f"Could not find the specification for issue {reg['issue'].get_simple_name()}")
            continue
        reg['issue'].description = corrresponding_spec['description']
        reg['issue'].file_extensions = corrresponding_spec['file_extensions']
        # print(reg['issue'].get_file_extensions())
        moved_label, sub_git_diff, sub_file_ctnt = was_code_moved(reg['repo_dir'], reg['commit_hash'], reg['issue'])
        print("was code moved? ", moved_label, curr_manual_label)
        if 'removed' in moved_label.lower():
            # print('Checking if the issue was fixed...')
            rec_fix, sub_git_diff, sub_file_ctnt = followed_correct_solution(reg['issue'],
                                                                             corrresponding_spec['expected_fix'],
                                                                             reg['repo_dir'], reg['commit_hash'])

            print("was issue fixed according to solution? ", rec_fix, corrresponding_spec['expected_fix'])
            if 'not' not in rec_fix.lower():
                final_label = "True_Positive"
                logs("A true positive!")
                per_issue_count[issue_name] = per_issue_count.get(issue_name, 0) + 1
        elif moved_label == 'Unknown':
            final_label = "Unknown"
        else:
            final_label = "Possible_False_Positive"
        print("Issue:", reg['issue'].get_simple_name(), "Final label: ", final_label)
        new_save_label(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], reg['issue'],
                   reg['commit_message'], curr_manual_label, final_label, had_git_diff=sub_git_diff, had_file_content=sub_file_ctnt)


if __name__ == '__main__':
    csv_filename = "all_regressions.csv"
    issue_lim = 100
    #evaluate_true_positives(csv_filename, lim_per_issue=issue_lim)
    augmentate_true_positives_dateset(csv_filename, lim_per_issue=issue_lim)
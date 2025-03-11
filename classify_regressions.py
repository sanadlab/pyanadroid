import csv
import os.path
import time
import traceback
import tiktoken
from dotenv import dotenv_values
from anadroid.analysis.metrics.Issues import issue_from_string
from anadroid.utils.Utils import execute_shell_command, loge, logs, logi
from together import Together

# Set the base URL for Together AI
API_KEY=dotenv_values('.env')['TOGETHER_AI_API_KEY']
client = Together(api_key=API_KEY)

TOKEN_LIMIT = 128_000
DEFAULT_ISSUE_FILE_EXTENSIONS='-- "*.java" "*.kt" "*.xml" "*.kts" "*.gradle"'


def get_token_count(texto, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(texto)
    return len(tokens)

def send_to_llm(msg):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        #model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        messages=[{"role": "user", "content": msg}],
    )
    return response.choices[0].message.content

def was_code_moved(repo_dir, curr_commit, issue):
    def_null_value = "No info available"
    question = """
        I want to know if the issue was: 
            Completely removed.
            Moved to another file/class/method (refactored).
            Kept in the same place with or without minor changes.
        Respond with only one of the following options: "Removed", "Moved", or "Kept", without any additional explanations"""
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
        {"Original file: " + issue.file if issue.file is not None else ""}
        {"Detected on previous Class/Method/Line: " + issue.get_issue_location()}
        Issue specification: {issue.description}
        Git diff between the previous commit and the current commit: {code_diff_res}
        Current file content: 
        {file_content}
        {question}
    """
    res = "Unknown"
    #print(prompt)
    try:
        res = send_to_llm(prompt)
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
        try:
            res = send_to_llm(prompt)
        except Exception as e:
            time.sleep(1)
            loge(f"Error sending to LLM: {e}")
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
            try:
                res = send_to_llm(prompt)
            except:
                res = "Unknown"
    return res.strip()

def get_code_diff(repo_dir, curr_commit, issue, def_null_value="No info available", optimize_token_count=True,
                  extensions=None):
    code_diff_target_extensions = '-- ' + extensions if extensions is not None else DEFAULT_ISSUE_FILE_EXTENSIONS
    issue_file = get_issue_file(repo_dir, curr_commit, issue)
    if issue_file is not None:
        diff_cmd = f"cd {repo_dir} && git checkout {curr_commit}; git diff HEAD^ {'-- ' + issue_file}"
    else:
        # TODO code_diff_target_extensions
        diff_cmd = f"cd {repo_dir} && git checkout {curr_commit}; git diff HEAD^ {code_diff_target_extensions}"
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
    file_cmd = f'cd {repo_dir} ; git checkout {curr_commit} > /dev/null 2>&1 ; find . -type f -name {os.path.basename(issue.file)} | head -1'
    #print("file comd", file_cmd)
    file_find = execute_shell_command(file_cmd)
    file_find.validate()
    return file_find.output.strip()
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

def merge_duplicate_issues_on_regressions(regression_list):
    print('initial total regressions', len(regression_list))
    merged_regressions= []
    for i, reg in enumerate(regression_list):
        is_equal = lambda a,b : (a['issue'].get_simple_name() == b['issue'].get_simple_name() and a['repo_dir'] == b['repo_dir']
                                 and a['prev_commit_hash'] == b['prev_commit_hash'] and a['commit_hash'] == b['commit_hash'])
        equiv_issues = [r for r in regression_list if is_equal(r, reg) and r['issue'].detection_tool_name != reg['issue'].detection_tool_name]
        if any(equiv_issues):
            if reg['issue'].is_less_descriptive(equiv_issues[0]['issue']) or not reg['issue'].is_more_descriptive(equiv_issues[0]['issue']):
                print('skipping', reg['issue'].get_simple_name(), 'on', reg['repo_dir'], 'commit', reg['commit_hash'])
                equiv_merged_issues = [r for r in merged_regressions if
                                is_equal(r, reg) and r['issue'].detection_tool_name != reg['issue'].detection_tool_name]
                if not any(equiv_merged_issues):
                    merged_regressions.append(reg)
                #merged_regressions.append(reg)
                continue
        merged_regressions.append(reg)
    return merged_regressions

def followed_correct_solution(issue, expected_fix, repo_dir, curr_commit):
    question = f"""
        I want to know if this specific issue as fixed and the program maintains its functionality.  
        Respond with only one of the following options: "Fixed" or "Not fixed", without any additional explanations
    """
    code_diff_res = get_code_diff(repo_dir, curr_commit, issue, extensions=issue.get_file_extensions())
    file_content = get_file_content(repo_dir, curr_commit, issue)
    prompt = f"""
        Given the following statically identified issue previously identified on this Android project:
        {"Original file: " + issue.file if issue.file is not None else ""}
        {"Class/Method/Line : " + issue.get_issue_location()}
        Issue specification: {issue.description}
        Expected fix: {expected_fix}
        Git diff between the previous commit and the current commit: {code_diff_res}
         Current file content: 
        {file_content}
        {question}
    """
    #print(prompt)
    try:
        res = send_to_llm(prompt)
    except Exception as e:
        traceback.print_exc()
        time.sleep(1)
        loge(f"Error sending to LLM: {e}")
        prompt = f"""
                Given the following statically identified issue previously identified on an Android project:
                {"Original file: " + issue.file if issue.file is not None else ""}
                {"Class/Method/Line : " + issue.get_issue_location()}
                Issue specification: {issue.description}
                Expected fix: {expected_fix}
                Git diff between the previous commit and the current commit: {code_diff_res}
                {question}
            """
        try:
            res = send_to_llm(prompt)
        except Exception as e:
            time.sleep(1)
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
            try:
                res = send_to_llm(prompt)
            except:
                return "Unknown"
    print(res)
    return res.strip()


def load_regressions_csv(csv_file="regressions.csv.short"):
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


def main():
    order_label = [ 'prob_removal', 'def_removal', 'prob_move']
    issue_spec = load_issue_specification_list()
    print("loaded issue specification")
    regressions = merge_duplicate_issues_on_regressions(load_regressions_csv())
    regressions = sorted(regressions, key=lambda x: order_label.index(x['classification']))
    prev_labels = load_labels()
    #print(was_code_moved())
    print("Regressions to classify: ", len(regressions))
    for i, reg in enumerate(regressions):
        logi(f"regression {i+1} of {len(regressions)}")
        print(reg)
        reg_key = gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], reg['issue'].get_simple_name())
        if reg_key in prev_labels:
            print("Already classified")
            continue
        print('-----')
        curr_manual_label = reg['classification']
        #print(curr_manual_label)
        final_label = "Possible_True_Positive"
        corrresponding_spec = get_corresponding_spec(reg['issue'], issue_spec)
        if corrresponding_spec is None:
            loge(f"Could not find the specification for issue {reg['issue'].get_simple_name()}")
        reg['issue'].description = corrresponding_spec['description']
        reg['issue'].file_extensions = corrresponding_spec['file_extensions']
        print(reg['issue'].get_file_extensions())
        moved_label = was_code_moved(reg['repo_dir'], reg['commit_hash'], reg['issue']).lower()
        print("was code moved? ", moved_label, curr_manual_label)
        if 'removed' in moved_label:
            #print('Checking if the issue was fixed...')
            rec_fix = followed_correct_solution(reg['issue'], corrresponding_spec['expected_fix'], reg['repo_dir'], reg['commit_hash'])
            #print("was issue fixed according to solution? ", rec_fix, corrresponding_spec['expected_fix'])
            if 'not' not in rec_fix.lower():
                final_label = "True_Positive"
                logs("A true positive!")
        else:
            final_label = "Possible_False_Positive"
        print("Issue:", reg['issue'].get_simple_name(), "Final label: ", final_label)
        save_label(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], reg['issue'].get_simple_name(),
                   reg['commit_message'], curr_manual_label, final_label)


def gen_label_key(repo_dir, prev_commit_hash, commit_hash, issue_name):
    return '-'.join([repo_dir, prev_commit_hash, commit_hash, issue_name])

def load_labels(filename="classified_regressions.csv"):
    labels = {}
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            key = gen_label_key(row[1], row[2], row[3], row[0])
            labels[key] = {
                'issue': row[0],
                'repo_dir': row[1],
                'prev_commit_hash': row[2],
                'commit_hash': row[3],
                'commit_message': row[4],
                'manual_label': row[5],
                'final_label': row[6]
            }
    return labels


def save_label(repo_dir, prev_commit_hash, commit_hash, issue_name, commit_msg, manual_label, final_label):
    file_path = "classified_regressions.csv"
    with open(file_path, 'a+') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([issue_name, repo_dir, prev_commit_hash, commit_hash, commit_msg, manual_label, final_label])

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
        for row in reader:
            issue_name = row[0].strip()
            if issue_name.strip() == '' or len(row) < 16:
                continue
            issues[issue_name] = {
                'description': row[13],
                'sample': row[14],
                'expected_fix': row[15],
                'file_extensions': row[16].strip().split(',')
            }
    return issues



if __name__ == '__main__':
    main()
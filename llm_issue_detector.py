import os.path
import random
import re

import tiktoken
import csv
from dotenv import dotenv_values

from anadroid.analysis.metrics.Issues import issue_from_string
from anadroid.utils.Utils import execute_shell_command, loge, logs, logi, logw
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


def send_to_llm(msg, max_tokens=None):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        #model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        messages=[{"role": "user", "content": msg}, {"role": "assistant", "content": "option: "}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content



def zero_shot_issues_detection(code_sample, max_tokens=32):
    prompt = f"""
    Analyze the following code and identify any performance issues:
    {code_sample}
    Answer only with the issues found, or "No issues" if none are present.
    """
    try:
        return send_to_llm(prompt, max_tokens=max_tokens).strip()
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        return "Analysis failed"


def blind_test_issue_detection_compare(code_sample, code_sample2):
    prompt = f"""
    Analyze the following alternative solutions.
    Sample 1:
    {code_sample}
    
    Sample 2:
    
    {code_sample2}

    Which solution is more efficient? Provide only the number of the most efficient solution as the answer and nothing more.
    """
    #print(prompt)
    try:
        return send_to_llm(prompt, max_tokens=6).strip()
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        return "Unknown"



def zero_shot_issue_detection_detailed(code_sample, issues_specification):
    prompt = f"""
    Analyze the following Android code for statically-detectable performance issues:

    {code_sample}

    Identify any of these issues:
    {issues_specification}
    
    Respond with only with name of the issues found, or "No issues detected" if none are present.
    """

    try:
        return send_to_llm(prompt).strip()
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        return "Analysis failed"

def read_file_content(filepath):
    with open(filepath, 'r') as f:
        return ''.join(f.readlines())

def load_issue_specification_list(filename="performance_issues_list.csv", examples_fldr="issue_examples"):
    issues = {}
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)
        for i, row in enumerate(reader):
            #print(i)
            issue_name = row[0].strip()
            if issue_name.strip() == '' or len(row) < 16:
                continue
            try:
               issue = {
                    'name': issue_name,
                    'description': row[14],
                    'sample': row[15],
                    'expected_fix': row[16],
                    'file_extensions': row[17].strip().split(','),
                    'severity': row[18],
                    'example_1': read_file_content(os.path.join(examples_fldr, row[19].strip())),
                    'example_2':  read_file_content(os.path.join(examples_fldr, row[20].strip())),
                    'example_1_annotated': read_file_content(os.path.join(examples_fldr, row[19].strip().replace("1.txt", "_annotated_1.txt"))),
                    'example_2_annotated': read_file_content(os.path.join(examples_fldr, row[20].strip().replace("2.txt", "_annotated_2.txt"))),
                }
            except:
                loge(f"Error loading issue {issue_name}")
                continue
            issues[issue_name] = issue
    return issues

def blind_test_procedure():
    issue_spec = load_issue_specification_list()
    for i, issue in enumerate(issue_spec):
        issue_spec_str = '\n'.join([f"{iss['name']}: {iss['description']}" for iss in list(issue_spec.values())[i:( i + 50)]])
        #print(issue_spec_str)
        print(f"Testing issue: {issue}")
        for j in range(1, 3):
            print(f"Example {j}")
            val = re.sub(r'-{3,}', '---', issue_spec[issue][f'example_{j}'] ).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example", len(val))
                print(val)
                exit(-1)
            prob, sol = val
            bld = zero_shot_issues_detection(prob)
            if "no issues" in bld:
                loge("No issues detected")
            else:
                logs("Issue detected")
            sol_list = [prob, sol]
            random.shuffle(sol_list)
            optimal_answer = 1 if prob == sol_list[1] else 2
            bld_cmp = blind_test_issue_detection_compare(sol_list[0], sol_list[1])
            print("optimal answer", optimal_answer, "llm answer", bld_cmp, " ||")
            if int(bld_cmp) == optimal_answer:
                logs(f"Correct answer")
            else:
                loge(f"Incorrect answer")
            bld_detailed = zero_shot_issue_detection_detailed(prob, issue_spec_str)
            if issue in bld_detailed:
                logs(f"{issue} detected")
            else:
                loge(f"{issue} not detected")
                print(bld_detailed)
            print("--------")

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


def load_classified_regressions(filename="classified_regressions.csv"):
    regressions = []
    if not os.path.exists(filename):
        return regressions
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            v = {
                    'issue_name': row[0],
                    'repo_dir': row[1],
                    'prev_commit_hash': row[2],
                    'fix_commit_hash': row[3],
                    'commit_message': row[4],
                    'pre_label': row[5],
                    'llm_label': row[6]

                }
            regressions.append(v)
            #print(v)
    #print(regressions)
    print(f"Loaded {len(regressions)} classified regressions")
    return regressions

def load_true_positive_issues():
    return [issue for issue in load_classified_regressions() if issue['llm_label'] == 'True_Positive']


def create_issue_buckets(issue_list, bucket_size=30):
    issue_buckets = {}
    for issue in issue_list:
        if issue['issue_name'] not in issue_buckets:
            issue_buckets[issue['issue_name']] = []
        is_issue_on_that_repo_already_there = any([i for i in issue_buckets[issue['issue_name']] if i['repo_dir'] == issue['repo_dir'] and i['prev_commit_hash'] == issue['prev_commit_hash']])
        if is_issue_on_that_repo_already_there or len(issue_buckets[issue['issue_name']]) >= bucket_size:
            continue
        issue_buckets[issue['issue_name']].append(issue)
    return issue_buckets


def get_issue_file(repo_dir, curr_commit, issue):
    if issue.file is None:
        return None
    file_cmd = f'cd {repo_dir} ; git checkout {curr_commit} > /dev/null 2>&1 ; find . -type f -name {os.path.basename(issue.file)} | head -1'
    #print("file comd", file_cmd)
    file_find = execute_shell_command(file_cmd)
    file_find.validate()
    return file_find.output.strip() if file_find.output.strip() != "" else None


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


def fetch_code_from_issue(issue_reg, regressions_list):
    matching_instance = [r for r in regressions_list if r['prev_commit_hash'] == issue_reg['prev_commit_hash']
                         and issue_reg['issue_name'] == r['issue'].get_simple_name()
                         and r['repo_dir'] == issue_reg['repo_dir']
                         and  issue_reg['issue_name'] == r['issue'].get_simple_name() ]
    if len(matching_instance) == 0:
        return None
    return get_file_content(matching_instance[0]['repo_dir'], matching_instance[0]['prev_commit_hash'],
                            matching_instance[0]['issue'], None)


def zero_shot_procedure():
    # load at most 30 instances of each issue
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    issue_list = load_true_positive_issues()
    issue_buckets = create_issue_buckets(issue_list)
    for issue_name, issue_list in issue_buckets.items():
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        issue_spec = issue_specs[issue_name]
        print(issue_spec)
        for j, issue_instance in enumerate(issue_list):
            print(f"Sample {j}")
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            if code_sample is None:
                loge(f"Code sample not found for {issue_instance}")
                continue
            res = zero_shot_issues_detection(code_sample, max_tokens=None)
            if "no issues" in res.lower():
                loge("No issues detected")
            else:
                print(res)
                logs("Issue detected")
            res2 = zero_shot_issue_detection_detailed(code_sample, issue_spec)
            print(res2)


def few_shot_issue_detection(code_sample, issue_spec, input_set):
    examples_st = '\n'.join([f"Example {i+1}:\n{ex[0]}\n\nExpected fix:\n{ex[1]}\n" for i, ex in enumerate(input_set)])
    prompt = f"""
    Given the following performance issue:
    {issue_spec['description']}
    and these code samples containing issue and the corresponding fix:
    {examples_st}
    Analyze the following code and evaluate if the performance issue exists. Answer only \"Exist\" or \"Not exist\".
    {code_sample}"""
    try:
        return send_to_llm(prompt).strip()
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        return "few shot failed"

def few_shot_procedure():
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    issue_list = load_true_positive_issues()
    issue_buckets = create_issue_buckets(issue_list)
    for issue_name, issue_list in issue_buckets.items():
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        issue_spec = issue_specs[issue_name]
        print(issue_spec)
        for j, issue_instance in enumerate(issue_list):
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            print(f"Sample {j}")
            val = re.sub(r'-{3,}', '---', issue_specs[issue_name][f'example_1']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example 1", len(val))
                print(val)
                exit(-1)
            prob, sol = val
            print("1-shot")
            input_set =  [(prob, sol)]
            res = few_shot_issue_detection(code_sample, issue_spec, input_set)
            print(res)
            val = re.sub(r'-{3,}', '---', issue_specs[issue_name][f'example_2']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example 2", len(val))
                print(val)
                exit(-1)
            prob2, sol2 = val
            input_set.append((prob2, sol2))
            print("2-shot")
            res2 = few_shot_issue_detection(code_sample, issue_spec, input_set)
            print(res2)

def chain_of_thought_detection(code_sample, issue_spec, input_set):
    examples_st = '\n'.join([f"Example {i+1}:\n{ex[0]}\n\nExpected fix:\n{ex[1]}\n" for i, ex in enumerate(input_set)])
    prompt = f"""
    Given the following performance issue:
    {issue_spec['description']}
    and these code samples containing issue and the corresponding fix:
    {examples_st}
    Analyze the following code and evaluate if the performance issue exists. Answer only \"Exist\" or \"Not exist\".
    {code_sample}"""
    #print(prompt)
    try:
        return send_to_llm(prompt).strip()
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        return "few shot failed"


def chain_of_thought_procedure():
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    issue_list = load_true_positive_issues()
    issue_buckets = create_issue_buckets(issue_list)
    for issue_name, issue_list in issue_buckets.items():
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        issue_spec = issue_specs[issue_name]
        print(issue_spec)
        for j, issue_instance in enumerate(issue_list):
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            print(f"Sample {j}")
            val = re.sub(r'-{3,}', '---', issue_specs[issue_name][f'example_1_annotated']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example 1", len(val))
                print(val)
                exit(-1)
            prob, sol = val
            val = re.sub(r'-{3,}', '---', issue_specs[issue_name][f'example_2_annotated']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example 2", len(val))
                print(val)
                exit(-1)
            prob2, sol2 = val
            input_set = [(prob, sol), (prob2, sol2)]
            res2 = chain_of_thought_detection(code_sample, issue_spec, input_set)
            print(res2)


def main():
    #blind_test_procedure()
    #zero_shot_procedure()
    #few_shot_procedure()
    chain_of_thought_procedure()

if __name__ == '__main__':
    main()
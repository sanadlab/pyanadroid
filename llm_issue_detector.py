import inspect
import os.path
import random
import re
import time
import traceback


import argparse
import csv
from dotenv import dotenv_values


from anadroid.analysis.metrics.Issues import issue_from_string
from anadroid.utils.Utils import execute_shell_command, loge, logs, logi, logw
from together import Together
from openai import OpenAI
from google import genai

from anadroid.view.cli.CliView import CLIView

# Set the base URL for Together AI
API_KEY=dotenv_values('.env')['TOGETHER_AI_API_KEY']
OPENAI_API_KEY=dotenv_values('.env')['OPEN_AI_KEY']
#client = Together(api_key=API_KEY)
#CURR_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

TOKEN_LIMIT = 128_000
DEFAULT_ISSUE_FILE_EXTENSIONS='-- "*.java" "*.kt" "*.xml" "*.kts" "*.gradle"'

RESULTS_FOLDER = "v2_llm_results"
#CURR_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
#CURR_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
#model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free
#CLASSIFIED_REGRESSIONS_FILE = "reclassified_true_positives.csv"
CLASSIFIED_REGRESSIONS_FILE = "true_positives_validated.csv"

LLM_DEFAULT_PARAMS = {
    'temperature': 0,
    'top_k': 1,
   # 'top_p': 0,
}

SUPPORTED_MODELS = {
    "llama-3.3-70B": {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    },
    "deepseek-R1-Llama": {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
    },
    "gpt-4o": {
        "model": "gpt-4o",
    },
    "gpt-4.1-mini": {
        "model": "gpt-4.1-mini-2025-04-14",
    },
    "gemini-2.0-flash": {
        "model": "gemini-2.0-flash",
    },
    "gemini-2.5-pro": {
        "model": "gemini-2.5-pro",
    },
    "mistral-nemo-instruct-2407": {
        "model": "mistral-nemo-instruct-2407",
    },
    "microsoft/phi-4-reasoning-plus": {
        "model": "microsoft/phi-4-reasoning-plus",
    },
    "gpt-oss-20b": {
        "model": "gpt-oss-20b",
    }
}

ISSUES_TO_EXCLUDE = {
    "InternalGetterSetter",
    "ViewTag",
    "UnusedResources",
    "UnusedIds"
}

def init_client(client_name, model):
    if client_name == "together":
        client = Together(api_key=dotenv_values('.env')['TOGETHER_AI_API_KEY'])
    elif client_name == "openai":
        client = OpenAI(api_key=dotenv_values('.env')['OPEN_AI_KEY'])
    elif client_name == "google":
        client = genai.Client(api_key=dotenv_values('.env')['GOOGLE_AI_STUDIO_API_KEY'])
    elif client_name == "local":
        if 'mistral' in model:
            client = OpenAI(api_key='ok', base_url='https://33cb3ca52b71.ngrok-free.app/v1/')
        else:
            client = OpenAI(api_key='ok', base_url='https://f1821545febf.ngrok-free.app/v1/')
    else:
        client = None
    return client


def get_model(model_name):
    if model_name not in SUPPORTED_MODELS and model_name != "None":
        raise Exception(f"Model {model_name} not supported")
    model = SUPPORTED_MODELS[model_name]['model'] if model_name in SUPPORTED_MODELS and 'model' in SUPPORTED_MODELS[model_name] else "None"
    return model



def save_answer_to_file(prompt, result, procedure_name):
    directory = os.path.join(RESULTS_FOLDER, CURR_MODEL.replace("/","_"), "outputs")
    if not os.path.exists(directory):
        os.makedirs(directory)
    key = procedure_name + '_' + str(hash(result[:16])) + ".txt"
    filename = os.path.join(directory, procedure_name + '_' + str(hash(result[:16])) + ".txt")
    print("filename is ", filename)
    with open(filename, 'a+') as file:
        file.write(prompt + "\n" + result)

#def send_to_llm(msg, max_tokens=None, temperature=LLM_DEFAULT_PARAMS['temperature'], top_k=LLM_DEFAULT_PARAMS['top_k'], top_p=None):
def send_to_llm(msg, max_tokens=None, temperature=None, top_k=None, top_p=None):
    if isinstance(CURR_CLIENT, Together):
        time.sleep(100)
        response = CURR_CLIENT.chat.completions.create(
            model=CURR_MODEL,
            messages=[{"role": "user", "content": msg}, {"role": "assistant", "content": "option: "}],
            max_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else (16 if not 'deepseek' in CURR_MODEL else None),
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )
        if 'deepseek' in CURR_MODEL and max_tokens is not None:
            mt = max_tokens if max_tokens is not None and max_tokens > 16 else 32
            return response.choices[0].message.content[-mt:].replace("<think>", "").replace("</think>", "").replace("\n", " ")
        return response.choices[0].message.content.replace("<think>", "").replace("</think>", "").replace("\n"," ")
    elif isinstance(CURR_CLIENT, OpenAI) and not('gpt' in CURR_MODEL and not 'oss' in CURR_MODEL):
        try:
            time.sleep(5)
            response = CURR_CLIENT.chat.completions.create(
                model=CURR_MODEL,
                messages=[
                    {"role": "system", "content": "You are a like a static analysis tool that flags performance issues in Android code. Don't include any reasoning"},
                    {"role": "user", "content": msg}
                ],
                max_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else 32,
                temperature=temperature
            )

        except Exception as e:
            traceback.print_exc()
            loge(f"Error sending to LLM: {e}")
            time.sleep(10)
            response = CURR_CLIENT.chat.completions.create(
                model=CURR_MODEL,
                messages=[
                    {"role": "system",
                     "content": "You are a like a static analysis tool that flags performance issues in Android code. Don't include any reasoning"},
                    {"role": "user", "content": msg}
                ],
                max_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                temperature=temperature
            )
        #print(response)
        return response.choices[-1].message.content
    elif isinstance(CURR_CLIENT, OpenAI):
        try:
            time.sleep(2)
            response = CURR_CLIENT.responses.create(
                model=CURR_MODEL,
                instructions="Act like a static analysis tool",
                input=msg,
                max_output_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                temperature=temperature
            )

        except Exception as e:
            traceback.print_exc()
            loge(f"Error sending to LLM: {e}")
            time.sleep(20)
            response = CURR_CLIENT.responses.create(
                model=CURR_MODEL,
                instructions="Act like a static analysis tool",
                input=msg,
                max_output_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                temperature=temperature
            )
        #print(response)
        return response.output_text
    elif isinstance(CURR_CLIENT, genai.Client):
        try:
            time.sleep(2)
            response = CURR_CLIENT.models.generate_content(
                model=CURR_MODEL,
                contents=msg,
                config={
                    #"max_output_tokens": max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                    "temperature": temperature,
                },
            )
        except Exception as e:
            loge(f"Error sending to LLM: {e}")
            time.sleep(30)
            response = CURR_CLIENT.models.generate_content(
                model=CURR_MODEL,
                contents=msg,
                config={
                    # "max_output_tokens": max_tokens if max_tokens is not None and max_tokens > 16 else 16,
                    "temperature": temperature,
                },
            )
        return response.text
    else:
        return None

def zero_shot_issues_detection(code_sample, max_tokens=32, error_val=None, call_id=None):
    prompt = f"""
    Analyze the following Android code and identify any potential performance issues:
    {code_sample}
    Answer only with the issues found, or "No issues" if none are present.
    """
    try:
        val = send_to_llm(prompt, max_tokens=max_tokens).strip()
        # get current_function name
        save_answer_to_file(prompt, val, f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return val.replace(";", "").replace("\n", " ") if val is not None else error_val
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        save_answer_to_file(prompt, str(e), f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return error_val


def blind_test_issue_detection_compare(code_sample, code_sample2, call_id):
    prompt = f"""
    Analyze the following alternative code solutions for Android.
    Sample 1:
    {code_sample}
    
    Sample 2:
    
    {code_sample2}

     I want to know which option is the most efficient/optimized. Respond with only one of the following options: "1" or "2", without any additional explanations
    """
    #print(prompt)
    try:
        val = send_to_llm(prompt, max_tokens=16).strip()
        save_answer_to_file(prompt, val, f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return val.replace(";", "").replace("\n", " ") if val is not None else 'Unknown'
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        save_answer_to_file(prompt, str(e), f"{inspect.currentframe().f_code.co_name}_{call_id}" )
        return 'Unknown'



def zero_shot_issue_detection_detailed(code_sample, issues_specification, call_id):
    prompt = f"""
    Analyze the following Android code for statically-detectable performance issues:

    {code_sample}

    Identify any of these issues:
    {issues_specification}
    
    Respond with only the name of the issues found, separated by commas, or "No issues detected" if none are present.
    """
    try:
        val = send_to_llm(prompt, max_tokens=1024).strip()
        save_answer_to_file(prompt, val, f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return val.replace(";", "").replace("\n", " ") if val is not None else "Unknown"
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        save_answer_to_file(prompt, str(e),f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return "Unknown"

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
            if issue_name in ISSUES_TO_EXCLUDE:
                logw(f"Excluding issue {issue_name} since it is on the blacklist")
                continue
            try:
                #print(issue_name)
                #print(row)
                issue = {
                    'name': issue_name,
                    'description': row[18],
                    'sample': row[19],
                    'expected_fix': row[20],
                    'file_extensions': row[21].strip().split(','),
                    'severity': row[22],
                    'example_1': read_file_content(os.path.join(examples_fldr, row[23].strip())),
                    'example_2':  read_file_content(os.path.join(examples_fldr, row[24].strip())),
                    'example_1_annotated': read_file_content(os.path.join(examples_fldr, row[23].strip().replace("1.txt", "_annotated_1.txt"))),
                    'example_2_annotated': read_file_content(os.path.join(examples_fldr, row[24].strip().replace("2.txt", "_annotated_2.txt"))),
                }

            except Exception as e:
                loge(f"Error loading issue {issue_name}")
                print(e)
                print(row)
                continue
            issues[issue_name] = issue
    return issues

def blind_test_procedure_examples(repeat=False):
    filename = "blind_test_examples.csv"
    issue_spec = load_issue_specification_list()
    already_processed_issues = load_engineered_issues(filename)
    print(f"Loaded {len(issue_spec)} issues")
    for i, issue in enumerate(issue_spec):
        issue_spec_str = '\n'.join([f"{iss['name']}: {iss['description']}" for iss in list(issue_spec.values())[i:( i + 50)]])
        #print(issue_spec_str)
        if issue in already_processed_issues and not repeat:
            print(f"Skipping {issue}")
            continue
        print(f"Testing issue: {issue}")
        for j in range(1, 3):
            print(f"Example {j}")
            val = re.sub(r'-{3,}', '---', issue_spec[issue][f'example_{j}'] ).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example", len(val))
                print(val)
                exit(-1)
            prob, sol = val
            if prob is None or sol is None:
                print("Invalid example", len(val))
                print(val)
                exit(-1)
            if prob == sol:
                loge("Invalid example: problem and solution are the same")
                exit(-2)
            sol_list = [prob, sol]
            random.shuffle(sol_list)
            optimal_answer = 1 if prob == sol_list[1] else 2
            bld_cmp = blind_test_issue_detection_compare(sol_list[0], sol_list[1], call_id=f"{inspect.currentframe().f_code.co_name}_{issue}_{j}")
            print(bld_cmp)
            # use regex to extract number from bld_cmp string
            try:
                answer = re.search(r'\d', bld_cmp)
                print("llm answer", answer.group(0), "optimal answer", optimal_answer)
                correct_call = "Detected" if int(answer.group(0)) == optimal_answer else "Not detected"
            except:
                correct_call = "Inconclusive" if bld_cmp != "Unknown" else bld_cmp
            if correct_call == "Detected":
                logs(f"Correct answer")
            else:
                loge(f"Incorrect answer " + correct_call)
                print(bld_cmp)
            save_label(filename, issue, f"example_{j}",
                       bld_cmp, 'TP', correct_call)

def save_label(file_path, issue_name, issue_instance_id, result, expected, label, results_folder=RESULTS_FOLDER):
    print(file_path)
    target_folder = os.path.join(results_folder, CURR_MODEL)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    with open(os.path.join(target_folder, file_path), 'a+') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([issue_name] + issue_instance_id.split(";") + [result, expected, label])

def blind_test_procedure_real(issue_source):
    if issue_source == "vibe_coding":
        loge("Vibe coding not supported. there is no corresponding solutions available")
        return
    filename = f"{issue_source}_blind_test_real.csv"
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    issue_list = get_issue_list(issue_source)
    issue_buckets = create_issue_buckets(issue_list, bucket_size=100)
    already_processed_issues = load_engineered_issues(filename)
    for issue_name, issue_list in issue_buckets.items():
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        try:
            issue_spec = issue_specs[issue_name]
        except:
            loge(f"Error loading issue {issue_name}")
            continue
        #print(issue_spec)
        for j, issue_instance in enumerate(issue_list):
            print(f"Sample {j}")
            issue_instance_id = f"{issue_instance['repo_dir']}" + (f";{issue_instance['prev_commit_hash']}" if issue_instance.get('prev_commit_hash', None) is not None else "")
            if issue_instance_id in already_processed_issues.get(issue_name, {}):
                print(f"Skipping {issue_instance_id}")
                continue
            print(issue_instance)
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            sol_sample = fetch_sol_code_from_issue(issue_instance, regressions)
            if code_sample is None or sol_sample is None or code_sample == sol_sample:
                loge("Invalid examples: " + str(issue_name) + f" equals ? {code_sample == sol_sample} None? {code_sample is None} {sol_sample is None}")
                continue
            sol_list = [code_sample, sol_sample]
            random.shuffle(sol_list)
            optimal_answer = 1 if code_sample == sol_list[1] else 2
            bld_cmp = blind_test_issue_detection_compare(sol_list[0], sol_list[1], call_id=f"{inspect.currentframe().f_code.co_name}_{issue_name}_{j}")
            print("optimal answer", optimal_answer, "llm answer", bld_cmp, " ||")
            try:
                answer = re.search(r'\d', bld_cmp)
                print("llm answer", answer.group(0), "optimal answer", optimal_answer)
                correct_call = "Detected" if int(answer.group(0)) == optimal_answer else "Not detected"
            except:
                correct_call = "Inconclusive" if bld_cmp != "Unknown" else bld_cmp
            if correct_call == "Detected":
                logs(f"Correct answer")
            else:
                loge(f"Incorrect answer " + correct_call)
            save_label(filename, issue_name, issue_instance_id, bld_cmp.replace(";", ""), 'TP' ,correct_call)
            print("--------")

def load_regressions_csv(csv_file="all_regressions.csv"):
    regressions = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            if len(row) <= 5:
                continue
            v = {
                    'repo_dir': row[0].replace("\"",""),
                    'prev_commit_hash': row[1],
                    'commit_hash': row[2],
                    'commit_message': row[3],
                    'issue': issue_from_string(''.join(row[4:-1])),
                    'classification': row[-1],
                }
            if v['issue'] is None:
                #loge(f"Error loading issue from string: {row[4]}")
                continue
            regressions.append(v)
            #print('caoc')
    print("sapinho", len(regressions))
    return regressions

def load_classified_extra_c2(filename="final_all_man_annotated.csv"):
    labels = []
    if not os.path.exists(filename):
        return labels
    i = 0
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # gen_label_key(reg['repo_dir'], reg['prev_commit_hash'], reg['commit_hash'], issue_name)
            print(i)
            label = {
                'tool': row[0],
                'issue_name': row[1],
                'repo_dir': row[2],
                'issue_location': row[3],
                'prev_commit_hash': row[4],
                'fix_commit_hash': row[5],
                'commit_message': row[6],
                'sub_git_diff': row[7],
                'sub_file_ctnt': row[8],
                'pre_label': row[9],
                'llm_label': row[10],
                #'llm_label_2': row[10] if len(row) < 11 else row[11],
                'reason': row[11]
            }
            if len(row) > 12:
                label['manual_label'] = row[-1]
                if row[-1] in ['real_unknown']:
                    continue
            labels.append(label)
            i = i + 1
    return labels

def load_classified_regressions(filename=CLASSIFIED_REGRESSIONS_FILE):
    regressions = []
    if not os.path.exists(filename):
        return regressions
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            if len(row) < 10:
                continue
            v = {
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
            if len(row) > 10:
                v['validated_label'] = row[10].replace(',', '').replace('real_true_positive', "True_Positive").replace('real_false_positive', 'False_Positive') if len(row) > 10 and row[10] is not None else None

            regressions.append(v)
            #print(v)
    #print(regressions)

    print(f"Loaded {len(regressions)} classified regressions")
    #print(regressions)
    return regressions

def load_true_positive_issues():
    return [issue for issue in load_classified_regressions()
                if issue.get('validated_label', '') in ['True_Positive', 'real_true_positive']
                or (issue.get('validated_label', None) is None and ['llm_label'] == 'True_Positive')
            ]

def create_issue_buckets(issue_list, bucket_size=50, ignore_duplicate_file=False):
    issue_buckets = {}
    for issue in issue_list:
        if issue['issue_name'] not in issue_buckets:
            issue_buckets[issue['issue_name']] = []
        if ignore_duplicate_file:
            #print(issue.get('issue_location', '').split('|')[0].split(os.sep)[-1])
            is_issue_on_that_repo_already_there = any([i for i in issue_buckets[issue['issue_name']] if i['repo_dir'] == issue['repo_dir']
                                            and i.get('prev_commit_hash', None) == issue.get('prev_commit_hash', None)
                                            and i.get('issue_location', '').split('|')[0].split(os.sep)[-1] == issue.get('issue_location', '').split('|')[0].split(os.sep)[-1]
                                            ])
        else:
            is_issue_on_that_repo_already_there = False
        if is_issue_on_that_repo_already_there or len(issue_buckets[issue['issue_name']]) >= bucket_size:
            continue
        issue_buckets[issue['issue_name']].append(issue)
    #print(sum(len(v) for v in issue_buckets.values()), "issues loaded")
    return issue_buckets


def get_issue_file(repo_dir, curr_commit, issue, filename=None):
    if filename is None and (issue is None or getattr(issue, 'file') is None):
        return None
    file_n = filename if filename is not None else issue.file
    cm = curr_commit if curr_commit is not None else 'master' if issue is None else getattr(issue, 'file')
    if cm == '':
        cm = 'master'
    if repo_dir == '':
        return None
    file_cmd = f'cd {repo_dir} ; git checkout -f {cm} > /dev/null 2>&1 ; find {repo_dir} -type f -name { os.path.basename(file_n)} | head -1'
    #print(file_cmd)
    file_find = execute_shell_command(file_cmd)
    #print(file_find)
    file_find.validate()
    return file_find.output.strip() if file_find.output.strip() != "" else None


def get_file_content(repo_dir, curr_commit, issue, filename=None):
    issue_file = get_issue_file(repo_dir, curr_commit, issue, filename)
    if issue_file is None:
        return None
    cont_cmd = f'git -C {repo_dir} show {curr_commit}:{issue_file.strip()}'
    #print(cont_cmd)
    file_content_res = execute_shell_command(cont_cmd)
    if file_content_res.return_code != 0 and issue_file is not None and os.path.exists(issue_file):
        file_content_res = execute_shell_command(f'cat {issue_file}')
    #ret_file_code = file_content_res.return_code
    file_content = file_content_res.output
    if file_content.strip() == "":
        file_content = None
    return file_content


def fetch_code_from_issue(issue_reg, regressions_list):
    matching_instance = [r for r in regressions_list if r.get('prev_commit_hash', None) == issue_reg.get('prev_commit_hash', None)
                         and issue_reg['issue_name'] == r['issue'].get_simple_name()
                         and r['repo_dir'] == issue_reg['repo_dir']
                         and  issue_reg['issue_name'] == r['issue'].get_simple_name() ]
    if len(matching_instance) == 0:
        return get_file_content(issue_reg['repo_dir'],
                                issue_reg.get('prev_commit_hash',None),
                                None, filename=issue_reg['issue_location'].split("|")[0].split(":")[-1].strip())

    has_line_info = matching_instance[0]['issue'].line is not None
    if has_line_info:
        print(issue_reg['issue_name'], "has Line  info", matching_instance[0]['issue'].line)
    return get_file_content(matching_instance[0]['repo_dir'], matching_instance[0]['prev_commit_hash'],
                            matching_instance[0]['issue'], None)


def fetch_sol_code_from_issue(issue_reg, regressions_list):
    #print(issue_reg)
    #print(regressions_list[0])
    matching_instance = [r for r in regressions_list if r.get('commit_hash') == issue_reg.get('fix_commit_hash')
                         and issue_reg['issue_name'] == r['issue'].get_simple_name()
                         and r['repo_dir'] == issue_reg['repo_dir']
                         and  issue_reg['issue_name'] == r['issue'].get_simple_name() ]
    if len(matching_instance) == 0:
        return get_file_content(issue_reg['repo_dir'],
                                issue_reg.get('fix_commit_hash', None),
                                None, filename=issue_reg['issue_location'].split("|")[0].split(":")[-1].strip())
    return get_file_content(matching_instance[0]['repo_dir'], matching_instance[0]['commit_hash'],
                            matching_instance[0]['issue'], None)


def zero_shot_code_samples():
    issue_specs = load_issue_specification_list()
    filename = "zero_shot_samples.csv"
    already_processed_issues = load_engineered_issues(filename)
    for i, issue in enumerate(issue_specs):
        # print(issue_spec_str)
        if issue in already_processed_issues:
            print(f"Skipping {issue}")
            continue
        print(f"Testing issue: {issue}")
        for j in range(1, 3):
            print(f"Example {j}")
            val = re.sub(r'-{3,}', '---', issue_specs[issue][f'example_{j}']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example", len(val))
                print(val)
                exit(-1)
            prob, _ = val
            res = zero_shot_issues_detection(prob, call_id=f"{inspect.currentframe().f_code.co_name}_{issue}_{j}")
            if res is None:
                correct_call = "Inconclusive"
                res = correct_call
                loge("Inconclusive")
            elif "no issues" in res.lower():
                loge("No issues detected")
                correct_call = "Not Detected"
            else: # issue.lower() in res.lower():
                logs("Issue detected")
                correct_call = "Detected"
                logs("Issue detected")
            save_label(filename, issue, f"Example_{j}" ,res.replace(";", ""), 'TRUE',
                       correct_call)

def zero_shot_procedure(issue_source, randomize=False):
    # load at most N instances of each issue
    PROMPT_ISSUE_LIST_SIZE = 25
    filename = f"{issue_source}_zero_shot_real_detailed_{'randomized_sliding_window_' if randomize else ''}{PROMPT_ISSUE_LIST_SIZE}.csv"
    n_instances = 50
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    print("Loaded", len(regressions), "regressions")
    issue_list = get_issue_list(issue_source)
    issue_buckets = create_issue_buckets(issue_list, bucket_size=n_instances)
    already_processed_issues = load_engineered_issues(filename)
    #zero_shot_code_samples()
    i = 0
    issue_names_list = list(issue_specs.keys())
    for issue_name, issue_list in issue_buckets.items():
        index_of_issue = issue_names_list.index(issue_name) if issue_name not in ISSUES_TO_EXCLUDE else -1
        if randomize:
            random.shuffle(issue_names_list)
            index_of_issue = issue_names_list.index(issue_name) if issue_name not in ISSUES_TO_EXCLUDE else -1
        issues_on_list = issue_names_list[max(0, index_of_issue-1): min(len(issue_names_list), index_of_issue + (PROMPT_ISSUE_LIST_SIZE - 1))]
        issue_spec_str = '\n'.join(
            [f"{issue_specs[iss]['name']}: {issue_specs[iss]['description']}" for iss in  issues_on_list])
        # issue_spec_str = '\n'.join(
        #             [f"{iss['name']}: {iss['description']}" for iss in list(issue_specs.values())[(min(max(0, index_of_issue-1), len(list(issue_specs.values()))-25)): (index_of_issue + 24)]])
        #         i = i + 1
        i = i + 1
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        print("feeding ", len(issue_spec_str.split('\n')) , ' issues as list')
        try:
            issue_spec = issue_specs[issue_name]
        except:
            loge(f"Error loading issue {issue_name}")
            continue
        if issue_name not in issue_spec_str:
            print("bad algo")
            exit(-2)
        for j, issue_instance in enumerate(issue_list):
            print(f"Sample {j}")
            print(issue_instance)
            issue_instance_id = f"{issue_instance['repo_dir']}" + (
                f";{issue_instance['issue_location']}" if issue_instance.get('issue_location',
                                                                               None) is not None else "")
            if issue_instance_id in already_processed_issues.get(issue_name, {}):
                print(f"Skipping {issue_instance_id}")
                continue
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            if code_sample is None or code_sample == '':
                loge(f"Code sample not found for {issue_instance}")
                continue
            expected_label = issue_instance['manual_label'] if 'manual_label' in issue_instance else issue_instance['llm_label'] if 'validated_label' not in issue_instance else issue_instance[
                'validated_label']
            print(expected_label, issue_instance)
            res = zero_shot_issue_detection_detailed(code_sample, issue_spec_str, call_id=f"{issue_name}_{j}")
            print('res', res)
            print(issue_name)
            if res is None:
                correct_call = "Inconclusive"
                res = correct_call
                loge("Inconclusive")
            elif "no issues" in res.lower():
                loge("No issues detected")
                correct_call = "Not Detected"
            elif issue_name.lower() in res.lower():
                logs("Issue detected")
                correct_call = "Detected"
            elif len([x for x in issues_on_list if x.lower() in res.lower()]) > 0:
                loge("Other issue detected")
                correct_call = "Not Detected"
            else:
                correct_call = "Inconclusive"
                res = correct_call
            save_label(filename, issue_name, issue_instance_id,
                       res.replace(";","").replace("\n", ' '),expected_label, correct_call)


def few_shot_issue_detection(code_sample, issue_spec, input_set, call_id=None, no_fix=True):
    if no_fix:
        examples_st = '\n'.join(
            [f"Example {i + 1}:\n{ex[0]}\n\n" for i, ex in enumerate(input_set)])
    else:
        examples_st = '\n'.join([f"Example {i+1}:\n{ex[0]}\n\nExpected fix:\n{ex[1]}\n" for i, ex in enumerate(input_set)])
    prompt = f"""
    Given the following performance issue:
    {issue_spec['name']}
    {issue_spec['description']}
    and these Android code samples containing such issue{' and the corresponding fix' if not no_fix else ''}:
    {examples_st}
    And the following code to be analyzed:
    
    {code_sample}
    
    Analyze the code above and evaluate if the {issue_spec['name']} issue exists. Answer only with \"Exists\" or \"Does not exist\".
    """
    try:
        val = send_to_llm(prompt).strip()
        save_answer_to_file(prompt, val, f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return val.replace(";", "").replace("\n", " ") if val is not None else "few shot failed"
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        save_answer_to_file(prompt, str(e), f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return "few shot failed"



def few_shot_procedure(issue_source="true_positives", no_fix=True):
    print("few shot")
    filename = f"{issue_source}_2_shot{'_nofix' if no_fix else ''}.csv"
    n_instances = 50
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    issue_list = get_issue_list(issue_source)
    print(len(issue_list))
    issue_buckets = create_issue_buckets(issue_list, bucket_size=n_instances)
    already_processed_issues = load_engineered_issues(filename)
    for issue_name, issue_list in issue_buckets.items():
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        try:
            issue_spec = issue_specs[issue_name]
        except:
            loge(f"Error loading issue {issue_name}")
            continue
        #print(issue_spec)
        for j, issue_instance in enumerate(issue_list):

            issue_commit_hash = issue_instance.get('prev_commit_hash', '')
            issue_instance_id = f"{issue_instance['repo_dir']}{(';' + issue_commit_hash) if issue_commit_hash != '' else ''}"
            #issue_instance_id = f"{issue_instance['repo_dir']}{os.path.basename(issue_instance.get('issue_location'))}{(';' + issue_commit_hash) if issue_commit_hash != '' else ''}"
            #print(already_processed_issues.get(issue_name))
            if issue_instance_id in already_processed_issues.get(issue_name, {}) and already_processed_issues.get(issue_name)[issue_instance_id][-1].lower() not in ['unknown', "inconclusive"]:
                print(f"Skipping {issue_instance_id}")
                continue
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            if code_sample is None or code_sample == '':
                loge(f"Code sample not found for {issue_instance}")
                continue
            print(f"Sample {j}")
            val = re.sub(r'-{3,}', '---', issue_specs[issue_name][f'example_1']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example 1", len(val))
                print(val)
                exit(-1)
            prob, sol = val
            print("1-shot")
            input_set =  [(prob, sol)]
            res = few_shot_issue_detection(code_sample, issue_spec, input_set, call_id=f"{inspect.currentframe().f_code.co_name}_{issue_name}_{j}", no_fix=no_fix)
            if "not exist" in res.lower():
                loge("No issues detected")
                correct_call = "Not Detected"
                print(res)
            elif 'exists' in res.lower() and 'not' not in res.lower():
                logs("Issue detected")
                correct_call = "Detected"
            else:
                correct_call = "Inconclusive"
                #print(res)
                loge(correct_call)
            expected_label = issue_instance['llm_label'] if 'validated_label' not in issue_instance else issue_instance['validated_label']
            #issue_instance_id = f"{issue_instance['repo_dir']};{issue_commit_hash}"
            save_label(f"{issue_source}_1_shot{'_nofix' if no_fix else ''}.csv", issue_name, issue_instance_id,
                       res.replace(";",""), expected_label, correct_call)
            print(res)
            val = re.sub(r'-{3,}', '---', issue_specs[issue_name][f'example_2']).split("---")
            if len(val) > 2 or len(val) < 2:
                print("Invalid example 2", len(val))
                print(val)
                exit(-1)
            prob2, sol2 = val
            input_set.append((prob2, sol2))
            print("2-shot")
            res = few_shot_issue_detection(code_sample, issue_spec, input_set, call_id=f"{inspect.currentframe().f_code.co_name}_2_{issue_name}_{j}", no_fix=no_fix)
            if "not exist" in res.lower():
                loge("No issues detected")
                correct_call = "Not Detected"
            elif 'exists' in res.lower():
                logs("Issue detected")
                correct_call = "Detected"
            else:
                correct_call = "Inconclusive"
                # print(res)
                loge(correct_call)
            save_label(filename, issue_name, issue_instance_id,
                       res.replace(";", ""), expected_label, correct_call)

def chain_of_thought_detection(code_sample, issue_spec, input_set, call_id, no_fix=True):
    if no_fix:
        examples_st = '\n'.join(
            [f"Example {i + 1}:\n{ex[0]}\n\n" for i, ex in enumerate(input_set)])
    else:
        examples_st = '\n'.join([f"Example {i+1}:\n{ex[0]}\n\nExpected fix:\n{ex[1]}\n" for i, ex in enumerate(input_set)])
    prompt = f"""
    Given the following performance issue:
    {issue_spec['name']}
    {issue_spec['description']}
    and these annotated code samples containing such issue and a corresponding fix:
    {examples_st}
    And the following code to be analyzed:
    
    {code_sample}
    
    Analyze the code above and evaluate if the {issue_spec['name']} issue exists. Answer only with \"Exists\" or \"Does not exist\"."""
    #print(prompt)
    try:
        val = send_to_llm(prompt).strip()
        save_answer_to_file(prompt, val, f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return val.replace(";", "").replace("\n", " ") if val is not None else "Failed"
    except Exception as e:
        loge(f"Error sending to LLM: {e}")
        save_answer_to_file(prompt, str(e), f"{inspect.currentframe().f_code.co_name}_{call_id}")
        return "Failed"


def load_engineered_issues(filename):
    target_file = os.path.join(RESULTS_FOLDER, CURR_MODEL, filename)
    print(target_file)
    if not os.path.exists(target_file):
        return {}
    print(target_file)
    with open(target_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        issues = {}
        for row in reader:
            if len(row) < 3:
                continue
            #row[0] = row[0].strip().replace("\"", "")
            #row[1] = row[1].strip().replace("\"", "")
            if row[0] not in issues:
                issues[row[0]] = {}
            issues[row[0]][row[1]+';'+row[2]] = row
    return issues

def chain_of_thought_procedure(repeat=False, issue_source="true_positives", no_fix=True):
    filename = f"{issue_source}_cot{'_nofix' if no_fix else ''}.csv"
    n_instances = 100
    already_processed_issues = load_engineered_issues(filename)
    issue_specs = load_issue_specification_list()
    regressions = load_regressions_csv()
    issue_list = get_issue_list(issue_source)
    issue_buckets = create_issue_buckets(issue_list, bucket_size=n_instances)
    non_proc_candidates = already_processed_issues.copy()
    for issue_name, issue_list in issue_buckets.items():
        print(f"Checking issue: {issue_name}", len(issue_list), "instances")
        try:
            issue_spec = issue_specs[issue_name]
        except:
            loge(f"Error loading issue {issue_name}")
            continue
        print(issue_spec)
        for j, issue_instance in enumerate(issue_list):
            issue_commit_hash = issue_instance.get('prev_commit_hash', '')
            issue_instance_id = f"{issue_instance['repo_dir']}{(';' + issue_commit_hash) if issue_commit_hash != '' else ''}"

            if issue_instance_id in already_processed_issues.get(issue_name, {}):
                print(f"Skipping {issue_instance_id}")
                non_proc_candidates.pop(issue_name, None)
                continue
            code_sample = fetch_code_from_issue(issue_instance, regressions)
            if code_sample is None:
                loge(f"Code sample not found for {issue_instance}")
                continue
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
            res = chain_of_thought_detection(code_sample, issue_spec, input_set,  call_id=f"{inspect.currentframe().f_code.co_name}_{issue_name}_{j}", no_fix=no_fix)
            print(res)
            if "not exist" in res.lower():
                loge("No issues detected")
                correct_call = "Not Detected"
            elif 'exists' in res.lower():
                logs("Issue detected")
                correct_call = "Detected"
            else:
                correct_call = "Inconclusive"
                # print(res)
                loge(correct_call)
            expected_label = issue_instance['llm_label'] if 'validated_label' not in issue_instance else issue_instance['validated_label']
            save_label(filename, issue_name, issue_instance_id,
                       res.replace(";", ""), expected_label, correct_call)
    print(non_proc_candidates)

def blind_shot(issue_source):
    blind_test_procedure_examples()
    blind_test_procedure_real(issue_source=issue_source)

def zero_shot(issue_source):
    print("Zero shot")
    #zero_shot_code_samples()
    zero_shot_procedure(issue_source=issue_source)

def main(issue_source, no_fix=True):
    #blind_shot(issue_source=issue_source)
    zero_shot(issue_source=issue_source)
    #few_shot_procedure(issue_source=issue_source, no_fix=no_fix)
    #chain_of_thought_procedure(issue_source=issue_source, no_fix=no_fix)


def get_issue_list(source):
    if "true_positives" in source:
        return load_true_positive_issues()
    elif source == "vibe_coding":
        res = load_vibe_coding_issues()
        return res
    elif source == "true_positive_fixes":
        res  = load_true_positive_issues()
        return res
    elif source == "remaining_c2":
        res  = load_classified_extra_c2()
        return res
    else:
        raise Exception(f"Unknown issue source {source}")

def load_vibe_coding_issues(filename="clean_vibe_coding_issues_annotated.csv"):
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return None
    with open(filename, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)
        issues = []
        for row in reader:
            #print(row)
            if len(row) < 12:
                continue
            issue = {
                'issue_name': row[1],
                'repo_dir': row[0],
                'issue_location': row[6],
                'validated_label': row[9],
                'reason_label': row[10],
                'llm_label': row[11]
            }
            issues.append(issue)
    return issues


if __name__ ==  '__main__':
    # parse args
    parser = argparse.ArgumentParser(description='LLM Issue Detector')
    parser.add_argument('--model', type=str, required=True, help='Model to use', choices=list(SUPPORTED_MODELS.keys()) + ["None"])
    parser.add_argument('--client', type=str, required=True, help='Client to use', choices=['together', 'openai', 'google', "local"])
    parser.add_argument('--repeat', action='store_true', help='Repeat the procedure even if it  was already executed', default=False)
    parser.add_argument('--issue_source', help='issue source to use', choices=['true_positive_fixes', 'remaining_c2', 'vibe_coding'], default='true_positives')
    args = parser.parse_args()
    global CURR_MODEL
    CURR_MODEL = get_model(args.model)
    global CURR_CLIENT
    CURR_CLIENT = init_client(args.client, CURR_MODEL)
    print(f"Using model {CURR_MODEL} with client {args.client}")
    not_fix=False
    main(args.issue_source, no_fix=not_fix)
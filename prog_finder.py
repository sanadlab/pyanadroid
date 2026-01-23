import csv
import os.path
import time
import traceback
from dotenv import dotenv_values
from anadroid.utils.Utils import execute_shell_command, loge, logs, logi
from builDroid.agents.base import retry
from openai import OpenAI
from google import genai

# script that looks in the bigger progressions csv file to search for specific line corresponding to the

MODEL = 'gemini-2.5-pro'

PATTERN_EXCEPTIONS = {
   # 'DAAP': {'CollectionOfViews'},
}

IGNORE_ISSUES = ['UnusedIds', 'UnusedResources', 'SyntheticAccessor']

def init_client(client_name):
    if client_name == "openai":
        client = OpenAI(api_key=dotenv_values('.env')['OPEN_AI_KEY'])
    elif client_name == "google":
        client = genai.Client(api_key=dotenv_values('.env')['GOOGLE_AI_STUDIO_API_KEY'])
    else:
        client = None
    return client



def send_to_llm(msg, client, max_tokens=None):
    if isinstance(client, OpenAI):
        try:
            time.sleep(2)
            response = client.responses.create(
                model=MODEL,
                instructions="Act like a static analysis tool",
                input=msg,
                max_output_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else 16
            )
        except Exception as e:
            loge(f"Error sending to LLM: {e}")
            time.sleep(20)
            response = client.responses.create(
                model=MODEL,
                instructions="Act like a static analysis tool",
                input=msg,
                max_output_tokens=max_tokens if max_tokens is not None and max_tokens > 16 else 16
            )
        #print(response)
        return response.output_text
    elif isinstance(client, genai.Client):
        try:
            time.sleep(2)
            response = client.models.generate_content(
                model=MODEL,
                contents=msg,
            )
        except Exception as e:
            loge(f"Error sending to LLM: {e}")
            time.sleep(30)
            response = client.models.generate_content(
                model=MODEL,
                contents=msg,
            )
        return response.text
    else:
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
            }
            #print(f"Loaded issue {i+1}: { issues[issue_name]}")
    return issues

def explain_why(file_content, issue):
    question = f"""
                Explain why this performance issue is not present in this file and what could have caused it to be a false positive raised by a static analysis tool.
            """
    # code_diff_res = get_code_diff(repo_dir, curr_commit, issue, extensions=issue.get_file_extensions())
    prompt = f"""
                Given the following specification of this statically detectable performance issue:
                Issue specification: {issue['description']}
                Expected fix: {issue['expected_fix']}
                File content: 
                {file_content}
                {question}
            """
    submitted_file_content = True
    submitted_git_diff = True
    # print(prompt)
    client = init_client("google")
    try:
        res = send_to_llm(prompt, client)
        return res
    except Exception as e:
        traceback.print_exc()
        time.sleep(2)
        loge(f"Error sending to LLM: {e}")
    return "Error"

def check_if_fp(file_content, issue, explain=True):
    question = f"""
            I want to know if this specific issue exists in this file.
            Respond with only one of the following options: "Exist" or "Does not Exist", without any additional explanations
        """
    # code_diff_res = get_code_diff(repo_dir, curr_commit, issue, extensions=issue.get_file_extensions())
    prompt = f"""
            Given the following specification of this statically detectable performance issue:
            Issue specification: {issue['description']}
            Expected fix: {issue['expected_fix']}
            File content: 
            {file_content}
            {question}
        """
    submitted_file_content = True
    submitted_git_diff = True
    # print(prompt)
    client = init_client("google")
    explan = ''
    try:
        res = send_to_llm(prompt, client)
        if 'not' in res and explain:
            explan = explain_why(file_content, issue)
        return res, explan
    except Exception as e:
        traceback.print_exc()
        time.sleep(2)
        loge(f"Error sending to LLM: {e}")
    return "Error", explan


def main(pos_file, reg_file):
    proc_file = process_files(pos_file, reg_file)
    issue_spec = load_issue_specification_list()
    #final_fp_file = 'final_sats_false_positives.csv'
    final_fp_file = 'final_sats_false_positives_extra_tools.csv'
    extra_tp_file = 'final_sats_extra_tp_positives_extra_tools.csv'
    existing_lines = []
    existing_tp_lines = []
    if os.path.exists(final_fp_file):
        # load existing results
        print(f"Loading existing results from {final_fp_file}")
        with open(final_fp_file, 'r') as f:
            existing_lines = f.readlines()
        print(f"Loaded {len(existing_lines)} existing results")
    if os.path.exists(extra_tp_file):
        print(f"Loading existing results from {extra_tp_file}")
        with open(extra_tp_file, 'r') as f:
            existing_tp_lines = f.readlines()
        print(f"Loaded {len(existing_tp_lines)} existing results")
    # read file
    print('reading', proc_file)
    with open(proc_file, 'r') as f:
        lines = f.readlines()
    print(f"Processing {len(lines)} lines from {proc_file}")
    for i, li in enumerate(lines):
        if any([x for x in existing_lines if li.strip() in x and 'Error sending to LLM' not in li]):
            print(f"Skipping existing line {i+1}/{len(lines)}")
            continue
        if  any([x for x in existing_tp_lines if li.strip() in x and 'Error sending to LLM' not in li]):
            print(f"Skipping existing line {i+1}/{len(lines)}")
            continue
        parts = li.strip().split(';')
        #print(parts)
        tool = parts[0]
        if 'lint' not in tool.lower():
            continue
        #print(tool)
        project = parts[1].strip().replace('NONE_TRANSFORMED_', '')
        issue_hash = parts[2].strip()
        issue = parts[5].split(',')[0].strip()

        try:
            if len(parts[5].split(',')) > 10:
                file = parts[5].split(',')[-5].strip().replace('NONE_TRANSFORMED_', '')
            else:
                file = parts[5].split(',')[5].strip().replace('NONE_TRANSFORMED_', '')
            #print(tool, issue, project, file, issue_hash)
            fl_cntnt = get_file_content(project, issue_hash, file)
        except:
            continue
        if fl_cntnt is None:
            loge(f"File content not found for {file} in project {project} at commit {issue_hash}")
            continue
        issue_definition =  issue_spec.get(issue, None)
        if issue_definition is None:
            loge(f"Issue definition not found for issue {issue}")
            continue
        print(issue_definition)
        if issue not in ["HasmapUsage",
                    "Overdraw",
                    "URLCaching",
                    "NestedWeight",
                    "SyntheticAccessor",
                    "CollectionOfBitmaps",
                    "InefficientDataFormatAndParser",
                    "StaticBitmap",
                    "InternalGetterSetter",
                    "UselessStringValueOf",
                    "StaticContext",
                    "StringToString",
                    "BigIntegerInstantiation",
                    "UseArraysAsList",
                    "UseStringBufferLength",
                    "DroppedData",
                    "MemberIgnoringMethod",
                    "RigidAlarmManager",
                    "UseIndexOfChar",
                    "UseStringBufferForStringAppends",
                    "ConsecutiveLiteralAppends",
                    "NoLowMemoryResolver",
                    "AppendCharacterWithChar",
                    "AvoidFileStream",
                    "AvoidArrayLoops"]:
            continue

        res, exp = check_if_fp(fl_cntnt, issue_definition,
                               explain=not (tool in PATTERN_EXCEPTIONS and issue in PATTERN_EXCEPTIONS[tool]))
        print(res)
        if 'not' in res:
            logi(f'found one: {tool} | {issue} | {exp}')
            #fp_results.append(f'{li.strip()};{exp.replace("\n",'')};sat_false_positive')
            # save results to csv file
            with open(final_fp_file, 'a+') as f:
                x = exp.replace('\n','').replace(';', ',')
                r = f"{li.strip()};{x};sat_false_positive"
                f.write(f'{r}\n')
        elif 'xist' in res:
            logi(f'found one true positive: {tool} | {issue} | {res}')
            with open(extra_tp_file, 'a+') as f:
                x = res.replace("\n","")
                r = f"{li.strip()};{x};sat_true_positive"
                f.write(f'{r}\n')




def get_issue_file(repo_dir, curr_commit, filename):
    file_cmd = f'cd {repo_dir} ; git checkout -f {curr_commit} > /dev/null 2>&1 ; find . -type f -name {os.path.basename(filename)} | grep -v NONE_TRANSFORMED_ | head -1'
    print("file comd", file_cmd)
    file_find = execute_shell_command(file_cmd)
    file_find.validate()
    return file_find.output.strip() if file_find.output.strip() != "" else None

def get_file_content(repo_dir, curr_commit, filename, def_null_value=None):
    print(curr_commit)
    issue_file = get_issue_file(repo_dir, curr_commit, filename)
    if issue_file is None:
        return def_null_value
    cont_cmd = f'cd {repo_dir} && git show {curr_commit}:{issue_file.strip()}'
    print(cont_cmd)
    file_content_res = execute_shell_command(cont_cmd)
    file_content_res.validate()
    #ret_file_code = file_content_res.return_code
    file_content = file_content_res.output
    if file_content.strip() == "":
        file_content = def_null_value
    return file_content

def process_files(pos_file, reg_file, override=False):
    # read lines of reg_file csv file
    issue_count = {}
    max_issue_ct = 25
    filename = 'tool_annotated_' + pos_file
    if not override and os.path.exists(filename):
        return filename
    new_lines = []
    with open(reg_file, 'r') as f:
        reg_lines = f.readlines()
    # read pos_file csv file
    with open(pos_file, 'r') as f:
        pos_lines = f.readlines()
    for pos_line in pos_lines:
        pos_parts = pos_line.strip().split(';')
        #issue = pos_parts[0]
        #file = pos_parts[2]
        if len(pos_parts) < 6:
            print("Skipping invalid line:", pos_line)
            continue
        issue = pos_parts[4].split(',')[0].strip()
        if issue in IGNORE_ISSUES:
            continue
        if issue not in issue_count:
            issue_count[issue] = 0
        if issue_count[issue] >= max_issue_ct:
            print(f"Skipping issue {issue} as it has reached the maximum count of {max_issue_ct}")
            continue

        new_lines.append(f'Lint;{pos_line}')
        '''for reg_line in reg_lines:
            #print(issue, reg_line)
            if issue in reg_line  and issue_hash in reg_line and fix_hash in reg_line:
                tool = reg_line.split(';')[4].split(',')[3].strip()
                print("issue ", issue, ' found by ',  tool)
                new_lines.append(f'{tool};{pos_line}')
                issue_count[issue] += 1
                break'''
        # write new lines to new csv file

    with open(filename, 'w') as f:
        for line in new_lines:
            f.write(line)
    return filename

if __name__ == '__main__':
    #main("true_positives_validated.csv", 'fixed_big_progressions.csv')
    main("lintinho.csv", 'fixed_big_progressions.csv')
import csv
import os.path

from anadroid.analysis.metrics.Issues import issue_from_string
from anadroid.utils.Utils import execute_shell_command



def load_regressions_csv(csv_file="all_regressions.csv"):
    regressions = {}
    with open(csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            # /Users/rar9993/repos/research/fdroid_apps/native_apps/Player,7783f82bc5e9e238100ca9be0cd440b0a072d0e1,Merge branch 'master' into flavorless,"KnownStaticPerformanceIssues.MEMBER_IGNORING_METHOD, PERFORMANCE, None, DAAP None, /src/online/java/com/brouken/player/UpdateCheckJobService.java, None, None, None, None",def_removal
            if len(row) <= 5:
                continue
            try:
                issue =  issue_from_string(''.join(row[4:-1]))
            except:
                continue
            v = {
                    'repo_dir': row[0].replace("\"",""),
                    'prev_commit_hash': row[1],
                    'commit_hash': row[2],
                    'commit_message': row[3],
                    'issue': issue,
                    'classification': row[-1],
                }
            if v['issue'] is None:
                #loge(f"Error loading issue from string: {row[4]}")
                continue
            try:
                key = v['repo_dir'].strip() + '_' + v['prev_commit_hash'].strip() + '_' + str(v['issue'].issue_type.value.strip())
            except:
                continue
            #print(key)
            regressions[key] = [v] if key not in regressions else regressions[key] + [v]
            #print('caoc')
    print("sapinho", len(regressions))
    return regressions

def get_possible_hash_key(cand_result):
    return str(hash(cand_result[:16]))

def get_prompt_pre_end(task):
    if task == 'cot':
        return "Analyze the code above"
    return 'potato'

def main(task, dirname, issue_reg_file):
    list_of_csvs_res = execute_shell_command('find ' + dirname + ' -name "*' + task + '*.csv"')
    print(list_of_csvs_res.output)
    progs = load_regressions_csv(issue_reg_file)
    for csvf in list_of_csvs_res.output.strip().split('\n'):
        print('Processing ' + csvf)
        if 'gemini-2.5' not in csvf:
            continue
        model = csvf.split('/')[1]
        lines = open(csvf).readlines()
        print(len(lines))
        for csvline in lines:
            print('Processing ' + csvline)
            task_full_n = 'chain' if task == 'cot' else task
            issue = csvline.split(';')[0].strip()
            csv_key = '_'.join([csvline.split(';')[1], csvline.split(';')[2], csvline.split(';')[0]])
            #print(csv_key)
            old_file_key = get_possible_hash_key(csvline.split(';')[-1].strip())
            cmd = f"find {os.path.join(dirname, model)} -type f -name '*{issue}*.txt' | grep {task_full_n} "
            #print(cmd)
            corresponding_cand_files = execute_shell_command(cmd).output.strip().split('\n')
            #print(corresponding_cand_files)
            if len(corresponding_cand_files) == 0 or corresponding_cand_files == ['']:
                print(f"Warning: did not find candidate file for {csv_key} in model {model}")
            elif len(corresponding_cand_files) > 1:
                poss_cand = [cf for cf in corresponding_cand_files if old_file_key in cf]
                if len(poss_cand) == 1:
                    candidate = poss_cand[0]
                else:
                    print(corresponding_cand_files)
                    for cf in corresponding_cand_files:
                        file_c = execute_shell_command("tail -10 " + cf).output.split('\n')
                        print(file_c)
                        file_end = get_prompt_pre_end(task)
                        print(file_end)
                        # get line after the prompt

                        index_c = [i for i,line in enumerate(file_c) if file_end in line]
                        if len(index_c) == 0:
                            print('Warning: did not find prompt end in file ' + cf)
                            exit(-10)
                        index = index_c[0]
                        print('result', file_c[index+1])
                        cand_key = get_possible_hash_key('\n'.join(file_c[index+1]))
                        print(cand_key, cf)
                        if cand_key in cf:
                            print('Found candidate file:', cf)
                            exit(0)

                        print('---'* 10)
                        #exit(0)
                    exit(0)

            else:
                print(issue ,corresponding_cand_files[0])
            #print(corresponding_cand_files.output


if __name__ == '__main__':
    main(task='cot', dirname='v2_llm_results', issue_reg_file='fixed_big_progressions.csv')
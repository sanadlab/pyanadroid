import csv
import os
import traceback

from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK
from anadroid.analysis.ComposedAnalyzer import ComposedAnalyzer
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.device.MockedDevice import MockedDevice
from anadroid.utils.Utils import execute_shell_command, mega_find, logi, logs, loge


def init_pyanadroid(repo_dir):
    return AnaDroid(arg1=repo_dir,
                    testing_framework=TESTING_FRAMEWORK.NONE,
                    device=MockedDevice(),
                    profiler=PROFILER.NONE,
                    load_projects=True,
                    instrumenter=None)

def load_project_issues(proj_results_dir):
    issues_list = []
    adoctor_file = os.path.join(proj_results_dir, 'adoctor.csv')
    if os.path.exists(adoctor_file):
        #print("adoctor")
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
        for eco_dir in eco_android_dirs:
            issues_list = issues_list + EcoAndroidAnalysis().get_issues(eco_dir)
    lint_results = mega_find(proj_results_dir, pattern="*lint*.xml", type_file='f', maxdepth=2)
    if len(lint_results) > 0:
        for lint_file in lint_results:
            issues_list = issues_list + LintAnalysis().get_issues(lint_file)
    return issues_list

def analyze_repo(repos_dir):
    anadroid = init_pyanadroid(repos_dir)
    anadroid.pre_build_analyzers = ComposedAnalyzer(None,[DAAPAnalysis(), PMDAnalysis(), ADoctorAnalysis()])
    repo_list = list(anadroid.app_projects_ut)
    sorted_repo_list = []
    print("Sorting repos")
    for repo_dir in repo_list:
        print("Checking repo: ", repo_dir)
        bname, commit_list = extract_and_write_commit_history(repo_dir)
        sorted_repo_list.append((repo_dir, bname, commit_list))
    sorted_repo_list = sorted(sorted_repo_list, key=lambda x: len(x[2]))
    for repo_dir, branch_name, commit_list in sorted_repo_list:
        print("branch name is: ", branch_name, "and has ", len(commit_list), " commits")
        checkout_res = execute_shell_command(f"cd {repo_dir} && git checkout {branch_name}")
        checkout_res.validate()
        branch_name, commit_list = extract_and_write_commit_history(repo_dir)
        #print(commit_list)
        checkout_res.validate()
        prev_issue_list = []
        prev_commit_hash = None
        for i, commit in enumerate(commit_list):
            commit_hash = commit['hash']
            print(f"Checking out commit {i}/{len(commit_list)}: {commit_hash} -> {commit['message']}")
            #time.sleep(1)
            # Checkout the commit
            cmd = f"cd {repo_dir} && git checkout {commit_hash}"
            print(cmd)
            checkout_res = execute_shell_command(cmd)
            checkout_res.validate()
            print(checkout_res)
            # Run analysis tool (replace with actual analysis command)
            print(f"Running analysis on commit: {commit_hash}")
            anadroid.app_projects_ut = [repo_dir]
            res_dirs = anadroid.just_static_analyze()
            commit['issues'] = load_project_issues(res_dirs[0]) if len(res_dirs) > 0 else []
            logi(f"commit {commit_hash} has {len(commit['issues'])} issues")
            #analysis_res.validate()
            #print(f"Analysis completed for commit: {commit_hash}\n")
            checkout_res = execute_shell_command(f"cd {repo_dir} && git checkout {branch_name}")
            regressions = issue_regression(commit['issues'], prev_issue_list)
            if len(regressions) > 0:
                with open('regressions.csv', 'a+') as file:
                    writer = csv.writer(file, delimiter=';')
                    for reg in regressions:
                        line = [repo_dir, prev_commit_hash, commit_hash, commit['message'].replace(';', '.'), str(reg[0]), reg[1]]
                        writer.writerow(line)
            save_issues(commit['issues'], repo_dir, commit_hash)
            prev_issue_list = commit['issues']
            prev_commit_hash = commit_hash

def save_issues(issues, dir_path, commit_hash):
    file_path = os.path.join(dir_path, f"{commit_hash}_issues.csv")
    with open(file_path, 'w') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Issue Type', 'File', 'Line', 'Description'])
        for issue in issues:
            writer.writerow(str(issue).replace(',', ';').split(';'))

def issue_regression(curr_issue_list, prev_issue_list):
    regressions = []
    for issue in prev_issue_list:
        if issue not in curr_issue_list:
            loge(f"Regression found: {issue}")
            classif = classify_regression(issue, curr_issue_list)
            logi(f"Classification: {classif}")
            regressions.append((issue, classif))
    return regressions


def classify_regression(issue, curr_issue_list):
    issues_of_that_kind = [i for i in curr_issue_list if i.get_simple_name() == issue.get_simple_name()]
    issue_exists_on_proj = any(issues_of_that_kind)
    if not issue_exists_on_proj:
        return 'def_removal'
    issue_exists_on_file = any([i for i in issues_of_that_kind if i.file == issue.file])
    if issue_exists_on_file:
        return 'prob_move'
    return 'prob_removal'


def download_repo(repo_url):
    pass

def extract_and_write_commit_history(repo_dir):
    info = []
    branch_name_res = execute_shell_command(f"cd {repo_dir} && git branch --show-current")
    branch_name_res.validate()
    branch_name = branch_name_res.output.strip().replace("/", "-")
    res = execute_shell_command(f"cd {repo_dir} && git log --pretty=format:\"%H|%an|%ad|%BXX\" --date=iso")
    #print(res)
    res.validate()
    filename= os.path.join(repo_dir,f'{branch_name}_commit_data.csv' )
    with open(filename, 'w') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Commit Hash', 'Author', 'Date', 'Message'])
        for commit in res.output.split("XX\n"):
            vals = commit.split("|")
            if len(vals) > 1:
                try:
                    writer.writerow(vals)
                    info.append({
                        'hash': vals[0],
                        'author': vals[1],
                        'date': vals[2],
                        'message': vals[3].replace(';', '.').replace("\n", "\t")
                    })
                except:
                    traceback.print_exc()
                    print(commit)
    return branch_name, info[::-1]


if __name__ == '__main__':
    repos_directory = "/Users/rar9993/repos/research/fdroid_apps/native_apps/"
    analyze_repo(repos_directory)
    #uniformize_csv('regressions.csv')
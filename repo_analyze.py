import csv
import os
import traceback
import argparse
import multiprocessing
from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK
from anadroid.analysis.ComposedAnalyzer import ComposedAnalyzer
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.device.MockedDevice import MockedDevice
from anadroid.utils.Utils import execute_shell_command, logi, loge, mega_find


lock = multiprocessing.Lock()

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


def analyze_repo_subset(repos_list):
    """Analyzes a subset of repositories."""
    sorted_repo_list = []
    print("Sorting repos")
    for repo_dir in repos_list:
        print("Checking repo: ", repo_dir)
        bname, commit_list = extract_and_write_commit_history(repo_dir)
        sorted_repo_list.append((repo_dir, bname, commit_list))
    sorted_repo_list = sorted(sorted_repo_list, key=lambda x: len(x[2]))
    for repo_dir, branch_name, commit_list in sorted_repo_list:
        try:
            anadroid = init_pyanadroid(repo_dir)
            anadroid.pre_build_analyzers = ComposedAnalyzer(None, [DAAPAnalysis(), PMDAnalysis(), ADoctorAnalysis()])
            print(f"Analyzing repo: {repo_dir}")
            #branch_name, commit_list = extract_and_write_commit_history(repo_dir)
            print(f"Branch: {branch_name}, Commits: {len(commit_list)}")
            prev_issue_list = []
            prev_commit_hash = None
            for i, commit in enumerate(commit_list):
                commit_hash = commit['hash']
                print(f"Checking out commit {i + 1}/{len(commit_list)}: {commit_hash}")
                execute_shell_command(f"cd {repo_dir} && git reset --hard && git clean -fd && git checkout {commit_hash}").validate()
                # Run static analysis
                anadroid.app_projects_ut = [repo_dir]
                res_dirs = anadroid.just_static_analyze()
                commit['issues'] = load_project_issues(res_dirs[0]) if res_dirs else []
                logi(f"Commit {commit_hash} has {len(commit['issues'])} issues")
                # Checkout back to branch
                execute_shell_command(f"cd {repo_dir} && git reset --hard && git clean -fd && git checkout {branch_name}").validate()
                regressions = issue_regression(commit['issues'], prev_issue_list)
                if regressions:
                    with lock:
                        with open('regressions.csv', 'a+') as file:
                            writer = csv.writer(file, delimiter=';')
                            for reg in regressions:
                                writer.writerow(
                                    [repo_dir, prev_commit_hash, commit_hash, commit['message'].replace(';', '.'),
                                     str(reg[0]), reg[1]])
                save_issues(commit['issues'], repo_dir, commit_hash)
                prev_issue_list = commit['issues']
                prev_commit_hash = commit_hash

        except Exception as e:
            loge(f"Error analyzing repo {repo_dir}: {e}")
            traceback.print_exc()


def analyze_repos(repos_directory, num_processes=1):
    anadroid = init_pyanadroid(repos_directory)
    repo_list = list(anadroid.app_projects_ut)

    if num_processes > 1:
        # Parallel Execution
        chunk_size = len(repo_list) // num_processes
        repo_chunks = [repo_list[i:i + chunk_size] for i in range(0, len(repo_list), chunk_size)]
        print(f"Running analysis in parallel with {num_processes} processes")
        for c in repo_chunks:
            print(len(c))
        with multiprocessing.Pool(num_processes) as pool:
            pool.map(analyze_repo_subset, repo_chunks)
    else:
        # Sequential Execution
        print("Running analysis sequentially")
        analyze_repo_subset(repo_list)


def extract_and_write_commit_history(repo_dir):
    """Extracts and saves commit history for a repo."""
    info = []
    branch_name_res = execute_shell_command(f"cd {repo_dir} && git branch --show-current")
    branch_name_res.validate()
    branch_name = branch_name_res.output.strip().replace("/", "-")

    res = execute_shell_command(f"cd {repo_dir} && git log --pretty=format:\"%H|%an|%ad|%BXX\" --date=iso")
    res.validate()

    filename = os.path.join(repo_dir, f'{branch_name}_commit_data.csv')
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


def save_issues(issues, dir_path, commit_hash):
    """Saves issues to a CSV file."""
    file_path = os.path.join(dir_path, f"{commit_hash}_issues.csv")
    with open(file_path, 'w') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Issue Type', 'File', 'Line', 'Description'])
        for issue in issues:
            writer.writerow(str(issue).replace(',', ';').split(';'))


def issue_regression(curr_issue_list, prev_issue_list):
    """Detects issue regressions."""
    regressions = []
    for issue in prev_issue_list:
        if issue not in curr_issue_list:
            loge(f"Regression found: {issue}")
            classif = classify_regression(issue, curr_issue_list)
            logi(f"Classification: {classif}")
            regressions.append((issue, classif))
    return regressions


def classify_regression(issue, curr_issue_list):
    """Classifies issue regressions."""
    issues_of_that_kind = [i for i in curr_issue_list if i.get_simple_name() == issue.get_simple_name()]
    issue_exists_on_proj = any(issues_of_that_kind)
    if not issue_exists_on_proj:
        return 'def_removal'
    issue_exists_on_file = any(i for i in issues_of_that_kind if i.file == issue.file)
    if issue_exists_on_file:
        return 'prob_move'
    return 'prob_removal'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze repositories sequentially or in parallel.")
    parser.add_argument("repos_directory", type=str, help="Path to the directory containing repositories")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel processes (default: 1)")
    args = parser.parse_args()
    analyze_repos(args.repos_directory, args.parallel)

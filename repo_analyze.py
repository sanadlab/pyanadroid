import csv
import os
import time
import traceback
import argparse
import multiprocessing
from os.path import expanduser

from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK
from anadroid.analysis.ComposedAnalyzer import ComposedAnalyzer
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.ChimeraAnalysis import ChimeraAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.DetektAnalysis import DetektAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.InferAnalysis import InferAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.analysis.pre_build_analysis.XALintAnalysis import XALintAnalysis
from anadroid.analysis.post_build_analysis.DroidLensAnalyzer import DroidLensAnalysis
from anadroid.analysis.post_build_analysis.EcoAndroidResourceLeaksAnalyzer import EcoAndroidResourceLeaksAnalysis
from anadroid.device.MockedDevice import MockedDevice
from anadroid.utils.Utils import execute_shell_command, logi, loge, mega_find
from anadroid.analysis.pre_build_analysis.SpotBugsAnalysis import SpotBugsAnalysis


lock = multiprocessing.Lock()


def init_pyanadroid(repo_dir, only_last_version=True):
    return AnaDroid(arg1=repo_dir,
                    results_dir="anadroid_results",
                    testing_framework=TESTING_FRAMEWORK.NONE,
                    device=MockedDevice(),
                    profiler=PROFILER.NONE,
                    load_projects=True,
                    rebuild_apps= not only_last_version,
                    reinstrument=True,
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
        print(eco_android_dirs)
        for eco_dir in eco_android_dirs:
            issues_list = issues_list + EcoAndroidAnalysis().get_issues(eco_dir)
    lint_results = mega_find(proj_results_dir, pattern="*lint*.xml", type_file='f', maxdepth=2)
    if len(lint_results) > 0:
        for lint_file in lint_results:
            issues_list = issues_list + LintAnalysis().get_issues(lint_file) + XALintAnalysis().get_issues(lint_file) + ChimeraAnalysis().get_issues(lint_file)
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
    return issues_list


def issue_file_exists(repo_dir, curr_commit, issue):
        """
        Checks if a file from an issue object exists in a specific git commit.

        This is a safe, read-only operation that does not modify the working directory.

        Args:
            repo_dir: The absolute path to the git repository.
            curr_commit: The commit hash or reference (e.g., branch name).
            issue: An object with a '.file' attribute containing the file path
                   relative to the repository root.

        Returns:
            - True if the file exists in the commit.
            - False if the file does not exist or if inputs are invalid.
            - None if issue.file is not set.
        """
        # 1. Initial validation
        if not hasattr(issue, 'file') or issue.file is None:
            return None
        if not all([repo_dir, curr_commit, issue.file]) or not os.path.isdir(repo_dir):
            return False

        file_path = issue.file
        # The file path should not be absolute
        if os.path.isabs(file_path):
            #print(f"Warning: issue.file '{file_path}' should be a relative path.")
            # Attempt to make it relative (this might need adjustment based on your structure)
            if file_path.startswith(repo_dir):
                file_path = os.path.relpath(file_path, repo_dir)

        # 2. Build the command safely as a list of arguments
        #    -C tells git to run as if in repo_dir, avoiding 'cd'.
        #    cat-file -e checks for an object's existence and returns exit code 0 if found.
        command = [
            'git',
            '-C', repo_dir,
            'cat-file',
            '-e',
            f'{curr_commit}:{file_path}'
        ]

        try:
            res = execute_shell_command(' '.join(command))
            res.validate()
            # The command succeeds (returns 0) if and only if the file exists.
            return res.return_code == 0
        except:
            return False

def reset_repo(repo_dir, branch_name='-'):
    # # Ensure repo_dir is not dangerous (e.g., part of the current working directory, home, or root)
    dangerous_dirs = [os.getcwd(),  os.path.join(expanduser("~"))]
    if any(os.path.abspath(repo_dir).startswith('repos/pyanadroid') or os.path.abspath(repo_dir) in d for d in dangerous_dirs):
        loge(f"Operation aborted: {repo_dir} is a dangerous directory.", exit_on_error=True)
        time.sleep(3)
        return
    if branch_name == '-':
        # Try to find the main branch reliably
        branch_candidates = ["main", "master"]
        branch_name = None

        # First: Try origin/HEAD symbolic-ref
        symbolic_ref_cmd = (
            f"cd {repo_dir} && git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null"
        )
        branch_name_res = execute_shell_command(symbolic_ref_cmd)
        branch_name_res.validate()

        if branch_name_res.return_code == 0 and branch_name_res.output.strip():
            branch_name = branch_name_res.output.strip().replace("origin/", "").replace("/", "-")
        else:
            # Fallback to checking branch_candidates
            for candidate in branch_candidates:
                # Check if branch exists locally
                check_branch_cmd = (
                    f"cd {repo_dir} && git rev-parse --verify {candidate}"
                )
                branch_check_res = execute_shell_command(check_branch_cmd)
                if branch_check_res.return_code == 0:
                    branch_name = candidate
                    break


    res = execute_shell_command(
        f"cd {repo_dir} && git reset --keep && git reset --hard  && git checkout {branch_name} ")
    res.validate()
    print(res)


def analyze_repo_subset(repos_list, container_id=None, only_last_version=False):
    """Analyzes a subset of repositories."""
    sorted_repo_list = []
    source_code_analyzers = [DAAPAnalysis(), PMDAnalysis(), ADoctorAnalysis(), DetektAnalysis()]
    heaviweight_analyzers = [
        #LintAnalysis(in_container=container_id is not None, container_id=container_id),
        #InferAnalysis(in_container=container_id is not None, container_id=container_id),
        #SpotBugsAnalysis(in_container=container_id is not None, container_id=container_id),
    ]
    post_build_analyzers = [
        DroidLensAnalysis(),
        EcoAndroidResourceLeaksAnalysis()
    ]
    print("Sorting repos")
    for repo_dir in repos_list:
        print("Checking repo: ", repo_dir)
        bname, commit_list = extract_and_write_commit_history(repo_dir)
        time.sleep(3)
        sorted_repo_list.append((repo_dir, bname, commit_list))
    sorted_repo_list = sorted(sorted_repo_list, key=lambda x: len(x[2]))
    #print(sorted_repo_list)
    for repo_dir, branch_name, commit_list in sorted_repo_list:
        try:
            anadroid = init_pyanadroid(repo_dir)
            anadroid.pre_build_analyzers = ComposedAnalyzer(None,
                                                            inner_analyzers= source_code_analyzers + heaviweight_analyzers)
            print(f"Analyzing repo: {repo_dir}")
            #branch_name, commit_list = extract_and_write_commit_history(repo_dir)

            prev_issue_list = []
            prev_commit_hash = None
            res_dirs = []
            if len(commit_list) == 0 or only_last_version:
                if only_last_version:
                    reset_repo(repo_dir)

                for app_proj in anadroid.app_projects_ut:
                    try:
                        if len(heaviweight_analyzers) == 0:
                            anadroid.app_projects_ut = [repo_dir]
                            res_dirs = anadroid.just_static_analyze(retry=False)
                            issues = load_project_issues(res_dirs[0]) if res_dirs else []
                            print(len(issues), " issues")
                            print([x.get_simple_name() for x in issues])

                        else:
                            proj = anadroid.build_app_project(app_proj, build_apks=False)
                            anadroid.pre_build_analyzers = ComposedAnalyzer(None,
                                                                            inner_analyzers=heaviweight_analyzers)
                            anadroid.pre_build_analyzers.analyze_project(proj)
                            res_dirs = anadroid.just_static_analyze()
                            issues = load_project_issues(getattr(res_dirs[0], 'proj_dir', res_dirs[0])) if res_dirs else []
                            print(len(issues), " issues")
                            print([x.get_simple_name() for x in issues])
                    except Exception as e:
                        loge(f"Oh no. Error building project {app_proj}: {e}")
                        traceback.print_exc()
                continue
            print(f"Branch: {branch_name}, Commits: {len(commit_list)}")
            trunc_commit_set_size = (max(20, int(len(commit_list)/100)) if len(commit_list) > 100 else 5) if len(commit_list) > 20 else 3 if len(commit_list) > 10 else 1
            comm_set_list = [x for i, x in enumerate(commit_list) if i % trunc_commit_set_size == 0]
            print(f"Truncating commit set to every {trunc_commit_set_size} commits for analysis ({len(comm_set_list)} from Total of {len(commit_list)} commits)")
            
            for i, commit in enumerate(comm_set_list):
                commit_msgs_concat = " ; ".join([c['message'] for c in commit_list[max(0, (i - 1) * trunc_commit_set_size): (i * trunc_commit_set_size)]]) if i > 0 else commit['message']

                commit_hash = commit['hash']
                print(f"Checking out commit {i + 1}/{len(comm_set_list)}: {commit_hash}")
                reset_repo(repo_dir, commit_hash)
                #execute_shell_command(f"cd {repo_dir} && git reset --hard && git clean -fd && git checkout -f {commit_hash}").validate()
                # Run static analysis
                anadroid.app_projects_ut = [repo_dir]
                res_dirs = anadroid.just_static_analyze()
                commit['issues'] = load_project_issues(res_dirs[0]) if res_dirs else []
                logi(f"Commit {commit_hash} has {len(commit['issues'])} issues")
                # Checkout back to branch
                reset_repo(repo_dir, commit_hash)
                #execute_shell_command(f"cd {repo_dir} && git reset --hard && git clean -fd && git checkout -f {branch_name}").validate()
                regressions = issue_regression(commit['issues'], prev_issue_list, repo_dir, commit_hash)
                if regressions:
                    with lock:
                        with open('v2_regressions.csv', 'a+') as file:
                            writer = csv.writer(file, delimiter=';')
                            for reg in regressions:
                                writer.writerow(
                                    [repo_dir, prev_commit_hash, commit_hash,commit_msgs_concat.replace(';', '.'),
                                     str(reg[0]), reg[1]])
                save_issues(commit['issues'], repo_dir, commit_hash)
                prev_issue_list = commit['issues']
                prev_commit_hash = commit_hash

        except Exception as e:
            loge(f"Error analyzing repo {repo_dir}: {e}")
            traceback.print_exc()


def analyze_repos(repos_directory, num_processes=1, container_id=None, only_last_version=False):
    anadroid = init_pyanadroid(repos_directory, only_last_version)
    repo_list = list(anadroid.app_projects_ut)
    if num_processes > 1:
        # Parallel Execution
        chunk_size = len(repo_list) // num_processes

        repo_chunks = [repo_list[i:i + chunk_size] for i in range(0, len(repo_list), chunk_size)]
        args_for_pool = [(chunk, container_id, only_last_version) for chunk in repo_chunks]
        print(f"Running analysis in parallel with {num_processes} processes")
        for c in repo_chunks:
            print(len(c))
        with multiprocessing.Pool(num_processes) as pool:
            pool.starmap(analyze_repo_subset, args_for_pool)
    else:
        # Sequential Execution
        print("Running analysis sequentially")
        analyze_repo_subset(repo_list, container_id, only_last_version)


def extract_and_write_commit_history(repo_dir):
    """Robustly extracts and saves commit history to a CSV file."""

    info = []

    # Ensure the directory is a valid git repo
    if not os.path.isdir(os.path.join(repo_dir, '.git')):
        print(f"Error: {repo_dir} is not a valid git repository.")
        return None, []

    # Try to find the main branch reliably
    branch_candidates = ["main", "master"]
    branch_name = None

    # First: Try origin/HEAD symbolic-ref
    symbolic_ref_cmd = (
        f"cd {repo_dir} && git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null"
    )
    branch_name_res = execute_shell_command(symbolic_ref_cmd)
    branch_name_res.validate()

    if branch_name_res.return_code == 0 and branch_name_res.output.strip():
        branch_name = branch_name_res.output.strip().replace("origin/", "").replace("/", "-")
    else:
        # Fallback to checking branch_candidates
        for candidate in branch_candidates:
            # Check if branch exists locally
            check_branch_cmd = (
                f"cd {repo_dir} && git rev-parse --verify {candidate}"
            )
            branch_check_res = execute_shell_command(check_branch_cmd)
            if branch_check_res.return_code == 0:
                branch_name = candidate
                break

    # Still not found? Use HEAD
    if not branch_name:
        head_cmd = f"cd {repo_dir} && git rev-parse --abbrev-ref HEAD"
        head_res = execute_shell_command(head_cmd)
        if head_res.return_code == 0 and head_res.output.strip():
            branch_name = head_res.output.strip().replace("/", "-")
        else:
            print("Error: couldn't detect main branch.")
            return None, []

    # Try to checkout branch
    checkout_cmd = f"cd {repo_dir} && git checkout {branch_name}"
    checkout_res = execute_shell_command(checkout_cmd)
    if checkout_res.return_code != 0:
        print(f"Error: failed to checkout branch {branch_name}. forcing checkout")
        reset_repo(repo_dir, branch_name)

    # Try to export commit log
    log_cmd = (
        f'cd {repo_dir} && git log --pretty=format:"%H|%an|%ad|%BXX" --date=iso'
    )
    log_res = execute_shell_command(log_cmd)
    log_res.validate()
    if log_res.return_code != 0 or not log_res.output.strip():
        print(f"Error: failed to extract git log. {log_res.errors}")
        return branch_name, []

    # Prepare output file
    filename = os.path.join(repo_dir, f'{branch_name}_commit_data.csv')
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Commit Hash', 'Author', 'Date', 'Message'])

            for commit in log_res.output.split("XX\n"):
                vals = commit.split("|")
                if len(vals) > 3:
                    # Replace semicolons and sanitize line breaks
                    msg = vals[3].replace(';', '.').replace("\r", " ").replace("\n", " ")
                    try:
                        writer.writerow([vals[0], vals[1], vals[2], msg])
                        info.append({
                            'hash': vals[0],
                            'author': vals[1],
                            'date': vals[2],
                            'message': msg,
                        })
                    except Exception as e:
                        print(f"Error writing commit: {vals}. Exception: {e}")
                        traceback.print_exc()
    except Exception as e:
        print(f"Error writing to file: {filename}. Exception: {e}")
        traceback.print_exc()
        return branch_name, []
    # Reverse for chronological order
    return branch_name, info[::-1]



def save_issues(issues, dir_path, commit_hash):
    """Saves issues to a CSV file."""
    file_path = os.path.join(dir_path, f"{commit_hash}_issues.csv")
    with open(file_path, 'w') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Issue Type', 'File', 'Line', 'Description'])
        for issue in issues:
            writer.writerow(str(issue).replace(',', ';').split(';'))


def issue_regression(curr_issue_list, prev_issue_list, repo_dir, curr_commit):
    """Detects issue regressions."""
    regressions = []
    for issue in prev_issue_list:
        if issue not in curr_issue_list:
            loge(f"Regression found: {issue}")
            classif = classify_regression(issue, curr_issue_list, repo_dir, curr_commit)
            logi(f"Classification: {classif}")
            regressions.append((issue, classif))
    return regressions


def classify_regression(issue, curr_issue_list, repo_dir, curr_commit):
    """Classifies issue regressions."""
    issues_of_that_kind = [i for i in curr_issue_list if i.get_simple_name() == issue.get_simple_name()]
    issue_exists_on_proj = any(issues_of_that_kind)
    if not issue_exists_on_proj:
        file_still_exists = issue_file_exists(repo_dir, curr_commit, issue)
        if not file_still_exists:
            logi(f"File does not exist: {issue.file}")
            return 'file_removed'
        return 'def_removal'
    issue_exists_on_file = any(i for i in issues_of_that_kind if i.get_file_id() == issue.get_file_id())
    if issue_exists_on_file:
        return 'prob_move'
    if issue_exists_on_proj and not any([i for i in issues_of_that_kind if  os.path.basename(getattr(i, 'file', 'i')) == os.path.basename(getattr(issue, 'file', 'issue'))] ):
        return 'def_removal'
    return 'prob_removal'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze repositories sequentially or in parallel.")
    parser.add_argument("repos_directory", type=str, help="Path to the directory containing repositories")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel processes (default: 1)")
    parser.add_argument("--only_last_version", action='store_true',default=False,
                        help="Analyze only the last version of each repo")
    parser.add_argument("--chunk", action='store_true', default=False,
                        help="divide commit list in chunks for analysis")
    parser.add_argument("--container_id", default=None, type=str,
                        help="set container id for analysis tools")
    args = parser.parse_args()
    analyze_repos(args.repos_directory, args.parallel, args.container_id, args.only_last_version)

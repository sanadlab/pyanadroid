import os
import time
import traceback
import argparse
import multiprocessing
from os.path import expanduser

from anadroid.utils.Utils import loge, execute_shell_command, mega_find


def reset_repo(repo_dir, branch_name='-', clean_instrumentation=False):
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

    if clean_instrumentation:
        # remove NONE_TRANSFORMED directory
        instr_dir = mega_find(repo_dir, pattern="NONE_TRANSFORMED_*", type_file='d', maxdepth=1)
        for d in instr_dir:
            print(d)
            #execute_shell_command(f"rm -rf {d}").validate()
    cmd =  f"cd {repo_dir} && git reset --keep && git reset --hard  && git checkout -f {branch_name} "
    print(cmd)
    res = execute_shell_command(cmd)
    res.validate()
    print(res)



def main(repos_dir='native_apps'):
    for f in os.listdir(os.path.expanduser(repos_dir)):
        repo_path = os.path.join(repos_dir, f)
        if os.path.isdir(repo_path):
            try:
                reset_repo(repo_path, branch_name='-')
            except Exception as e:
                print(f"Error processing {repo_path}: {e}\n{traceback.format_exc()}")
        filepath = os.path.join(repo_path, 'scc.json')
        print(f'Generating scc for {repo_path} at {filepath}')
        os.system(f'scc {repo_path} -f json > {filepath}')


if __name__ == '__main__':
    main('~/repos/research/fdroid_apps/native_apps')
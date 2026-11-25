import importlib.resources
import re
import shlex
from datetime import datetime
import subprocess
import signal
import os
import threading
import time
from enum import Enum
from termcolor import colored
from textops import find
import os
from os.path import expanduser


DEFAULT_ANALYZERS_FILENAME =  "analyzer_filters.json"

class LogSeverity(Enum):
    DEBUG = "Debug"
    SUCCESS = "Success"
    WARNING = "Warning"
    INFO = "Info"
    ERROR = "Error"
    FATAL = "Fatal"


def get_color(sev):
    return {
        'Debug': 'cyan',
        'Success': 'green',
        'Warning': 'yellow',
        'Info': 'blue',
        'Error': 'magenta',
        'Fatal': 'red'
    }.get(sev, 'green')


EVAL_TIME = time.time()
# debug messages are always written to the log file. The console shows them in verbose mode only
VERBOSE = os.environ.get("ANADROID_VERBOSE", "") == "1"
LOG_LOCK = threading.Lock()


def set_verbose(verbose):
    """shows (or hides) debug messages on the console."""
    global VERBOSE
    VERBOSE = verbose

def get_analyzers_filter_file():
    return os.path.join(get_general_config_dir(), DEFAULT_ANALYZERS_FILENAME)\
        if not os.path.exists(DEFAULT_ANALYZERS_FILENAME) else DEFAULT_ANALYZERS_FILENAME


def log(message, log_sev=LogSeverity.INFO, curr_time=None, to_file=True):
    curr_time = time.time() if curr_time is None else curr_time
    color = get_color(log_sev.value)
    adapted_time = datetime.fromtimestamp(curr_time).strftime("%Y-%m-%d-%H-%M-%S")
    str_to_print = "[%s] %s: %s" % (log_sev.value, adapted_time, message)
    with LOG_LOCK:
        if log_sev != LogSeverity.DEBUG or VERBOSE:
            print(colored(str_to_print, color))
        if to_file:
            os.makedirs(get_log_dir(), exist_ok=True)
            with open(get_log_file(), "a+") as f:
                f.write(str_to_print + "\n")


def get_log_dir():
    return os.path.join(os.getcwd(), "logs")


def get_log_file():
    """path of the log file of the current run."""
    return os.path.join(get_log_dir(), datetime.fromtimestamp(EVAL_TIME).strftime("%Y-%m-%d-%H-%M-%S") + ".log")


def get_reference_dir(packname):
    """directory of an installed package (e.g. anadroid)."""
    return str(importlib.resources.files(packname))


def get_resources_dir(packname="anadroid", default_res_dir="resources"):
    ref_dir = get_reference_dir(packname)
    return os.path.join(ref_dir, default_res_dir)


def get_keystore_path():
    return os.path.join(get_resources_dir(), "keys", "pynadroid-releases.keystore")


def get_keystore_pwd():
    return "pynadroid"


def get_general_config_dir(packname="anadroid", default_res_dir="resources"):
    return os.path.join(get_resources_dir(packname, default_res_dir), "config")


def get_pack_dir(packname="anadroid"):
    return get_reference_dir(packname)


def get_results_dir(default_results_dir="anadroid_results"):
    return default_results_dir


def extract_pkg_name_from_apk(apkpath):
    aapt_executable = find_build_tool("aapt")
    if aapt_executable is None:
        raise Exception("Unable to find aapt executable in $ANDROID_HOME/build-tools")
    res = execute_shell_command(f"{aapt_executable}  dump badging {apkpath} | grep 'package: name='")
    res.validate(Exception("error while executing aapt"))
    pkg_name = res.output.split(" ")[1].replace("name=", "").replace("'", "")
    return pkg_name


def extract_version_from_apk(apkpath):
    aapt_executable = find_build_tool("aapt")
    if aapt_executable is None:
        raise Exception("Unable to find aapt executable in $ANDROID_HOME/build-tools")
    res = execute_shell_command(f"{aapt_executable}  dump badging {apkpath} | grep 'versionName='")
    res.validate(Exception("error while executing aapt"))
    return res.output.split(" ")[3].replace("versionName=", "").replace("'", "")


def get_date_str():
    res = execute_shell_command("date +\"%d_%m_%y_%H_%M_%S\"")
    if res.validate(Exception("Unable to get date")):
        return res.output.strip()


def find_build_tool(tool_name):
    """finds a tool (e.g. aapt, apksigner) in the newest installed version of the Android build tools.
    Returns:
        str: path of the tool, or None if no installed version has it.
    """
    build_tools_dir = os.path.join(os.environ.get("ANDROID_HOME", ""), "build-tools")
    if not os.path.isdir(build_tools_dir):
        return None
    versions_with_tool = [v for v in os.listdir(build_tools_dir)
                          if os.path.isfile(os.path.join(build_tools_dir, v, tool_name))]
    if len(versions_with_tool) == 0:
        return None
    newest = max(versions_with_tool, key=lambda v: [int(n) for n in re.findall(r'\d+', v)])
    return os.path.join(build_tools_dir, newest, tool_name)


def get_apksigner_bin():
    apksigner = find_build_tool("apksigner")
    if apksigner is None:
        raise Exception("No apksigner found in $ANDROID_HOME/build-tools")
    return apksigner


def sign_apk(apk_path):
    # deprecated after api 26: "jarsigner -verbose -sigalg SHA2-256withRSA -digestalg SHA2-256
    # -keystore {keystore} {apk_path} {key_alias} <<< \"{passwd}\""
    # .format(keystore=PYNADROID_KEYSTORE_PATH,apk_path=apk_path,key_alias=KEY_ALIAS,passwd=PASSWORD)
    signer_bin = get_apksigner_bin()
    cmd = """{signer_bin} sign --ks {keystore_path} --ks-pass pass:{passwd} {apk_path}""".format(
       signer_bin=signer_bin,
       keystore_path=get_keystore_path(),
       apk_path=apk_path,
       passwd=get_keystore_pwd()
    )
    logd(f"Running command: {cmd}")
    res = execute_shell_command(cmd)
    res.validate("error signing apk " + apk_path)
    return res


def execute_shell_command(cmd, args=(), timeout=None, in_container=False, container_id=None, replace_paths=[]):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    if in_container:
        return DockerCommandWrapper(container_id, replace_paths).execute(command)
    #print("Executing command", cmd)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        logw(f"Command timed out after {timeout} seconds: {command}")
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # Kill the whole process group
        out, err = proc.communicate()  # keep the output written before the timeout
        proc.returncode = 1
    return COMMAND_RESULT(proc.returncode, out.decode("utf-8", errors='replace'), err.decode('utf-8', errors='replace'),
                          cmd=command)


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


class COMMAND_RESULT(object):
    def __init__(self, res, out, err, cmd=None):
        self.return_code = res
        self.output = out
        self.errors = err
        self.cmd = cmd

    def validate(self, e=None):
        if int(self.return_code) != 0:
            if len(self.errors) > 2:
                logw(f"Command failed with return code {self.return_code}: {self.cmd}\n"
                     f"Last error lines: {self.errors.strip()[-1000:]}")
                logd(f"Output of the failed command: {self.output}")
                if e is None:
                    return False
                elif isinstance(e, Exception):
                    raise e
                else:
                    loge(e)
                    return False
            else:
                #print(self)
                return True
        else:
            return True

    def __str__(self):
        return str(
            {'return_code': self.return_code,
             'output': self.output,
             'errors': self.errors
             })


def log_to_file(content, filename, mode='a+'):
    with open(filename, mode) as u:
        u.write(content + "\n")


def logd(message, to_file=True):
    log(message, log_sev=LogSeverity.DEBUG, to_file=to_file)


def logi(message, to_file=True):
    log(message, log_sev=LogSeverity.INFO, to_file=to_file)


def logw(message, to_file=True):
    log(message, log_sev=LogSeverity.WARNING, to_file=to_file)


def loge(message, to_file=True, exit_on_error=False, error_code=3):
    log(message, log_sev=LogSeverity.ERROR, to_file=to_file)
    if exit_on_error:
        exit(error_code)


def logf(message, to_file=True):
    log(message, log_sev=LogSeverity.FATAL, to_file=to_file)


def logs(message, to_file=True):
    log(message, log_sev=LogSeverity.SUCCESS, to_file=to_file)


import os
import re
from pathlib import Path
from typing import Optional


def _extract_package_name(file_path: Path) -> Optional[str]:
    """Reads the first 'package ...' line from a Java/Kotlin file."""
    # A simple regex to find a package declaration.
    # It handles optional semicolons and varying whitespace.
    package_regex = re.compile(r"^\s*package\s+([\w\.]+)")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = package_regex.match(line)
                if match:
                    return match.group(1)  # Return the package name, e.g., "com.example.app"
    except (IOError, UnicodeDecodeError):
        # Ignore files that can't be read.
        pass
    return None


def find_source_root_dynamically(project_dir: str, exclude_test=True) -> Optional[str]:
    """
    Finds the primary Java/Kotlin source root by locating the most top-level
    source file and inspecting its package declaration.

    Args:
        project_dir: The root directory of the project to scan.

    Returns:
        The path to the source root (e.g., '.../app/src/main/java'),
        or None if no source files are found or logic fails.
    """
    project_path = Path(project_dir)
    source_files = []

    # 1. Find all .java and .kt files, prioritizing shallower files
    # We can walk the tree and add files as we find them. If we sort later,
    # it's just as good.
    for ext in ("*.java", "*.kt"):
        if exclude_test:
            # Exclude test directories
            for path in project_path.rglob(ext):
                if 'test' not in path.parts and 'androidTest' not in path.parts:
                    source_files.append(path)
        else:
            source_files.extend(project_path.rglob(ext))

    if not source_files:
        logw(f"No .java or .kt files found in {project_dir}")
        return None

    # Sort files by path depth to find the "most top-level" one.
    # This is a good heuristic for finding a representative file.
    source_files.sort(key=lambda p: len(p.parts))

    # 2. Iterate through the top few files to find one with a package
    for top_file in source_files[:10]:  # Check a few candidates for robustness
        package_name = _extract_package_name(top_file)

        if package_name:
            # 3. Based on its package, retrieve the parent directory
            package_as_path = Path(package_name.replace('.', os.sep))
            file_parent_dir = top_file.parent

            # We assume the file_parent_dir ends with the package_as_path.
            # We can find the source root by removing that suffix.
            if str(file_parent_dir).endswith(str(package_as_path)):
                # Use string manipulation which is safer than path logic here
                # In Python 3.9+ you can use removesuffix()
                source_root = str(file_parent_dir)[:-len(str(package_as_path))].rstrip(os.sep)
                return source_root

    # Fallback: If no files with a package declaration are found, we can make a guess.
    # This often happens with files in the default package.
    logw(f"Could not determine the source root of {project_dir} from package declarations")
    if source_files:
        # A reasonable fallback is the parent directory of the top-level file.
        return str(source_files[0].parent)

    return None



class DockerCommandWrapper:
    def __init__(self, container_name, paths_to_truncate=[]):
        """
        container_name: str - Name or ID of the Docker container
        path_mapping: dict - Dictionary mapping local paths to container paths
          e.g. {"/local/path": "/container/path"}
        """
        self.container_name = container_name
        self.mappings = {
            expanduser("~") + os.sep: '',
            os.getcwd(): '',
            '$HOME/spotbugs/spotbugs-4.9.3': 'opt/spotbugs'
        }
        if os.environ.get('ANDROID_HOME'):
            self.mappings[os.environ.get('ANDROID_HOME')] = '/home/vscode/Android/Sdk'
        self.mappings.update({k: '' for k in paths_to_truncate})

    def _replace_paths(self, command):
        # Replace local paths in command with container paths
        for local_path, container_path in sorted(self.mappings.items(), key=lambda x: -len(x[0])):
            command = command.replace(local_path, container_path)
        return command

    def execute(self, command):
        # Replace paths to simulate local execution but inside container
        cmd_in_container = self._replace_paths(command)
        # Build docker exec command
        docker_cmd = ["docker", "exec", self.container_name, "sh", "-c", shlex.quote(cmd_in_container)]
        # Execute the command
        logd(f"Running command: {' '.join(docker_cmd)}")
        result = execute_shell_command(' '.join(docker_cmd))
        result.validate()
        return result

    def pull(self, path, overwrite=True):
        local_path = path
        container_path = self._replace_paths(path)
        docker_cmd = ["docker", "cp", f"{self.container_name}:{container_path}", local_path]
        if overwrite and os.path.exists(local_path):
            not_dangerous = os.path.abspath(local_path) not in ('/', '', os.getcwd())
            if os.path.isdir(local_path) and not_dangerous:
                logd(f"Removing existing directory {local_path} for overwrite")
                subprocess.run(['rm', '-rf', local_path])
            elif os.path.isfile(local_path):
                logd(f"Removing existing file {local_path} for overwrite")
                os.remove(local_path)
        logi(f"Pulling {container_path} from container {self.container_name} to {local_path}")
        result = execute_shell_command(' '.join(docker_cmd))
        result.validate()
        logd(f"Command result: {result}")
        return result

    def push(self, path, overwrite=True):
        local_path = path
        container_path = self._replace_paths(path)
        if not overwrite:
            # Check if the path already exists in the container
            check_cmd = f"docker exec {self.container_name} sh -c 'test -e {container_path} && echo exists || echo not_exists'"
            check_result = execute_shell_command(check_cmd)
            logd(f"Command result: {check_result}")
            if "not_exists" not in check_result.output:
                logi(f"Path {container_path} already exists in container {self.container_name}. Skipping push")
                return check_result
        docker_rm_cmd = f"docker exec {self.container_name} sh -c 'rm -rf {container_path}'"
        #print(docker_rm_cmd)
        execute_shell_command(docker_rm_cmd)
        #print(res)
        docker_cmd = ["docker", "cp", local_path, f"{self.container_name}:{container_path}"]
        logd(f"Running command: {' '.join(docker_cmd)}")
        logi(f"Pushing {local_path} to {container_path} in container {self.container_name}")
        result = execute_shell_command(' '.join(docker_cmd))
        result.validate()
        logd(f"Command result: {result}")
        return result
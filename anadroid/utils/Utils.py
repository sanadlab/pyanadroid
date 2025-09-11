import re
from datetime import datetime
import subprocess
import signal
import os
import time
from enum import Enum
from termcolor import colored
from textops import find
import os
from os.path import expanduser


DEFAULT_ANALYZERS_FILENAME =  "analyzer_filters.json"

class LogSeverity(Enum):
    SUCCESS = "Success"
    WARNING = "Warning"
    INFO = "Info"
    ERROR = "Error"
    FATAL = "Fatal"


def get_color(sev):
    return {
        'Success': 'green',
        'Warning': 'yellow',
        'Info': 'blue',
        'Error': 'magenta',
        'Fatal': 'red'
    }.get(sev, 'green')


EVAL_TIME = time.time()

def get_analyzers_filter_file():
    return os.path.join(get_general_config_dir(), DEFAULT_ANALYZERS_FILENAME)\
        if not os.path.exists(DEFAULT_ANALYZERS_FILENAME) else DEFAULT_ANALYZERS_FILENAME


def log(message, log_sev=LogSeverity.INFO, curr_time=None, to_file=True):
    curr_time = time.time() if curr_time is None else curr_time
    color = get_color(log_sev.value)
    adapted_time = datetime.fromtimestamp(curr_time).strftime("%Y-%m-%d-%H-%M-%S")
    adapted_time_f = datetime.fromtimestamp(EVAL_TIME).strftime("%Y-%m-%d-%H-%M-%S")
    str_to_print = "[%s] %s: %s" % (log_sev.value, adapted_time, message)
    print(colored(str_to_print, color))
    if to_file:
        log_dir = get_log_dir()
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        filename = f'{adapted_time_f}.log'
        f = open(os.path.join(get_log_dir(), filename), "a+")
        f.write(str_to_print+"\n")
        f.close()


def get_log_dir():
    return os.path.join(os.getcwd(), "logs")


def get_reference_dir(packname):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, packname)


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
    ref_dir = default_results_dir
    if not os.path.exists(ref_dir):
        os.mkdir(ref_dir)
    return ref_dir


def extract_pkg_name_from_apk(apkpath):
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"aapt\" | sort | tail -1")
    res.validate(Exception("Unable to find aapt executable"))
    aapt_executable = res.output.strip()
    res = execute_shell_command(f"{aapt_executable}  dump badging {apkpath} | grep 'package: name='")
    res.validate(Exception("error while executing aapt"))
    pkg_name = res.output.split(" ")[1].replace("name=", "").replace("'", "")
    return pkg_name


def extract_version_from_apk(apkpath):
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"aapt\" | sort | tail -1")
    res.validate(Exception("Unable to find aapt executable"))
    aapt_executable = res.output.strip()
    res = execute_shell_command(f"{aapt_executable}  dump badging {apkpath} | grep 'versionName='")
    res.validate(Exception("error while executing aapt"))
    return res.output.split(" ")[3].replace("versionName=", "").replace("'", "")


def get_date_str():
    res = execute_shell_command("date +\"%d_%m_%y_%H_%M_%S\"")
    if res.validate(Exception("Unable to get date")):
        return res.output.strip()


def get_apksigner_bin():
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"apksigner\" | sort")
    if res.validate(Exception("No apksigner found")):
        return res.output.split()[0]
    return "$ANDROID_HOME/build-tools/30.0.3/apksigner"


def sign_apk(apk_path):
    # deprecated after api 26: "jarsigner -verbose -sigalg SHA2-256withRSA -digestalg SHA2-256
    # -keystore {keystore} {apk_path} {key_alias} <<< \"{passwd}\""
    # .format(keystore=PYNADROID_KEYSTORE_PATH,apk_path=apk_path,key_alias=KEY_ALIAS,passwd=PASSWORD)
    signer_bin = get_apksigner_bin()
    cmd = """{signer_bin} sign --ks {keystore_path} {apk_path} <<< {passwd}""".format(
       signer_bin=signer_bin,
       keystore_path=get_keystore_path(),
       apk_path=apk_path,
       passwd=get_keystore_pwd()
    )
    print(cmd)
    res = execute_shell_command(cmd)
    res.validate("error signing apk " + apk_path)
    return res


def execute_shell_command(cmd, args=(), timeout=None, in_container=False, container_id=None, replace_paths=[]):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print("Executing command", cmd)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    try:
        if in_container:

            doc =  DockerCommandWrapper(container_id, replace_paths)
            return doc.execute(command)
        else:
            out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        print(f"Command {cmd} timed out")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # Kill the whole process group
        proc.returncode = 1
    return COMMAND_RESULT(proc.returncode, out.decode("utf-8", errors='replace'), err.decode('utf-8', errors='replace'))


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


class COMMAND_RESULT(object):
    def __init__(self, res, out, err):
        self.return_code = res
        self.output = out
        self.errors = err

    def validate(self, e=None):
        if int(self.return_code) != 0:
            if len(self.errors) > 2:
                if e is None:
                    print(self)
                    return False
                elif isinstance(e, Exception):
                    print(self)
                    raise e
                else:
                    loge(e)
                    print(self)
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
        print("Warning: No .java or .kt files found.")
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
    print("Warning: Could not determine source root from package declarations.")
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
            os.environ.get('ANDROID_HOME'): '/home/vscode/Android/Sdk',
            '$HOME/spotbugs/spotbugs-4.9.3': 'opt/spotbugs'
        }
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
        docker_cmd = ["docker", "exec", self.container_name, "sh", "-c", "\"", cmd_in_container, "\""]
        # Execute the command
        print(' '.join(docker_cmd))
        result = execute_shell_command(' '.join(docker_cmd))
        result.validate()
        return result

    def pull(self, path):
        local_path = path
        container_path = self._replace_paths(path)
        docker_cmd = ["docker", "cp", f"{self.container_name}:{container_path}", local_path]
        print('pulling ', container_path, ' to ', local_path, ' '.join(docker_cmd))
        result = execute_shell_command(' '.join(docker_cmd))
        result.validate()
        print(result)
        return result

    def push(self, path, overwrite=True):
        local_path = path
        container_path = self._replace_paths(path)
        if not overwrite:
            # Check if the path already exists in the container
            check_cmd = f"docker exec {self.container_name} sh -c 'test -e {container_path} && echo exists || echo not_exists'"
            check_result = execute_shell_command(check_cmd)
            print(check_result)
            if "not_exists" not in check_result.output:
                print(f"Path {container_path} already exists in the container. Skipping push.")
                return check_result
        print('Proceed with pushing the file/directory')
        docker_cmd = ["docker", "cp", local_path, f"{self.container_name}:{container_path}"]
        print('pushing ', container_path, ' to ', local_path, ' '.join(docker_cmd))
        result = execute_shell_command(' '.join(docker_cmd))
        result.validate()
        print(result)
        return result
from abc import ABC

from anadroid.utils.Utils import execute_shell_command, logi


def get_java_version(result):
    result = str(result)
    if '1.8' in result or str(result).strip() == '8':
        return 8
    elif '1.9' in result or str(result).strip() == '9':
        return 9
    elif '1.11' in result or '11.' in result or str(result).strip() == '11':
        return 11
    elif '1.17' in result or '17.' in result or str(result).strip() == '17':
        return 17
    elif '1.21' in result or '21.' in result or str(result).strip() == '21':
        return 21
    return 21

def change_java_version_cmd(java_version):
    # TODO: change this
    cmd = f"source .java_version_cmds ; j{java_version};"
    return cmd
    #execute_shell_command(f"source ~/.zshrc ; j{java_version}")

def get_gradle_matching_version(gradle_version):
    if gradle_version is None:
        return 17
    try:
        gradle_version = float(f"{gradle_version.split(".")[0]}.{gradle_version.split(".")[-2 if len(gradle_version.split(".")) > 2 else -1]}")
    except ValueError:
        return 17
    
    if gradle_version <= 4.10:
        return 8
    elif 4.10 < gradle_version <= 5.6:
        return 11
    elif 5.6 < gradle_version <= 7.4:
        return 17
    else:
        return 21

class JavaVersionManager(ABC):
    def __init__(self):
        self.java_versions = {8, 11, 17, 21}

    def get_change_java_retry_cmd(self, output, **kwargs):
        if 'java' in output or 'jvm' in output or 'source release' in output:
            result = execute_shell_command('java -version').output
            print(result.strip())
            java_version = get_java_version(result.strip())
            if java_version in self.java_versions:
                self.java_versions.remove(java_version)
            if len(self.java_versions) > 0:
                java_version = self.java_versions.pop()
                cmd = change_java_version_cmd(java_version)
                return True, cmd
        return False, ''

    def change_java_version(self, java_version):
        java_version = int(get_java_version(java_version))
        if java_version in self.java_versions:
            cmd = change_java_version_cmd(java_version)
            logi(f"changing java version to {java_version}")
            print(execute_shell_command(cmd))
            return True
        return False

    def get_change_java_version_cmd(self, java_version):
        java_version = int(get_java_version(java_version))      
        if java_version in self.java_versions:
            cmd = change_java_version_cmd(java_version)
            return True, cmd
        return False, ''


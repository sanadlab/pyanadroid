from abc import ABC

from anadroid.utils.Utils import execute_shell_command


def get_java_version(result):
    if '1.8' in result:
        return 8
    elif '1.9' in result:
        return 9
    elif '1.11' or '11.' in result:
        return 11
    elif '1.17' or '17.' in result:
        return 17
    elif '1.21' or '21.' in result:
        return 21

def change_java_version_cmd(java_version):
    # TODO: change this
    cmd = f"source ~/.zshrc ; j{java_version};"
    return cmd
    #execute_shell_command(f"source ~/.zshrc ; j{java_version}")

class JavaRetry(ABC):
    def __init__(self):
        self.java_versions = {8, 11, 17, 21}

    def change_java_retry(self, output, **kwargs):
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
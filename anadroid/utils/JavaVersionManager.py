import glob
import os
import re
from abc import ABC

from anadroid.utils.Utils import logd
from anadroid.utils.Utils import execute_shell_command, logi, logw

# locations where JDKs are usually installed (macOS and Linux)
JAVA_SEARCH_GLOBS = [
    os.path.expanduser("~/.sdkman/candidates/java/*"),
    "/opt/homebrew/opt/openjdk@*",
    "/usr/local/opt/openjdk@*",
    "/Library/Java/JavaVirtualMachines/*",
    "/usr/lib/jvm/*",
]
# sub-directories of an installation that can contain the JDK home
JAVA_HOME_SUBDIRS = ["", os.path.join("Contents", "Home"), os.path.join("libexec", "openjdk.jdk", "Contents", "Home")]


def get_java_home_version(java_home):
    """reads the major java version from the release file of a JDK home. Returns None if not found."""
    release_file = os.path.join(java_home, "release")
    if not os.path.isfile(release_file):
        return None
    with open(release_file, encoding="utf-8", errors="ignore") as f:
        match = re.search(r'JAVA_VERSION="(\d+)\.(\d+)', f.read())
    if match is None:
        return None
    major, minor = int(match.group(1)), int(match.group(2))
    return minor if major == 1 else major


def find_java_home(java_version):
    """finds the home directory of an installed JDK with the given major version.
    The environment variable JAVA_HOME_<version> (e.g. JAVA_HOME_17) has priority.
    Returns:
        str: JDK home, or None if there is no JDK with that version.
    """
    from_env = os.environ.get(f"JAVA_HOME_{java_version}")
    if from_env:
        return from_env
    for pattern in JAVA_SEARCH_GLOBS:
        for candidate in sorted(glob.glob(pattern)):
            for subdir in JAVA_HOME_SUBDIRS:
                java_home = os.path.join(candidate, subdir) if subdir else candidate
                if get_java_home_version(java_home) == int(java_version):
                    return java_home
    return None


def get_java_version(result):
    """reads the major java version from a number (17), a version (1.8.0_442, 17.0.4) or the output of
    `java -version`. Returns 21 if there is no version in the text."""
    match = re.search(r'(\d+)(?:\.(\d+))?', str(result))
    if match is None:
        return 21
    major = int(match.group(1))
    return int(match.group(2)) if major == 1 and match.group(2) else major


def get_change_java_version_cmd(java_version, on_container=False):
    if not on_container:
        java_home = find_java_home(java_version)
        if java_home is None:
            logw(f"No JDK {java_version} found. Set JAVA_HOME_{java_version}. Using the default java")
            return ""
        cmd = f'export JAVA_HOME="{java_home}"; export PATH="$JAVA_HOME/bin:$PATH";'
    else:
        if int(java_version) <= 8:
            opt = f"/usr/lib/jvm/java-{java_version}-openjdk-amd64/jre/bin/java"
        else:
            opt = f"/usr/lib/jvm/java-{java_version}-openjdk-amd64/bin/java"

        cmd = f'sudo update-alternatives --set java {opt};'
        if int(java_version) >= 17:
            cmd += "echo \'org.gradle.jvmargs=--add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED\' >> gradle.properties ;"
    return cmd
    #execute_shell_command(f"source ~/.zshrc ; j{java_version}")

def get_gradle_matching_version(gradle_version):
    if gradle_version is None:
        return 17
    parts = re.findall(r'\d+', str(gradle_version))
    if len(parts) == 0:
        return 17
    # compare as (major, minor). A float comparison puts 8.10 before 8.4
    version = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    if version <= (4, 10):
        return 8
    elif version < (7, 3):
        return 11
    elif version < (8, 5):
        return 17
    return 21

class JavaVersionManager(ABC):
    def __init__(self):
        self.java_versions = {8, 11, 17, 21}

    def get_change_java_retry_cmd(self, output, **kwargs):
        on_container = kwargs.get('on_container', False)
        if 'java' in output or 'jvm' in output or 'source release' in output:
            res = execute_shell_command('java -version')
            result = res.output + res.errors  # java writes the version to stderr
            java_version = get_java_version(result.strip())
            if java_version in self.java_versions:
                self.java_versions.remove(java_version)
            if len(self.java_versions) > 0:
                java_version = self.java_versions.pop()
                cmd = get_change_java_version_cmd(java_version, on_container)
                return True, cmd
        return False, ''

    def change_java_version(self, java_version, **kwargs):
        on_container = kwargs.get('on_container', False)
        java_version = int(get_java_version(java_version))
        if java_version in self.java_versions:
            cmd = get_change_java_version_cmd(java_version, on_container)
            logi(f"changing java version to {java_version}")
            logd(f"Command result: {execute_shell_command(cmd)}")
            return True
        return False


    def get_change_java_version_cmd(self, java_version, **kwargs):
        on_container = kwargs.get('on_container', False)
        java_version = int(get_java_version(java_version))
        if java_version in self.java_versions:
            cmd = get_change_java_version_cmd(java_version, on_container)
            return True, cmd
        return False, 
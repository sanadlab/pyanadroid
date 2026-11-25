"""Finds and downloads the external tools (jars and binaries) that PyAnaDroid runs.

A tool is searched in this order:
1. the path in the environment variable PYANADROID_<NAME> (e.g. PYANADROID_JINST);
2. the tools directory (~/.cache/pyanadroid/tools, or PYANADROID_TOOLS_DIR), filled by `pyanadroid --setup`;
3. the file bundled in the package resources.
"""
import hashlib
import json
import os
import shutil
import stat
import urllib.request
import zipfile

from anadroid.utils.Utils import get_resources_dir, logi, logs

MANIFEST_FILE = os.path.join(get_resources_dir(), "tools.json")
with open(MANIFEST_FILE, encoding="utf-8") as _manifest:
    TOOLS = json.load(_manifest)


def get_tools_dir():
    """directory with the downloaded tools."""
    return os.environ.get("PYANADROID_TOOLS_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "pyanadroid", "tools")


def get_env_var_name(name):
    return "PYANADROID_" + name.upper()


def find_tool_path(name):
    """returns the path of a tool. Does not check that the bundled file exists.
    Args:
        name: name of the tool in the manifest (resources/tools.json).
    """
    tool = TOOLS[name]
    from_env = os.environ.get(get_env_var_name(name))
    if from_env:
        return from_env
    downloaded = os.path.join(get_tools_dir(), tool["file"])
    if os.path.exists(downloaded):
        return downloaded
    return os.path.join(get_resources_dir(), "jars", tool["file"])


def find_pmd():
    """returns the path of the PMD executable: PMD_HOME, then the PATH. PyAnaDroid does not download PMD."""
    pmd_home = os.environ.get("PMD_HOME")
    if pmd_home:
        return os.path.join(pmd_home, "bin", "pmd")
    return shutil.which("pmd") or "pmd"


def download_tool(name):
    """downloads a tool to the tools directory and checks its SHA-256 checksum.
    Returns:
        str: path of the tool.
    """
    tool = TOOLS[name]
    tools_dir = get_tools_dir()
    target = os.path.join(tools_dir, tool["file"])
    is_archive = tool.get("archive", False)
    download_path = os.path.join(tools_dir, f"{name}.download")
    os.makedirs(os.path.dirname(target) if not is_archive else tools_dir, exist_ok=True)
    logi(f"Downloading {name} from {tool['url']}")
    checksum = hashlib.sha256()
    with urllib.request.urlopen(tool["url"]) as response, open(download_path, "wb") as out:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            checksum.update(chunk)
            out.write(chunk)
    if checksum.hexdigest() != tool["sha256"]:
        os.remove(download_path)
        raise ValueError(f"Checksum of {name} is {checksum.hexdigest()}. Expected {tool['sha256']}. File removed")
    if is_archive:
        with zipfile.ZipFile(download_path) as archive:
            archive.extractall(tools_dir)
        os.remove(download_path)
        os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    else:
        os.replace(download_path, target)
    logs(f"{name} is ready at {target}")
    return target


def setup_tools(names=None):
    """downloads the tools that are not in the tools directory.
    Args:
        names: names of the tools. All the tools of the manifest by default.
    """
    for name in names or TOOLS:
        target = os.path.join(get_tools_dir(), TOOLS[name]["file"])
        if os.path.exists(target):
            logi(f"{name} is already at {target}")
        else:
            download_tool(name)

import os
import re
import shutil
from enum import Enum


from termcolor import colored
from textops import grep, cat, echo, sed
from anadroid.build.SdkManagerWrapper import SDKManager
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import mega_find, get_resources_dir, loge

RES_DIR = get_resources_dir()
GRADLE_RES_DIR = os.path.join(RES_DIR, "build", "gradle")
GRADLE_WRAPPER_DIR = os.path.join(GRADLE_RES_DIR, "wrapper", "gradle")

KEYSTORE_ERROR_COUNT = 0

class KNOWN_ERROR(Enum):
    """Enumerates the list of known gradle build errors that possibly can be fixed the framework."""
    GOOGLE_REPO_ERROR = "method google() for arguments"
    LIBS_ERROR = "No signature of method: java.util.ArrayList.call() is applicable for argument types"
    MIN_SDK_ERROR = "uses-sdk:minSdkVersion (.+) cannot be smaller than version (.+) declared in"
    BUILD_SDK_ERROR = "The SDK Build Tools revision \((.+)\) is too low for project "
    WRAPPER_ERROR = "try editing the distributionUrl"
    WRAPPER_MISMATCH_ERROR = "Failed to notify project evaluation listener"
    WRAPPER_PROP_ERROR = "Wrapper properties file"
    NDK_TOOLCHAIN_ERROR = "NDK toolchains folder"
    BUILD_TOOLS_CPU_ERROR = "Bad CPU type in executable"
    NO_WRAPPER = "Could not find or load main class org.gradle.wrapper.GradleWrapperMain"
    NO_GRADLEW_EXEC = "gradlew: No such file or directory"
    NO_TARGET_PLATFORM = "failed to find target with hash string"
    NO_BUILD_TOOLS = "failed to find Build Tools revision"
    MAYBE_MISSING_GOOGLE_REPO = "Could not resolve all dependencies for configuration"
    USER_HAS_TO_ACCEPT_INSTALL = "INSTALL_FAILED_USER_RESTRICTED"
    NDK_BAD_CONFIG = "did not contain a valid NDK and couldn't be used"
    WRONG_KEYSTORE = "Keystore file (.+) not found for signing"
    ERROR_SIGNING_CONFIG = "signing configuration"
    #UNSUPPORTED_DEPENDENCY_VERSION = "The Android Gradle plugin supports only Butterknife Gradle plugin version 9.0.0-rc2 and higher."


def get_sdk_version_regex(kind):
    """regex for a numeric min/target sdk version. Supports `minSdkVersion 21`, `minSdkVersion(21)`,
    `minSdk 21` and `minSdk = 21`.
    Args:
        kind: 'min' or 'target'.
    """
    return r'\b(%sSdk(?:Version)?)(\s*=\s*|\s*\(\s*|[ \t]+)(\d+)' % kind


def replace_sdk_version(content, kind, new_version):
    """replaces the numeric min/target sdk version in the content of a gradle file."""
    return re.sub(get_sdk_version_regex(kind), lambda m: f"{m.group(1)}{m.group(2)}{new_version}", content)


def is_known_error(output):
    """Given the build output, checks if a known error occurred.

    Returns:
        object (obJ:`KNOW_ERROR`): the inferred error. If the error is not known, returns None.
    """
    for error in KNOWN_ERROR:
        is_this_error = error.value in output or re.search(error.value, output) is not None
        if is_this_error:
            return error
    return None


def solve_known_error(proj, error, error_msg, **kwargs):
    """Tries to fix known build error.
    Args:
        proj(obj:`AndroidProject`): project that raised the error.
        error(obj:`KNOWN_ERROR`):
        error_msg(str): build output containing the error.
    """
    if error == KNOWN_ERROR.WRAPPER_MISMATCH_ERROR:
        #adjust gradle wrapper version
        grad_prop_files = mega_find(proj.proj_dir, "gradle-wrapper.properties", type_file='f')
        bld_gradle_files = proj.get_build_files()
        for f in bld_gradle_files:
            possible_plgin_vers = str(cat(f) | grep("com.android.tools.build:gradle*"))
            has_plg_version = possible_plgin_vers != ""
            if not has_plg_version:
                continue
            plg_version = possible_plgin_vers.split(":")[-1]
            adeq_v = get_adequate_gradle_version(plg_version)
            for fprop in grad_prop_files:
                update_gradle_wrapper_version(fprop, adeq_v)

    elif error == KNOWN_ERROR.NO_WRAPPER:
        # no wrapper config
        try:
            shutil.copytree(GRADLE_WRAPPER_DIR, os.path.join(proj.proj_dir, "gradle"), dirs_exist_ok=True)
        except:
            pass

    elif error == KNOWN_ERROR.NO_GRADLEW_EXEC:
        shutil.copy(os.path.join(GRADLE_RES_DIR, "gradlew"), proj.proj_dir)
        #shutil.copytree(os.path.join(GRADLE_RES_DIR, "gradlew"), proj.proj_dir)

    elif error == KNOWN_ERROR.NO_TARGET_PLATFORM:
        # extract version -> use sdkmanager to download -> retry
        missing_platform = re.search("android-([0-9]+)", error_msg)
        if missing_platform is None:
            loge("Unable to find the version of the missing platform in the build output")
            return None
        SDKManager().download_platform(missing_platform.groups()[0])

    elif error == KNOWN_ERROR.NO_BUILD_TOOLS:
        # the build tools version being used was not downloaded
        current_build_tools_version = kwargs.get('build-tools')
        SDKManager().download_build_tools_version(current_build_tools_version)

    elif error == KNOWN_ERROR.BUILD_TOOLS_CPU_ERROR:
        # usually this error can be solved by upgrading BuildToolsVersion
        sdkman = SDKManager()
        current_build_tools_version = kwargs.get('build-tools')
        available_build_tools_list = sdkman.get_list_of_available_build_tools()
        new_vers = upgrade_version_from_version_list(available_build_tools_list, current_build_tools_version)
        sdkman.download_build_tools_version(new_vers)
        for bld_file in proj.get_build_files():
            replace_build_tools_version(bld_file, current_build_tools_version, new_vers)

    elif error == KNOWN_ERROR.MAYBE_MISSING_GOOGLE_REPO:
        # add repository in main gradle file
        main_grdl = proj.root_build_file
        add_google_repo(main_grdl)
        has_glu_glu = "google()" in str(cat(proj.root_build_file))
        if not has_glu_glu:
            add_google_repo_build_script(main_grdl)
    elif error == KNOWN_ERROR.MIN_SDK_ERROR:
        # a library needs a higher min sdk version. Use the version of the library
        required_version = re.search(KNOWN_ERROR.MIN_SDK_ERROR.value, error_msg).groups()[1].strip()
        if not required_version.isdigit():
            loge(f"Unable to read the required min sdk version from '{required_version}'")
            return None
        for bld_file in proj.get_build_files():
            file_ctent = str(cat(bld_file))
            new_file = replace_sdk_version(file_ctent, 'min', required_version)
            if new_file != file_ctent:
                with open(bld_file, 'w') as u:
                    u.write(new_file)
    elif error == KNOWN_ERROR.WRAPPER_ERROR:
        # can be solved the same way of WRAPPER_MISMATCH_ERROR
        recom_v = re.search("Minimum supported Gradle version is (.*). Current version", error_msg)
        recom_v = f'{recom_v.groups()[0].strip()}-all' if recom_v else get_adequate_gradle_version(get_gradle_plugin_version(proj.root_build_file))
        grad_prop_files = mega_find(proj.proj_dir, "gradle-wrapper.properties", type_file='f')
        if len(grad_prop_files) == 0:
            loge(f"No gradle-wrapper.properties file in {proj.proj_dir}. Unable to change the Gradle version")
            return None
        update_gradle_wrapper_version(grad_prop_files[0], recom_v )
        #solve_known_error(proj, error=KNOWN_ERRORS.WRAPPER_MISMATCH_ERROR, **kwargs)

    elif error == KNOWN_ERROR.NDK_BAD_CONFIG:
        loge("BAD NDK configuration. please update ndk path in resources/config/local.properties")
        local_Prop_file = os.path.join(RES_DIR, "config", "local.properties")
        shutil.copy(local_Prop_file, proj.proj_dir)
    elif error == KNOWN_ERROR.GOOGLE_REPO_ERROR:
        # upgrade build tools (min  at least 3.6)
        min = DefaultSemanticVersion("3.6.3")
        current_build_version = get_gradle_plugin_version(proj.root_build_file)
        replace_gradle_plugin_version( proj.root_build_file, current_build_version, min)
        solve_known_error(proj, KNOWN_ERROR.WRAPPER_MISMATCH_ERROR, error_msg, **kwargs)
    elif error == KNOWN_ERROR.WRONG_KEYSTORE or error == KNOWN_ERROR.ERROR_SIGNING_CONFIG:
        # replace signingConfig references in gradle files
        for bld_file in proj.get_build_files():
            new_file = str(cat(bld_file)).replace("signingConfig signingConfigs.release", "signingConfig null").replace("signingConfig signingConfigs.debug", "signingConfig null")
            # remove signingConfigs block from gradle files
            #new_file = re.sub(r'signingConfigs \{[^}]+}+}', ' ', new_file, flags=re.DOTALL)
            with open(bld_file, 'w') as u:
                u.write(new_file)

        #copy default keystore file and change keystore references in gradle files
        '''global KEYSTORE_ERROR_COUNT

        if KEYSTORE_ERROR_COUNT == 0:
            keystore_file = (re.search("Keystore file (.+) not found for signing", error_msg).groups()[0]
                             .replace("'", "").replace("\'","").strip())
            default_keystore = os.path.join(RES_DIR, "keys", "pynadroid-releases.keystore")
            shutil.copy(default_keystore, proj.proj_dir)
            for bld_file in proj.get_build_files():
                new_file = str(cat(bld_file)).replace(keystore_file, f"{default_keystore}")
                with open(bld_file, 'w') as u:
                    u.write(new_file)

            KEYSTORE_ERROR_COUNT += 1
        else:'''
        # remove storeFile reference
        for bld_file in proj.get_build_files():
            new_file = re.sub(r'storeFile\s+file\(.*\)', '', str(cat(bld_file)))
            with open(bld_file, 'w') as u:
                u.write(new_file)

    else:
        loge(f"Unable to solve {error}")
    return None


# (minimum plugin (AGP) version, Gradle version to use), in ascending order.
# Based on https://developer.android.com/build/releases/gradle-plugin#updating-gradle
GRADLE_VERSION_PER_PLUGIN_VERSION = [
    ("1.0.0", "2.3"), ("1.2.0", "2.9"), ("1.5.0", "2.13"), ("2.1.3", "3.5"), ("2.3.0", "3.3"),
    ("3.0.0", "4.1"), ("3.1.0", "4.4"), ("3.2.0", "4.6"), ("3.3.0", "4.10.1"), ("3.4.0", "5.1.1"),
    ("3.5.0", "5.4.1"), ("3.6.0", "5.6.4"), ("4.0.0", "6.1.1"), ("4.1.0", "6.5"), ("4.2.0", "6.7.1"),
    ("7.0.0", "7.0"), ("7.1.0", "7.2"), ("7.2.0", "7.3.3"), ("7.3.0", "7.4"), ("7.4.0", "7.5"),
    ("8.0.0", "8.0"), ("8.2.0", "8.2"), ("8.3.0", "8.4"), ("8.4.0", "8.6"), ("8.5.0", "8.7"),
    ("8.7.0", "8.9"), ("8.8.0", "8.10.2"), ("8.9.0", "8.11.1"), ("8.11.0", "8.13"),
    # 9.1 to 9.4: minimum of 9.0. If Gradle asks for a newer version, the WRAPPER_ERROR rule uses that version
    ("9.0.0", "9.1.0"), ("9.5.0", "9.6.0"),
]


def get_adequate_gradle_version(plugin_version):
    """given the gradle plugin version, returns an adequate gradle version to match the plugin version.

    Based on https://developer.android.com/studio/releases/gradle-plugin#updating-gradle table.
    Args:
        plugin_version: Gradle-plugin version.

    Returns:
        version: adequate gradle version.
    """
    version = DefaultSemanticVersion(plugin_version)
    adequate_version = None
    for min_plugin_version, gradle_version in GRADLE_VERSION_PER_PLUGIN_VERSION:
        if version >= DefaultSemanticVersion(min_plugin_version):
            adequate_version = gradle_version
    return f"{adequate_version}-all" if adequate_version is not None else None


def upgrade_version_from_version_list( version_list , upgradable_candidate, opt="max"):
    if opt == "min":
        list_of_bigger_patches = filter(lambda x: x.major == upgradable_candidate.major
                                               and x.minor == upgradable_candidate.minor
                                                    and x.patch > upgradable_candidate.patch,
                                        version_list)
        final_l = sorted(list_of_bigger_patches, key=lambda x: x.patch, reverse=True)
        if len(final_l) > 0:
            return final_l[0]
    else:
        # try major first
        list_of_bigger_majors = filter(lambda x: x.major > upgradable_candidate.major, version_list)
        final_l = list(sorted(set(list_of_bigger_majors), key=lambda x: x.major))

        if len(final_l) > 0:
            return final_l[0]

    # minor version
    list_of_bigger_minors = filter(
        lambda x: x.major == upgradable_candidate.major and x.minor > upgradable_candidate.minor, version_list)
    final_l = sorted(list_of_bigger_minors, key=lambda x: x.minor, reverse=True)
    if len(final_l) > 0:
        return final_l[0]

    if opt == "min":
        # major version
        list_of_bigger_majors = filter(lambda x: x.major > upgradable_candidate.major, version_list)
        final_l = sorted(list_of_bigger_majors, key=lambda x: x.major)

        if len(final_l) > 0:
            return final_l[0]
    else:
        # try major first
        list_of_bigger_patches = filter(lambda
                                            x: x.major == upgradable_candidate.major and x.minor == upgradable_candidate.minor and x.patch > upgradable_candidate.patch,
                                        version_list)
        final_l = sorted(list_of_bigger_patches, key=lambda x: x.patch, reverse=True)
        if len(final_l) > 0:
            return final_l[0]

    return upgradable_candidate


def replace_build_tools_version(bld_file, old_bld_version, new_bld_version):
    """replace build tools version on bld_file gradle file.
    Args:
        bld_file: path of build file.
        old_bld_version: old version.
        new_bld_version: new version.
    """
    old_str = str(old_bld_version)
    new_str = str(new_bld_version)
    new_file = re.sub(old_str, new_str, str(cat(bld_file)))
    with open(bld_file, 'w') as u:
        u.write(new_file)


def replace_gradle_plugin_version(bld_file, old_v, new_v):
    """replace gradle plugin version on bld_file gradle file.
    Args:
        bld_file: path of build file.
        old_v: old version.
        new_v: new version.
    """
    new_file = str(cat(bld_file)).replace(f'com.android.tools.build:gradle:{str(old_v)}', f'com.android.tools.build:gradle:{str(new_v)}')
    with open(bld_file, 'w') as u:
        u.write(new_file)


def add_google_repo(main_grdl):
    """Adds Google as repository to allprojects in main_grdl gradle file.
    Args:
        main_grdl: path of build file.
    """
    file_ctent = str(cat(main_grdl))
    new_file = file_ctent + "\nallprojects {repositories { maven { url 'https://maven.google.com/'\nname 'Google'}}}"
    with open(main_grdl, 'w') as u:
        u.write(new_file)


def add_google_repo_build_script(main_grdl):
    """Adds Google as repository to buildscript block in main_grdl file.
    Args:
        main_grdl: path of build file.
    """
    file_ctent = str(cat(main_grdl))
    new_file = file_ctent + "\nbuildscript {repositories { google() }}"
    with open(main_grdl, 'w') as u:
        u.write(new_file)


def update_gradle_wrapper_version(gradle_wrap_prop_filepath, new_v):
    """updates gradle wrapper version in properties file.
    Args:
        gradle_wrap_prop_filepath: properties file path.
        new_v: new version.
    """
    if new_v is None:
        loge(f"No adequate Gradle version found. {gradle_wrap_prop_filepath} was not changed")
        return
    fl_ctnt = file_content = str(cat(gradle_wrap_prop_filepath))
    current_v = str(echo(fl_ctnt)
                    | grep("distributionUrl=.*")).split("/")[-1].replace("gradle-", "").replace(".zip", "")
    file_content = file_content.replace(f"gradle-{current_v}.zip", f"gradle-{new_v}.zip")
    with open(gradle_wrap_prop_filepath, 'w') as u:
        u.write(file_content)


def get_gradle_plugin_version(gradle_file):
    """returns gradle plugin version.
    gets value of com.android.tools.build contained in gradle_file.

    Args:
        gradle_fileU (str): build.gradle filepath.

    Returns:
        gradle_plugin_version (str): plugin version.
    """
    gradle_plugin_version = str(cat(gradle_file) | grep("com.android.tools.build")
                                | sed("classpath|com.android.tools.build:gradle:|\"", "")).strip().replace("'","")
    return gradle_plugin_version

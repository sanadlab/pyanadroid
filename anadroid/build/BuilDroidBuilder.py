import os
import time

import builDroid
from builDroid import new_experiment, clone_and_set_metadata
from prompt_toolkit.key_binding.bindings.named_commands import self_insert
from textops import grep
import re
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.application.Application import App
from anadroid.build.AbstractBuilder import AbstractBuilder
from anadroid.build.NaiveGradleBuilder import BUILD_SUCCESS_VALUE
from anadroid.device.MockedDevice import MockedDevice
from anadroid.utils.Utils import mega_find, execute_shell_command, sign_apk, log_to_file, loge, logw, logs, logi


class BuilDroidBuilder(AbstractBuilder):
    def __init__(self, proj, device, resources_dir, instrumenter):
        super(BuilDroidBuilder, self).__init__(proj, device, resources_dir, instrumenter)
        self.build_flags = {}
        self.retry_on_fail = self.get_config("retry_failed", True)

    def build_proj_and_apk(self, build_type=BUILD_TYPE.DEBUG, build_tests_apk=False, rebuild=False):
        """builds project and generates apk of build type. It can optionally build the tests apk and/or rebuild
        the current project in case it was already built.
        Args:
            build_type(BUILD_TYPE): type of build to perform.
            build_tests_apk(bool): True if the tests' apk has to be generated, False otherwise.
            rebuild(bool): True if the current build has to be cleaned and rebuilt, False otherwise.

        Returns:
            bool: build results.
        """
        if not self.was_last_build_successful() or rebuild:
            builDroid.process_repository(self.proj.proj_dir, local_path=True, project_name=self.proj.proj_name,
                                         override_project=True)
            if not self.was_last_build_successful():
                return False
        return True

    def install_apks(self, build_type=BUILD_TYPE.DEBUG, install_apk_test=False):
        """install apk of build_type and optionally de tests apk.
        Args:
            build_type(BUILD_TYPE): build type.
            install_apk_test(bool): True if the tests' apk has to be installed, False otherwise.

        Returns:
            apps_list(list): list of installed apks.
        """
        apks = mega_find(os.path.join("buildAnaDroid_tests", self.proj.proj_dir, "outputs"), pattern="*.apk", type_file='f')
        for apk in apks:
            if build_type.value.lower() not in apk:
                continue
            self.device.install_apk(apk)

    def uninstall_all_apks(self):
        """uninstall all project apks."""
        if isinstance(self.device, MockedDevice):
            return
        apk_matching = self.device.get_package_matching(self.proj.pkg_name)
        if apk_matching is None:
            logw("No APKs matching project package name found")
            return
        logs(f"Uninstalling package {apk_matching}")
        ret = self.device.uninstall_pkg(apk_matching)
        if ret:
            logs(f"Package {apk_matching} uninstalled successfully")

    def create_app_from_installed_apk(self, gradle_output, build_type):
        """create App object from installed apk on device.
        Args:
            gradle_output: build output.
            build_type: build type.

        Returns:
            app(App): created app.
        """
        installed_apk_simple_name = re.search(r"Installing APK \'(.*?)\'", gradle_output).groups()[0]
        full_apk_path = next(
            filter(lambda x: str(x).endswith(installed_apk_simple_name), self.proj.get_apks(build_type=build_type)),
            self.proj.get_apks(build_type=build_type)[0])
        new_pkgs = self.device.get_new_installed_pkgs()
        if len(new_pkgs) == 0:
            # app was already installed
            logi("app already installed")
            app_pack = self.device.get_package_matching(self.proj.pkg_name)
            new_pkgs.append(app_pack)
        apk_pkg = new_pkgs[-1]  # ASSUMING JUST ONE
        app = App(self.device, self.proj, apk_pkg, apk_path=full_apk_path, local_res_dir=self.proj.results_dir)
        return app

    def sign_apks(self, build_type=BUILD_TYPE.DEBUG):
        """Sign project apks of build_type.
        Args:
            build_type: build type.

        Returns:
            bool: True if success, False otherwise.
        """
        if self.was_last_build_successful(task="sign") or build_type == BUILD_TYPE.DEBUG:
            return True
        for apk_path in self.proj.get_apks(build_type):
            ret, o, e = sign_apk(apk_path)
            if ret == 0 and len(e) < 3:
                logs("APK Successfully signed")
                return True
            else:
                loge(f"Error signing apk {apk_path} {e}")
                print(e)
                return False

    def build_apk(self, build_type=BUILD_TYPE.DEBUG):
        pass

    def build_tests_apk(self):
       pass

    def build(self, rebuild=False):
       pass

    def was_last_build_successful(self, task="build"):
        """checks if last build attempt was successful.
        inspects BUILD_RESULTS_FILE file and checks build result.
        Returns:
            bool: True if build was successful, False otherwise.
        """
        return self.was_attempted_to_build_before() and not self.needs_rebuild()

    def __has_built_apks(self):
        """checks if project has apks already built.
        Returns:
            bool: True if has, False otherwise.
        """
        return len(mega_find(self.proj.proj_dir, pattern="*.apk", type_file='f')) > 0

    def needs_rebuild(self):
        """checks if project needs rebuild.
        Returns:
            bool: True if needs, False otherwise.
        """
        return not self.__has_built_apks()  # TODO check build type and maybe last build output, lint, etc

    def was_attempted_to_build_before(self):
        """checks if there was a build attempt before.
        Returns:
            bool: True if yes, False otherwise.
        """
        return os.path.exists(os.path.join("builDroid_tests", self.proj.proj_name))

import json
import os
from abc import ABC, abstractmethod
from shutil import copy

from anadroid.Config import get_general_config

BUILD_RESULTS_FILE = "buildStatus.json"
SUCCESS_VALUE = "Success"
ERROR_VALUE = "Error"
BUILD_SUCCESS_VALUE = "BUILD SUCCESSFUL"

class AbstractBuilder(ABC):
    """
    An abstract class that defines the API for building apps using supported build systems.

    Attributes:
        android_home_dir (str): The path of the local Android home directory (value of $ANDROID_HOME).
        proj (`AndroidProject`): The project to build.
        device (`Device`): The targeted device.
        resources_dir (str): The pyanadroid resources directory.
        instrumenter (`AbstractInstrumenter`): The instrumentation tool used.
        config: Build configurations.

    """

    def __init__(self, proj, device, resources_dir, instrumenter, name='abstract_builder'):
        """
        Initializes a new instance of the AbstractBuilder class.

        Args:
            proj (`AndroidProject`): The project to build.
            device (`Device`): The targeted device.
            resources_dir (str): The pyanadroid resources directory.
            instrumenter (`AbstractInstrumenter`): The instrumentation tool used.

        """
        super().__init__()
        self.name = name
        self.android_home_dir = self.__get_android_home()
        self.proj = proj
        self.resources_dir = resources_dir
        self.instrumenter = instrumenter
        self.device = device
        self.__get_device_info()
        self.config = get_general_config("build")

    def set_project(self, project):
        self.proj = project

    @staticmethod
    def __get_android_home():
        """
        Gets the value of the environment variable ANDROID_HOME.

        Returns:
            android_home (str): Path to the Android SDK installation folder.

        Raises:
            Exception: If ANDROID_HOME is not set.

        """
        android_home = os.environ.get('ANDROID_HOME')
        if android_home is None or android_home == "":
            raise Exception("ANDROID_HOME not set")
        return android_home

    def __get_device_info(self):
        """
        Placeholder method for retrieving device information.
        Subclasses should implement this method to fetch device-related details.

        """
        pass

    @abstractmethod
    def build_apk(self):
        """
        Abstract method for building the main APK of the app.
        Subclasses must provide an implementation for building the APK.

        """
        pass

    @abstractmethod
    def build_tests_apk(self):
        """
        Abstract method for building the test APKs of the app.
        Subclasses must provide an implementation for building test APKs.

        """
        pass

    @abstractmethod
    def build(self):
        """
        Abstract method for the complete build process of the app.
        Subclasses must provide an implementation for the full build process.

        """
        pass

    def get_config(self, key, default=None):
        """
        Gets a configuration value identified by the given key.
        If no configuration is found, returns the specified default value.

        Args:
            key: The configuration key.
            default: The default value to return if the key is not found.

        Returns:
            value (str): The value of the configuration key, or the default value.

        """
        return self.config.get(key, default)

    def regist_successful_build(self, task="build"):
        """record successful build in file.
        Args:
            task: build task name.
        """
        filename = f"{self.name}_{BUILD_RESULTS_FILE}"
        filepath = os.path.join(self.proj.proj_dir, filename)
        js = {}
        if os.path.exists(filepath):
            with open(filepath, 'r') as fl:
                js = json.load(fl)

        js[task] = SUCCESS_VALUE
        with open(filepath, 'w') as outfile:
            json.dump(js, outfile)
        copy(filepath, os.path.join(self.proj.results_dir, filename))

    def regist_error_build(self, task="build"):
        """record successful build in file.
        Args:
            task: build task name.
        """
        filename = f"{self.name}_{BUILD_RESULTS_FILE}"
        filepath = os.path.join(self.proj.proj_dir, filename)
        js = {}
        if os.path.exists(filepath):
            with open(filepath, 'r') as fl:
                js = json.load(fl)
        js[task] = ERROR_VALUE
        with open(filepath, 'w') as outfile:
            json.dump(js, outfile)
        copy(filepath, os.path.join(self.proj.results_dir, filename))

    def get_previous_build_report_file(self):
        """Gets the path to the build report file.

        Returns:
            str: The path to the build report file.
        """

        real_filename = f"{self.name}_{BUILD_RESULTS_FILE}"
        if os.path.exists(os.path.join(self.proj.proj_dir, real_filename)):
            return os.path.join(self.proj.proj_dir, real_filename)
        elif os.path.exists(os.path.join(self.proj.results_dir, real_filename)):
            return os.path.join(self.proj.results_dir, real_filename)

        # for compat purposes only
        filename = BUILD_RESULTS_FILE
        if os.path.exists(os.path.join(self.proj.proj_dir, filename)):
            return os.path.join(self.proj.proj_dir, filename)
        elif os.path.exists(os.path.join(self.proj.results_dir, filename)):
            return os.path.join(self.proj.results_dir, filename)
        return os.path.join(self.proj.results_dir, real_filename)
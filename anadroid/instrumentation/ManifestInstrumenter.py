import os
import shutil
import xml.etree.ElementTree as ET

from anadroid.instrumentation.AbstractInstrumenter import AbstractInstrumenter
from anadroid.Types import TESTING_APPROACH, TESTING_FRAMEWORK, INSTRUMENTATION_TYPE
from anadroid.instrumentation.Types import INSTRUMENTATION_STRATEGY
from anadroid.utils.Utils import logi, logw, loge

# Android's XML namespace
ANDROID_NS = 'http://schemas.android.com/apk/res/android'


class AndroidManifestInstrumenter(AbstractInstrumenter):
    """
    Implements the AbstractInstrumenter interface to instrument an AndroidManifest.xml file.
    This instrumenter ensures the app is fully debuggable for analysis.
    - It always sets `android:debuggable="true"`.
    - For projects targeting API 29 (Android 10) or higher, it also adds
      `<profileable android:shell="true" />` to allow low-overhead profiling tools
      to attach even to non-debuggable builds, while still keeping the app debuggable
      for full analysis capabilities.
    """

    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_"):
        """
        Initializes the instrumenter.
        Args:
            profiler: The profiler object (part of the framework, maintained for interface compatibility).
            mirror_dirname(str): The name of the directory where the instrumented project will be stored.
        """
        super().__init__(profiler, mirror_dirname)
        # Register the Android namespace to be used by the XML parser.
        # This is crucial for finding and writing attributes like 'android:debuggable'.
        ET.register_namespace('android', ANDROID_NS)

    def get_log_filename(self):
        """Returns the log filename for this instrumenter."""
        return "manifest_instrumentation.log"

    def init(self):
        """Initializes any required resources. Nothing to do for this instrumenter."""
        pass

    def instrument(self, android_project, **kwargs):
        """
        Instruments the Android project by modifying its AndroidManifest.xml.

        This method creates a copy of the project, finds the manifest file in the copy,
        and then modifies the <application> tag to make it debuggable and/or profileable.

        Args:
            android_project: An object representing the Android project to be instrumented.
                             It is expected to have a `target_sdk_version` attribute.
            **kwargs: Additional arguments to maintain interface compatibility.

        Returns:
            str: The path to the directory containing the instrumented project.
        """
        # For interface compatibility, we accept these arguments but don't use them directly
        # as manifest instrumentation is independent of testing strategy.
        instr_type = kwargs.get("instr_type", INSTRUMENTATION_TYPE.MANIFEST)
        test_approach = kwargs.get("test_approach", TESTING_APPROACH.WHITEBOX)
        instr_strategy = kwargs.get("instr_strategy", INSTRUMENTATION_STRATEGY.METHOD_CALL)

        target_dir = os.path.join(android_project.proj_dir, self.mirror_dirname)

        if self.needs_reinstrumentation(android_project, test_approach, instr_type, instr_strategy):
            logi(f"Instrumenting AndroidManifest.xml for project at '{android_project.proj_dir}'")

            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(android_project.proj_dir, target_dir, ignore=shutil.ignore_patterns(self.mirror_dirname))

            relative_manifest_path = os.path.relpath(android_project.main_manif_file, android_project.proj_dir)
            manifest_path_in_target = os.path.join(target_dir, relative_manifest_path)

            if not os.path.exists(manifest_path_in_target):
                loge(f"AndroidManifest.xml not found at expected location: {manifest_path_in_target}")
                raise FileNotFoundError("Unable to find AndroidManifest.xml in the copied project.")

            try:
                # Call the new method that handles both debuggable and profileable attributes
                self.__make_app_debuggable_and_profileable(manifest_path_in_target, android_project)

                self.write_instrumentation_log_file(android_project, test_approach, instr_type, instr_strategy)
                logi(f"Successfully instrumented AndroidManifest.xml. Transformed project is at '{target_dir}'")
            except Exception as e:
                loge(f"Failed to instrument AndroidManifest.xml: {e}")
                shutil.rmtree(target_dir, ignore_errors=True)
                raise e
        else:
            logw("AndroidManifest.xml already has the required instrumentation state. Skipping.")

        return target_dir

    def __make_app_debuggable_and_profileable(self, manifest_path, android_project):
        """
        Parses the XML file, sets android:debuggable="true", and adds a <profileable> tag
        if the project's target SDK is 29 or higher.

        Args:
            manifest_path (str): The full path to the AndroidManifest.xml file.
            android_project: The project object, used to get the target SDK version.
        """
        logi(f"Modifying manifest at: {manifest_path}")
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        application_node = root.find('application')
        if application_node is None:
            raise ValueError("'<application>' tag not found in AndroidManifest.xml")

        # 1. Set android:debuggable="true" (unconditionally)
        debuggable_attr_key = f'{{{ANDROID_NS}}}debuggable'

        #logi("Set android:debuggable=\"true\" in the <application> tag.")

        # 2. Conditionally add <profileable android:shell="true" />
        try:
            target_sdk = int(self.profiler.device.get_device_sdk_version())
            if target_sdk >= 29:
                # Check if the <profileable> tag already exists to avoid duplicates
                if application_node.find('profileable') is None:
                    logi(f"Target SDK ({target_sdk}) >= 29. Adding <profileable> tag.")
                    # Create the new <profileable> element
                    profileable_node = ET.SubElement(application_node, 'profileable')
                    # Set the 'android:shell' attribute on the new element
                    shell_attr_key = f'{{{ANDROID_NS}}}shell'
                    profileable_node.set(shell_attr_key, 'true')
                else:
                    application_node.set(debuggable_attr_key, 'true')
                    logw("<profileable> tag already exists. Skipping addition.")
        except (ValueError, TypeError, AttributeError):
            logw(f"Could not determine target SDK version from project. Skipping <profileable> tag addition.")

        # 3. Write all changes back to the file
        tree.write(manifest_path, encoding='utf-8', xml_declaration=True)

    # The following methods ensure this class satisfies the AbstractInstrumenter interface.
    # Since manifest modification doesn't require build changes, these return empty/False values.

    def needs_build_plugin(self):
        """Returns False as no build plugins are needed."""
        return False

    def get_build_plugins(self):
        """Returns an empty list as no build plugins are needed."""
        return []

    def needs_build_dependency(self):
        """Returns False as no build dependencies are needed."""
        return False

    def get_build_dependencies(self):
        """Returns an empty list as no build dependencies are needed."""
        return []

    def needs_build_classpaths(self):
        """Returns False as no classpath dependencies are needed."""
        return False

    def get_build_classpaths(self):
        """Returns an empty list as no classpath dependencies are needed."""
        return []
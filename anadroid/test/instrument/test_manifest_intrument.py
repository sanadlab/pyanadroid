import time
from unittest import TestCase
from textops import cat, grep
from anadroid.Types import PROFILER
from anadroid.application.AndroidProject import AndroidProject
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrumentation.ManifestInstrumenter import AndroidManifestInstrumenter
from anadroid.profiler.ManafaProfiler import ManafaProfiler


class TestManifestInstrument(TestCase):
    device = MockedDevice()
    profiler = ManafaProfiler(profiler=PROFILER.MANAFA,device=device)
    instrumenter = AndroidManifestInstrumenter(profiler)

    def test_instrument_below29(self):
        """Tests instrumentation of AndroidManifest.xml."""
        proj_dir = "/Users/rar9993/repos/pyanadroid/demoProjects/SampleApp"
        start_time = time.time()
        android_project = AndroidProject('SampleApp', proj_dir)
        instr_dir = self.instrumenter.instrument(android_project=android_project, mirror_dirname="_TRANSFORMED_")
        instr_project = AndroidProject('SampleApp', instr_dir)
        end_time = time.time()
        print(f"Instrumentation completed in {end_time - start_time} seconds.")
        self.assertTrue(self.instrumenter.mirror_dirname.endswith("_TRANSFORMED_"))
        manifest_file = instr_project.main_manif_file
        file_content = str( cat(manifest_file) | grep("debuggable"))
        self.assertIn('android:debuggable="true"', file_content, "Debuggable attribute not set correctly.")

    def test_instrument_above29(self):
        """Tests instrumentation of AndroidManifest.xml."""
        proj_dir =  "/Users/rar9993/repos/pyanadroid/demoProjects/SampleApp"
        self.device.props["ro.build.version.sdk"] = 31
        start_time = time.time()
        android_project = AndroidProject('SampleApp', proj_dir)
        instr_dir = self.instrumenter.instrument(android_project=android_project, mirror_dirname="_TRANSFORMED_")
        instr_project = AndroidProject('SampleApp', instr_dir)
        end_time = time.time()
        print(f"Instrumentation completed in {end_time - start_time} seconds.")
        self.assertTrue(self.instrumenter.mirror_dirname.endswith("TRANSFORMED_"))
        manifest_file = instr_project.main_manif_file
        print(manifest_file)
        file_content = str( cat(manifest_file) | grep("debuggable"))
        self.assertIn('android:debuggable="true"', file_content, "Debuggable attribute not set correctly.")
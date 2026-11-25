import os
from abc import ABC, abstractmethod
from shutil import copy

from anadroid.Types import BUILD_SYSTEM, TESTING_APPROACH, TESTING_FRAMEWORK
from anadroid.instrumentation.AbstractInstrumenter import AbstractInstrumenter
from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE, INSTRUMENTATION_STRATEGY
from anadroid.utils.Utils import mega_find, logw

DEFAULT_LOG_FILENAME="instrumentation_log.json"

class NoneInstrumenter(AbstractInstrumenter):
    """Implements defined interface of AbstractInstrumenter to simulate instrumentation while not performing any
    project sources' changes.
   """
    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_"):
        super().__init__(profiler, mirror_dirname)

    def init(self):
        pass

    def needs_reinstrumentation(self, proj, test_approach, instr_type, instr_strategy):
        return

    def get_dirname(self, mirror_dirname="_TRANSFORMED_"):
        return f'NONE{mirror_dirname}'

    def instrument(self, android_project, mirror_dirname="_TRANSFORMED_", test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY,
                   instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST, **kwargs):
        """
        just clone the project files to a new directory.
        """
        new_dir_name = f'NONE{mirror_dirname}'
        new_proj_dir = os.path.join(android_project.proj_dir, new_dir_name)
        if not os.path.exists(new_proj_dir) or self.needs_reinstrumentation(android_project, test_approach, instr_type, instr_strategy):
            if not os.path.exists(new_proj_dir):
                os.mkdir(new_proj_dir)
            all_proj_files = list(map(lambda x: x.replace(android_project.proj_dir + os.sep, ""),
                                      filter(lambda t: mirror_dirname not in t, mega_find(android_project.proj_dir))))
            all_proj_files.sort(key=lambda s: len(s))
            for file_p in all_proj_files:
                full_file_path = os.path.join(android_project.proj_dir, file_p)
                target_file_path = os.path.join(android_project.proj_dir, new_dir_name, file_p)
                if '.git' in full_file_path:
                    continue
                if os.path.exists(target_file_path):
                    continue
                elif os.path.isdir(full_file_path):
                    if "TRANSFORMED" in file_p:
                        continue
                    os.mkdir(target_file_path)
                elif ('outputs' in full_file_path and 'build' in full_file_path
                      and os.path.isfile(full_file_path) and file_p.endswith('.apk')):
                    continue
                    #android_project.apk_files.append(target_file_path)
                elif not os.path.exists(target_file_path):
                    if 'lint' in file_p and not 'lint-baseline' in file_p and 'xml' in file_p:
                        continue
                    copy(full_file_path, target_file_path)

        else:
            logw("Same instrumentation of last time. Skipping instrumentation phase")
        return new_proj_dir

    def needs_build_plugin(self):
        return False

    def get_build_plugins(self):
        return {}

    def needs_build_dependency(self):
        return False

    def get_build_dependencies(self):
        return []


    def needs_build_classpaths(self):
        return False

    def get_build_classpaths(self):
       return []

    def get_log_filename(self):
        return DEFAULT_LOG_FILENAME

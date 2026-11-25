import re
from abc import abstractmethod

from anadroid.analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import get_analyzers_filter_file

DEFAULT_CFG_ANALYZERS_FILE = get_analyzers_filter_file()

# test source sets of Gradle: test, androidTest, their variants (testDebug, androidTestFree) and sharedTest
TEST_SOURCE_SET_REGEX = re.compile(r'^(?:(?:test|androidTest)(?:[A-Z]\w*)?|sharedTest)$')
# default test classes that Android Studio creates
TEST_FILENAME_MARKS = ("InstrumentedTest", "ExampleUnitTest")


def is_test_file(filepath):
    """checks if a file is test code.
    A file is test code if one of its directories is a test source set (e.g. src/test, src/androidTest),
    or if it is one of the default test classes of Android Studio.
    A path that only contains the text "test" (e.g. latest, contest) is not test code.
    """
    if not filepath:
        return False
    parts = re.split(r'[\\/]', str(filepath))
    return any(TEST_SOURCE_SET_REGEX.match(directory) for directory in parts[:-1]) \
        or any(mark in parts[-1] for mark in TEST_FILENAME_MARKS)


class StaticAnalyzer(AbstractAnalyzer):
    def __init__(self, analyzers_cfg_file=DEFAULT_CFG_ANALYZERS_FILE, **kwargs):
        super().__init__(analyzers_cfg_file, **kwargs)
        self.identifiable_issues = {}

    @abstractmethod
    def analyze_project(self, project, **kwargs):
        pass

    #@abstractmethod
    def get_project_metrics(self, project, **kwargs):
        pass

    def get_issues(self, project, ignore_tests=True) -> list:
        return []
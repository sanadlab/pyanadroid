from abc import abstractmethod

from anadroid.analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import get_analyzers_filter_file

DEFAULT_CFG_ANALYZERS_FILE = get_analyzers_filter_file()


class StaticAnalyzer(AbstractAnalyzer):
    def __init__(self, analyzers_cfg_file=DEFAULT_CFG_ANALYZERS_FILE):
        super().__init__(analyzers_cfg_file)
        self.identifiable_issues = {}

    @abstractmethod
    def analyze_project(self, project, **kwargs):
        pass

    #@abstractmethod
    def get_project_metrics(self, project, **kwargs):
        pass

    def get_issues(self, project) -> list:
        return []
from anadroid.analysis.ComposedAnalyzer import ComposedAnalyzer
from anadroid.analysis.pre_build_analysis.InferAnalysis import InferAnalysis
from anadroid.analysis.pre_build_analysis.SpotBugsAnalysis import SpotBugsAnalysis
from repo_analyze import init_pyanadroid


def main():
    repo_dir = 'demoProjects/MyApplication/ManafaProfiler_TRANSFORMED_'
    anadroid = init_pyanadroid(repo_dir)
    anadroid.pre_build_analyzers = ComposedAnalyzer(None, [
        SpotBugsAnalysis(),
        InferAnalysis(),
    ])
    anadroid.just_static_analyze()

if __name__ == '__main__':
    main()
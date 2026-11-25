from importlib import import_module

# name (used in the command line) -> class name. The module has the same name as the class.
PRE_BUILD_ANALYZERS = {
    "scc": "SCCAnalyzer",
    "lint": "LintAnalysis",
    "pmd": "PMDAnalysis",
    "daap": "DAAPAnalysis",
    "adoctor": "ADoctorAnalysis",
    "ecoandroid": "EcoAndroidAnalysis",
    "detekt": "DetektAnalysis",
    "spotbugs": "SpotBugsAnalysis",
    "infer": "InferAnalysis",
    "chimera": "ChimeraAnalysis",
    "xalint": "XALintAnalysis",
}


def create_pre_build_analyzers(names):
    """Creates the static analyzers with the given names.
    Args:
        names: names of analyzers (keys of PRE_BUILD_ANALYZERS).

    Returns:
        list: analyzer objects, in the same order.
    """
    analyzers = []
    for name in names:
        class_name = PRE_BUILD_ANALYZERS.get(name.lower())
        if class_name is None:
            raise ValueError(f"Unknown static analyzer {name}. Available: {', '.join(PRE_BUILD_ANALYZERS)}")
        module = import_module(f"{__name__}.{class_name}")
        analyzers.append(getattr(module, class_name)())
    return analyzers

from enum import Enum

from anadroid.instrumentation.Types import INSTRUMENTATION_TYPE


class BUILDER(Enum):
    ANADROID_GRADLE_BUILDER = 'AnadroidBuilder'
    BUILDROID = 'Buildroid'

class BUILD_SYSTEM(Enum):
    """Enumerates the build systems that can be used to build Android apps."""
    GRADLE = 'Gradle'
    ANT = 'Ant'
    MAVEN = "Maven"
    UNKNOWN = "Unknown"


class TESTING_FRAMEWORK(Enum):
    """Enumerates supported testing frameworks"""
    MONKEY = "Monkey"
    MONKEY_RUNNER = "Monkeyrunner"
    JUNIT = "JUnit"
    RERAN = "RERAN"
    ESPRESSO = "Espresso"
    ROBOTIUM = "Robotium"
    APP_CRAWLER = "Crawler"
    DROIDBOT = "Droidbot"
    CUSTOM = "Custom"
    OTHER = "Other"
    NONE = "None"


class PROFILER(Enum):
    """Enumerates sota energy profilers."""
    TREPN = 'Trepn'
    GREENSCALER = 'GreenScaler'
    PETRA = 'Petra'
    MONSOON = 'Monsoon'
    MANAFA = "E-manafa"
    NONE = "None"


class INSTRUMENTER(Enum):
    """Enumerates sota instrumentation tools."""
    JINST = 'JInst'
    HUNTER = 'Hunter'
    MANIFEST = 'Manifest'
    NONE = "None"


class TESTING_APPROACH(Enum):
    """Enumerates the 3 testing approaches."""
    WHITEBOX = "WhiteBox"
    BLACKBOX = "BlackBox"
    GREYBOX = "GreyBox"


class ANALYZER(Enum):
    """Enumerates the supported analyzers"""
    OLD_ANADROID_ANALYZER = 'Old Anadroid Analyzer'
    MANAFA_ANALYZER = 'Manafa Analyzer'

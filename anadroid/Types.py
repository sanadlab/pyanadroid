from enum import Enum

from anadroid.instrument.Types import INSTRUMENTATION_TYPE


class BUILD_SYSTEM(Enum):
    GRADLE = 'Gradle'
    ANT = 'Ant'
    MAVEN = "Maven"
    UNKNOWN = "Unknown"

class TESTING_FRAMEWORK(Enum):
    MONKEY = "Monkey"
    MONKEY_RUNNER = "Monkeyrunner"
    JUNIT = "JUnit"
    RERAN = "RERAN"
    ESPRESSO = "Espresso"
    ROBOTIUM = "Robotium"
    APP_CRAWLER = "APP_CRAWLER"
    DROIDBOT = "Droidbot"
    OTHER = "Other"

class PROFILER(Enum):
    TREPN = 'Trepn Profiler'
    GREENSCALER = 'GreenScaler'
    PETRA = 'Petra'
    MONSOON = 'Monsoon'
    MANAFA = "E-manafa"

class INSTRUMENTER(Enum):
    JINST = 'JInst'
    HUNTER = 'Hunter'

class TESTING_APPROACH(Enum):
    WHITEBOX = "WhiteBox"
    BLACKBOX = "BlackBox"
    GREYBOX = "GreyBox"

class ANALYZER(Enum):
    OLD_ANADROID_ANALYZER = 'Old Anadroid Analyzer'
    MANAFA_ANALYZER = 'Manafa Analyzer'

SUPPORTED_TESTING_APPROACHES = {
    TESTING_APPROACH.WHITEBOX
}

SUPPORTED_TESTING_FRAMEWORKS = {
    TESTING_FRAMEWORK.MONKEY,
    TESTING_FRAMEWORK.RERAN,
    TESTING_FRAMEWORK.APP_CRAWLER,
    TESTING_FRAMEWORK.MONKEY_RUNNER
}

SUPPORTED_BUILDING_SYSTEMS = {
    BUILD_SYSTEM.GRADLE
}

SUPPORTED_PROFILERS = {
    PROFILER.TREPN,
    PROFILER.MANAFA
}

SUPPORTED_INSTRUMENTERS = {
    INSTRUMENTER.JINST
}

SUPPORTED_ANALYZERS = {
    ANALYZER.OLD_ANADROID_ANALYZER,
    ANALYZER.MANAFA_ANALYZER
}

SUPPORTED_INSTRUMENTATION_TYPES = {
    INSTRUMENTATION_TYPE.TEST,
    INSTRUMENTATION_TYPE.ANNOTATION
}
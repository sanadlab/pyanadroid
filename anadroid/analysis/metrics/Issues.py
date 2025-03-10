import traceback
from enum import Enum


class IssueCategory(Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    USABILITY = "USABILITY"
    CORRECTNESS = "CORRECTNESS"
    ACCESSIBILITY = "ACCESSIBILITY"


def issue_from_string(issue_str, sep=','):
    issue_str = issue_str.strip()
    issue_parts = issue_str.split(sep)
    if len(issue_parts) < 9:
        return None
    try:
        issue_type = KnownStaticPerformanceIssues(issue_parts[0].split('.')[-1])
    except:
        traceback.print_exc()
        #print(issue_parts[0])
        issue_type = issue_parts[0].strip()
    #print(issue_parts)
    category = IssueCategory(issue_parts[1].strip())
    severity = issue_parts[2].strip()  if  issue_parts[2].strip()  != "None" else None
    detec_tool = issue_parts[3].strip()  if  issue_parts[3].strip()  != "None" else None
    description = issue_parts[4].strip() if  issue_parts[4].strip()  != "None" else None
    file = issue_parts[5].strip() if  issue_parts[5].strip()  != "None" else None
    line = issue_parts[6].strip() if  issue_parts[6].strip()  != "None" else None
    column = issue_parts[7].strip() if  issue_parts[7].strip()  != "None" else None
    method = issue_parts[8].strip() if  issue_parts[8].strip()  != "None" else None
    code = issue_parts[9].strip() if len(issue_parts) > 9 and issue_parts[9].strip()  != "None" else None
    i_class = issue_parts[10].strip() if len(issue_parts) > 10 and issue_parts[10].strip()  != "None" else None
    return Issue(issue_type, category, severity, description, file, i_class, detec_tool, line, column, method, code=code)

class Issue(object):
    def __init__(self, issue_type, category=IssueCategory.PERFORMANCE, severity=None, description=None, file=None,
                 i_class=None, detection_tool_name=None,
                 line=None, column=None, method=None, code=None, file_extensions=None):
        self.issue_type = issue_type
        self.category = category
        self.severity = severity
        self.description = description
        self.file = file
        self.i_class = i_class
        self.line = line
        self.column = column
        self.method = method
        self.code = code
        self.detection_tool_name = detection_tool_name
        self.file_extensions = None

    def get_file_extensions(self):
        return self.file_extensions if self.file_extensions is None else ' '.join(self.file_extensions)

    def __str__(self):
        return (f"{self.get_simple_name()}, {self.category.value}, {self.severity}, {self.detection_tool_name},"
                f" {self.description}, {self.file}, {self.line}, {self.column}, {self.method}, {self.code}")

    def get_issue_location(self):
        loc = []
        if self.line is not None:
            loc.append(f"line:{self.line}")
        if self.method is not None:
            loc.append(f"method:{self.method}")
        if self.i_class is not None:
            loc.append(f"class:{self.i_class}")
        if self.file is not None:
            loc.append(f"file:{self.file}")
        loc.reverse()
        return '|'.join(loc)

    def get_simple_name(self):
        return getattr(self.issue_type, 'value', str(self.issue_type))

    def __repr__(self):
        return self.get_simple_name() + " @ " + self.get_issue_location()

    def __eq__(self, other):
        return (str(self.issue_type) == str(other.issue_type)
                and getattr(self, 'file', None) == getattr(other, 'file', None)
                and getattr(self, 'i_class', None) == getattr(other, 'i_class', None)
                and getattr(self, 'method', None) == getattr(other, 'method', None)
                )

    def is_more_descriptive(self, other_issue):
        # evaluate if has more non None fields than other_issue
        return sum([1 for attr in ['file', 'i_class', 'method', 'line'] if getattr(self, attr, None) is not None]) > \
                sum([1 for attr in ['file', 'i_class', 'method', 'line'] if getattr(other_issue, attr, None) is not None])

    def is_less_descriptive(self, other_issue):
        # evaluate if has more non None fields than other_issue
        return sum([1 for attr in ['file', 'i_class', 'method', 'line'] if getattr(self, attr, None) is not None]) < \
                sum([1 for attr in ['file', 'i_class', 'method', 'line'] if getattr(other_issue, attr, None) is not None])

class KnownStaticPerformanceIssues(Enum):
    LAUNCH_ACTIVITY_FROM_NOTIFICATION = "LaunchActivityFromNotification"
    EXPENSIVE_ASSERTION = "ExpensiveAssertion"
    DUPLICATE_STRINGS = "DuplicateStrings"
    ASSERTION_SIDE_EFFECT = "AssertionSideEffect"
    SLOW_FOR_LOOP = "SlowForLoop"
    DRAW_ALLOCATION = "DrawAllocation"
    RECYCLE = "Recycle"
    WAKE_LOCK = "WakeLock"
    WAKELOCK_TIMEOUT = "WakelockTimeout"
    VIEW_HOLDER = "ViewHolder"
    OBSOLETE_LAYOUT_PARAM = "ObsoleteLayoutParam"
    BLOB_CLASS = "BLOBClass"
    SWISS_ARMY_KNIFE = "SwissArmyKnife"
    LONG_METHOD = "Longmethod"
    COMPLEX_CLASS = "ComplexClass"
    INTERNAL_GETTER_SETTER = "InternalGetterSetter"
    MEMBER_IGNORING_METHOD = "MemberIgnoringMethod"
    NO_LOW_MEMORY_RESOLVER = "NoLowMemoryResolver"
    LEAKING_INNER_CLASS = "LeakingInnerClass"
    UNSUITED_LRU_CACHE_SIZE = "UnsuitedLRUCacheSize"
    HASHMAP_USAGE = "HashmapUsage"
    UI_OVERDRAW = "UIOverdraw"
    INVALIDATE_WITHOUT_RECT = "InvalidatewithoutRect"
    UNSUPPORTED_HARDWARE_ACCELERATION = "UnsupportedHardwareAcceleration"
    HEAVY_ASYNC_TASK = "HeavyAsyncTask"
    HEAVY_SERVICE_START = "HeavyServiceStart"
    HEAVY_BROADCAST_RECEIVER = "HeavyBroadcastReceiver"
    BITMAP_FORMAT_USAGE = "BitmapFormatUsage"
    UNCLOSED_CLOSEABLE = "UnclosedCloseable"
    CAMERA_LEAK = "CameraLeak"
    SENSOR_LEAK = "SensorLeak"
    MEDIA_LEAK = "MediaLeak"
    LEAKING_THREAD = "LeakingThread"
    LEAKING_HANDLER = "LeakingHandler"
    DATA_TRANSMISSION_WITHOUT_COMPRESSION = "DataTransmissionWithoutCompression"
    VACUOUS_BACKGROUND_SERVICE = "VacuousBackgroundService"
    LIFECYCLE_CONTAINMENT = "LifecycleContainment"
    EARLY_RESOURCE_BINDING = "EarlyResourceBinding"
    IMMORTALITY_BUG = "ImmortalityBug"
    RIGID_ALARM_MANAGER = "RigidAlarmManager"
    INEFFICIENT_SQL_QUERY = "InefficientSQLQuery"
    DEBUGGABLE_RELEASE = "DebuggableRelease"
    INEFFICIENT_DATA_FORMAT_AND_PARSER = "InefficientDataFormatAndParser"
    MEMOIZATION_CHANCE = "MemoizationChance"
    DYNAMIC_WAIT_TIME = "DynamicWaitTime"
    INFO_WARNING_FCM = "InfoWarningFCM"
    PASSIVE_PROVIDER_LOCATION = "PassiveProviderLocation"
    SSL_SESSION_CACHING = "SSLSessionCaching"
    URL_CACHING = "URLCaching"
    CHECK_LAYOUT_SIZE = "CheckLayoutSize"
    CHECK_METADATA = "CheckMetadata"
    CHECK_NETWORK = "CheckNetwork"
    DIRTY_RENDERING = "DirtyRendering"
    EXCESSIVE_LOOP_CALLS_DETECTOR = "ExcessiveLoopCallsDetector"
    NESTED_WEIGHT = "NestedWeight"
    CONFIG_CHANGES = "ConfigChanges"
    DROPPED_DATA = "DroppedData"
    COLLECTION_OF_BITMAPS = "CollectionOfBitmaps"
    COLLECTION_OF_VIEWS = "CollectionOfViews"
    STATIC_BITMAP = "StaticBitmap"
    STATIC_CONTEXT = "StaticContext"
    STATIC_VIEW = "StaticView"
    STATIC_FIELD_LEAK = "StaticFieldLeak"
    APPEND_CHARACTER_WITH_CHAR = "AppendCharacterWithChar"
    AVOID_ARRAY_LOOPS = "AvoidArrayLoops"
    AVOID_CALENDAR_DATE_CREATION = "AvoidCalendarDateCreation"
    AVOID_FILE_STREAM = "AvoidFileStream"
    AVOID_INSTANTIATING_OBJECTS_IN_LOOPS = "AvoidInstantiatingObjectsInLoops"
    BIG_INTEGER_INSTANTIATION = "BigIntegerInstantiation"
    CONSECUTIVE_APPENDS_SHOULD_REUSE = "ConsecutiveAppendsShouldReuse"
    CONSECUTIVE_LITERAL_APPENDS = "ConsecutiveLiteralAppends"
    STRING_FORMAT_TRIVIAL = "StringFormatTrivial"
    INEFFICIENT_EMPTY_STRING_CHECK = "InefficientEmptyStringCheck"
    INEFFICIENT_STRING_BUFFERING = "InefficientStringBuffering"
    INSUFFICIENT_STRING_BUFFER_DECLARATION = "InsufficientStringBufferDeclaration"
    OPTIMIZABLE_TO_ARRAY_CALL = "OptimizableToArrayCall"
    REDUNDANT_FIELD_INITIALIZER = "RedundantFieldInitializer"
    STRING_INSTANTIATION = "StringInstantiation"
    STRING_TO_STRING = "StringToString"
    TOO_FEW_BRANCHES_FOR_SWITCH = "TooFewBranchesForSwitch"
    USE_ARRAY_LIST_INSTEAD_OF_VECTOR = "UseArrayListInsteadOfVector"
    USE_ARRAYS_AS_LIST = "UseArraysAsList"
    USE_INDEX_OF_CHAR = "UseIndexOfChar"
    USE_IO_STREAMS_WITH_APACHE_COMMONS_FILE_ITEM = "UseIOStreamsWithApacheCommonsFileItem"
    USELESS_STRING_VALUE_OF = "UselessStringValueOf"
    USE_STRING_BUFFER_FOR_STRING_APPENDS = "UseStringBufferForStringAppends"
    USE_STRING_BUFFER_LENGTH = "UseStringBufferLength"
    ADD_EMPTY_STRING = "AddEmptyString"
    USELESS_PARENT = "UselessParent"
    USELESS_LEAF = "UselessLeaf"
    ANIMATOR_KEEP = "AnimatorKeep"
    OBSOLETE_SDK_INT = "ObsoleteSdkInt"
    NOTIFY_DATA_SET_CHANGED = "NotifyDataSetChanged"
    NOTIFICATION_TRAMPOLINE = "NotificationTrampoline"
    DUPLICATE_DIVIDER = "DuplicateDivider"
    USE_VALUE_OF = "UseValueOf"
    UNPACKED_NATIVE_CODE = "UnpackedNativeCode"
    UNUSED_RESOURCES = "UnusedResources"
    UNUSED_IDS = "UnusedIds"
    INEFFICIENT_WEIGHT = "InefficientWeight"
    DISABLE_BASELINE_ALIGNMENT = "DisableBaselineAlignment"
    MERGE_ROOT_FRAME = "MergeRootFrame"
    DEV_MODE_OBSOLETE = "DevModeObsolete"
    LIFECYCLE_ANNOTATION_PROCESSOR_WITH_JAVA8 = "LifecycleAnnotationProcessorWithJava8"
    ANNOTATION_PROCESSOR_ON_COMPILE_PATH = "AnnotationProcessorOnCompilePath"
    LOG_CONDITIONAL = "LogConditional"
    WEARABLE_BIND_LISTENER = "WearableBindListener"
    USABLE_SPACE = "UsableSpace"
    VECTOR_PATH = "VectorPath"
    UNUSED_NAMESPACE = "UnusedNamespace"
    REDUNDANT_NAMESPACE = "RedundantNamespace"
    VIEW_TAG = "ViewTag"
    TOO_MANY_VIEWS = "TooManyViews"
    TOO_DEEP_LAYOUT = "TooDeepLayout"
    USE_COMPOUND_DRAWABLES = "UseCompoundDrawables"
    USE_OF_BUNDLED_GOOGLE_PLAY_SERVICES = "UseOfBundledGooglePlayServices"

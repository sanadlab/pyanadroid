from enum import Enum


class IssueCategory(Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    USABILITY = "USABILITY"
    CORRECTNESS = "CORRECTNESS"
    ACCESSIBILITY = "ACCESSIBILITY"


class Issue(object):
    def __init__(self, issue_type, category=IssueCategory.PERFORMANCE, severity=None, description=None, file=None,
                 i_class=None,
                 line=None, column=None, method=None, code=None):
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

    def __str__(self):
        return (f"{self.issue_type}, {self.category.value}, {self.severity},"
                f" {self.description}, {self.file}, {self.line}, {self.column}, {self.method}, {self.code}")

    def get_issue_location(self):
        if self.line is not None:
            return f"{self.file}:{self.line}"
        if self.method is not None:
            return f"{self.file}:{self.method}"
        if self.i_class is not None:
            return f"{self.file}:{self.i_class}"
        if self.file is not None:
            return self.file

    def __repr__(self):
        return getattr(self.issue_type, 'value', str(self.issue_type)) + " @ " + self.get_issue_location()



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

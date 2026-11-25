import matplotlib.pyplot as plt
import numpy as np

ISSUE_CATEGORY_MAPPING = {
    "SlowForLoop": ["Suboptimal Algorithm"],
    "DrawAllocation": ["Resource Management"],
    "Recycle": ["Resource Management", "API Misuse"],
    "WakeLock": ["Concurrency", "Resource Management"],
    "WakelockTimeout": ["Resource Management"],
    "ViewHolder": ["Suboptimal Algorithm", "Resource Management"],
    "ObsoleteLayoutParam": ["Resource Management", "Code Smell"],
    "BLOBClass": ["Code Smell"],
    "SwissArmyKnife": ["Code Smell"],
    "Longmethod": ["Code Smell"],
    "ComplexClass": ["Code Smell"],
    "InternalGetterSetter": ["Obsolete Solution"],
    "MemberIgnoringMethod": ["Suboptimal Algorithm"],
    "NoLowMemoryResolver": ["Resource Management"],
    "LeakingInnerClass": ["Code Smell"],
    "UnsuitedLRUCacheSize": ["Resource Management"],
    "HashmapUsage": ["Data Manipulation", "Obsolete Solution"],
    "Overdraw": ["Resource Management"],
    "UIOverdraw": ["Resource Management"],
    "InvalidatewithoutRect": ["Unnecessary Computation"],
    "UnsupportedHardwareAcceleration": ["Suboptimal Algorithm"],
    "HeavyAsyncTask": ["Concurrency", "Suboptimal Algorithm"],
    "HeavyServiceStart": ["Suboptimal Algorithm"],
    "HeavyBroadcastReceiver": ["Suboptimal Algorithm"],
    "BitmapFormatUsage": ["Resource Management"],
    "UnclosedCloseable": ["Resource Management"],
    "CameraLeak": ["Resource Management"],
    "MediaLeak": ["Resource Management"],
    "LeakingThread": ["Resource Management"],
    "LeakingHandler": ["Resource Management"],
    "DataTransmissionWithoutCompression": ["RPC/IPC", "Suboptimal Algorithm"],
    "VacuousBackgroundService": ["Resource Management"],
    "LifecycleContainment": ["Resource Management"],
    "EarlyResourceBinding": ["Resource Management"],
    "ImmortalityBug": ["Resource Management"],
    "RigidAlarmManager": ["Suboptimal Algorithm"],
    "InefficientSQLQuery": ["Data Access", "RPC/IPC"],
    "DebuggableRelease": ["Resource Management"],
    "InefficientDataFormatAndParser": ["Data Access", "Suboptimal Algorithm"],
    "MemoizationChance": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "DynamicWaitTime": ["Suboptimal Algorithm", "RPC/IPC"],
    "InfoWarningFCM": ["Obsolete Solution"],
    "PassiveProviderLocation": ["Resource Management"],
    "SSLSessionCaching": ["RPC/IPC"],
    "URLCaching": ["RPC/IPC", "Unnecessary Computation"],
    "CheckLayoutSize": ["Resource Management", "Unnecessary Computation"],
    "CheckMetadata": ["Unnecessary Computation"],
    "CheckNetwork": ["RPC/IPC"],
    "DirtyRendering": ["Unnecessary Computation"],
    "ExcessiveLoopCallsDetector": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "NestedWeight": ["Resource Management", "Suboptimal Algorithm"],
    "ConfigChanges": ["Resource Management"],
    "DroppedData": ["Resource Management"],
    "CollectionOfBitmaps": ["Resource Management"],
    "CollectionOfViews": ["Resource Management"],
    "StaticBitmap": ["Code Smell"],
    "StaticContext": ["Code Smell"],
    "StaticView": ["Code Smell"],
    "StaticFieldLeak": ["Code Smell"],
    "UselessStringValueOf": ["Data Manipulation", "Unnecessary Computation"],
    "AppendCharacterWithChar": ["Data Manipulation", "Suboptimal Algorithm"],
    "AvoidArrayLoops": ["Data Manipulation", "Obsolete Solution"],
    "AvoidCalendarDateCreation": ["Obsolete Solution", "Unnecessary Computation"],
    "AvoidFileStream": ["Data Access", "Obsolete Solution"],
    "AvoidInstantiatingObjectsInLoops": ["Unnecessary Computation"],
    "BigIntegerInstantiation": ["Data Manipulation", "Unnecessary Computation"],
    "ConsecutiveAppendsShouldReuse": ["Data Manipulation", "Code Smell"],
    "ConsecutiveLiteralAppends": ["Data Manipulation", "Code Smell"],
    "InefficientEmptyStringCheck": ["Data Manipulation", "Suboptimal Algorithm"],
    "InefficientStringBuffering": ["Data Manipulation"],
    "InsufficientStringBufferDeclaration": ["Data Manipulation"],
    "OptimizableToArrayCall": ["Data Manipulation", "Suboptimal Algorithm"],
    "RedundantFieldInitializer": ["Code Smell"],
    "StringInstantiation": ["Data Manipulation", "Unnecessary Computation"],
    "StringToString": ["Data Manipulation", "Unnecessary Computation"],
    "TooFewBranchesForSwitch": ["Code Smell"],
    "UseArrayListInsteadOfVector": ["Obsolete Solution", "Data Manipulation"],
    "UseArraysAsList": ["Obsolete Solution", "Data Manipulation"],
    "UseIndexOfChar": ["Data Manipulation", "Suboptimal Algorithm"],
    "UseIOStreamsWithApacheCommonsFileItem": ["Data Access", "API Misuse"],
    "UseStringBufferForStringAppends": ["Data Manipulation"],
    "UseStringBufferLength": ["Data Manipulation", "Suboptimal Algorithm"],
    "AddEmptyString": ["Data Manipulation", "Unnecessary Computation"],
    "UselessParent": ["Resource Management"],
    "UselessLeaf": ["Resource Management"],
    "AnimatorKeep": ["Resource Management"],
    "ObsoleteSdkInt": ["Obsolete Solution", "Code Smell"],
    "DuplicateDivider": ["Obsolete Solution", "Code Smell"],
    "UseValueOf": ["Data Manipulation", "Unnecessary Computation"],
    "UnpackedNativeCode": ["Build Optimization"],
    "UnusedResources": ["Resource Management"],
    "UnusedIds": ["Resource Management", "Code Smell"],
    "InefficientWeight": ["Resource Management", "Suboptimal Algorithm"],
    "DisableBaselineAlignment": ["Resource Management", "Suboptimal Algorithm"],
    "MergeRootFrame": ["Resource Management"],
    "DevModeObsolete": ["Build Optimization", "Obsolete Solution"],
    "LifecycleAnnotationProcessorWithJava8": ["Build Optimization", "Obsolete Solution"],
    "AnnotationProcessorOnCompilePath": ["Build Optimization"],
    "LogConditional": ["Code Smell"],
    "WearableBindListener": ["Obsolete Solution"],
    "UsableSpace": ["Data Access", "Obsolete Solution"],
    "VectorPath": ["Resource Management"],
    "UnusedNamespace": ["Resource Management", "Code Smell"],
    "RedundantNamespace": ["Resource Management", "Code Smell"],
    "ViewTag": ["Obsolete Solution"],
    "TooManyViews": ["Resource Management", "Suboptimal Algorithm"],
    "TooDeepLayout": ["Resource Management", "Suboptimal Algorithm"],
    "UseCompoundDrawables": ["Resource Management", "Suboptimal Algorithm"],
    "UseOfBundledGooglePlayServices": ["Build Optimization"],
    "StringFormatTrivial": ["Data Manipulation", "Unnecessary Computation"],
    "AssertionSideEffect": ["Unnecessary Computation", "Code Smell"],
    "DuplicateStrings": ["Resource Management", "Code Smell"],
    "ExpensiveAssertion": ["Unnecessary Computation", "Code Smell"],
    "LaunchActivityFromNotification": ["Code Smell"],
    "NotificationTrampoline": ["Obsolete Solution"],
    "AutoboxingStateCreation": ["Data Manipulation"],
    "AutoboxingStateValueProperty": ["Data Manipulation", "Unnecessary Computation"],
    "FrequentlyChangedStateReadInComposition": ["Unnecessary Computation"],
    "KaptUsageInsteadOfKsp": ["Build Optimization", "Obsolete Solution"],
    "NotifyDataSetChanged": ["Suboptimal Algorithm", "Obsolete Solution"],
    "UnnecessaryArrayInit": ["Data Manipulation", "Unnecessary Computation"],
    "SyntheticAccessor": ["Suboptimal Algorithm"],
    "UseOfNonLambdaOffsetOverload": ["Unnecessary Computation"],
    "InefficientKeySetIterator": ["Data Manipulation", "Suboptimal Algorithm"],
    "InvariantCall": ["Unnecessary Computation"],
    "IPCOnUIThread": ["Suboptimal Algorithm", "RPC/IPC"],
    "RegexOpOnUIThread": ["Unnecessary Computation"],
    "ExpensiveExecutionTime": ["Suboptimal Algorithm"],
    "HugeSharedStringConstant": ["Data Manipulation"],
    "BlockingMethodsOnURL": ["RPC/IPC"],
    "ExplicitGarbageCollection": ["Suboptimal Algorithm", "Code Smell"],
    "BoxedPrimitiveToString": ["Data Manipulation", "Unnecessary Computation"],
    "BoxedPrimitiveForParsing": ["Data Manipulation", "Unnecessary Computation"],
    "BoxedPrimitiveForCompare": ["Data Manipulation", "Unnecessary Computation"],
    "UnboxedAndCorecedForTernaryOperator": ["Data Manipulation"],
    "UnboxingImmediatelyReboxed": ["Data Manipulation", "Unnecessary Computation"],
    "BoxingImmediatelyUnboxed": ["Data Manipulation", "Unnecessary Computation"],
    "BoxingImmediatelyUnboxedToPerformCoercion": ["Data Manipulation", "Unnecessary Computation"],
    "NewForGetClass": ["Unnecessary Computation"],
    "NextIntViaNextDouble": ["Suboptimal Algorithm"],
    "UnusedField": ["Code Smell", "Unnecessary Computation"],
    "UnreadField": ["Code Smell"],
    "UncalledPrivateMethod": ["Code Smell"],
    "UseStringBufferConcatenation": ["Data Manipulation", "Suboptimal Algorithm"],
    "ElementsGetLengthInLoop": ["Data Access", "Unnecessary Computation"],
    "PrepareStatementInLoop": ["Data Access", "Unnecessary Computation"],
    "PatternCompileInLoop": ["Unnecessary Computation"],
    "InefficientLastIndexOf": ["Data Manipulation", "Suboptimal Algorithm"],
    "UnnecessaryMath": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "BloatedSynchronizedBlock": ["Concurrency"],
    "DubiousListCollection": ["Data Manipulation", "Suboptimal Algorithm"],
    "DubiousSetofCollections": ["Data Manipulation", "Suboptimal Algorithm"],
    "ContainsOnCollectedStream": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "AvoidSizeOnCollectedStream": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "UseFindFirst": ["Unnecessary Computation", "Suboptimal Algorithm"],
    "ExecutorNotShuttingDown": ["Resource Management"],
    "DoubleBufferCopy": ["Data Access", "Suboptimal Algorithm"],
    "ListIndexIterating": ["Suboptimal Algorithm"],
    "LocalSynchronizedCollection": ["Concurrency", "Unnecessary Computation"],
    "RunFinalization": ["Code Smell", "API Misuse"],
    "InstanceBasedThreadLocal": ["Concurrency"],
    "PossibleMemoryBloat": ["Resource Management"],
    "TailRecursion": ["Suboptimal Algorithm"],
    "UseEnumCollections": ["Data Manipulation", "Obsolete Solution"],
    "ArrayPrimitive": ["Data Manipulation"],
    "CouldBeSequence": ["Suboptimal Algorithm"],
    "SpreadOperator": ["Data Manipulation"],
    "UnnecessaryPartOfBinaryExpression": ["Code Smell"],
    "UnnecessaryTypeCasting": ["Code Smell", "Unnecessary Computation"],
    "LogToStringParameter": ["Unnecessary Computation", "API Misuse"],
    "LogAppendedStringInFormat": ["Data Manipulation", "API Misuse"],
    "UseSingletonList": ["Suboptimal Algorithm", "API Misuse"],
    "CallingSizeOnSubContainer": ["Unnecessary Computation"],
    "ContainsKeyBeforeGet": ["Suboptimal Algorithm"],
    "GetBeforeRemove": ["Suboptimal Algorithm"],
    "NeedlessInstanceRetrieval": ["Unnecessary Computation"],
    "NeedlessMemberCollectionSynchronization": ["Unnecessary Computation", "Concurrency"],
    "OptionalPrimitiveVariantPreferred": ["Data Manipulation", "Suboptimal Algorithm"],
    "OptionalIssuesUsesImmediateExecution": ["Unnecessary Computation"],
    "PreSizeCollections": ["Suboptimal Algorithm"],
    "SubOptimalCollectionSizing": ["Suboptimal Algorithm"],
    "StaticArrayCreatedInMethod": ["Unnecessary Computation"],
    "SubOptimalExpressionOrder": ["Suboptimal Algorithm"],
    "SQLInLoop": ["Data Access", "Suboptimal Algorithm"],
    "ContainsBeforeAdd": ["Unnecessary Computation"],
    "ContainsBeforeRemove": ["Unnecessary Computation"],
    "UseAddAll": ["Suboptimal Algorithm"],
    "UnjitableMethod": ["Code Smell"],
    "ForEachOnRange": ["Suboptimal Algorithm"]
}

vibe_all_flagged_issues_projs = {
    "FlappyBird": 41,
    "GPTFlappyBird": 22,
    "Game2048": 34,
    "GPTGame2048": 27,
    "WeatherApp": 20,
    "GPTWeather": 6,
    "TodoNotes": 8,
    "GPTToDoNotes": 22,
    "ScientificCalculator": 13,
    "GPTScientificCalculator": 14,
    "GalleryApp": 25,
    "GPTPhotoGallery": 11,
}

vibe_tps_projs = {
    "FlappyBird": 8,
    "GPTFlappyBird": 5,
    "Game2048": 10,
    "GPTGame2048": 4,
    "WeatherApp": 3,
    "GPTWeather": 3,
    "TodoNotes": 4,
    "GPTToDoNotes": 7,
    "ScientificCalculator": 3,
    "GPTScientificCalculator": 2,
    "GalleryApp": 2,
    "GPTPhotoGallery": 5
}

vibe_total_annotated_issues = {
    "FlappyBird": 10,
    "GPTFlappyBird": 8,
    "Game2048": 14,
    "GPTGame2048": 9,
    "WeatherApp": 4,
    "GPTWeather": 5,
    "TodoNotes": 6,
    "GPTToDoNotes": 13,
    "ScientificCalculator": 4,
    "GPTScientificCalculator": 3,
    "GalleryApp": 5,
    "GPTPhotoGallery": 9
}

similar_all_flagged_issues_projs = {
    "CalcYou": 4,
    "Calculator-You": 97,
    "game2048": 0,
    "privacy-friendly-2048": 175,
    "Gallery": 0,
    "Tulsi": 142,
    "NotePad": 331,
    "another-notes-app": 11,
    "World-Weather": 226,
    "weather-overview": 44,
    "beat-feet": 0,
    "lato": 148,
}

similar_tps_issues_projs = {
    "CalcYou": 3.25,
    "Calculator-You": 49.2352225735552,
    "game2048": 0,
    "privacy-friendly-2048": 119.78049935981787,
    "Gallery": 0,
    "Tulsi": 119.54717813051145,
    "NotePad": 176.82692325231386,
    "another-notes-app": 2.9473684210526314,
    "World-Weather": 122.58952922415187,
    "weather-overview": 33.31876149436044,
    "beat-feet": 0,
    "lato": 69.67408992298802,
}

similar_total_annotated_issues = {
    "CalcYou": 4,
    "Calculator-You": 91,
    "game2048": 0,
    "privacy-friendly-2048": 111,
    "Gallery": 0,
    "Tulsi": 0,
    "NotePad": 191,
    "another-notes-app": 1,
    "World-Weather": 157,
    "weather-overview": 28,
    "beat-feet": 1,
    "lato": 23,
}


def plot_histogram():
    # Combine keys from all dictionaries
    projects = list(vibe_all_flagged_issues_projs.keys())
    x = np.arange(len(projects))  # X-axis positions
    # Extract values for each dictionary
    all_flagged = [vibe_all_flagged_issues_projs[proj] for proj in projects]
    tps = [vibe_tps_projs[proj] for proj in projects]
    total_annotated = [vibe_total_annotated_issues[proj] for proj in projects]

    # Plot histograms
    bar_width = 0.25
    plt.figure(figsize=(12, 6))
    bars1 = plt.bar(x - bar_width, all_flagged, width=bar_width, label='All Flagged Issues', color='blue')
    bars2 = plt.bar(x, total_annotated, width=bar_width, label='Total Annotated Issues', color='green')
    bars3 = plt.bar(x + bar_width, tps, width=bar_width, label='True Positives', color='orange')
    label_font_size = 8
    # Add labels on top of bars
    for bar in bars1:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(bar.get_height()), ha='center', va='bottom', fontsize=label_font_size )
    for bar in bars2:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(bar.get_height()), ha='center', va='bottom', fontsize=label_font_size )
    for bar in bars3:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(bar.get_height()), ha='center', va='bottom', fontsize=label_font_size)

    # Add labels and legend
    plt.xlabel('Projects', fontweight='bold')
    plt.ylabel('Count', fontweight='bold')
    plt.title('PAPs Occurrences Across Projects', fontweight='bold')
    plt.xticks(x, projects, rotation=30, ha='right', fontsize=8)
    plt.legend()
    plt.tight_layout()
    plt.show()


    projects = list({k: v for k,v in similar_total_annotated_issues.items() if v>0}.keys())
    x = np.arange(len(projects))  # X-axis positions
    # Extract values for each dictionary
    all_flagged = [similar_all_flagged_issues_projs[proj] for proj in projects]
    tps = [similar_tps_issues_projs[proj] for proj in projects]
    total_annotated = [similar_total_annotated_issues[proj] for proj in projects]

    # Plot histograms
    plt.figure(figsize=(12, 6))
    bars1 = plt.bar(x - bar_width, all_flagged, width=bar_width, label='All Flagged Issues', color='blue')
    bars2 = plt.bar(x, total_annotated, width=bar_width, label='Total Annotated Issues', color='green')
    bars3 = plt.bar(x + bar_width, tps, width=bar_width, label='True Positives', color='orange')

    # Add labels on top of bars
    for bar in bars1:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),  int(bar.get_height()), ha='center',
                 va='bottom', fontsize=label_font_size, rotation=0)
    for bar in bars2:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), int(bar.get_height()), ha='center',
                 va='bottom', fontsize=label_font_size , rotation=0)
    for bar in bars3:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), int(bar.get_height()), ha='center',
                 va='bottom', fontsize=label_font_size , rotation=0)

    # Add labels and legend
    plt.xlabel('Projects', fontweight='bold')
    plt.ylabel('Count', fontweight='bold')
    plt.title('Comparison of Issues Across Projects', fontweight='bold')
    plt.xticks(x, projects, rotation=30, ha='right', fontsize=8)
    plt.legend()
    plt.tight_layout()
    plt.show()

def print_stats():
    print(f'total vibe issues: {sum(vibe_all_flagged_issues_projs.values())}')
    print(f'total similar issues: {sum(similar_all_flagged_issues_projs.values())}')

def main():
    print_stats()
    plot_histogram()

if __name__ == '__main__':
    main()
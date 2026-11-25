import csv

from classify_issue_occurences import print_stats

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

def main(filename, categs=False):
    with open(filename, 'r') as file2:
        reader1 = csv.reader(file2, delimiter=';')
        stats = {}
        for row in reader1:
            #print(row)
            iss_name = row[1].strip()
            tool_name = row[0].strip()
            proj = row[2].replace('/NONE_TRANSFORMED_','').strip()
            file = row[3].strip()
            decision = row[4].strip()
            issue_categs = ISSUE_CATEGORY_MAPPING.get(iss_name, []) if categs else []
            if (decision == 'true' or "true_positive" in decision):
                stats['true_positive'] = stats.get('true_positive', 0) + 1
                stats[f'iss_{iss_name}_true_positive'] = stats.get(f'iss_{iss_name}_true_positive', 0) + 1
                for c in issue_categs:
                    k = iss_name + c + "_true_positive"
                    stats[k] = stats.get(k, 0) + 1
            elif ('false' in decision or ('unknown' not in decision and decision not in (
                    "true_positive", 'true', 'real_true_positive'))):
                stats['false_positive'] = stats.get('false_positive', 0) + 1
                stats[f'iss_{iss_name}_false_positive'] = stats.get(f'iss_{iss_name}_false_positive', 0) + 1
                for c in issue_categs:
                    k = iss_name + c + "_false_positive"
                    stats[k] = stats.get(k, 0) + 1
            else:
                stats['unknown'] = stats.get('unknown', 0) + 1
                stats[f'iss_{iss_name}_unknown'] = stats.get(f'iss_{iss_name}_unknown', 0) + 1
                for c in issue_categs:
                    k = iss_name + c + "_unknown"
                    stats[k] = stats.get(k, 0) + 1
                continue

    #get_stats(stats, sum(stats.values()), filename, analyze_catgs=categs, count_unknown=True)
    print(stats)
    print_stats_per_issue(stats)




def get_stats(stats, total, input_file, analyze_catgs=True, count_unknown=False):
    # calculate precision, recall, f1 score

    precision = stats.get('true_positive', 0) / (stats.get('true_positive', 0) + stats.get('false_positive', 0)) if (stats.get('true_positive', 0) + stats.get( 'false_positive', 0)) > 0 else 0
    recall = stats.get('true_positive', 0) / (stats.get('true_positive', 0) + stats.get('false_negative', 0)) if (
                                                                                                                         stats.get(
                                                                                                                             'true_positive',
                                                                                                                             0) + stats.get(
                                                                                                                     'false_negative',
                                                                                                                     0)) > 0 else 0
    if count_unknown:
        precision_u = stats.get('true_positive', 0) / (stats.get('unknown', 0) + stats.get('true_positive', 0) + stats.get('false_positive', 0)) if (stats.get('true_positive',
                                                                                                  0) + stats.get(
            'false_positive', 0)) > 0 else 0
        recall_u = stats.get('true_positive', 0) / (stats.get('unknown', 0) + stats.get('true_positive', 0) + stats.get('false_negative', 0)) if (
                                                                                                                             stats.get(
                                                                                                                                 'true_positive',
                                                                                                                                 0) + stats.get(
                                                                                                                         'false_negative',
                                                                                                                         0)) > 0 else 0
        f1_score_u = 2 * (precision_u * recall_u) / (precision_u + recall_u) if (precision_u + recall_u) > 0 else 0


    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    print("============= ", input_file, " =============")
    print(f"Total: {total}")
    print(f"True Positive: {stats.get('true_positive', 0)}")
    print(f"False Positive: {stats.get('false_positive', 0)}")
    print(f"True Negative: {stats.get('true_negative', 0)}")
    print(f"False Negative: {stats.get('false_negative', 0)}")
    print(f"Unknown: {stats.get('unknown', 0)}")
    print(f"Precision: {round(precision * 100, 2)}%")
    print(f"Recall: {round(recall * 100, 2)}%")
    print(f"F1 Score: {round(f1_score * 100, 2)}%")
    if count_unknown:
        print(f"Precision (Unknown): {round(precision_u * 100, 2)}%")
        print(f"Recall (Unknown): {round(recall_u * 100, 2)}%")
        print(f"F1 Score (Unknown): {round(f1_score_u * 100, 2)}%")
    print("Accuracy: ", (stats.get('true_positive', 0) + stats.get('true_negative', 0)) / total if total > 0 else 0)
    print("----------------------")

    if not analyze_catgs:
        return

    # print per category stats (precision, recall, etc) (split by _)
    categories = set()
    for key in stats.keys():
        if '_' in key and len(key.split('_')) > 2:
            categories.add(key.split('_')[0])
    for category in sorted(categories, key=lambda x: x.lower()):
        tp = stats.get(category + '_true_positive', 0)
        fp = stats.get(category + '_false_positive', 0)
        tn = stats.get(category + '_true_negative', 0)
        fn = stats.get(category + '_false_negative', 0)
        total = tp + fp + tn + fn
        if total == 0:
            continue
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        print(f"Category: {category}")
        print(f"  True Positive: {tp}")
        print(f"  False Positive: {fp}")
        print(f"  True Negative: {tn}")
        print(f"  False Negative: {fn}")
        print(f"  Precision: {round(precision * 100, 2)}%")
        print(f"  Recall: {round(recall * 100, 2)}%")
        print(f"  F1 Score: {round(f1_score * 100, 2)}%")
        print("----------------------")


def print_stats_per_issue(stats):
    issue_stats = {}
    for key in [x for x in stats.keys() if 'iss_' in x]:
        if '_' in key and len(key.split('_')) > 2:
            issue_name = '_'.join(key.split('_')[:-2]).replace("iss_", '')
            metric = '_'.join(key.split('_')[-2:])
            print(issue_name, metric)
            if issue_name not in issue_stats:
                issue_stats[issue_name] = {}
            issue_stats[issue_name][metric] = stats[key]
    js = {}
    for issue_name in sorted(issue_stats.keys(), key=lambda x: x.lower()):
        issue = issue_stats[issue_name]
        tp = issue.get('true_positive', 0)
        fp = issue.get('false_positive', 0)
        tn = issue.get('true_negative', 0)
        fn = issue.get('false_negative', 0)
        #unk = issue.get('unknown', 0)
        total = tp + fp + tn + fn #+ unk
        if total == 0:
            continue
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        print(f"Issue: {issue_name}")
        js[issue_name] = {
            'true_positive': tp,
            'false_positive': fp,
            'true_negative': tn,
            'false_negative': fn,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }
       # print(f"{issue_name}#-#{round(precision * 100, 2)}")
        #print(f"  True Positive: {tp}")
        #print(f"  False Positive: {fp}")
        #print(f"  True Negative: {tn}")
        #print(f"  False Negative: {fn}")
        #print(f"  Precision: {round(precision * 100, 2)}%")
        #print(f"  Recall: {round(recall * 100, 2)}%")
        #print(f"  F1 Score: {round(f1_score * 100, 2)}%")
        print("----------------------")
        with open("issue_level_annotated_stats.json", 'w') as outfile:
            import json
            json.dump(js, outfile, indent=4)

if __name__ == '__main__':
    filename = "llm_gen_datasets/maloco_merged_dataset_annotated.csv"
    main(filename)
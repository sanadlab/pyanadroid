import sys
import csv


def stats_for_blind_test(input_files):
    for input_file in input_files:
        stats = {}
        total = 0
        with open(input_file, 'r') as infile:
            reader = csv.reader(infile, delimiter=';')
            for row in reader:
                if len(row) < 3:
                    continue
                if row[-1].lower().strip() == 'detected':
                    stats['true_positive'] = stats.get('true_positive', 0) + 1
                elif row[-1].lower().strip() == 'not detected':
                    stats['false_positive'] = stats.get('false_positive', 0) + 1
                else:
                    stats['unknown'] = stats.get('unknown', 0) + 1
                    continue
                total += 1
        # calculate precision, recall, f1 score
        precision = stats.get('true_positive', 0) / (
                    stats.get('true_positive', 0) + stats.get('false_positive', 0)) if (stats.get('true_positive',
                                                                                                  0) + stats.get(
            'false_positive', 0)) > 0 else 0
        recall = stats.get('true_positive', 0) / (stats.get('true_positive', 0) + stats.get('false_negative', 0)) if (
                                                                                                                                 stats.get(
                                                                                                                                     'true_positive',
                                                                                                                                     0) + stats.get(
                                                                                                                             'false_negative',
                                                                                                                             0)) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        print("============= ", input_file, " =============")
        print(f"Total: {total}")
        print(f"True Positive: {stats.get('true_positive', 0)}")
        print(f"False Positive: {stats.get('false_positive', 0)}")
        print(f"True Negative: {stats.get('true_negative', 0)}")
        print(f"False Negative: {stats.get('false_negative', 0)}")
        print(f"Unknown: {stats.get('unknown', 0)}")
        print(f"Precision: {round(precision*100, 2)}%")
        print(f"Recall: {recall}")
        print(f"F1 Score: {round(f1_score*100, 2)}%")
        print("Accuracy: ", (stats.get('true_positive', 0) + stats.get('true_negative', 0)) / total if total > 0 else 0)
        print("----------------------")

def stats_for_n_shot(input_files):
    # open csv file and read content
    for input_file in input_files:
        stats = {}
        total = 0
        with open(input_file, 'r') as infile:
            reader = csv.reader(infile, delimiter=';')
            for row in reader:
                if len(row) < 3:
                    print(f"Skipping row in {input_file}: {row}")
                    continue
                #print(row)
                if (row[-2].lower().strip() == 'true' or row[-2].lower().strip() == "true_positive") and row[
                    -1].lower().strip() == 'detected':
                    stats['true_positive'] = stats.get('true_positive', 0) + 1
                elif (row[-2].lower().strip() == 'false' or row[-2].lower().strip() not in (
                "true_positive", 'true')) and row[-1].lower().strip() == 'detected':
                    stats['false_positive'] = stats.get('false_positive', 0) + 1
                elif (row[-2].lower().strip() == 'false' or row[-2].lower().strip() not in (
                "true_positive", 'true')) and row[-1].lower().strip() == 'not detected':
                    stats['true_negative'] = stats.get('true_negative', 0) + 1
                elif (row[-2].lower().strip() == 'true' or row[-2].lower().strip() == "true_positive") and row[
                    -1].lower().strip() == 'not detected':
                    stats['false_negative'] = stats.get('false_negative', 0) + 1
                else:
                    stats['unknown'] = stats.get('unknown', 0) + 1
                    continue
                total += 1
        # calculate precision, recall, f1 score
        precision = stats.get('true_positive', 0) / (
                    stats.get('true_positive', 0) + stats.get('false_positive', 0)) if (stats.get('true_positive',
                                                                                                  0) + stats.get(
            'false_positive', 0)) > 0 else 0
        recall = stats.get('true_positive', 0) / (stats.get('true_positive', 0) + stats.get('false_negative', 0)) if (
                                                                                                                                 stats.get(
                                                                                                                                     'true_positive',
                                                                                                                                     0) + stats.get(
                                                                                                                             'false_negative',
                                                                                                                             0)) > 0 else 0
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
        print("Accuracy: ", (stats.get('true_positive', 0) + stats.get('true_negative', 0)) / total if total > 0 else 0)
        print("----------------------")

def stats_for_zero_shot(input_files):
    for f in input_files:
        print(f)

def process_files(input_files):
    for f in input_files:
        if 'blind' in f:
            stats_for_blind_test([f])
        elif 'zero_shot' not in f or 'detailed' in f:
            stats_for_n_shot([f])
        else:
            stats_for_zero_shot([f])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python prompt_eng_tasks.py <input_file>")
        sys.exit(1)
    process_files(sys.argv[1:])

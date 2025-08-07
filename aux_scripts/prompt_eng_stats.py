import csv
import json
import os

import pandas as pd
from matplotlib import pyplot as plt


def main():
    # load csvs in llm_results folder
    csv_files = [os.path.join(root, file) for root, dirs, files in os.walk('llm_results') for file in files if file.endswith('.csv')]
    prompt_res = {}
    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            # parse csv into dict
            csv_dict = {}
            csv_reader = csv.reader(f, delimiter=';')
            for row in csv_reader:
                if row[0] not in csv_dict:
                    csv_dict[row[0]] = {
                        'detected': 0,
                        'inconclusive': 0,
                        'not detected': 0,
                        'unknown': 0,
                        'total': 0
                    }
                csv_dict[row[0]][row[-1].lower()] += 1
                csv_dict[row[0]]['total'] += 1

        prompt_res[csv_file] = csv_dict
    # for each csv file, plot a table with the results using pyplot
    det_rates = {}
    for csv_file, issues in prompt_res.items():
        issue_names = list(issues.keys())
        fig, ax = plt.subplots()
        ax.axis('off')
        df = pd.DataFrame({
            'Issue': issue_names,
            'Detected (%)': [round(issues[issue]['detected'] / issues[issue]['total'] * 100, 3) for issue in issue_names],
            'Not Detected (%)': [round(issues[issue]['not detected'] / issues[issue]['total'] * 100, 3) for issue in issue_names],
            'Inconclusive (%)': [round(issues[issue]['inconclusive'] / issues[issue]['total'] * 100, 3) for issue in issue_names],
            'Unknown (%)': [round(issues[issue]['unknown'] / issues[issue]['total'] * 100, 3) for issue in issue_names]
        })
        det_rates[csv_file] = [x for x in df['Detected (%)']]
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(14)
        table.scale(1.5, 1.5)
        # tight layout
        plt.tight_layout()
        # set window title
        plt.get_current_fig_manager().set_window_title(f'Results for {os.path.basename(csv_file)}')


        #plt.title(f'Results for {os.path.basename(csv_file)}')
        plt.show()

    # plot detection rates as bloxplot
    plt.figure(figsize=(10, 6))
    plt.boxplot(det_rates.values(), labels=[os.path.basename(csv_file) for csv_file in prompt_res.keys()])
    plt.xlabel('CSV Files', fontweight='bold')
    plt.ylabel('Detected (%)', fontweight='bold')
    plt.title('Detection Rates')
    plt.tight_layout()
    plt.show()

    '''
    # for each csv file, plot the results using pyplot
    for csv_file, issues in prompt_res.items():
        plt.figure(figsize=(10, 6))
        issue_names = list(issues.keys())
        detected = [issues[issue]['detected'] for issue in issue_names]
        inconclusive = [issues[issue]['inconclusive'] for issue in issue_names]
        not_detected = [issues[issue]['not detected'] for issue in issue_names]
        unknown = [issues[issue]['unknown'] for issue in issue_names]
        total = [issues[issue]['total'] for issue in issue_names]
        bar_width = 0.2

        r5 = range(len(issue_names))
        r1 = [x + bar_width for x in r5]
        r2 = [x + bar_width for x in r1]
        r3 = [x + bar_width for x in r2]
        r4 = [x + bar_width for x in r3]

        plt.bar(r5, total, color='black', width=bar_width, edgecolor='grey', label='Total')
        plt.bar(r1, detected, color='green', width=bar_width, edgecolor='grey', label='Detected')
        plt.bar(r3, not_detected, color='red', width=bar_width, edgecolor='grey', label='Not Detected')
        plt.bar(r2, inconclusive, color='orange', width=bar_width, edgecolor='grey', label='Inconclusive')
        plt.bar(r4, unknown, color='grey', width=bar_width, edgecolor='grey', label='Unknown')
        plt.xlabel('Issues', fontweight='bold')
        plt.ylabel('Count', fontweight='bold')
        plt.title(f'Results for {os.path.basename(csv_file)}')
        plt.xticks([r + bar_width for r in range(len(issue_names))], issue_names, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.show()'''




if __name__ == '__main__':
    main()
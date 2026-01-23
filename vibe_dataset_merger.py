import csv
import random

TARGET_NAME = "llm_gen_datasets/maloco_merged_dataset_annotated.csv"

def main(csv1, csv2, csv3):
    row_set = {}
    read_rows = 0
    with open(csv1, 'r') as file1:
        reader1 = csv.reader(file1, delimiter=';')
        for row in reader1:
            #print(row)
            if len(row) < 4:
                continue
            tool_name = row[0].strip()
            iss_name = row[1].strip()
            proj = row[2].strip()
            file = row[3].strip()
            man_decision = row[-1].strip().split(',')[0].strip()
            key = f"{tool_name}_{iss_name}_{proj}_{file.split('/')[-1]}"
            row_set[key] =  {
                    'tool_name': tool_name,
                    'iss_name': iss_name,
                    'proj': proj.replace('/NONE_TRANSFORMED_',''),
                    'file': file.replace('/NONE_TRANSFORMED_',''),
                    'man_decision': man_decision
                }
            read_rows += 1
    print(f"Read {read_rows} rows from {csv1}", len(row_set))
    read_rows = 0
    with open(csv3, 'r') as file3:
        reader1 = csv.reader(file3, delimiter=';')
        for row in reader1:
            proj = row[0].split(';')[0].replace('"','').strip()
            iss_name =  row[0].split(';')[-1].replace('"','').strip()
            tool_name = row[3].strip()
            file = row[5].strip().split('/')[-1]
            man_decision = 'real_true_positive' if "TRUE" in row[8].upper() else 'real_false_positive'
            key = f"{tool_name}_{iss_name}_{proj}_{file.split('/')[-1]}"
            if key in row_set:
                key += f"_{random.randint(0,10000000)}"
            row_set[key] = {
                'tool_name': tool_name,
                'iss_name': iss_name,
                'proj': proj.replace('/NONE_TRANSFORMED_',''),
                'file': file.replace('/NONE_TRANSFORMED_',''),
                'man_decision': man_decision
            }
            read_rows += 1
    print(f"Read {read_rows} rows from {csv3}", len(row_set))
    read_rows = 0
    with open(csv2, 'r') as file2:
        reader1 = csv.reader(file2, delimiter=';')
        for row in reader1:
            # print(row)
            iss_name = row[0].strip()
            tool_name = row[1].strip()
            proj = row[2].replace('/NONE_TRANSFORMED_','').strip()
            file = row[3].replace('/NONE_TRANSFORMED_','').strip().split('/')[-1]
            man_decision = row[-1].strip().split(',')[0].strip()
            key = f"{tool_name}_{iss_name}_{proj}_{file.split('/')[-1]}"
            row_set[key] = {
                'tool_name': tool_name,
                'iss_name': iss_name,
                'proj': proj,
                'file': file,
                'man_decision': man_decision
            }
            read_rows += 1
    print(f"Read {read_rows} rows from {csv2}", len(row_set))
    with open(TARGET_NAME, 'w') as outfile:
        for row in row_set.values():
            outfile.write( ';'.join(row.values()) + "\n")


if __name__ == '__main__':
    main("llm_gen_datasets/nothing.csv",
         "llm_gen_datasets/all_validated_annotated_issues.csv",
         "llm_gen_datasets/vibe_coding_issues_annotated.csv"
         )
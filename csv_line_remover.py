
# remove lines of csv containing a certain string. the string to match and name of the file are passed by arg

import csv
import sys
import os

def remove_lines_from_csv(match_string, file_path):
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        return
    count = 0
    temp_file_path = file_path + '.tmp'

    with open(file_path, 'r', newline='') as csvfile, open(temp_file_path, 'w', newline='') as temp_csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        writer = csv.writer(temp_csvfile,delimiter=';')

        for row in reader:
            if match_string not in ','.join(row):
                writer.writerow(row)
            else:
                count += 1

    os.replace(temp_file_path, file_path)
    print(f"Lines containing '{match_string}' ({count}) have been removed from {file_path}.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_line_remover.py <match_string>  <file_path>")
        sys.exit(1)

    match_string = sys.argv[1]
    file_paths = sys.argv[2:]
    print(file_paths)
    for fp in file_paths:
        remove_lines_from_csv(match_string, fp)
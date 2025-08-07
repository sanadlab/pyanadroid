import ast
import os
import sys
import csv

if len(sys.argv) != 2:
    print("Usage: python dataset_path_fixer.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = "fixed_" + os.path.basename(input_file)


with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.reader(infile, delimiter=';')
    row_set = set()
    for row in reader:
        #print(row)
        row_str = ';'.join(row).replace("ruirua", 'rar9993')
        proj_path = row[0].replace("ruirua", 'rar9993')
        orig_path = proj_path
        if not os.path.exists(proj_path):
            # maybe changed to another path
            #print(proj_path ,"nao existe")
            if 'native_apps' in proj_path:
                proj_path = proj_path.replace('native_apps', 'cross_platform_apps')
                if not os.path.exists(proj_path):
                    proj_path = proj_path.replace('cross_platform_apps', 'unknown')
                    if not os.path.exists(proj_path):
                        print(proj_path ,"nao existe")
                        continue
            elif 'cross_platform_apps' in proj_path:
                proj_path = proj_path.replace('cross_platform_apps', 'native_apps')
                if not os.path.exists(proj_path):
                    proj_path = proj_path.replace('native_apps', 'unknown')
                    if not os.path.exists(proj_path):
                        print(proj_path, "nao existe")
                        continue
            elif 'unknown' in proj_path:
                proj_path = proj_path.replace('unknown', 'native_apps')
                if not os.path.exists(proj_path):
                    proj_path = proj_path.replace('native_apps', 'cross_platform_apps')
                    if not os.path.exists(proj_path):
                        print(proj_path, "nao existe")
                        continue
        row_set.add(row_str.replace(orig_path, proj_path))
    for r in row_set:
        #print(row)
        outfile.write(r + "\n")




print(f"Fixed paths written to {output_file}")

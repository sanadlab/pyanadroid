
import os
import shutil
import sys

if len(sys.argv) != 2:
    print("Usage: python results_dir_merger.py <input_dir>")
    sys.exit(1)


input_dir = sys.argv[1]

unknown = [x for x in os.listdir(input_dir) if 'unknown' in x]
for proj_res_dir in [x for x in os.listdir(input_dir) if 'unknown' not in x]:
    app_id = proj_res_dir.split('--')[0]
    if f"{app_id}--unknown" in unknown and os.path.exists(os.path.join(input_dir, f"{app_id}--unknown")):
        print(app_id, proj_res_dir)
        if app_id not in ['app', 'android']:
            print("moving ", f"{app_id}--unknown", " to ", proj_res_dir)
            for inside_res_dir in [os.path.join(os.path.join(input_dir, f"{app_id}--unknown", x)) for x in os.listdir(os.path.join(input_dir, f"{app_id}--unknown"))]:
                if os.path.isdir(inside_res_dir):
                    try:
                        shutil.move(inside_res_dir, os.path.join(input_dir, proj_res_dir))
                    except:
                        for x in os.listdir(os.path.join(input_dir, f"{app_id}--unknown")):
                            shutil.move(os.path.join(input_dir, f"{app_id}--unknown", x), os.path.join(input_dir, proj_res_dir, x))
            shutil.rmtree(os.path.join(input_dir, f"{app_id}--unknown"))

            #shutil.move(os.path.join(input_dir,  f"{app_id}--unknown"), os.path.join(input_dir, proj_res_dir))
            #exit(0)

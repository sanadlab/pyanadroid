
import os, csv

from anadroid.utils.Utils import mega_find

base_dirs = ["native_apps"]
tool_ct = {}
tool_list = ['adoctor', 'ecoandroid', 'daap', 'pmd', 'ecoandroid_rl', 'lint', 'droidlens', 'chimera', 'xAL']
processed_ids = set()
for t in tool_list:
    tool_ct[t] = {'success': 0, 'fail': 0, 'total': set()}
for base_dir in base_dirs:
    for proj_dir in [os.path.join(base_dir, x) for x in os.listdir(base_dir)]:
        for ver_dir in [ os.path.join(proj_dir, x) for x in os.listdir(proj_dir)]:
            # get all files inside verdir
            if not os.path.isdir(ver_dir):
                continue
            ver_id = os.path.basename(ver_dir)
            if ver_id in processed_ids:
                continue
            processed_ids.add(ver_id)
            file_list = [os.path.join(ver_dir, x) for x in os.listdir(ver_dir)]
            if not any(x.endswith("adoctor.csv") for x in file_list):
                tool_ct['adoctor']['fail'] += 1
                tool_ct['adoctor']['total'].add(ver_id)
            else:
                tool_ct['adoctor']['success'] += 1
                tool_ct['adoctor']['total'].add(ver_id)
            #print(file_list)
            ecos = [ x for x in file_list if "ecoandroid" in x and not 'resource_leaks' in x]
            #print(ecos)
            if len(ecos) > 0:
                xml_files = [ x for x in os.listdir(ecos[0]) if x.endswith(".xml")]
                if len(xml_files) > 0:
                    tool_ct['ecoandroid']['success'] += 1
                    tool_ct['ecoandroid']['total'].add(ver_id)
                else:
                    tool_ct['ecoandroid']['fail'] += 1
                    tool_ct['ecoandroid']['total'].add(ver_id)

            rl_ecos = [ x for x in mega_find(ver_dir, pattern='*ecoandroid*') if 'resource_leaks' in x]
            print(rl_ecos)
            # print(ecos)
            if len(rl_ecos) > 0:
                csv_files = [ x for x in os.listdir(rl_ecos[0]) if x.endswith("all.csv")]
                if len(csv_files) > 0:
                    tool_ct['ecoandroid_rl']['success'] += 1
                    tool_ct['ecoandroid_rl']['total'].add(ver_id)
                else:
                    tool_ct['ecoandroid_rl']['fail'] += 1
                    tool_ct['ecoandroid_rl']['total'].add(ver_id)
            daap = [ x for x in file_list if "daap" in x and x.endswith(".json")]
            if len(daap) > 0:
                tool_ct['daap']['success'] += 1
                tool_ct['daap']['total'].add(ver_id)
            else:
                tool_ct['daap']['fail'] += 1
                tool_ct['daap']['total'].add(ver_id)
            lint = [ x for x in file_list if "lint" in x and x.endswith(".xml")]
            if len(lint) > 0:
                tool_ct['lint']['success'] += 1
                tool_ct['lint']['total'].add(ver_id)
            else:
                tool_ct['lint']['fail'] += 1
                tool_ct['lint']['total'].add(ver_id)
            pmd = [ x for x in file_list if "pmd_analysis" in x and x.endswith(".json")]
            if len(pmd) > 0:
                tool_ct['pmd']['success'] += 1
                tool_ct['pmd']['total'].add(ver_id)
            else:
                tool_ct['pmd']['fail'] += 1
                tool_ct['pmd']['total'].add(ver_id)
            drods = mega_find(ver_dir, pattern='*droidlens*', type_file="d")
            if sum([len(os.listdir(x)) for x in drods]) > 0:
                tool_ct['droidlens']['success'] += 1
                tool_ct['droidlens']['total'].add(ver_id)
            else:
                tool_ct['droidlens']['fail'] += 1
                tool_ct['droidlens']['total'].add(ver_id)
for t in tool_ct:
    print(t, tool_ct[t]['success'], tool_ct[t]['fail'], len(tool_ct[t]['total']))
    #print(tool_ct[t]['total'])
    if len(tool_ct[t]['total']) > 0:
        print("Success rate: ", (tool_ct[t]['success'] / len(tool_ct[t]['total'])) * 100)
        print("Fail rate: ", (tool_ct[t]['fail'] / len(tool_ct[t]['total'])) * 100)
    #print("Success rate: ", (tool_ct[t]['success'] / (tool_ct[t]['success'] + tool_ct[t]['fail'])) * 100)
    #print("Fail rate: ", (tool_ct[t]['fail'] / (tool_ct[t]['success'] + tool_ct[t]['fail'])) * 100)
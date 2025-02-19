import ast
import json
import os
from os import listdir
from subprocess import Popen, PIPE, TimeoutExpired
from datetime import datetime
import matplotlib.pyplot as plt
from pylab import *

from textops import find, cat

from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis

EXCLUDED_LANGS = {'gitignore', 'Markdown', 'License', 'JSON', 'YAML', 'Prolog', 'Batch', 'Properties File'}
INCLUDED_LANGS = {'Java', 'Python', 'Dart', 'TypeScript', 'JavaScript', 'C', 'C Header', 'C++', 'Kotlin', 'Rust'}





def get_project_root_dir(proj_path):
    """infers Android project root directory."""
    has_gradle_right_next = mega_find(proj_path, pattern="build.gradle", maxdepth=4, type_file='f')
    if len(has_gradle_right_next) > 0:
        top_gradle_file = min(has_gradle_right_next, key=len)
        return os.path.dirname(top_gradle_file)
    return None


def is_android_project(dirpath):
    """determines if a given directory is an Android Project.
    looks for settings.gradle files.
    Args:
        dirpath: path of the directory.

    Returns:
        bool: True if file is in diretory, False otherwise.
    """
    return any([f for f in listdir(dirpath) if '.gradle' in f])


def load_projects(dirpath):
    """loads Android Projects from a directory containing one or more projects."""
    return_projs = []
    if is_android_project(dirpath):
        potential_projects = [dirpath]
    else:
        potential_projects = list(
            filter(lambda x: os.path.isdir(os.path.join(dirpath, x)), os.listdir(dirpath)))
    for maybe_proj in potential_projects:
        path_dir = os.path.join(dirpath, maybe_proj)
        proj_fldr = get_project_root_dir(path_dir)
        if proj_fldr is not None:
            return_projs.append(proj_fldr)
        else:
            children_dirs = list(filter(lambda x: os.path.isdir(os.path.join(path_dir, x)), os.listdir(path_dir)))
            for child in children_dirs:
                child_path_dir = os.path.join(path_dir, child)
                proj_fldr = get_project_root_dir(child_path_dir)
                if proj_fldr is not None:
                    return_projs.append(proj_fldr)
    return return_projs


def build_scc_json_for_all_projs(dirpath):
    projs = load_projects(dirpath)
    print(f"total projs: {len(projs)}")
    for pdir in projs:
        res, o, e = execute_shell_command(f"scc {pdir} -f json > {os.path.join(pdir,'scc.json')}")


def execute_shell_command(cmd, args=[], timeout=None):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print(command)
    proc = Popen(command, stdout=PIPE, stderr=PIPE,shell=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except TimeoutExpired as e:
        print("command " + cmd + " timed out")
        out = e.stdout if e.stdout is not None else out
        err = e.stderr if e.stderr is not None else err
        proc.kill()
        proc.returncode = 1
    return proc.returncode, out.decode("utf-8"), err.decode('utf-8')


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


class LanguageStats(object):
    def __init__(self):
        self.language_info = {}
        self.proj_info = {}
        self.parsed_files = set()
        self.pure_native = {
            "Java": [],
            "Java+C": [],
            "Kotlin": [],
            "Kotlin+C":[],
            "mix": [],
            "C": [],
        }
        self.cross = {
            "JavaScript": [],
            "Dart": [],
            "Java": [],
            "Kotlin": [],
            "C": [],
        }

    def add_language_info(self, proj_path, lang_info):
        #print(lang_info)
        if 'Name' not in lang_info or lang_info['Name'] in EXCLUDED_LANGS or lang_info['Name'] not in INCLUDED_LANGS:
            return
        if lang_info['Name'] in self.language_info:
            # update stats
            self.language_info[lang_info['Name']] = {
                'proj_count': 1 + self.language_info[lang_info['Name']]['proj_count'],
                'total_loc': lang_info['Code'] + self.language_info[lang_info['Name']]['total_loc'],
                'total_cc': lang_info['Complexity'] + self.language_info[lang_info['Name']]['total_cc'],
                'total_files': lang_info['Count'] + self.language_info[lang_info['Name']]['total_files'],
                'proj_files': self.language_info[lang_info['Name']]['proj_files'] + [proj_path]
            }
        else:
            # new entry
            self.language_info[lang_info['Name']] = {
                'proj_count': 1,
                'total_loc': lang_info['Code'],
                'total_cc': lang_info['Complexity'],
                'total_files': lang_info['Count'],
                'proj_files': [proj_path]
            }
        # add unique stats



    def parse_file(self, filepath):
        with open(filepath, 'r') as jj:
            info = json.load(jj)
        proj_results_dir = os.path.dirname(filepath)
        proj_file = os.path.join(proj_results_dir, 'project_path.txt')
        proj_path = str(cat(proj_file))
        if 'unknown' in proj_path:
            # could be moved to another dir
            pot_pat_ot = proj_path.replace('unknown', 'others')
            pot_pat_nat = proj_path.replace('unknown', 'native_apps')
            pot_pat_cross = proj_path.replace('unknown', 'cross_platform_apps')
            if os.path.exists(proj_path):
                proj_path = proj_path
            elif os.path.exists(pot_pat_nat):
                proj_path = pot_pat_nat
            elif os.path.exists(pot_pat_cross):
                proj_path = pot_pat_cross
            elif os.path.exists(pot_pat_ot):
                proj_path = pot_pat_ot
        if not os.path.exists(proj_file):
            print("jasus maximo proj nao existe")
            return
        for lang_info in info:
            self.add_language_info(proj_path, lang_info)
            self.parsed_files.add(filepath)
        is_native = self.check_native(proj_path, info)
        if not os.path.exists(proj_path):
            print("jasus")
            return

        issues = self.load_project_issues(proj_results_dir)

        self.proj_info[proj_path] = {
            'lang_info': info,
            'is_native': is_native,
            'is_on_play_store': self.check_store(proj_path),
            'last_app_update': self.get_last_update(proj_path),
            'last_app_update_year': datetime.datetime.fromtimestamp(self.get_last_update(proj_path)/1000).year,
            'app_category': self.get_app_category(proj_path),
            'issues': issues
        }

    def load_project_issues(self,proj_results_dir):
        issues_list = []
        adoctor_file = os.path.join(proj_results_dir, 'adoctor.csv')
        if os.path.exists(adoctor_file):
            #print("adoctor")
            issues_list = issues_list + ADoctorAnalysis().get_issues(adoctor_file)
        pmd_files = mega_find(proj_results_dir, pattern="*pmd_analysis.json", type_file='f', maxdepth=2)
        if len(pmd_files) > 0:
            for pmd_file in pmd_files:
                issues_list = issues_list + PMDAnalysis().get_issues(pmd_file)
        daap_files = mega_find(proj_results_dir, pattern="*daap_analysis.json", type_file='f', maxdepth=2)
        if len(daap_files) > 0:
            for daap_file in daap_files:
                issues_list = issues_list + DAAPAnalysis().get_issues(daap_file)
        eco_android_dirs = mega_find(proj_results_dir, pattern="*ecoandroid*", type_file='d', maxdepth=2)
        if len(eco_android_dirs) > 0:
            for eco_dir in eco_android_dirs:
                issues_list = issues_list + EcoAndroidAnalysis().get_issues(eco_dir)
        lint_results = mega_find(proj_results_dir, pattern="*lint*.xml", type_file='f', maxdepth=2)
        if len(lint_results) > 0:
            for lint_file in lint_results:
                issues_list = issues_list + LintAnalysis().get_issues(lint_file)
        return issues_list


    def check_store(self, project_path):
        store_file = os.path.join(project_path, 'is_on_play_store.log')
        if not os.path.exists(store_file):
            return False
        return str(cat(store_file)).lower() == 'true'

    def get_last_update(self, project_path):
        last_up_file = os.path.join(project_path, 'lastUpdate.log')
        if not os.path.exists(last_up_file):
            return 0
        text = str(cat(last_up_file))
        #print(last_up_file)
        #print(text)
        return int(text)

    def get_app_category(self, project_path):
        categ_file = os.path.join(project_path, 'categories.log')
        #print(categ_file)
        if not os.path.exists(categ_file):
            return []
        text = str(cat(categ_file))
        #print(text)
        if ']' not in text:
            return [ text.replace("'", "").replace("[", '') ]
        else:
            return ast.literal_eval(text)


    def check_native(self,filepath, info):
        has_java = any([x for x in info if x['Name'] == 'Java'])
        has_kotlin = any([x for x in info if x['Name'] == 'Kotlin'])
        has_js = any([x for x in info if x['Name'] in ['JavaScript', 'TypeScript']])
        has_dart = any([x for x in info if x['Name'] == 'Dart'])
        has_cpp = any([x for x in info if x['Name'] in ['C', 'C++']])
        is_cross = has_js or has_dart
        is_native = has_java or has_kotlin and not is_cross
        if is_native:
            pure_java = has_java and not has_kotlin
            pure_kt = has_kotlin and not has_java
            if pure_java:
                self.pure_native['Java'] = self.pure_native['Java'] + [filepath]
                if has_cpp:
                    self.pure_native['Java+C'] = self.pure_native['Java+C']  + [filepath]
            elif pure_kt:
                self.pure_native['Kotlin'] = self.pure_native['Kotlin']  + [filepath]
                if has_cpp:
                    self.pure_native['Kotlin+C'] = self.pure_native['Kotlin+C']  + [filepath]
            else:
                self.pure_native['mix'] = self.pure_native['mix'] + [filepath]
            if has_cpp:
                self.pure_native['C'] = self.pure_native['C']  + [filepath]
        elif is_cross:
            if has_dart:
                self.cross['Dart'] = self.cross['Dart']  + [filepath]
            elif has_js:
                self.cross['JavaScript'] = self.cross['JavaScript']  + [filepath]

        return is_native


    def search_and_parse_files_in_dir(self, directory_path, expected_filename="scc.json"):
        file_list = mega_find(directory_path, pattern=expected_filename, type_file='f')
        for filepath in file_list:
            self.parse_file(filepath)

    def gen_langs_boxplots_loc(self):
        fig1, en_box = plt.subplots()
        the_list = [ list(map(lambda z: z['Code'], x)) for x in map(lambda t: t['proj_files'], self.language_info.values())]
        #print(the_list)

        bp_dict = en_box.boxplot(x=the_list,
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' LoC")
        plt.show()



        x='''
        bp_dict = plt.boxplot(the_list, self.language_info.keys(),  patch_artist=True)
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

        # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.show()'''

    def gen_langs_boxplots_cc(self):
        fig1, en_box = plt.subplots()
        the_list = [ list(map(lambda z: z['Complexity'], x)) for x in map(lambda t: t['proj_files'], self.language_info.values())]

        bp_dict = en_box.boxplot(x=the_list,
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' CC")
        plt.show()


    def gen_langs_boxplots_total_files(self):
        fig1, en_box = plt.subplots()
        the_list = [list(map(lambda z: z['Count'], x)) for x in
                    map(lambda t: t['proj_files'], self.language_info.values())]

        bp_dict = en_box.boxplot(x=the_list,
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 )
        i = 0
        for line in bp_dict['medians']:
            x, y = line.get_xydata()[1]  # top of median line
            xx, yy = line.get_xydata()[0]
            text(x, y, '%.2f' % y, fontsize=12)  # draw above, centered
            # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
            i = i + 1

            # set colors
        colors = ['lightblue', 'darkkhaki']
        i = 0
        for bplot in bp_dict['boxes']:
            i = i + 1
            bplot.set_facecolor(colors[i % len(colors)])

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' #Files")
        plt.show()

    def gen_stats(self):
        print(json.dumps(self.language_info, indent=1))

    def plot_language_histogram(self):
        langs = list(self.language_info.keys())
        proj_counts = [self.language_info[lang]['proj_count'] for lang in langs]
        plt.figure(figsize=(10, 6))
        plt.bar(langs, proj_counts, color='skyblue')
        plt.xlabel('Programming Languages')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per Language' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()



    def gen_langs_pure_histogram(self, discriminate_play=True):
        if not discriminate_play:
            langs = [x for x in self.pure_native.keys()] + [x for x in self.cross.keys()]
            proj_counts = [len(self.pure_native[lang]) for lang in self.pure_native.keys()] + [len(self.cross[lang]) for lang in self.cross.keys()]
        else:
            langs = []
            proj_counts = []
            for l, projs in self.pure_native.items():
                play_c = len([x for x in projs if self.proj_info[x]['is_on_play_store']])
                langs.append(l)
                proj_counts.append(len(self.pure_native[l]))
                langs.append(l+'_play')
                proj_counts.append(play_c)
            for l, projs in self.cross.items():
                play_c = len([x for x in projs if self.proj_info[x]['is_on_play_store']])
                langs.append(l)
                proj_counts.append(len(self.cross[l]))
                langs.append(l + '_play')
                proj_counts.append(play_c)
        #proj_counts = [self.language_info[lang]['proj_count'] for lang in langs]
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(langs, proj_counts)
        colors = ['lightblue', 'darkkhaki']
        i = 1
        for bar in bar_dict:
            i = i + 1
            bar.set_facecolor(colors[i % len(colors)])
        plt.xlabel('Pure  Projects')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects containing only one language' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(rotation=45, ha='right')
        # put labels on each bar
        for i in range(len(proj_counts)):
            if proj_counts[i] > 0:
                plt.text(i, proj_counts[i], str(proj_counts[i]), ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

    def gen_cross_play_histogram(self):
        langs = ['native', 'native_play', 'cross', 'cross_play']
        proj_counts = [
            len([x for x in self.proj_info.values() if x['is_native']]),
            len([x for x in self.proj_info.values() if x['is_native'] and x['is_on_play_store']]),
            len([x for x in self.proj_info.values() if not x['is_native']]),
            len([x for x in self.proj_info.values() if not x['is_native'] and x['is_on_play_store']]),
        ]
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(langs, proj_counts)
        colors = ['lightblue', 'darkkhaki']
        i = 1
        for bar in bar_dict:
            i = i + 1
            bar.set_facecolor(colors[i % len(colors)])
        plt.xlabel('Pure  Projects')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects containing only one language' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(rotation=45, ha='right')
        # put labels on each bar
        for i in range(len(proj_counts)):
            if proj_counts[i] > 0:
                plt.text(i, proj_counts[i], str(proj_counts[i]), ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_age(self):
        """generates a histogram of the age of the apps."""
        age_years = {}
        #age_years = set([datetime.datetime.fromtimestamp(x['last_app_update']/1000).year for x in self.proj_info.values()])
        for proj in self.proj_info.values():
            year = proj['last_app_update_year']
            if year == 1970:
                continue
            age_years[year] = age_years[year] + 1 if year in age_years else 1

        #proj_counts = [len([x for x in self.proj_info.values() if datetime.datetime.fromtimestamp(x['last_app_update']/1000).year == y]) for y in age_years]
        plt.figure(figsize=(10, 6))
        plt.bar(age_years.keys(), age_years.values(), color='skyblue')
        for i in age_years.keys():
            plt.text(i, age_years[i], str(age_years[i]), ha='center', va='bottom')
        plt.xlabel('Programming Languages')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per Language' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(list(age_years.keys()), rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_age_play(self):
        """generates a histogram of the age of the apps."""
        age_years = {}
        #age_years = set([datetime.datetime.fromtimestamp(x['last_app_update']/1000).year for x in self.proj_info.values()])
        for proj in self.proj_info.values():
            year = proj['last_app_update_year']
            if year == 1970:
                continue
            if proj['is_on_play_store']:
                key = f"{year}_play"
                age_years[key] = age_years[key] + 1 if key in age_years else 1
            age_years[str(year)] = age_years[str(year)] + 1 if str(year) in age_years else 1
        age_years = {k: v for k, v in sorted(age_years.items(), key=lambda item: str(item[0]).split('_')[0])}
        #proj_counts = [len([x for x in self.proj_info.values() if datetime.datetime.fromtimestamp(x['last_app_update']/1000).year == y]) for y in age_years]
        plt.figure(figsize=(10, 6))
        colors = ['lightblue', 'darkkhaki']
        bar_dict = plt.bar(age_years.keys(), age_years.values())
        for i in age_years.keys():
            plt.text(i, age_years[i], str(age_years[i]), ha='center', va='bottom')
        i = 1
        for bar in bar_dict:
            i = i + 1
            bar.set_facecolor(colors[i % len(colors)])

        plt.xlabel('Programming Languages')
        plt.ylabel('Number of Projects')
        plt.title('Number of Projects per Language' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(list(age_years.keys()), rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    # issues
    def gen_plot_apps_issues(self):
        #all_issues = set()
        issues_dict = {}
        for proj, proj_d in self.proj_info.items():
            for issue in proj_d['issues']:
                if issue is None or issue.issue_type is None:
                    continue
                #all_issues.add(issue.issue_type)
                issue_name = getattr(issue.issue_type, 'value', issue.issue_type).strip().lower()
                if issue_name not in issues_dict:
                    issues_dict[issue_name] = set()
                    issues_dict[issue_name].add(proj)
                else:
                    issues_dict[issue_name].add(proj)
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(issues_dict.keys(), [len(x) for x in issues_dict.values()])
        for i in issues_dict.keys():
            plt.text(i, len(issues_dict[i]), str(len(issues_dict[i])), ha='center', va='bottom')
        plt.xlabel('Issues')
        plt.ylabel('Number of Projects')
        plt.title('Project count per issue ' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def gen_plot_apps_issues_occurrences(self):
        #all_issues = set()
        issues_dict = {}
        for proj, proj_d in self.proj_info.items():
            for issue in proj_d['issues']:
                if issue is None or issue.issue_type is None:
                    continue
                #all_issues.add(issue.issue_type)
                issue_name = getattr(issue.issue_type, 'value', issue.issue_type).strip().lower()
                if issue_name not in issues_dict:
                    issues_dict[issue_name] = [proj]
                else:
                    issues_dict[issue_name].append(proj)
        plt.figure(figsize=(10, 6))
        bar_dict = plt.bar(issues_dict.keys(), [len(x) for x in issues_dict.values()])
        for i in issues_dict.keys():
            plt.text(i, len(issues_dict[i]), str(len(issues_dict[i])), ha='center', va='bottom')
        plt.xlabel('Issues')
        plt.ylabel('# Occurrences')
        plt.title('Project count per issue ' + f" (Total Projects: {len(self.parsed_files)})")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def gen_plot_app_play_issues(self):
        # plot a box plot displaying on median how many distinct issues there are in play store apps vs non store apps
        play_store_issues = []
        non_play_store_issues = []

        for proj, proj_d in self.proj_info.items():
            distinct_issues = len(set([getattr(issue.issue_type, 'value', issue.issue_type).strip().lower() for issue in proj_d['issues'] if issue and issue.issue_type]))
            if proj_d['is_on_play_store']:
                play_store_issues.append(distinct_issues)
            else:
                non_play_store_issues.append(distinct_issues)

        data = [play_store_issues, non_play_store_issues]
        plt.figure(figsize=(10, 6))
        plt.boxplot(data, patch_artist=True, labels=['Play Store Apps', 'Non-Play Store Apps'])
        plt.ylabel('Number of Distinct Issues')
        plt.title('Median Number of Distinct Issues in Play Store Apps vs Non-Play Store Apps')
        plt.show()


    def gen_plot_app_play_issues_occurrences_critical(self):
        # plot a box plot displaying on median how many issues there are in play store apps vs non store apps
        play_store_issues = []
        non_play_store_issues = []
        for proj, proj_d in self.proj_info.items():
            issues = [x for x in proj_d['issues'] if is_critical_issue(getattr(x.issue_type, 'value', x.issue_type ))]
            issue_c = len(issues)
            if proj_d['is_on_play_store']:
                play_store_issues.append(issue_c)
            else:
                non_play_store_issues.append(issue_c)

        data = [play_store_issues, non_play_store_issues]
        plt.figure(figsize=(10, 6))
        plt.boxplot(data, patch_artist=True, labels=['Play Store Apps', 'Non-Play Store Apps'])
        plt.ylabel('Number of Distinct Critical Issues')
        plt.title('Median Number of occurences of critical Issues in Play Store Apps vs Non-Play Store Apps')
        plt.show()


    def gen_plot_app_play_issues_occurrences(self):
        # plot a box plot displaying on median how many issues there are in play store apps vs non store apps
        play_store_issues = []
        non_play_store_issues = []
        for proj, proj_d in self.proj_info.items():
            issue_c = len(proj_d['issues'])
            if proj_d['is_on_play_store']:
                play_store_issues.append(issue_c)
            else:
                non_play_store_issues.append(issue_c)

        data = [play_store_issues, non_play_store_issues]
        plt.figure(figsize=(10, 6))
        plt.boxplot(data, patch_artist=True, labels=['Play Store Apps', 'Non-Play Store Apps'])
        plt.ylabel('#occurrence of Issues')
        plt.title('Median Number of Issues in Play Store Apps vs Non-Play Store Apps')
        plt.show()


    def gen_plot_issues_per_year(self):
        issues_per_year = {}
        for proj, proj_d in self.proj_info.items():
            year = proj_d['last_app_update_year']
            if year == 1970:
                continue
            distinct_issues = len(set([getattr(issue.issue_type, 'value', issue.issue_type).strip().lower() for issue in proj_d['issues'] if issue and issue.issue_type]))
            if year in issues_per_year:
                issues_per_year[year].append(distinct_issues)
            else:
                issues_per_year[year] = [distinct_issues]

        years = sorted(issues_per_year.keys())

        plt.figure(figsize=(10, 6))
        plt.boxplot([issues_per_year[y] for y in years], patch_artist=True, tick_labels=years)
        plt.xlabel('Year')
        plt.ylabel('Number of Distinct Issues')
        plt.title('Number of Distinct Issues per Year of Last Update')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()



def main(lookup_dir):
    #lookup_dir = "/Users/ruirua/repos/pyAnaDroid/demoProjects"
    #build_scc_json_for_all_projs(lookup_dir)
    ls = LanguageStats()
    ls.search_and_parse_files_in_dir(lookup_dir, expected_filename="scc.json")
    #print(json.dumps(ls.language_info, indent=1))
    #ls.plot_language_histogram()
    #ls.gen_langs_boxplots_loc()
    #ls.gen_langs_boxplots_cc()
    #ls.gen_langs_boxplots_total_files()
    #ls.gen_langs_pure_histogram()
    #ls.gen_cross_play_histogram()
    #ls.gen_stats()
    ls.gen_plot_app_play_issues_occurrences_critical()
    ls.gen_plot_apps_age_play()
    ls.gen_plot_apps_age()
    ls.gen_plot_apps_issues()
    ls.gen_plot_apps_issues_occurrences()

    ls.gen_plot_app_play_issues()
    ls.gen_plot_app_play_issues_occurrences()
    ls.gen_plot_issues_per_year()

def is_critical_issue(issue_name):
    if issue_name is None:
        return False
    issue_id = issue_name.strip().lower()
    critical_issues = ['wakelock', 'drawallocation', 'uioverdraw', 'viewholder', 'nestedweight']
    return issue_id in critical_issues


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("error. provide input dir")
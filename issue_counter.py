import os

from anadroid.analysis.post_build_analysis.DroidLensAnalyzer import DroidLensAnalysis
from anadroid.analysis.post_build_analysis.EcoAndroidResourceLeaksAnalyzer import EcoAndroidResourceLeaksAnalysis
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.ChimeraAnalysis import ChimeraAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.DetektAnalysis import DetektAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.InferAnalysis import InferAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis
from anadroid.analysis.pre_build_analysis.SpotBugsAnalysis import SpotBugsAnalysis
from anadroid.analysis.pre_build_analysis.XALintAnalysis import XALintAnalysis
from anadroid.utils.Utils import mega_find
from aux_scripts.language_counter import merge_duplicate_issues


def load_project_issues(proj_results_dir):
    issues_list = []
    adoctor_file = os.path.join(proj_results_dir, 'adoctor.csv')
    if os.path.exists(adoctor_file):
        # print("adoctor")
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
        print(eco_android_dirs)
        for eco_dir in eco_android_dirs:
            if 'resource_leaks' in eco_dir:
                issues_list = issues_list + list(
                    filter(lambda x: x not in issues_list, EcoAndroidResourceLeaksAnalysis().get_issues(eco_dir)))
            else:
                issues_list = issues_list + list(
                    filter(lambda x: x not in issues_list, EcoAndroidAnalysis().get_issues(eco_dir)))
    lint_results = mega_find(proj_results_dir, pattern="*lint*.xml", type_file='f', maxdepth=2)
    if len(lint_results) > 0:
        lint_issues = set()
        for lint_file in lint_results:
            try:
                lint_issues.update(LintAnalysis().get_issues(lint_file))
                lint_issues.update(XALintAnalysis().get_issues(lint_file, ignore_lint_issues=True))
                lint_issues.update(ChimeraAnalysis().get_issues(lint_file, ignore_lint_issues=True))
            except:
                pass
        issues_list = issues_list + list(lint_issues)
    detekt_results = mega_find(proj_results_dir, pattern="*detekt_analysis.xml", type_file='f', maxdepth=2)
    if len(detekt_results) > 0:
        for detekt_file in detekt_results:
            issues_list = issues_list + DetektAnalysis().get_issues(detekt_file)
    spotbugs_results = mega_find(proj_results_dir, pattern="*spotbugs*.xml", type_file='f', maxdepth=2)
    if len(spotbugs_results) > 0:
        for spotbugs_file in spotbugs_results:
            issues_list = issues_list + SpotBugsAnalysis().get_issues(spotbugs_file)
    infer_results = mega_find(proj_results_dir, pattern="*infer_report.json", type_file='f', maxdepth=2)
    if len(infer_results) > 0:
        for infer_file in infer_results:
            issues_list = issues_list + InferAnalysis().get_issues(infer_file)
    droidlens_results = mega_find(proj_results_dir, pattern="*droidlens*", type_file='d', maxdepth=2)
    if len(droidlens_results) > 0:
        for droidlens_dir in droidlens_results:
            issues_list = issues_list + list(
                filter(lambda x: x not in issues_list, DroidLensAnalysis().get_issues(droidlens_dir)))
    print(f"Loaded {len(issues_list)} issues from {proj_results_dir}")
    return issues_list

if __name__ == '__main__':
    res_dir = 'llm_gen_datasets/fdroid_vibe_anadroid_results/similar'
    proj_res_dirs = mega_find(res_dir, type_file='d', maxdepth=2)
    i_list = []
    for i, p in enumerate(proj_res_dirs):
        iss_ =  merge_duplicate_issues(load_project_issues(p))
        print('potato', p, len(iss_))
        i_list = i_list + iss_

    print('total issues ', len(i_list))
    # write list to file
    with open('total_issues.txt', 'w') as f:
        for item in i_list:
            f.write("%s\n" % item)
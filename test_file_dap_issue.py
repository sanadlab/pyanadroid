import os.path

from anadroid.analysis.post_build_analysis.DroidLensAnalyzer import DroidLensAnalysis
from anadroid.analysis.post_build_analysis.EcoAndroidResourceLeaksAnalyzer import EcoAndroidResourceLeaksAnalysis
from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.utils.Utils import execute_shell_command

if __name__ == '__main__':
    #path = '/Users/rar9993/repos/research/fdroid_apps/native_apps/app_ship_capt_crew/'
    #cmd = f"cd {path} && java -jar ~/repos/pyanadroid/anadroid/resources/jars/DAAP-1.0.jar app ALL"
    #res = execute_shell_command(cmd)
    #print(res)
    #dap = DAAPAnalysis()
    #dap.parse_write_output(res, 'jinga')
    #path = '/Users/rar9993/repos/research/fdroid_apps/native_apps/attendance-viewer'
    #path = 'native_apps/BaldPhone--com.bald.uriah.baldphone/1e57ae0fba470455b58bc494da9994cf9807ee5b/0.0.0/oldRuns/ecoandroid_resource_leaks'
    path = 'native_apps/Device-Explorer--com.iamtrk/8bc5b8d8455a7c81585f30aaf1df7a8af343b772/0.0.0/oldRuns/droidlens_analysis_output'
    analyzer = DroidLensAnalysis()
    iss = analyzer.get_issues(path)
    #doctor = ADoctorAnalysis()
    #iss = doctor.get_issues(os.path.join(path, 'batata'))
    print(iss)
    print(set(map(lambda x: x.issue_type, iss)))


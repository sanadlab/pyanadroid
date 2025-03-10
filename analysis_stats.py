from anadroid.analysis.pre_build_analysis.ADoctorAnalysis import ADoctorAnalysis
from anadroid.analysis.pre_build_analysis.DAAPAnalysis import DAAPAnalysis
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.analysis.pre_build_analysis.LintAnalysis import LintAnalysis
from anadroid.analysis.pre_build_analysis.PMDAnalysis import PMDAnalysis


def language_stats():
    pass


def main():
    language_stats()


def test_issues_get():
    #sa = ADoctorAnalysis()
    #file = '/Users/rar9993/repos/pyanadroid/anadroid_results/wonderdroid-x--com.atelieryl.wonderdroid/adoctor.csv'
    #sa = DAAPAnalysis()
    #file = '/Users/rar9993/repos/pyanadroid/anadroid_results/wonderdroid-x--com.atelieryl.wonderdroid/app_daap_analysis.csv'
    #sa = EcoAndroidAnalysis()
    #file = '/Users/rar9993/repos/pyanadroid/anadroid_results//weather-overview--app.weatheroverview/ecoandroid_app'
    #sa = LintAnalysis()
    sa = PMDAnalysis()
    #file = '/Users/rar9993/repos/pyanadroid/anadroid_results/NoPhoneSpam--at.bitfire.nophonespam/lint-results.xml'
    file = '/Users/rar9993/repos/pyanadroid/anadroid_results/NoPhoneSpam--at.bitfire.nophonespam/pmd_analysis.json'
    issues = sa.get_issues(file)
    print(issues)


if __name__ == '__main__':
    test_issues_get()
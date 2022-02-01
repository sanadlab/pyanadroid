from manafa.hunter_emanafa import HunterEManafa
import os

from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from manafa.utils.Logger import log

class ManafaAnalyzer(AbstractAnalyzer):
    def __init__(self, profiler):
        self.supported_filters = {"total_energy"}
        super(ManafaAnalyzer, self).__init__()
        self.profiler = profiler


    def setup(self, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    def analyze_test(self, app, test_id, **kwargs):
        pass

    # def analyze(self, app, output_log_file="hunter.log"):
    def analyze_tests(self, app, results_dir=None, **kwargs):
        #total, per_component, metrics = self.profiler.manafa.getConsumptionInBetween()
        hunter_trace = {}
        if isinstance(self.profiler.manafa, HunterEManafa):
            output_log_file = "hunter.log"
            results_dir = results_dir if results_dir is not None else app.curr_local_dir
            hunter_logs = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if 'hunter' in f]
            final_hunter = os.path.join(results_dir, output_log_file)
            # concat all hunter logs on final hunter
            between_tests = 0
            with open(final_hunter, 'w') as outfile:
                for fname in hunter_logs:
                    with open(fname) as infile:
                        size = os.path.getsize(fname)
                        for line in infile:
                            size -= len(line)
                            if not size and between_tests < (len(hunter_logs) - 1):
                                line_aux = line.rstrip()
                                outfile.write(line_aux + ';\n')
                            else:
                                outfile.write(line)
                        between_tests += 1

            # concat all consumption logs on final consumption
            consumption_logs = [f for f in os.listdir(results_dir) if 'consumption' in f]
            final_consumption = os.path.join(results_dir, "consumption.log")
            interval_line = "------------------------------------------\n"
            with open(final_consumption, 'w') as file:
                file.write(interval_line.join([open(i).read() for i in consumption_logs]))

    def validate_test(self, app, test_id, **kwargs):
        return self.validate_filters()

    def clean(self):
        pass

    def validate_filters(self):
        for filter_name, fv in self.validation_filters.filters.items():
            if filter_name in self.supported_filters:
                for filt in fv:
                    if not filt.apply_filter(self.get_val_for_filter(filter_name)):
                        log(f"filter {filter_name} failed")
                        return False
            else:
                log(f"unsupported filter {filter_name}")
                return False
        return True

    def get_val_for_filter(self, filter_name):
        if filter_name == "total_energy":
            tot, _, _ = self.profiler.manafa.getConsumptionInBetween()
            return tot
        else:
            log(f"unsupported filter {filter_name} by {self.__class__}")
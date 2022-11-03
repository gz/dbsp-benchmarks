# Loads two nexmark results from CI runs and compares their performance.
#
# Prints a bunch of text that can be copy-pasted into a github PR comment.
# Should be executed in the root directory of the dbsp (code) repository.

from nexmark import load_nexmark_result
from galen import load_galen_result
from ldbc import load_ldbc_result
from utils import MACHINES, DATA_PATH
from ci_history import parse_csv
from plumbum.cmd import git
from humanize import naturalsize
import argparse
import pandas as pd


def get_parser():
    "Construct argument parser"
    parser = argparse.ArgumentParser()
    # General build arguments
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("--machines", type=str, nargs='+', default=[n['name'] for n in MACHINES], choices=[n['name'] for n in MACHINES],
                        help="Only regenerate results for specific machine type.")
    return parser


def get_main_ref(i):
    git['fetch', 'origin', 'main']()
    git_rev_main = git['rev-parse', 'origin/main~{}'.format(i)]().strip()
    return git_rev_main


def get_ref_current():
    git_rev_current = git['rev-parse', 'HEAD']().strip()
    if not git_rev_current in machine_results:
        exit("Revision {} should exist because we just added it.".format(git_rev_current))
    return git_rev_current


MEASUREMENT_ERROR = 5  # percent
SERIOUS_DEGRADATION = 25  # percent


def percentage_to_icon(tput):
    pictogram = ":heavy_check_mark:"
    if tput > 100 + MEASUREMENT_ERROR:
        pictogram = ":evergreen_tree:"
    if tput < 100 - MEASUREMENT_ERROR:
        pictogram = ":small_red_triangle_down:"
    if tput < 100 - SERIOUS_DEGRADATION:
        pictogram = ":interrobang:"

    return pictogram


def format_percentage(p):
    p = round(p)
    return p - 100


def compare_ldbc(args):
    git_rev_current = get_ref_current()

    for i in range(0, 10):
        git_rev_main = get_main_ref(i)

        if git_rev_main in machine_results:
            main_results = load_ldbc_result(machine, git_rev_main, args)
            main_results = main_results.set_index('name')
            current_results = load_ldbc_result(machine, git_rev_current, args)
            current_results = current_results.set_index('name')

            df_compare = pd.DataFrame()
            df_compare['algorithm'] = main_results['algorithm']
            df_compare['dataset'] = main_results['dataset']
            df_compare['threads'] = main_results['threads']
            if i == 0:
                df_compare['main [kEVPS]'] = main_results['evps'] / 1000
            else:
                df_compare['main~{} [kEVPS]'.format(
                    i)] = main_results['evps'] / 1000
            df_compare['PR [kEVPS]'] = current_results['evps'] / 1000
            df_compare['Tput change [%]'] = (
                current_results['evps'] / main_results['evps']) * 100
            df_compare['Assessment'] = df_compare['Tput change [%]'].map(
                percentage_to_icon)
            regressed_queries = df_compare['Tput change [%]'] < (
                100 - MEASUREMENT_ERROR)
            df_compare['Tput change [%]'] = df_compare['Tput change [%]'].map(
                format_percentage)

            df_compare['Peak RSS diff'] = current_results['allocstats_after_peak_rss'] - \
                main_results['allocstats_after_peak_rss']
            df_compare['Peak RSS diff'] = df_compare['Peak RSS diff'].map(
                naturalsize)

            print()
            print("### LDBC")
            print()
            if regressed_queries.sum() > 0:
                print("* {} out of {} queries have regressed :exclamation:".format(
                    regressed_queries.sum(), len(df_compare)))
            print("* Compared results from {} (main) with {} (PR)".format(
                git_rev_main[0:7], git_rev_current[0:7]))
            if i > 0:
                print("No benchmark results found for current main revision, compared against {}".format(
                    git_rev_main))
            print()
            print(df_compare.to_markdown(index=False))
            break


def compare_nexmark(args):
    git_rev_current = get_ref_current()

    for i in range(0, 10):
        git_rev_main = get_main_ref(i)

        if git_rev_main in machine_results:
            main_results = load_nexmark_result(machine, git_rev_main, args)
            main_results = main_results.set_index('name')
            current_results = load_nexmark_result(
                machine, git_rev_current, args)
            current_results = current_results.set_index('name')

            main_results['tput'] = (
                main_results['num_events'] / main_results['elapsed']) / 1000
            current_results['tput'] = (
                current_results['num_events'] / current_results['elapsed']) / 1000

            df_compare = pd.DataFrame()
            if i == 0:
                df_compare['main [kOp/s]'] = main_results['tput']
            else:
                df_compare['main~{} [kOp/s]'.format(i)] = main_results['tput']
            df_compare['PR [kOp/s]'] = current_results['tput']
            df_compare['Tput change [%]'] = (
                current_results['tput'] / main_results['tput']) * 100
            df_compare['Assessment'] = df_compare['Tput change [%]'].map(
                percentage_to_icon)
            regressed_queries = df_compare['Tput change [%]'] < (
                100 - MEASUREMENT_ERROR)
            df_compare['Tput change [%]'] = df_compare['Tput change [%]'].map(
                format_percentage)

            df_compare['Peak RSS diff'] = current_results['allocstats_after_peak_rss'] - \
                main_results['allocstats_after_peak_rss']
            df_compare['Peak RSS diff'] = df_compare['Peak RSS diff'].map(
                naturalsize)

            print()
            print("### Nexmark")
            print()
            if regressed_queries.sum() > 0:
                print("* {} out of {} queries have regressed :exclamation:".format(
                    regressed_queries.sum(), len(df_compare)))
            print("* Compared results from {} (main) with {} (PR)".format(
                git_rev_main[0:7], git_rev_current[0:7]))
            if i > 0:
                print("No benchmark results found for current main revision, compared against {}".format(
                    git_rev_main))
            print()
            print(df_compare.to_markdown())
            break


def compare_nexmark_persistence(args):
    git_rev_current = get_ref_current()

    for i in range(0, 10):
        git_rev_main = get_main_ref(i)

        if git_rev_main in machine_results:
            main_results = load_nexmark_result(
                machine, git_rev_main, args, file_name='persistence_nexmark_results.csv.gz')
            main_results = main_results.set_index('name')
            current_results = load_nexmark_result(
                machine, git_rev_current, args, file_name='persistence_nexmark_results.csv.gz')
            current_results = current_results.set_index('name')
            current_results_dram = load_nexmark_result(
                machine, git_rev_current, args, file_name='dram_nexmark_results.csv.gz')
            current_results_dram = current_results_dram.set_index('name')

            main_results['tput'] = (
                main_results['num_events'] / main_results['elapsed']) / 1000
            current_results['tput'] = (
                current_results['num_events'] / current_results['elapsed']) / 1000
            current_results_dram['tput'] = (
                current_results_dram['num_events'] / current_results_dram['elapsed']) / 1000

            df_compare = pd.DataFrame()
            if i == 0:
                df_compare['main [kOp/s]'] = main_results['tput']
            else:
                df_compare['main~{} [kOp/s]'.format(i)] = main_results['tput']
            df_compare['PR [kOp/s]'] = current_results['tput']
            df_compare['Tput change [%]'] = (
                current_results['tput'] / main_results['tput']) * 100
            df_compare['PR DRAM [kOp/s]'] = current_results_dram['tput']
            df_compare['DRAM diff [%]'] = (
                current_results['tput'] / current_results_dram['tput']) * 100
            df_compare['Assessment'] = df_compare['Tput change [%]'].map(
                percentage_to_icon)
            regressed_queries = df_compare['Tput change [%]'] < (
                100 - MEASUREMENT_ERROR)
            df_compare['Tput change [%]'] = df_compare['Tput change [%]'].map(
                format_percentage)
            df_compare['DRAM diff [%]'] = df_compare['DRAM diff [%]'].map(
                format_percentage)

            print()
            print("### Nexmark (with Persistence)")
            print()
            if regressed_queries.sum() > 0:
                print("* {} out of {} queries have regressed :exclamation:".format(
                    regressed_queries.sum(), len(df_compare)))
            print("* Compared results from {} (main) with {} (PR)".format(
                git_rev_main[0:7], git_rev_current[0:7]))
            if i > 0:
                print("No benchmark results found for current main revision, compared against {}".format(
                    git_rev_main))
            print()
            print(df_compare.to_markdown())
            break


def compare_galen(args):
    git_rev_current = get_ref_current()

    for i in range(0, 10):
        git_rev_main = get_main_ref(i)

        if git_rev_main in machine_results:
            main_results = load_galen_result(machine, git_rev_main, args)
            main_results = main_results.set_index('name')
            current_results = load_galen_result(machine, git_rev_current, args)
            current_results = current_results.set_index('name')

            df_compare = pd.DataFrame()
            if i == 0:
                df_compare['main [s]'] = main_results['elapsed']
            else:
                df_compare['main~{} [s]'.format(i)] = main_results['elapsed']
            df_compare['PR [s]'] = current_results['elapsed']

            df_compare['Runtime change [%]'] = (
                current_results['elapsed'] / main_results['elapsed']) * 100
            df_compare['Assessment'] = df_compare['Runtime change [%]'].map(
                percentage_to_icon)
            regressed_queries = df_compare['Runtime change [%]'] < (
                100 - MEASUREMENT_ERROR)
            df_compare['Runtime change [%]'] = df_compare['Runtime change [%]'].map(
                format_percentage)

            print()
            print("### Galen")
            print()
            if regressed_queries.sum() > 0:
                print("* {} out of {} benchmarks have regressed :exclamation:".format(
                    regressed_queries.sum(), len(df_compare)))
            print("* Compared results from {} (main) with {} (PR)".format(
                git_rev_main[0:7], git_rev_current[0:7]))
            if i > 0:
                print("No benchmark results found for current main revision, compared against {}".format(
                    git_rev_main))
            print()
            print(df_compare.to_markdown())
            break


if __name__ == '__main__':
    args = get_parser().parse_args()

    if len(args.machines) == 1:
        machine = next(m for m in MACHINES if m['name'] == args.machines[0])

    machine_results = parse_csv(machine)

    # The 'Benchmark results' substring is used to find the comment (if
    # it exists), if you change it you need to adjust the github action
    # in `bench.yml`.
    print("## Benchmark results")

    compare_nexmark(args)
    compare_galen(args)
    compare_ldbc(args)
    compare_nexmark_persistence(args)

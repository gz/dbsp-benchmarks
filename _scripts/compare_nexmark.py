# Loads two nexmark results from CI runs and compares their performance.
#
# Prints a bunch of text that can be copy-pasted into a github PR comment.
# Should be executed in the root directory of the dbsp (code) repository.

from nexmark import load_nexmark_result
from utils import MACHINES, DATA_PATH
from ci_history import parse_csv
from plumbum.cmd import git
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


if __name__ == '__main__':
    args = get_parser().parse_args()

    if len(args.machines) == 1:
        machine = next(m for m in MACHINES if m['name'] == args.machines[0])

    machine_results = parse_csv(machine)
    git_rev_current = git['rev-parse', 'HEAD']().strip()
    if not git_rev_current in machine_results:
        exit("Revision {} should exist because we just added it.".format(git_rev_current))

    for i in range(0, 10):
        git_rev_main = git['rev-parse', 'origin/main~{}'.format(i)]().strip()
        # TODO: remove once we have some commits in main...
        git_rev_main = 'c332ad9170b1f3a3863622631c637d707285d5b6'

        if git_rev_main in machine_results:
            main_results = load_nexmark_result(machine, git_rev_main, args)
            main_results = main_results.set_index('name')
            current_results = load_nexmark_result(machine, git_rev_current, args)
            current_results = current_results.set_index('name')

            main_results['tput'] = main_results['num_events'] / main_results['elapsed']
            current_results['tput'] = current_results['num_events'] / current_results['elapsed']

            MEASUREMENT_ERROR = 5 # percent
            SERIOUS_DEGRADATION = 25 # percent
            def tput_fmt(tput):
                pictogram = ":heavy_check_mark:"
                if tput > 100 + MEASUREMENT_ERROR:
                    pictogram = ":evergreen_tree:"
                if tput < 100 - MEASUREMENT_ERROR:
                    pictogram = ":small_red_triangle_down:"
                if tput < 100 - SERIOUS_DEGRADATION:
                    pictogram = ":interrobang:"

                return pictogram

            df_compare = pd.DataFrame()
            if i == 0:
                df_compare['main [Op/s]'] = main_results['tput']
            else:
                df_compare['main~{} [Op/s]'.format(i)] = main_results['tput']
            df_compare['PR [Op/s]'] = current_results['tput']
            df_compare['Throughput relative to main [%]'] = (current_results['tput'] / main_results['tput']) * 100
            df_compare['Assessment'] = df_compare['Throughput relative to main [%]'].map(tput_fmt)
            regressed_queries = df_compare['Throughput relative to main [%]'] < (100 - MEASUREMENT_ERROR)

            # The 'Nexmark benchmark results' substring is used to find the
            # comment (if it exists), if you change it you need to adjust the
            # github action too.
            print("Nexmark benchmark results: {} out of {} queries have regressed.".format(regressed_queries.sum(), len(df_compare)))
            print()
            print("Compared {} against {}".format(git_rev_main[0:7], git_rev_current[0:7]))
            if i > 0:
                print("No benchmark results found for current main revision, compared against {}".format(git_rev_main))
            print()
            print(df_compare.to_markdown())
            break

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
        print (parse_csv(machine))

    machine_results = parse_csv(machine)
    git_rev_current = git['rev-parse', 'HEAD']
    git_rev_current = '48b3f76580532c6444080764f5145409ddbee03b'
    if not git_rev_current in machine_results:
        exit("Revision should exist because we just added it.")

    for i in range(0, 10):
        git_rev_main = git['rev-parse', 'origin/main~{}'.format(i)]
        git_rev_main = '48b3f76580532c6444080764f5145409ddbee03b'

        if git_rev_main in machine_results:
            main_results = load_nexmark_result(machine, git_rev_main, args)
            current_results = load_nexmark_result(machine, git_rev_current, args)
            print(main_results['name'])
            print(current_results['name'])

            df_compare = main_results.join(current_results, on='name', lsuffix='_main', rsuffix='_current')

            print(df_compare)
            """
            for benchmark in main_results.rows():
                print(benchmark)
                if benchmark not in current_results:
                    continue
                print("Benchmark: {}".format(benchmark['name']))
                #print("Main: {}".format(main_results[benchmark]))
                #print("Current: {}".format(current_results[benchmark]))
                #print("")


            print("Comparing {} to {}".format(main_results, current_results))
            break
            """

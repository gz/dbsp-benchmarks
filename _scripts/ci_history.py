import csv
from nexmark import nexmark_ci_graph
from utils import MACHINES, DATA_PATH
import argparse
import subprocess
import os
import sys


def parse_csv(machine):
    "Read the _data/$machine.csv file, create dict with revision as key for all entries"
    csv_data = {}
    with open(DATA_PATH / "{}.csv".format(machine['name'])) as f:
        reader = csv.reader(f)
        for row in list(reader)[1:]:
            csv_data[row[1]] = row
    return csv_data


def append_csv(machine):
    "Append date,revision,branch,commit_msg row to _data/$machine.csv"
    from plumbum.cmd import git, head
    git_commit_date = git['show', '-s', '--format=%cI']
    git_rev_current = git['rev-parse', 'HEAD']
    git_branch = os.environ.get('GITHUB_REF')
    if git_branch is None:
        git_branch = "unset"
    git_commit_msg = git['log', '--oneline',
                         '--format=%B', '-n', '1', 'HEAD'] | head['-n', '1']

    current_list = parse_csv(machine)
    if git_rev_current().strip() in current_list:
        # Don't insert twice in list (for repeated runs)
        print("Revision already added by previous run, skip insert.")
        return

    with open(DATA_PATH / "{}.csv".format(machine['name']), 'a') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC,
                            lineterminator='\n')
        writer.writerow([git_commit_date().strip(), git_rev_current().strip(),
                        git_branch.strip(), git_commit_msg().strip()])


def get_parser():
    "Construct argument parser"
    parser = argparse.ArgumentParser()
    # General build arguments
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("--benchmarks", type=str, nargs='+', default=['nexmark'],
                        help="Which benchmarks to plot.")
    parser.add_argument("--machines", type=str, nargs='+', default=[n['name'] for n in MACHINES], choices=[n['name'] for n in MACHINES],
                        help="Only regenerate results for specific machine type.")
    parser.add_argument("--append", action="store_true", default=False,
                        help="Append new results")
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()

    if args.append and len(args.machines) > 1:
        print("Can't append results for multiple machines")
        sys.exit(1)

    if args.append and len(args.machines) == 1:
        machine = next(m for m in MACHINES if m['name'] == args.machines[0])
        append_csv(machine)

    #for machine in args.machines:
    #    machine = next(m for m in MACHINES if m['name'] == machine)
    #    if 'nexmark' in args.benchmarks:
    #        nexmark_ci_graph(machine, args)

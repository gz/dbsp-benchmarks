from nexmark import nexmark_ci_graph
from utils import MACHINES
import argparse
import subprocess
import os

#
# Command line argument parser
#


def get_parser():
    parser = argparse.ArgumentParser()
    # General build arguments
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("--benchmarks", type=str, nargs='+', default=['nexmark'],
                        help="Which benchmarks to plot.")
    parser.add_argument("--no-fetch", action="store_true", default=False,
                        help="Don't fetch all git branches")
    parser.add_argument("--repo", type=str, default=os.path.abspath(os.path.curdir),
                        help="Source code repo checkout path.")

    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()

    if not args.no_fetch:
        checkout_master = subprocess.run(
            ["git", "fetch", "--all"], cwd=args.repo)
        assert checkout_master.returncode == 0

    for machine in MACHINES:
        if 'nexmark' in args.benchmarks:
            nexmark_ci_graph(machine, args)

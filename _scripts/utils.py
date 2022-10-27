import os
import numpy as np
import subprocess
import datetime
import pathlib
import gzip
from io import BytesIO

SCRIPT_PATH = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
NEXMARK_BENCHMARKS = (SCRIPT_PATH / '..').resolve() / 'nexmark'
DATA_PATH = (SCRIPT_PATH / '..').resolve() / '_data'

MACHINES = [
    {'name': 'skylake2x', 'cores': 28, 'threads': 56},
]


def parse_git_info(gitrev, repo):
    "Parse git information based on hash"
    find_branch_cmd = subprocess.run(["git", "branch", "--contains", gitrev],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo)
    if find_branch_cmd.returncode != 0:
        return None
    branches = ', '.join([branch.strip() for branch in str(
        find_branch_cmd.stdout, 'utf-8').strip().split('\n')])

    commit_one_line = subprocess.run(["git", "show", "-s", "--oneline", gitrev],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo)
    if commit_one_line.returncode != 0:
        return None
    commit_msg = str(commit_one_line.stdout, 'utf-8').strip(gitrev).strip()

    commit_date = subprocess.run(["git", "show", "-s", r"--format=%cI", gitrev],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo)
    if commit_date.returncode != 0:
        return None
    commit_date = datetime.datetime.fromisoformat(
        str(commit_date.stdout, 'utf-8').strip())
    return (branches, commit_msg, commit_date)

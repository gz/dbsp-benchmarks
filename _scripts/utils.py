import os
import numpy as np
import subprocess
import datetime
import pathlib
import gzip
from io import BytesIO
import pandas as pd

SCRIPT_PATH = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
NEXMARK_BENCHMARKS = (SCRIPT_PATH / '..').resolve() / 'nexmark'
GALEN_BENCHMARKS = (SCRIPT_PATH / '..').resolve() / 'galen'
LDBC_BENCHMARKS = (SCRIPT_PATH / '..').resolve() / 'ldbc'
DATA_PATH = (SCRIPT_PATH / '..').resolve() / '_data'

MACHINES = [
    {'name': 'skylake-2x', 'cores': 28, 'threads': 56},
]


def load_results_generic(results_csv_path):
    if results_csv_path.exists():
        return pd.read_csv(results_csv_path)
    else:
        return None

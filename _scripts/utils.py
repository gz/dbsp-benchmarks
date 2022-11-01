import os
import numpy as np
import subprocess
import datetime
import pathlib
import gzip
from io import BytesIO

SCRIPT_PATH = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
NEXMARK_BENCHMARKS = (SCRIPT_PATH / '..').resolve() / 'nexmark'
GALEN_BENCHMARKS = (SCRIPT_PATH / '..').resolve() / 'galen'
DATA_PATH = (SCRIPT_PATH / '..').resolve() / '_data'

MACHINES = [
    {'name': 'skylake-2x', 'cores': 28, 'threads': 56},
]

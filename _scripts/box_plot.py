import numpy as np
import pandas as pd

import plotnine

from plotnine import *
from plotnine import data
from pandas import DataFrame


small_rng = pd.read_csv('small_rng.csv')
small_rng['category'] = 'SmallRng'
thread_rng = pd.read_csv('small_rng.csv')
thread_rng['category'] = 'ThreadRng'



results = pd.concat([small_rng, thread_rng])
results['name'] = results['name'].str.replace('q', '').astype(int)

summary = results.groupby(['category', 'name']).agg({'elapsed': ['mean', 'std', 'min', 'max']})
summary = summary[summary['elapsed']['std'] > 2]
print(summary.to_markdown())

#results = results[results['name'] == summary['name']]

#small_rng.reset_index('name', inplace=True)

plot = (
    ggplot(results, aes("category", "elapsed"))
    #+ geom_violin()
    + geom_boxplot()
    + geom_jitter(position=position_jitter(height=0, width=0))
    + facet_grid('name ~ .', space='free', scales="free_y")
    + xlab("Query")
    + ylab("Runtime [s]")
    + theme_538()
)

plot.save(filename='box.png', height=25, width=5, dpi=300)
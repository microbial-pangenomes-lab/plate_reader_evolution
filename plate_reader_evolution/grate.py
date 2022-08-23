# Copyright 2019 Marco Galardini

import logging
import numpy as np
import pandas as pd
from scipy import stats


logger = logging.getLogger('evol.grate')


def calc_growth_rate(v, time='60T'):
    def rolling_fit(x):
        t = v.loc[x.index]
        return stats.linregress(t['time'], t['ln(od)']).slope

    rol = v.rolling(time, min_periods=5)
    mu = rol['time'].apply(rolling_fit).to_frame()

    mu = mu.rename(columns={'time': 'mu'})

	# nanoseconds to hours
    mu['time'] = mu.index.astype(int) / 1000 / 1000 / 1000 / 60 / 60
    return mu.set_index('time').T


def grate_delta(v):
    # experimental
    anc = v[v['treatment'] == 'ancestral']['grate'].mean()
    evolved = v[v['treatment'] != 'ancestral']

    evolved['delta'] = (evolved['grate'] - anc) / anc

    return evolved

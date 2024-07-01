#!/usr/bin/env python


import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

import seaborn as sns
from matplotlib import colors
import matplotlib.pyplot as plt
from matplotlib import rcParams


sns.set_style('ticks', rc={"axes.facecolor": (0, 0, 0, 0)})
sns.set_context('paper')

rcParams['font.family'] = 'sans-serif'


logger = logging.getLogger('evol')


def set_logging(v):
    logger.propagate = True
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    if v == 0:
        ch.setLevel(logging.INFO)
    elif v >= 1:
        ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


def get_options():
    description = 'Plot a series of heatmaps to make it easier to reconcile MIC replicates'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('raw',
                        help='Raw OD data (.tsv file)')
    parser.add_argument('mic',
                        help='Computed MIC values (.tsv file)')
    parser.add_argument('output',
                        help='Output directory for the heatmaps')

    parser.add_argument('--od-threshold',
                        type=float,
                        default=0.2,
                        help='Minimum normalised OD600 to consider growth '
                             '(default: %(default).2f)')

    parser.add_argument('--normalise-od',
                        type=float,
                        default=0.3,
                        help='Minimum OD600 to use for normalisation\'s '
                             'minimum '
                             '(default: %(default).2f)')

    parser.add_argument('--digits',
                        type=int,
                        default=3,
                        help='Significant digits to report for concentration '
                             '(default: %(default)d)')

    parser.add_argument('--format',
                        choices=('png',
                                 'tiff',
                                 'pdf',
                                 'svg',
                                 'jpg'),
                        default='png',
                        help='Output format for plots (default: %(default)s)') 

    parser.add_argument('-v', action='count',
                        default=0,
                        help='Increase verbosity level')

    return parser.parse_args()


def normalize(values, normalise=0.3, threshold=0.2):
    values = values[['od600', 'concentration']
            ].groupby('concentration').mean().reset_index()
    y = values['od600']
    if y[y > threshold].shape[0] == 0:
        y = pd.Series([0] * y.shape[0],
                      index=values['concentration'].values)
        return y
    ymin = y[y <= normalise]
    # also remove artifacts from very high
    # OD values
    if y.max() > 0.5:
        ymax = np.mean(y[y > 0.5])
    else:
        ymax = y.max()
    if ymin.shape[0] == 0:
        v = values['concentration'].max()
    else:
        ymin = np.mean(ymin)
        y = (y - ymin) / (ymax - ymin)
    y.index = values['concentration'].values
    return y


if __name__ == "__main__":
    options = get_options()
    raw = options.raw
    mic = options.mic
    output = options.output

    set_logging(options.v)

    logger.info(f'reading raw OD from {raw}')

    df = pd.read_csv(raw, sep='\t')
    df['strain'] = [f'NT{int(x)}' if str(x) != 'nan' and not str(x).startswith('NT')
                    else x
                    for x in df['strain'].values]

    reps = {}
    for i, rep in enumerate(sorted(df['date'].unique())):
        reps[rep] = f'r{i+1}'

    df['replicate'] = [reps[x] for x in df['date'].values]

    logger.info(f'reading compute MIC values from {mic}')

    c = pd.read_csv(mic, sep='\t')
    c['strain'] = [f'NT{int(x)}' if str(x) != 'nan' and not str(x).startswith('NT')
                   else x
                   for x in c['strain'].values]


    c['replicate'] = [reps[x] for x in c['date'].values]
    c = c.set_index(['strain', 'replicate'])['cmic']

    logger.info('Preparing raw OD matrix')

    df['concentration'] = [float(f'%.{options.digits}f' % x) for x in df['concentration']]
    m = df.pivot_table(index=['strain', 'replicate'],
                       columns='concentration',
                       values='od600')

    logger.info('Normalizing OD')

    n = df.groupby(['strain', 'replicate']).apply(normalize,
            normalise=options.normalise_od,
            threshold=options.od_threshold)

    logger.info('Preparing to plot')

    cmap = plt.get_cmap('viridis').copy()
    cmap.set_under('xkcd:light grey')

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), constrained_layout=True)
    for strain in sorted(df['strain'].dropna().unique()):
        fname = os.path.join(output, f'{strain}.{options.format}')

        logger.info(f'Ploting raw {strain}')

        ax = axes[0]

        hm = sns.heatmap(data=m.loc[strain], vmin=0,
                         vmax=0.6, cmap='cividis',
                         linewidths=0.5,
                         square=True, ax=ax, cbar=False)

        hm.set(ylabel='replicate',
               xlabel='concentration',
               title=f'{strain}, raw OD')

        for rep in sorted(c.loc[strain].index):
            cmic = c.loc[strain][rep]
            if np.isnan(cmic):
                continue
            hm.plot(list(n.columns).index(float(f'%.{options.digits}f' % cmic)) + 0.5,
                    list(n.loc[strain].index).index(rep) + 0.5,
                    'ro', markersize=4.5)

        logger.info(f'Ploting normalized {strain}')

        ax = axes[1]

        hm = sns.heatmap(data=n.loc[strain], vmin=0.2,
                         vmax=1, cmap=cmap,
                         linewidths=0.5,
                         square=True, ax=ax, cbar=False)

        hm.set(ylabel='replicate',
               xlabel='concentration',
               title=f'{strain}, normalized OD')

        for rep in sorted(c.loc[strain].index):
            cmic = c.loc[strain][rep]
            if np.isnan(cmic):
                continue
            hm.plot(list(n.columns).index(float(f'%.{options.digits}f' % cmic)) + 0.5,
                    list(n.loc[strain].index).index(rep) + 0.5,
                    'ro', markersize=4.5)

        plt.savefig(fname,
                    dpi=300, bbox_inches='tight',
                    transparent=True)

        for ax in axes:
            ax.clear()


#!/usr/bin/env python


import os
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .__init__ import __version__
from .grate import calc_growth_rate, grate_delta
from .plot import create_figure, plot_growth_rate
from .colorlog import ColorFormatter


logger = logging.getLogger('evol')


def set_logging(v):
    logger.propagate = True
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    if v == 0:
        ch.setLevel(logging.INFO)
    elif v >= 1:
        ch.setLevel(logging.DEBUG)
    formatter = ColorFormatter('%(asctime)s - %(name)s - $COLOR%(message)s$RESET','%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def get_options():
    description = 'Compute growth rates from a parsed plate reader experiment'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('data',
                        nargs='+',
                        help='Input reading from plate reader; '
                             'should contain the following columns: '
                             '"strain", "treatment", '
                             '"concentration", "plate", '
                             '"row", "column", '
                             '"experiment", "od600", "time"')
    parser.add_argument('output',
                        help='Output file for growth rate (tsv format)')

    parser.add_argument('--maximum-od',
                        type=float,
                        default=0.6,
                        help='Maximum OD600 to consider '
                             '(default: %(default).2f)')
    parser.add_argument('--window',
                        type=int,
                        default=60,
                        help='Time window to use '
                             '(minutes, default: %(default)d)')
    parser.add_argument('--top-mu',
                        type=int,
                        default=4,
                        help='How many growth rate estimates '
                             'to keep to compute the average '
                             '(default: the top %(default)d estimates)')

    parser.add_argument('--plot',
                        default=False,
                        action='store_true',
                        help='Plot growth curves '
                             '(default: doesn\'t)')
    parser.add_argument('--format',
                        choices=('png',
                                 'tiff',
                                 'pdf',
                                 'svg'),
                        default='png',
                        help='Output format for plots (default: %(default)s)') 
    parser.add_argument('--plots-output',
                        default='.',
                        help='Output directory for plots (default: %(default)s)')

    parser.add_argument('-v', action='count',
                        default=0,
                        help='Increase verbosity level')
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__)

    return parser.parse_args()


def plot(v, params, outdir, fmt, fig):
    name = '_'.join([str(x) for x in v.name])
    fname = os.path.join(outdir, f'{name}.{fmt}')
    logger.info(f'plotting growth rate {name}')
    logger.debug(f'creating file {fname}')
    p = params.loc[tuple(v.name), ['time', 'grate']]
    plot_growth_rate(v, p, fname, fig=fig, name=name)


def main():
    options = get_options()

    set_logging(options.v)

    df = []
    for filename in options.data:
        logger.info(f'reading data from {filename}')
        df.append(pd.read_csv(filename, sep='\t'))
    df = pd.concat(df)

    # trim the data at the maximum OD
    # TODO: trim using time
    df = df[df['od600'] < options.maximum_od]

    # seconds to hours
    df['time'] = df['time'] / 60 / 60
    # create a timedelta index
    # allows for rolling windows
    df.index = pd.to_timedelta(df['time'], unit='h')

    # take the natual log of OD600
    df['ln(od)'] = np.log(df['od600'])

    # ugly hack to allow groupby operations
    df['concentration'] = df['concentration'].fillna(0)

    groupby = ['plate', 'row', 'column', 'experiment',
               'strain', 'treatment', 'concentration']

    logger.info('computing growth rate for each well')

	# calculate growth rate
    mu = df.groupby(groupby
                   ).apply(calc_growth_rate,
                           time=f'{options.window}min').T
    # keep a copy of mu across all
    # windows for plotting
    mu_all = mu.copy()
    mu_all = mu_all.T.stack()
    mu_all.name = 'grate'
    mu_all = mu_all.reset_index()
    #
    # mu = mu.max()
    mu = mu.apply(lambda x: x.dropna().sort_values().tail(options.top_mu).mean())
    mu.name = 'grate'
    mu = mu.reset_index()

    # ugly hacks to add useful info
    mu['drug'] = [False if x == 0
                  else True
                  for x in mu['concentration'].values]
    mu['evolved'] = [x if x == 'ancestral'
                     else 'evolved'
                     for x in mu['treatment'].values]

    logger.info('computing growth rate delta w/r/t ancestral strain')

    try:
        # compute growth rate delta
        delta = mu.groupby('strain').apply(grate_delta).reset_index(drop=True)
    except Exception as e:
        logger.warning(f'could not compute delta growth rate ({str(e)}), skipping')
        delta = None

    # write output
    if delta is not None:
        mu = mu.set_index(groupby).join(
                delta.set_index(groupby)['delta'], how='left').reset_index()
    try:
        mu = mu.drop(columns=['level_6'])
    except:
        pass

    logger.info(f'writing output growth rates (and deltas) to {options.output}')

    mu.to_csv(options.output, sep='\t', index=False)

    if options.plot:
        fig = create_figure(figsize=(3.5, 3.5))

        df.groupby(groupby).apply(plot,
                                  params=mu_all.set_index(groupby),
                                  outdir=options.plots_output,
                                  fmt=options.format,
                                  fig=fig)


if __name__ == "__main__":
    main()


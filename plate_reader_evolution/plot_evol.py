#!/usr/bin/env python


import os
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .plot import make_color_dict, plot_legend, plot_passages, plot_appearance
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
    description = 'Plot OD600 values for an evolution experiment'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('data',
                        nargs='+',
                        help='Input reading from plate reader; '
                             'should contain the following columns: '
                             '"row", "column", '
                             '"plate", "passage", "strain", "treatment", '
                             '"concentration", '
                             '"experiment", "od600"')
    parser.add_argument('output',
                        help='Output directory')
   
    parser.add_argument('--threshold',
                        type=float,
                        default=0.5,
                        help='OD600 threshold to call growth '
                             '(default: %(default).2f)')
    parser.add_argument('--format',
                        choices=('png',
                                 'tiff',
                                 'pdf',
                                 'svg'),
                        default='png',
                        help='Output format (default: %(default)s)') 
    
    parser.add_argument('-v', action='count',
                        default=0,
                        help='Increase verbosity level')
    
    return parser.parse_args()


def main():
    options = get_options()

    set_logging(options.v)

    df = []
    for filename in options.data:
        logger.info(f'reading data from {filename}')
        df.append(pd.read_csv(filename, sep='\t'))
    df = pd.concat(df)

    # make sure we don't group replicates together
    df['id'] = [f'{e}{p}{x}{y}'
               for e, p, x, y in
               df[['experiment', 'plate', 'row', 'column']].values]

    # drop data with no treatment
    df = df.loc[df['treatment'].dropna().index].copy()

    logger.info(f'plotting strains legend')
    strains = sorted(set(df['strain'].dropna().unique()
                         ).difference(['Media Control']))
    strains_colors = make_color_dict(strains, cmap='hsv')
    fname = os.path.join(options.output, f'strain_legend.{options.format}')
    plot_legend(strains_colors, fname)

    df['treatment-id'] = [f'{treatment}-{conc}'
                          if treatment != 'GC'
                          else 'GC'
                          for treatment, conc in df[['treatment',
                                                     'concentration']].values]
    logger.info(f'plotting treatments legend')
    treatments = sorted(set(df['treatment-id'].dropna().unique()))
    treatments_colors = make_color_dict(treatments, cmap='tab10')
    fname = os.path.join(options.output, f'treatment_legend.{options.format}')
    plot_legend(treatments_colors, fname)

    # pivot the tables
    op = df.pivot_table(index=['treatment-id', 'strain', 'id'],
                        columns=['passage'], values='od600')

    logger.info(f'plotting all passages')
    fname = os.path.join(options.output, f'passages.{options.format}')
    plot_passages(op, treatments_colors, strains_colors, fname, 'OD600')
    
    # pivot the tables (average)
    op = df.pivot_table(index=['treatment-id', 'strain'],
                        columns=['passage'], values='od600')

    logger.info(f'plotting all passages (average)')
    fname = os.path.join(options.output, f'passages_average.{options.format}')
    plot_passages(op, treatments_colors, strains_colors, fname, 'OD600 (average)')

    # first appearance
    logger.info(f'computing the first appearance of resistance')
    df = df[df['passage'] > 0].copy()
    appearance = []
    for _, x in df.iterrows():
        if x['od600'] < options.threshold:
            v = 0
        else:
            if x['passage'] == df[df['treatment-id'] == df['treatment-id']]['passage'].max():
                v = 1
            elif df[(df['id'] == x['id']) &
                    (df['treatment'] == x['treatment']) &
                    (df['strain'] == x['strain']) &
                    (df['passage'] == x['passage'] + 1)]['od600'].values[0] >= options.threshold:
                v = 1
            else:
                v = 0
        appearance.append(v)
    df['appearance'] = appearance
    app = df[df['appearance'] > 0].groupby([
        'treatment-id', 'strain', 'id'])['passage'].min().reset_index()
    no_app = df[df['appearance'] == 0].groupby([
        'treatment-id', 'strain', 'id'])['passage'].max().reset_index()
    no_app = no_app[no_app['passage'] == df['passage'].max()].copy()
    no_app['passage'] = df['passage'].max() + 1
    app = pd.concat([app, no_app])
    app = app.groupby(['treatment-id', 'strain', 'id'])['passage'].min().reset_index()

    df = df.pivot_table(index=['treatment-id', 'strain', 'id'],
			columns=['passage'], values='appearance')

    logger.info(f'plotting first appearance (1)')
    fname = os.path.join(options.output, f'appearance_1.{options.format}')
    plot_passages(df, treatments_colors, strains_colors, fname, 'resistance',
                  cmap='Greys_r', vmax=1.3)
    
    logger.info(f'plotting first appearance (2)')
    fname = os.path.join(options.output, f'appearance_2.{options.format}')
    plot_appearance(app, strains_colors, fname)

if __name__ == "__main__":
    main()

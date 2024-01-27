#!/usr/bin/env python


import os
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .__init__ import __version__
from .mic import compute_mic
from .mic import fit_gompertz, fit_hill
from .plot import plot_mic, create_figure
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
    description = 'Compute IC50 and MIC from a parse plate reader experiment'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('data',
                        nargs='+',
                        help='Input reading from plate reader; '
                             'should contain the following columns: '
                             '"strain", "treatment", '
                             '"concentration", "plate", "passage", '
                             '"experiment", "od600"')
    parser.add_argument('output',
                        help='Output file (tsv format)')
    
    parser.add_argument('--minimum-od',
                        type=float,
                        default=0.2,
                        help='Minimum delta(OD600) to trigger curve fitting '
                             '(default: %(default).2f)')
    
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
    
    parser.add_argument('--stacked',
                        default=False,
                        action='store_true',
                        help='MIC assay is in 3D, '
                             'meaning it is "stacked" '
                             '(default: each replicate is in its own plate)')

    parser.add_argument('--skip-fitting',
                        default=False,
                        action='store_true',
                        help='Skip curve fitting, only compute cMIC '
                             '(default: also compute "regular" MIC and IC50)')

    parser.add_argument('--plot',
                        default=False,
                        action='store_true',
                        help='Plot MIC curves '
                             '(default: doesn\'t)')
    parser.add_argument('--format',
                        choices=('png',
                                 'tiff',
                                 'pdf',
                                 'svg',
                                 'jpg'),
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


def plot(v, params, outdir, fmt, fig, normalise, threshold):
    name = '_'.join([str(x) for x in v.name])
    fname = os.path.join(outdir, f'{name}.{fmt}')
    logger.info(f'plotting MIC {name}')
    logger.debug(f'creating file {fname}')
    p = params.loc[tuple(v.name), ['a', 'b', 'c', 'd', 'mic', 'cmic']]
    plot_mic(v, p, fname, normalise=normalise,
             threshold=threshold,
             fig=fig, name=name)


def main():
    options = get_options()

    set_logging(options.v)

    df = []
    for filename in options.data:
        logger.info(f'reading data from {filename}')
        df.append(pd.read_csv(filename, sep='\t'))
    df = pd.concat(df)
   
    if not options.stacked:
        groupby = ['experiment', 'plate', 'strain', 'treatment', 'passage', 'date']
    else:
        groupby = ['experiment', 'strain', 'treatment', 'passage', 'date']

    if not options.skip_fitting:
        # compute MICs
        logger.info('computing MICs (curve fitting)')
        mic = df.groupby(groupby).apply(fit_gompertz,
                                        estimate=True,
                                        sanity=options.minimum_od,
                                        normalise=options.minimum_od,
                                        )['mic'].to_frame()
    # compute MICs (classical "eyeballing" method)
    logger.info('computing MICs (eyeballing)')
    cmic = df.groupby(groupby).apply(compute_mic,
                                     threshold=options.od_threshold,
                                     normalise=options.minimum_od,
                                     )
    cmic.name = 'cmic'
    cmic = cmic.to_frame()
    if not options.skip_fitting:
        # fit hill function (IC50)
        logger.info('computing IC50s')
        params = df.groupby(groupby).apply(fit_hill,
                                           estimate=True,
                                           sanity=options.minimum_od,
                                               normalise=options.minimum_od)
        params = params.join(mic.join(cmic, how='outer'), how='outer')
    else:
        params = cmic
        for x in ['a', 'b', 'c', 'd', 'mic']:
            params[x] = np.nan

    params.to_csv(options.output,
                  sep='\t')

    if options.plot:
        fig = create_figure(figsize=(3.5, 3.5)) 
        
        df.groupby(groupby).apply(plot,
                                  params=params,
                                  normalise=options.minimum_od,
                                  threshold=options.od_threshold,
                                  outdir=options.plots_output,
                                  fmt=options.format,
                                  fig=fig)


if __name__ == "__main__":
    main()


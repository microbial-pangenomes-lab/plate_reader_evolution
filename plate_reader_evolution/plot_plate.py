#!/usr/bin/env python


import os
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .__init__ import __version__
from .plot import plot_plate, create_figure
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
    description = 'Plot OD600 values in plate format'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('data',
                        nargs='+',
                        help='Input reading from plate reader; '
                             'should contain the following columns: '
                             '"row", "column", '
                             '"plate", "passage", "date",'
                             '"experiment", "od600"')
    parser.add_argument('output',
                        help='Output directory')
   
    parser.add_argument('--p384',
                        action='store_true',
                        default=False,
                        help='Experiment is done on 384 plates (default: 96 wells, '
                             'would not work with time series data)')

    parser.add_argument('--date-is-replicate',
                        action='store_true',
                        default=False,
                        help='The "date" field indicates the replicate identifier')

    parser.add_argument('--mic',
                        action='store_true',
                        default=False,
                        help='Experiment is an MIC assesment (default: serial passaging)')

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
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__)
    
    return parser.parse_args()


def plot(v, outdir, fmt, fig, p384=False):
    name = '_'.join([str(x) for x in v.name])
    fname = os.path.join(outdir, f'{name}.{fmt}')
    logger.info(f'plotting plate {name}')
    logger.debug(f'creating file {fname}')
    plot_plate(v, fname, fig=fig, name=name, p384=p384)


def main():
    options = get_options()

    set_logging(options.v)

    fig = create_figure() 

    df = []
    for filename in options.data:
        logger.info(f'reading data from {filename}')
        df.append(pd.read_csv(filename, sep='\t'))
    df = pd.concat(df)

    if options.date_is_replicate:
        groupby = ['experiment', 'plate', 'passage', 'date']
    elif not options.mic:
        groupby = ['experiment', 'plate', 'passage']
    else:
        groupby = ['experiment', 'plate', 'passage', 'date']

    df.groupby(groupby).apply(plot,
                              outdir=options.output,
                              fmt=options.format,
                              fig=fig,
                              p384=options.p384)

if __name__ == "__main__":
    main()

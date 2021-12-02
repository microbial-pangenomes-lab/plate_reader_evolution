#!/usr/bin/env python


import os
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

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
                             '"plate", "passage", '
                             '"experiment", "od600"')
    parser.add_argument('output',
                        help='Output directory')
   
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


def plot(v, outdir, fmt, fig):
    name = '_'.join([str(x) for x in v.name])
    fname = os.path.join(outdir, f'{name}.{fmt}')
    logger.info(f'plotting plate {name}')
    logger.debug(f'creating file {fname}')
    plot_plate(v, fname, fig=fig, name=name)


def main():
    options = get_options()

    set_logging(options.v)

    fig = create_figure() 

    df = []
    for filename in options.data:
        logger.info(f'reading data from {filename}')
        df.append(pd.read_csv(filename, sep='\t'))
    df = pd.concat(df)
   
    groupby = ['experiment', 'plate', 'passage']

    df.groupby(groupby).apply(plot,
                              outdir=options.output,
                              fmt=options.format,
                              fig=fig)

if __name__ == "__main__":
    main()

#!/usr/bin/env python


import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .__init__ import __version__
from .parse import parse_ramp_design, parse_excel, parse_excel_time_series
from .parse import parse_shuffle_design
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
    description = 'Scan a directory to extract a plate reader experiment'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('folder',
                        help='Input folder: must contain one subfolder '
                             'per passage En_STEP (e.g. E1_0.125). '
                             'Each subfolder contains one excel file '
                             'per replicate in the format '
                             'DATE_STEP_PASSAGE_REPLICATE_DATE '
                             '(e.g. 300622_0.125_E1_0001_220630). '
                             'If a kynetic reading has been done, then '
                             'the file is called DATE_STEP_PASSAGE_REPLICATE')

    parser.add_argument('design',
                        help='Experiment/plate design: '
                             'excel file with multiple sheets; '
                             'should contain the "strain", "row" and '
                             '"columns" columns, plus a columns named as the '
                             'treatment argument, containing X times the '
                             'highest concentration in the ramp. The X '
                             'multiplication factor can be set with the '
                             '`--stock` argument')

    parser.add_argument('treatment',
                        help='Treatment name: '
                             'must be present as a column in the design file')

    parser.add_argument('output',
                        help='Output file (tsv format)')

    parser.add_argument('--prefix',
                        default=None,
                        help='Add a prefix to the strains (default: none)')
    parser.add_argument('--stock',
                        type=float,
                        default=10.,
                        help='By which factor the indicated concentration '
                             'in the design file must be divided by to get '
                             'the highest concentration used '
                             '(default: %(default).2f)')
    parser.add_argument('--steps',
                        type=int,
                        default=1,
                        help='How many passages before concentration increase '
                             '(default: %(default)d)')
    parser.add_argument('--multiplier',
                        type=float,
                        default=2.,
                        help='Concentration increase at each step (X times) '
                             '(default: %(default).2f)')
    parser.add_argument('--mic',
                        type=float,
                        default=16.,
                        help='How many times the original MIC is the highest '
                             'concentration in the ramp '
                             '(default: %(default).2f)')

    parser.add_argument('--shuffle-key',
                        default=None,
                        help='Randomization key file: '
                             'excel file with multiple sheets; '
                             'sheet name should be the replicate '
                             'that is shuffled, and should contain the'
                             '"row", "columns", "dest_row", "dest_column" '
                             'columns. If not provided it is assumed '
                             'that each replicate has the same layout')

    parser.add_argument('-v', action='count',
                        default=0,
                        help='Increase verbosity level')
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__)

    return parser.parse_args()


def main():
    options = get_options()
    folder = options.folder
    design = options.design
    treatment = options.treatment
    shuffle = options.shuffle_key
    mic = options.mic
    stock = options.stock
    steps = options.steps
    multiplier = options.multiplier

    set_logging(options.v)

    logger.info(f'reading plate design from {design}')

    de = parse_ramp_design(design, treatment, prefix=options.prefix)
    ded = []
    ds = {}
    if shuffle is not None:
        ds = parse_shuffle_design(shuffle)

    df = []
    for subfolder in [x for x in os.listdir(folder)
                      if os.path.isdir(os.path.join(folder, x))]:
        if len(subfolder.split('_')) < 2:
            logger.debug(f'skipping {subfolder} from {folder}')
        d_passage, d_step = subfolder.split('_')[:2]
        # make the passage bit an integer
        # TODO: cross check with the date
        n_passage = int(d_passage[1:])
        for infile in os.listdir(os.path.join(folder, subfolder)):
            if not infile.endswith('xlsx') and not infile.endswith('xls'):
                logger.debug(f'skipping {infile} from {subfolder}')
                continue

            n_fields = len(infile.split('_'))
            if n_fields < 4:
                logger.debug(f'skipping {infile} from {folder}')
                continue

            if n_fields == 4:
                replicate = infile.split('_')[-1]
            else:
                replicate = infile.split('_')[-2]
            replicate = replicate.split('.')[0]

            logger.info(f'about to parse {infile}')

            try:
                m = parse_excel(os.path.join(folder, subfolder, infile))
            except:
                # probably a time series, try the alternative approach
                logger.debug(f'could not parse {infile} from {subfolder} '
                             'trying to see if it is a timeseries')
                m = parse_excel_time_series(os.path.join(folder, subfolder, infile))
                # pick last time point
                m = m[m['time'] == m['time'].max()]['od600']

            # is this a shuffled replicate?
            if replicate in ds:
                logger.debug(f'replicate {replicate} is shuffled, correcting')
                # make a temp copy of the design
                dt = de.copy()
                nr = [ds[replicate][(r, c)][0]
                      for r, c in dt[['row', 'column']].values]
                nc = [ds[replicate][(r, c)][1]
                      for r, c in dt[['row', 'column']].values]
                dt['row'] = nr
                dt['column'] = nc
            else:
                dt = de.copy()
            dt['replicate'] = replicate
            ded.append(dt)

            # join with design table
            m = dt.set_index(['row', 'column'])[['strain',
                                                 treatment]].join(m.to_frame(), how='outer')
            m = m.rename(columns={treatment: 'mic'})
            m['concentration'] = m['mic'].copy()
            m['passage'] = n_passage
            m['replicate'] = replicate
            m = m.reset_index()

            df.append(m)

            logger.debug(f'parsed {infile}')

    de = pd.concat(ded)
    df = pd.concat(df)

    # add metadata
    df['treatment'] = treatment
    df['type'] = 'ramp'

    # encode the MIC ramp relative and absolute values
    passages = list(range(1, df['passage'].max() + 1 - steps))[::-1]
    mics = {x: (multiplier ** ((i // steps) + 1)) for i, x in enumerate(passages)}
    for i in range(steps):
        mics[df['passage'].max() - i] = 1
    high = de.set_index(['replicate', 'row', 'column'])[treatment].to_dict()
    df['mic'] = [mic / mics[x] for x in df['passage'].values]
    df['concentration'] = [high.get((rep, row, column), np.nan) / (mics[x] * stock)
                           for rep, row, column, x in
                           df[['replicate', 'row', 'column', 'passage']].values]

    df = df.sort_values(['passage', 'replicate', 'row', 'column'])

    df.to_csv(options.output, index=False, sep='\t')


if __name__ == "__main__":
    main()

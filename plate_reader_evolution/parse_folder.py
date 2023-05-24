#!/usr/bin/env python


import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .__init__ import __version__
from .parse import parse_plate_design, parse_excel, parse_excel_time_series
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
                        help='Input folder: must contain excel files in '
                             'the format PLATE_DATE_PASSAGE.xlsx. The '
                             'folder name should have the format '
                             'EXP_DATE_Evol_XXXX')
    
    parser.add_argument('design',
                        help='Experiment/plate design: '
                             'excel file with multiple sheets in the format '
                             'EXP_PLATE_DATE')
    
    parser.add_argument('output',
                        help='Output file (tsv format)')
    
    etype = parser.add_mutually_exclusive_group()
    etype.add_argument('--mic',
                       action='store_true',
                       default=False,
                       help='Folder contains MICs (default: evol. exp.)')
    etype.add_argument('--grate',
                       action='store_true',
                       default=False,
                       help='Folder contains growth curves (default: evol. exp.)')

    parser.add_argument('--p384',
                        action='store_true',
                        default=False,
                        help='Experiment is done on 384 plates (default: 96 wells, '
                             'would not work with time series data)')

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

    set_logging(options.v)

    logger.info(f'reading plate design from {design}')
    
    d = {}
    for name, exp, plate, df in parse_plate_design(design):
        d[exp] = d.get(exp, {})
        d[exp][plate] = df

    # check if the folder is in the right format
    a_folder = os.path.basename(os.path.normpath(folder))
    if len(a_folder.split('_')) < 4:
        logger.error(f'folder name ({a_folder}) does not respect naming convention '
                      'EXP_DATE_Evol_XXXX')
        sys.exit(1)

    exp, edate, etype, _ = a_folder.split('_')

    if (not options.mic and not options.grate) and etype.lower() != 'evol':
        logger.error('expecting "evol" in the folder name as experiment type'
                     f', found {etype}')
        sys.exit(1)
    elif options.mic and (etype.lower() != 'mics' and etype.lower() != 'mic'):
        logger.error('expecting "mics" or "mic" in the folder name as experiment type'
                     f', found {etype}')
        sys.exit(1)
    elif options.grate and etype.lower() != 'grate':
        logger.error('expecting "grate" in the folder name as experiment type'
                     f', found {etype}')
        sys.exit(1)
    if exp not in d:
        logger.error(f'experiment {exp} not in the design table')
        sys.exit(1)

    df = []
    for infile in os.listdir(folder):
        if not infile.endswith('xlsx') and not infile.endswith('xls'):
            logger.debug(f'skipping {infile} from {folder}')
            continue
        if len(infile.split('.')[0].split('_')) < 3:
            logger.debug(f'skipping {infile} from {folder}')
            continue

        plate, date, passage = infile.split('.')[0].split('_')[:3]
        if not options.mic and not options.grate:
            # make the passage bit an integer
            # TODO: cross check with the date
            n_passage = int(passage[1:])
        else:
            # either "start" or TBD
            n_passage = passage

        logger.info(f'about to parse {infile}')

        try:
            m = parse_excel(os.path.join(folder, infile), p384=options.p384)
        except:
            if options.p384:
                logger.error(f'could not parse {infile} from {folder}')
                sys.exit(1)

            # probably a time series, try the alternative approach
            logger.debug(f'could not parse {infile} from {folder} '
                         'trying to see if it is a timeseries')
            m = parse_excel_time_series(os.path.join(folder, infile))

        if plate not in d[exp]:
            logger.warning(f'plate {plate} from {exp} not in the design table')
            continue

        # join with design table
        if options.grate:
            m = d[exp][plate].set_index(['row', 'column']).join(m, how='outer')
        else:
            m = d[exp][plate].set_index(['row', 'column']).join(m.to_frame(), how='outer')
        m['plate'] = plate
        m['date'] = date
        m['passage'] = n_passage
        df.append(m)

        logger.debug(f'parsed {infile}')

    df = pd.concat(df)

    # add metadata
    df['experiment'] = exp
    df['type'] = etype.lower()

    df = df.sort_values(['plate', 'passage', 'date', 'row', 'column'])

    df.to_csv(options.output, sep='\t')


if __name__ == "__main__":
    main()

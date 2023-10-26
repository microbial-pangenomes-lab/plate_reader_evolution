#!/usr/bin/env python


import os
import sys
import shutil
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from .__init__ import __version__
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
    description = 'Scan a directory to rename raw readings for parse_folder'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('folder',
                        help='Input folder: must contain one directory per '
                             'day in the form MYEXP_PASSAGEID '
                             '( e.g. MYEXP_E1); inside there should be two files '
                             'for each plate reading, with format '
                             'ID_PASSAGEID_NUMBER_DATE.txt/.xls')
    
    parser.add_argument('conversion',
                        help='Numbered plate conversion file: '
                             'excel file with multiple columns in the format: '
                             'NUMBER -> NAME -> PLATE -> TYPE -> EXP')
    
    parser.add_argument('output',
                        help='Output directory')
    
    parser.add_argument('-v', action='count',
                        default=0,
                        help='Increase verbosity level')
    parser.add_argument('--version', action='version',
                        version='%(prog)s '+__version__)

    return parser.parse_args()


def main():
    options = get_options()
    folder = options.folder
    conversion = options.conversion
    output = options.output

    set_logging(options.v)

    logger.info(f'reading plate conversion from {conversion}')
    
    c = pd.read_excel(conversion, header=None)
    if c.shape[1] == 5:
        c.columns = ['id', 'name', 'plate', 'type', 'exp']
    else:
        c.columns = ['id', 'name', 'plate', 'type', 'exp'] + [f'extra_{i}' for i in c.columns[5:]]
    c = c.set_index('id')

    folders = [x for x in os.listdir(folder)
               if os.path.isdir(os.path.join(folder, x))
               and len(x.split('_')) == 2]
    logger.info(f'going to process {len(folders)} sub-directories')

    for f in folders:
        logger.info(f'processing {f}')
        date, passage = f.split('_')
        files = [x
                 for x in os.listdir(os.path.join(folder, f))
                 if x.endswith('.txt')
                 or x.endswith('.xls')]
        logger.debug(f'looking at {len(files)} file to convert')
        for i in files:
            logger.debug(f'processing {f} - {i}')
            extension = i.split('.')[-1]
            try:
                fdate, fpassage, number, date = i.split('.')[0].split('_')
            except ValueError:
                logger.warning(f'could not extract info from file name {i}, trying alternative approach')
                try:
                    fdate, number, date = i.split('.')[0].split('_')
                except ValueError:
                    logger.warning(f'could not extract info from file name {i} giving up')
                    continue
            number = int(number)
            if number not in c.index:
                logger.warning(f'could not find conversion for file {i}')
                continue
            name, plate, etype, exp = c.loc[number, ['name', 'plate', 'type', 'exp']].values
            outfolder = f'{exp}_renamed_{etype}_xxx'
            fname = f'{plate}_{date}-{name}_{passage}.{extension}'

            orig = os.path.join(folder, f, i)
            dest = os.path.join(output, outfolder, fname)
            try:
                os.mkdir(output)
            except:
                pass
            try:
                os.mkdir(os.path.join(output, outfolder))
            except:
                pass
            logger.debug(f'copying {orig} to {dest}')
            shutil.copy(orig, dest)

if __name__ == "__main__":
    main()

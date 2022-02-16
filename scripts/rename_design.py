#!/usr/bin/env python


import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
import logging.handlers

from plate_reader_evolution.parse import parse_plate_design
from plate_reader_evolution.colorlog import ColorFormatter


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

    parser.add_argument('rename',
                        help='File with renaming information')
    
    parser.add_argument('design',
                        help='Experiment/plate design: '
                             'excel file with multiple sheets in the format '
                             'EXP_PLATE_DATE')
    
    parser.add_argument('output',
                        help='Output')
    
    parser.add_argument('-v', action='count',
                        default=0,
                        help='Increase verbosity level')

    return parser.parse_args()


if __name__ == "__main__":
    options = get_options()
    rename = options.rename
    design = options.design
    output = options.output

    set_logging(options.v)

    logger.info(f'reading plate design from {design}')
    
    d = []
    for name, exp, plate, df in parse_plate_design(design):
        df['experiment'] = exp
        df['plate'] = plate
        df['name'] = name
        df['well'] = [f'{x}{y}' for x, y in df[['row', 'column']].values]
        df['strain'] = [str(int(x)) if str(x) != 'nan' else np.nan for x in df['strain'].values]
        d.append(df)
    d = pd.concat(d)

    r = pd.read_csv(rename, sep='\t')
    r['STRAIN'] = [str(int(x)) if str(x) != 'nan' else np.nan for x in r['STRAIN'].values]
    r['STRAIN'] = r['STRAIN'].astype(str)
    r['MIC_Plate'] = [f'P{x}' for x in r['MIC_Plate'].values]
    r['MIC_Row'] = [list('XABCDEFGH')[x] for x in r['MIC_Row'].values]

    d = d.set_index(['experiment', 'plate', 'row', 'strain'])
    r = r.set_index(['MIC_EXP', 'MIC_Plate', 'MIC_Row', 'STRAIN'])
    r.index.names = d.index.names

    j = d.join(r, how='inner')
    j = j.reset_index()

    j['new'] = [f'{strain}_{exp}_{plate}_{well}_{passage}_{notes}'
                for strain, exp, plate, well, passage, notes in
                j[['strain', 'EVOL_EXP', 'Evol_Plate', 'WELL', 'PASSAGE', 'HML']].values]

    with pd.ExcelWriter(output) as writer:  
        for name in j['name'].unique(): 
            t = j[j['name'] == name][['well', 'new', 'treatment', 'concentration']]
            t.columns = ['Plate Well', 'Description', 'Treatment', 'Concentration']
            t.to_excel(writer, sheet_name=name, index=False)

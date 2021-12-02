#!/usr/bin/env python


import logging
import numpy as np
import pandas as pd


logger = logging.getLogger('evol.parse')


def parse_excel(infile):
    '''Parse an excel output from the BioTek plate reader
    
    The expecation is that the OD values are a single timepoint, from a 96-well
    microplate.

    More replicates are possible and their number is determined heuristically
    '''
    m = pd.read_excel(infile)
    
    # trim to the actual results area
    n = m[m.columns[2]].dropna().iloc[1:]
    
    n_values = n.shape[0]
    
    # we assume a 96 well plate, so 8 rows
    repeats = n_values // 8
    rest = n_values % 8
    
    # if we have spare change must assume something is not right
    if rest != 0:
        raise ValueError(f'Could not parse {infile}; found {n_values} '
                          'measurements, not a multiple of 8')
    
    logger.debug(f'Found {repeats} from {infile}')
    
    # get the meat of the spreadsheet
    m = m.iloc[-n_values:, 2:-1]

    # assign row and col names
    m.index = list(''.join([x * repeats for x in 'ABCDEFGH']))
    m.columns = list(range(1, 13))

    m.index.name = 'row'
    m.columns.name = 'column'
    
    m = m.stack()
    m.name = 'od600'
    
    return m
    

def parse_plate_design(infile):
    '''Parse an excel table to access the plate designs

    Returns a generator of (design string, experiment, plate, design dataframe)

    The excel table may have multiple sheets

    TODO: indicate expected columns
    TODO: kwargs with columns to keep/in which order
    '''
    d = pd.read_excel(infile, sheet_name=None)
    for name, m in d.items():
        # separate row from column
        if 'Plate Well' not in m.columns:
            raise ValueError('Could not find a column named "Plate Well" '
                             f'in sheet {name} from {infile}')
        m['row'] = [x[0] for x in m['Plate Well'].values]
        m['column'] = [int(x[1:]) for x in m['Plate Well'].values]

        # "Description" actually refers to the strain
        m['strain'] = [x if x != 'blank'
                       else np.nan
                       for x in m['Description'].values]
        
        # TODO: check for missing column

        # rename the other columns
        m = m.rename(columns={'Treatment': 'treatment',
                              'Concentration': 'concentration'})

        # keep only the columns we want, in a specific order
        m = m[['row', 'column', 'strain', 'treatment', 'concentration']]

        # break down the design name
        experiment, plate = name.split('_')[:2]
        # remove dangling whitespaces
        experiment = experiment.strip()
        plate = plate.strip()

        logger.debug(f'found {experiment}, {plate} from {infile}')

        yield name, experiment, plate, m


if __name__ == '__main__':
    pass

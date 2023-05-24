#!/usr/bin/env python


import logging
import numpy as np
import pandas as pd


logger = logging.getLogger('evol.parse')


def parse_excel(infile, p384=False):
    '''Parse an excel output from the BioTek plate reader

    The expecation is that the OD values are a single timepoint, from a 96-well
    or 384-well microplate.

    More replicates are possible and their number is determined heuristically
    '''
    m = pd.read_excel(infile)

    # trim to the actual results area
    n = m[m.columns[2]].dropna().iloc[1:]

    n_values = n.shape[0]

    if not p384:
        # we assume a 96 well plate, so 8 rows
        repeats = n_values // 8
        rest = n_values % 8

        # if we have spare change must assume something is not right
        if rest != 0:
            raise ValueError(f'Could not parse {infile}; found {n_values} '
                              'measurements, not a multiple of 8')
    else:
        # we assume a 384 well plate, so 16 rows
        repeats = n_values // 16
        rest = n_values % 16

    logger.debug(f'Found {repeats} from {infile}')

    # get the meat of the spreadsheet
    m = m.iloc[-n_values:, 2:-1]

    # assign row and col names
    if not p384:
        m.index = list(''.join([x * repeats for x in 'ABCDEFGH']))
        m.columns = list(range(1, 13))
    else:
        m.index = list(''.join([x * repeats for x in 'ABCDEFGHIJKLMNOP']))
        m.columns = list(range(1, 25))

    m.index.name = 'row'
    m.columns.name = 'column'

    m = m.stack()
    m.name = 'od600'

    return m


def parse_excel_time_series(infile):
    '''Parse an excel output from the BioTek plate reader

    The expecation is that the OD values are multiple timepoints, from a 96-well
    microplate.
    '''
    m = pd.read_excel(infile, usecols='B:CU', parse_dates=False, date_parser=str)
    n = m.dropna()
    n = n.reset_index(drop=True)
    n.columns = n.iloc[0]

    n = n.iloc[1:].copy()

    time = []
    warning = True
    for x in n['Time'].astype('str'):
        if ' ' in x:
            # 24 hours have elapsed
            # extremely ugly hack
            if warning:
                logger.warning(f'{infile} went over 24 hours, applying ugly hack '
                               'if the read went over 48 hours DO NOT trust the output')
                warning = False
            extra_seconds = 24 * 60 * 60
            x = x.split()[-1]
        else:
            extra_seconds = 0
        seconds = extra_seconds + int(x.split(':')[0]) * 60 * 60 + int(x.split(':')[1]) * 60 + int(x.split(':')[2])
        time.append(seconds)
    n['time'] = time

    n = n.drop(columns=['Time', 'T° 600'])

    n = n.set_index('time').stack()
    n.name = 'od600'
    n.index.names = ['time', 'well']
    n = n.reset_index()
    n['row'] = [x[0] for x in n['well'].values]
    n['column'] = [int(x[1:]) for x in n['well'].values]

    n = n.drop(columns=['well'])

    return n.set_index(['row', 'column'])[['time', 'od600']]


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
        # ignore rows that don't have a value in the "Plate Well" column
        m = m[~m['Plate Well'].isna()].copy()
        #
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


def parse_ramp_design(infile, treatment, prefix=None):
    '''Parse an excel table to access the plate design for a ramp

    Given a column name of the treatment, return a single dataframe
    for one plate

    The excel table may have multiple sheets, they are iterated until the
    relevant dataframe is constructed

    TODO: indicate expected columns
    TODO: kwargs with columns to keep/in which order
    '''
    d = pd.read_excel(infile, sheet_name=None)
    for name, m in d.items():
        if treatment not in m.columns:
            logger.debug(f'skipping sheet {name} from {infile}, '
                         f'no column {treatment} found')
            continue
        # separate row from column
        if ('strain' not in m.columns
            or 'row' not in m.columns
            or 'column' not in m.columns):
            raise ValueError('Could not find the necessary columns '
                             '("strain", "row", "column") '
                             f'in sheet {name} from {infile}')
        # ignore rows that don't have a value in the "row" column
        m = m[~m['row'].isna()].copy()

        # keep only the columns we want, in a specific order
        m = m[['row', 'column', 'strain', treatment]]

        if prefix is not None:
            m['strain'] = [f'{prefix}{int(x)}' if str(x) != 'nan'
                           else np.nan
                           for x in m['strain'].values]
            m['strain'] = m['strain'].astype(str)

        logger.debug(f'found {treatment} from {infile}')

        return m


def parse_shuffle_design(infile):
    '''Parse an excel table to access the shuffling map for a replicate

    Returns a dictionary for each sheet
    '''
    res = {}
    d = pd.read_excel(infile, sheet_name=None)
    for name, m in d.items():
        res[name] = {}
        for r, c, nr, nc in m[['row', 'column',
                               'dest_row', 'dest_column']].values:
            res[name][(r, c)] = (nr, nc)

    logger.debug(f'parsed {len(res)} plate shuffled maps')

    return res


if __name__ == '__main__':
    pass

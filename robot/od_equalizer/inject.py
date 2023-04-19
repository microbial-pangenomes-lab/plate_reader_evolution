#!/usr/bin/env python

import argparse
import pandas as pd


def get_options():
    description = 'Inject data from a csv file into a OT-2 protocol'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('protocol',
                        help='Input protocol python file')
    parser.add_argument('table',
                        help='Input xlsx file, from plate reader')
    parser.add_argument('--tag',
                        default='HERE_INJECT_DATA',
                        help='Use a 384-well plate layout '
                             '(default: 96-well plate)')

    return parser.parse_args()


def parse_excel(infile):
    '''Parse an excel output from the BioTek plate reader

    The expecation is that the OD values are a single timepoint, from a 384-well
    microplate.

    More replicates are possible and their number is determined heuristically
    '''
    m = pd.read_excel(infile)

    # trim to the actual results area
    n = m[m.columns[2]].dropna().iloc[1:]

    n_values = n.shape[0]

    # we assume a 384 well plate, so 16 rows
    repeats = n_values // 16
    rest = n_values % 16

    # if we have spare change must assume something is not right
    if rest != 0:
        raise ValueError(f'Could not parse {infile}; found {n_values} '
                          'measurements, not a multiple of 16')

    # get the meat of the spreadsheet
    m = m.iloc[-n_values:, 2:-1]

    # assign row and col names
    m.index = list(''.join([x * repeats for x in 'ABCDEFGHIJKLMNOP']))
    m.columns = list(range(1, 25))

    m.index.name = 'row'
    m.columns.name = 'column'

    m = m.stack()
    m.name = 'od600'

    return m


if __name__ == '__main__':
    options = get_options()

    m = parse_excel(options.table).reset_index()
    m = m.groupby(['row', 'column'])['od600'].mean().reset_index()
    for l in open(options.protocol):
        if l.strip() != options.tag:
            print(l.rstrip())
        else:
            data = str([(r, c, v) for r, c, v in m.values])
            print(f'DATA = {data}')

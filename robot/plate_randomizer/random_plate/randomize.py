#!/usr/bin/env python

import sys
import copy
import random
import argparse

def get_options():
    description = 'Randomize a 96 well plate'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--seed',
                        type=int,
                        default=100,
                        help='Random seed for reproducible randomizations '
                             '(default: %(default)%d)')
    parser.add_argument('--plate-384',
                        action='store_true',
                        default=False,
                        help='Use a 384-well plate layout '
                             '(default: 96-well plate)')

    return parser.parse_args()

if __name__ == '__main__':
    options = get_options()

    # set random seed
    random.seed(options.seed, version=2)

    if options.plate_384:
        rows = 'ABCDEFGHIJKLMNOP'
        cols = range(1, 25)
        outer_rows = set(('A', 'B', 'O', 'P'))
        outer_cols = set((1, 2, 23, 24))
    else:
        rows = 'ABCDEFGH'
        cols = range(1, 13)
        outer_rows = set(('A', 'H'))
        outer_cols = set((1, 12))

    border = []
    middle = []
    for row in rows:
        for column in cols:
            if row in outer_rows:
                border.append( (row, column) )
            elif column in outer_cols:
                border.append( (row, column) )
            else:
                middle.append( (row, column) )

    o_border = copy.deepcopy(border)
    o_middle = copy.deepcopy(middle)

    # make randomizations
    random.shuffle(middle)
    random.shuffle(border)

    n_middle = []
    n_border = []
    for i, _ in enumerate(border):
        n_middle.append(border[i])
    for j in range(len(middle) - len(border)):
        n_middle.append(middle[j])
    for i in range(j+1, len(middle)):
        n_border.append(middle[i])

    assert(len(o_border) == len(n_border))
    assert(len(o_middle) == len(n_middle))

    # write the output out
    for (s_row, s_column), (d_row, d_column) in zip(border + middle,
                                                    n_border + n_middle):
        print(f'{s_row}\t{s_column}\t{d_row}\t{d_column}')

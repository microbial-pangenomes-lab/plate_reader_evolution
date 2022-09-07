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

    return parser.parse_args()

if __name__ == '__main__':
    options = get_options()

    # set random seed
    random.seed(options.seed, version=2)

    border = []
    middle = []
    for row in 'ABCDEFGH':
        for column in range(1, 13):
            if row == 'A' or row == 'H':
                border.append( (row, column) )
            elif column == 1 or column == 12:
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

    o_wells = sorted(o_border + o_middle, key=lambda x: x)

    # write the output out
    for (s_row, s_column), (d_row, d_column) in zip(o_wells, n_border + n_middle):
        print(f'{s_row}\t{s_column}\t{d_row}\t{d_column}')

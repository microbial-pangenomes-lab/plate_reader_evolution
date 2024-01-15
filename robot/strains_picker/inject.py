#!/usr/bin/env python

import argparse

def get_options():
    description = 'Inject data from a csv file into a OT-2 protocol'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('protocol',
                        help='Input protocol python file')
    parser.add_argument('table',
                        help='Input csv file, with no header')
    parser.add_argument('--tag',
                        default='HERE_INJECT_DATA',
                        help='Use a 384-well plate layout '
                             '(default: 96-well plate)')

    return parser.parse_args()

if __name__ == '__main__':
    options = get_options()

    for l in open(options.protocol):
        if l.strip() != options.tag:
            print(l.rstrip())
        else:
            data = str(open(options.table).readlines())
            print(f'DATA = {data}')

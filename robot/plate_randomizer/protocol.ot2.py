#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# in ul, depending on the volume a different pipette is used
TRANSFER_VOLUME = 15
# in ul, influences the height at which the tip is placed
SOURCE_VOLUME = 1500
# in ul, influences the height at which the tip is placed
DESTINATION_VOLUME = 1485
# should be a csv file with no header and 4 fields
# 1. source row (A to H)
# 2. source column (1 to 12)
# 3. destination row (A to H)
# 4. destination column (1 to 12)
TSV_FILE = 'my_randomization.tsv'
###############################################################################


import sys
import csv

from opentrons import protocol_api

metadata = {
    'protocolName': 'Plate randomizer',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }


def read_transfers(protocol, fname):
    # dictionary to keep track of transfers
    transfers = {}

    for csv_row in protocol.bundled_data[fname].decode('utf-8').rstrip().split('\n'):
        csv_row = csv_row.rstrip().split('\t')
        s_row, s_column, d_row, d_column = csv_row[:4]
        s_column = int(s_column)
        d_column = int(d_column)
        s_well = f'{s_row}{s_column}'
        d_well = f'{d_row}{d_column}'

        transfers[s_well] = d_well

    protocol.comment(f'Will perfom {len(transfers)} tranfers')
    return transfers


def make_transfer(protocol):
    transfers = read_transfers(protocol, TSV_FILE)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # left: p300 single
    # right: p20 single

    # 1. 300uL tips
    # 2. 20uL tips
    # 5. 96 deep-well plate (source)
    # 6. 96 deep-well plate (target)

    # tips
    tip300 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tip20 = protocol.load_labware('opentrons_96_tiprack_20ul', 2)

    # pipette arms
    # 1 - 300 uL
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tip300])
    # 1 - 20 uL
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tip20])

    # source plate
    s_plate = protocol.load_labware('vwr_96_wellplate_2000ul', 5)

    # destination plate
    d_plate = protocol.load_labware('vwr_96_wellplate_2000ul', 6)

    if TRANSFER_VOLUME > 20:
        pipette = p300
        #pipette.well_bottom_clearance.aspirate = 2
        #pipette.well_bottom_clearance.dispense = 2
    else:
        pipette = p20
        #pipette.well_bottom_clearance.aspirate = 2
        #pipette.well_bottom_clearance.dispense = 2

    # do the actual transfers
    for s_well, d_well in transfers.items():
        pipette.transfer(TRANSFER_VOLUME,
                         s_plate[s_well],
                         d_plate[d_well],
                         blow_out=True,
                         blowout_location='trash',
                         disposal_volume=5)

    if p300.has_tip:
        p300.drop_tip()
    if p20.has_tip:
        p20.drop_tip()

    protocol.set_rail_lights(False)

    protocol.home()
    protocol.cleanup()


def run(protocol: protocol_api.ProtocolContext):
    #try:
    make_transfer(protocol)
    #except Exception as e:
    #    protocol.comment(f'Error during execution')
    #    protocol.comment(str(e))
    #    protocol.comment(f'Will cleanup and abort run')
    #    for pipette in protocol.loaded_instruments.values():
    #        if pipette.has_tip:
    #            pipette.drop_tip()
    #    protocol.home()
    #    protocol.cleanup()

#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# layout (either 96 or 384)
LAYOUT = 384
# in ul, depending on the volume a different pipette is used
TRANSFER_VOLUME = 15
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 picking a small volume from 1.5mL, then use 10 mm
P20_SOURCE_CLEARANCE = 10
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 dropping a small volume into 1.5mL, then use 10 mm
P20_DESTINATION_CLEARANCE = 10
# NOTE: injected data file
# should be a csv file with no header and 4 fields
# 1. source row (A to H)
# 2. source column (1 to 12)
# 3. destination row (A to H)
# 4. destination column (1 to 12)
###############################################################################


import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'Plate randomizer',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }


HERE_INJECT_DATA

def read_transfers(protocol):
    # dictionary to keep track of transfers
    transfers = {}

    for csv_row in DATA:
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
    transfers = read_transfers(protocol)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # left: p300 single
    # right: p20 single

    # 1 to 4: tips appropriate to the transfer volume
    # (if 96 well plate, only the first position is filled)
    # 5. 96 deep-well plate (source)
    # 6. 96 deep-well plate (target)

    # tips
    if LAYOUT == 96:
        positions = (1,)
    elif LAYOUT == 384:
        positions = range(1, 5)

    tips = []
    for position in positions:
        if TRANSFER_VOLUME > 20:
            tip = protocol.load_labware('opentrons_96_tiprack_300ul', position)
        else:
            tip = protocol.load_labware('opentrons_96_tiprack_20ul', position)
        tips.append(tip)

    # pipette arms
    if TRANSFER_VOLUME > 20:
        # 1 - 300 uL
        pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=tips)
    else:
        # 1 - 20 uL
        pipette = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    if LAYOUT == 96:
        labware = 'vwr_96_wellplate_2000ul'
    elif LAYOUT == 384:
        labware = 'corning_384_wellplate_240ul'

    # source plate
    s_plate = protocol.load_labware(labware, 5)

    # destination plate
    d_plate = protocol.load_labware(labware, 6)

    if TRANSFER_VOLUME > 20:
        pipette.well_bottom_clearance.aspirate = 2
        pipette.well_bottom_clearance.dispense = 1
    else:
        pipette.well_bottom_clearance.aspirate = P20_SOURCE_CLEARANCE
        pipette.well_bottom_clearance.dispense = P20_DESTINATION_CLEARANCE

    # do the actual transfers
    for s_well, d_well in transfers.items():
        pipette.transfer(TRANSFER_VOLUME,
                         s_plate[s_well],
                         d_plate[d_well],
                         blow_out=True,
                         blowout_location='trash',
                         disposal_volume=5)

    if pipette.has_tip:
        pipette.drop_tip()

    protocol.home()
    protocol.cleanup()

    protocol.set_rail_lights(False)


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

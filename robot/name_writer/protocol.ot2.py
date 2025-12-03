#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# in ul, depending on the volume a different pipette is used
TRANSFER_VOLUME = 60
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 picking a small volume from 1.5mL, then use 10 mm
P20_SOURCE_CLEARANCE = 10
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 dropping a small volume into 1.5mL, then use 10 mm
P20_DESTINATION_CLEARANCE = 10
# NOTE: injected data file
# should be a csv file with no header and 3 fields
# 1. destination row (A to H)
# 2. destination column (1 to 12)
# 3. plate position (1 or 7)
###############################################################################


import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'Name writer',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }


HERE_INJECT_DATA

def read_transfers(protocol):
    # dictionary to keep track of transfers
    transfers = {}

    for csv_row in DATA:
        csv_row = csv_row.rstrip().split('\t')
        d_row, d_column, d_plate = csv_row[:3]
        d_plate = int(d_plate)
        d_column = int(d_column)
        d_well = f'{d_row}{d_column}'

        transfers[d_plate] = transfers.get(d_plate, [])
        transfers[d_plate].append(d_well)

    protocol.comment(f'Will perfom tranfers over {len(transfers)}')
    return transfers


def make_transfer(protocol):
    transfers = read_transfers(protocol)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # left: p300 single
    # right: p20 single

    # 1: tips
    # 5. 96 deep-well plate 1
    # 6. 96 deep-well plate 2

    positions = (5,)

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

    labware = 'corning_96_wellplate_360ul_flat'
    sourceware = 'marcolifesciences12x6ml_12_reservoir_6000ul'

    # source plate
    s_plate = protocol.load_labware(sourceware, 4)

    plate1 = protocol.load_labware(labware, 1)
    plate7 = protocol.load_labware(labware, 7)
    
    plates = {1: plate1,
              7: plate7}


    if TRANSFER_VOLUME > 20:
        pipette.well_bottom_clearance.aspirate = 2
        pipette.well_bottom_clearance.dispense = 1
    else:
        pipette.well_bottom_clearance.aspirate = P20_SOURCE_CLEARANCE
        pipette.well_bottom_clearance.dispense = P20_DESTINATION_CLEARANCE

    # do the actual transfers
    for plate_number, d_wells in transfers.items():
        d_plate = plates[plate_number]

        pipette.distribute(TRANSFER_VOLUME,
                           s_plate.wells_by_name()['A1'],
                           [d_plate.wells_by_name()[d_well] for d_well in d_wells],
                           blow_out=True,
                           blowout_location='source well')

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

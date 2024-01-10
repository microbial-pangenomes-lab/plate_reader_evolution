#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# in ul, depending on the volume a different pipette is used
TRANSFER_VOLUME = 1
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 picking a small volume from 1.5mL, then use 10 mm
P20_SOURCE_CLEARANCE = 3
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 dropping a small volume into 1.5mL, then use 10 mm
P20_DESTINATION_CLEARANCE = 10
# NOTE: injected data file
# should be a csv file with no header and 5 fields
# 1. source plate (position in OT-2 deck, so 1 to 11)
# 2. source row (A to H)
# 3. source column (1 to 12)
# 4. destination row (A to H)
# 5. destination column (1 to 12)
###############################################################################


import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'Strain picker',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }


HERE_INJECT_DATA

def read_transfers(protocol):
    # dictionary to keep track of transfers
    transfers = {}

    for csv_row in DATA:
        csv_row = csv_row.rstrip().split('\t')
        s_location, s_row, s_column, d_row, d_column = csv_row[:5]
        s_location = int(s_location)
        s_column = int(s_column)
        d_column = int(d_column)
        s_well = f'{s_row}{s_column}'
        d_well = f'{d_row}{d_column}'

        transfers[s_location] = transfers.get(s_location, {})
        transfers[s_location][s_well] = d_well

    protocol.comment(f'Will perfom {len(transfers)} tranfers')
    return transfers


def make_transfer(protocol):
    transfers = read_transfers(protocol)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # right: p20 single

    # 1, 2, 3, 10: p20 tips
    # 4 to 9. 384 well plates (sources)
    # 11. 384 deep-well plate (target)

    # tips
    tips = []
    for position in (1, 2, 3, 10):
        tip = protocol.load_labware('opentrons_96_tiprack_20ul', position)
        tips.append(tip)

    # pipette arms
    # 1 - 20 uL
    pipette = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    # source plate(s)
    d_s_plates = {}
    for s_location in transfers:
        s_plate = protocol.load_labware('corning_384_wellplate_112ul_flat', s_location)
        d_s_plates[s_location] = s_plate

    # destination plate
    d_plate = protocol.load_labware('corning_384_wellplate_240ul', 11)

    pipette.well_bottom_clearance.aspirate = P20_SOURCE_CLEARANCE
    pipette.well_bottom_clearance.dispense = P20_DESTINATION_CLEARANCE

    # do the actual transfers
    for s_location in transfers:
        s_plate = d_s_plates[s_location]
        for s_well, d_well in transfers[s_location].items():
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

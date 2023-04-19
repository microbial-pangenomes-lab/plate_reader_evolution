#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# target OD, assuming a starting OD of 1
TARGET_OD = 0.0001
# volume of the intermediate dilution plate
# in uL
DILUTION_VOLUME_1 = 150
# volume of the  final plates
# in uL
DILUTION_VOLUME_2 = 60
# when using 384 plate the 300 ul tips need to be higher
# to avoid overflows (in mm)
P300_CLEARANCE = 15
###############################################################################

import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'OD equalizer',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }

HERE_INJECT_DATA

def read_transfers(protocol):
    # dictionary to keep track of transfers
    dilution_1 = {}

    od_1 =  TARGET_OD * 10
    for row, column, od in DATA:
        column = int(column)
        od = float(od)
        well = f'{row}{column}'

        v1 = od_1 * DILUTION_VOLUME_1 / od
        if v1 < 1:
            raise ValueError(f'First dilution for {well} is below 1uL ({v1})')
        if v1 > 300:
            raise ValueError(f'First dilution for {well} is above 300uL ({v1})')
        dilution_1[well] = v1, DILUTION_VOLUME_1 - v1

    v2 = TARGET_OD * DILUTION_VOLUME_2 / od_1
    if v2 < 1:
        raise ValueError(f'Second dilution (for all wells) is below 2uL ({v2})')
    if v2 > 300:
        raise ValueError(f'Second dilution (for all wells) is above 300uL ({v2})')

    return dilution_1, v2


def od_equalizer(protocol):
    transfers, transfer_2 = read_transfers(protocol)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # right: p20 single
    # left: p300 single

    # 384 well layout
    # 3, 2, 9, 8: 20uL tips
    # 1, 7: 300uL tips
    # 4: media reservoir
    # 6: source deep 384 plate
    # 5: intermediate deep 384 plate

    # tips
    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', i)
              for i in [3, 2, 9, 8]]
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', i)
               for i in [1, 7]]

    media_position = 4
    source_position = 6
    intermediate_position = 5
    plate_labware = 'corning_384_wellplate_240ul'

    source_plate = protocol.load_labware(plate_labware, source_position)
    intermediate_plate = protocol.load_labware(plate_labware, intermediate_position)

    # 1 - 20 uL
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=tips20)
    # 20 - 300 uL
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)
    p300.well_bottom_clearance.dispense = P300_CLEARANCE

    # media reservoir
    media_plate = protocol.load_labware('brand_1_reservoir_220000ul', media_position)

    # do the actual transfers

    # 1. media
    v300 = [media_volume for well, (bug_volume, media_volume) in transfers.items()
            if media_volume > 20]
    d300 = [intermediate_plate.wells_by_name()[well]
            for well, (bug_volume, media_volume) in transfers.items()
            if media_volume > 20]
    v20 = [media_volume for well, (bug_volume, media_volume) in transfers.items()
           if media_volume <= 20]
    d20 = [intermediate_plate.wells_by_name()[well]
           for well, (bug_volume, media_volume) in transfers.items()
           if media_volume <= 20]
    for vol, dest, pipette in zip([v300, v20],
                                 [d300, d20],
                                 [p300, p20]):
        if len(vol) > 0:
            pipette.distribute(vol,
                               media_plate.wells_by_name()['A1'],
                               dest,
                               blow_out=True,
                               blowout_location='source well')

    # 2. bug
    for well, (bug_volume, media_volume) in transfers.items():
        if bug_volume > 20:
            # should never happen, really
            pipette = p300
        else:
            pipette = p20
        pipette.transfer(bug_volume,
                         source_plate.wells_by_name()[well],
                         intermediate_plate.wells_by_name()[well])

    if p20.has_tip:
        p20.drop_tip()

    if p300.has_tip:
        p300.drop_tip()

    protocol.home()
    protocol.cleanup()

    protocol.set_rail_lights(False)


def run(protocol: protocol_api.ProtocolContext):
    #try:
    od_equalizer(protocol)
    #except Exception as e:
    #    protocol.comment(f'Error during execution')
    #    protocol.comment(str(e))
    #    protocol.comment(f'Will cleanup and abort run')
    #    for pipette in protocol.loaded_instruments.values():
    #        if pipette.has_tip:
    #            pipette.drop_tip()
    #    protocol.home()
    #    protocol.cleanup()

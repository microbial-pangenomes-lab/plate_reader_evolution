#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# in ul
TRANSFER_VOLUME = 6
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 picking a small volume from 1.5mL, then use 10 mm
P20_SOURCE_CLEARANCE = 10
# in mm, influences the height at which the tip is placed
# depends on how much volume the source well has
# if using a p20 dropping a small volume into 1.5mL, then use 10 mm
P20_DESTINATION_CLEARANCE = 3
###############################################################################


import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'MIC strain distributor',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }


def make_transfer(protocol):
    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # right: p20 single

    # 1, 2, 7, 8: p20 tips
    # 4. 384 well plate (source)
    # 5. 384 deep-well plate (target)

    # tips
    tips = []
    for position in (10,):
        tip = protocol.load_labware('opentrons_96_tiprack_20ul', position)
        tips.append(tip)

    # pipette arms
    # 1 - 20 uL
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tips)

    # source plate
    # s_plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 7)
    s_plate = protocol.load_labware('corning_384_wellplate_240ul', 7)

    # destination plates
    d_plates = []
    for position in range(1, 7):
        d_plate = protocol.load_labware('corning_384_wellplate_112ul_flat', position)
        d_plates.append(d_plate)

    pipette.well_bottom_clearance.aspirate = P20_SOURCE_CLEARANCE
    pipette.well_bottom_clearance.dispense = P20_DESTINATION_CLEARANCE

    # do the actual transfers
    columns = range(2, 24)
    for i, column in enumerate(columns):
        for d_plate in d_plates:
            pipette.distribute(TRANSFER_VOLUME,
                               s_plate.wells_by_name()[f'A{column}'],
                               [d_plate.wells_by_name()[f'A{x}']
                                for x in list(range(2, 24))[::-1]],
                               blow_out=True,
                               blowout_location='trash')
            pipette.distribute(TRANSFER_VOLUME,
                               s_plate.wells_by_name()[f'B{column}'],
                               [d_plate.wells_by_name()[f'B{x}']
                                for x in list(range(2, 24))[::-1]],
                               blow_out=True,
                               blowout_location='trash')

        protocol.comment('')
        protocol.comment(f'Finished dispensing column {column} ({i+1}/{len(columns)})')
        if column != 23:
            protocol.comment('')
            protocol.comment('Please introduce a new set of plates and a new tip box')
            protocol.comment('')
            protocol.pause('When done click Resume')
            protocol.comment('')
            pipette.reset_tipracks()

    protocol.comment('')
    protocol.comment('Goodbye, come again')

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

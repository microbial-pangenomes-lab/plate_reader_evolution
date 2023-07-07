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
# modifier for the dispense flow rate
# a value of 1 means that the rate is as the default
# a value of 0.5 half of the default
# a value of 2 double of the default
DISPENSE_RATE_MODIFIER = 0.5
# tip box position on deck
TIPS_POSITION = 10
# source plate position on deck
SOURCE_PLATE_POSITION = 7
# destination plates positions on deck
# separate each number with a comma
DESTINATION_PLATE_POSITIONS = [1, 2, 3, 4, 5, 6]
# change to "True" to do one transfer for each column
# default is to use the "distribute" command that can do
# multiple columns in one go
USE_TRANSFER = False
# change to "True" to do the transfer for the first column only
# for testing purposes
TEST_RUN = False
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

    # tips
    tips = []
    for position in (TIPS_POSITION,):
        tip = protocol.load_labware('opentrons_96_tiprack_20ul', position)
        tips.append(tip)

    # pipette arms
    # 1 - 20 uL
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tips)
    pipette.flow_rate.dispense = pipette.flow_rate.dispense * DISPENSE_RATE_MODIFIER

    # source plate
    #s_plate = protocol.load_labware('corning_384_wellplate_112ul_flat', SOURCE_PLATE_POSITION)
    s_plate = protocol.load_labware('corning_384_wellplate_240ul', SOURCE_PLATE_POSITION)

    # destination plates
    d_plates = []
    for position in DESTINATION_PLATE_POSITIONS:
        d_plate = protocol.load_labware('corning_384_wellplate_112ul_flat', position)
        d_plates.append(d_plate)

    pipette.well_bottom_clearance.aspirate = P20_SOURCE_CLEARANCE
    pipette.well_bottom_clearance.dispense = P20_DESTINATION_CLEARANCE

    # do the actual transfers
    if TEST_RUN:
        columns = [2, ]
        d_plates = [d_plates[0], ]
    else:
        columns = range(2, 24)
    for i, column in enumerate(columns):
        for d_plate in d_plates:
            if USE_TRANSFER:
                pipette.pick_up_tip()
                for x in list(range(2, 24))[::-1]:
                    pipette.aspirate(TRANSFER_VOLUME,
                                     s_plate.wells_by_name()[f'A{column}'])
                    pipette.dispense(TRANSFER_VOLUME,
                                     d_plate.wells_by_name()[f'A{x}'])
                pipette.drop_tip()
                pipette.pick_up_tip()
                for x in list(range(2, 24))[::-1]:
                    pipette.aspirate(TRANSFER_VOLUME,
                                     s_plate.wells_by_name()[f'B{column}'])
                    pipette.dispense(TRANSFER_VOLUME,
                                     d_plate.wells_by_name()[f'B{x}'])
                pipette.drop_tip()
            else:
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
        if column != columns[-1]:
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

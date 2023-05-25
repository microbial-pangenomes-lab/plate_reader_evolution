#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# how many plates to do in total
# computed as follows for each drug:
# each plate can do 16 MIC tests
# there are ~384 strains to test
# in duplicate
PLATES = 48
# by how much the drug gets diluted at each step
DILUTION_FACTOR = 1.4
# in uL
# assumed to be 1/2 of final volume for the MIC
TARGET_VOLUME = 30
# in uL, how much volume each column
# can hold, useful to tell the user how many
# columns need to be filled
STOCK_COLUMN_VOLUME = 220000
STOCK_COLUMN_OVERHEAD_VOLUME = 5000
# same for water, in this case it's a single column
WATER_COLUMN_VOLUME = 220000
WATER_COLUMN_OVERHEAD_VOLUME = 5000
# when using 384 plate the 300 ul tips need to be higher
# to avoid overflows (in mm)
P300_CLEARANCE_MEDIA = 15
P300_CLEARANCE_DRUG = 15
###############################################################################

import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'MIC plate maker',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }


def check_column(used_volume,
                 column_volume, column_overhead_volume,
                 current_pointer,
                 plate, current_column, maximum_columns=1):
    if used_volume > column_volume - column_overhead_volume:
        used_volume = 0
        current_column += 1
        if current_column > maximum_columns:
            protocol.comment('WARNING: reservoir is estimated to have ran out')
            current_column = 1
        current_pointer = plate[f'A{current_column}']
    return used_volume, current_column, current_pointer


def check_volumes(protocol,
                  dilution_factor,
                  target_volume,
                  plates,
                  stock_column_volume, stock_column_overhead_volume,
                  water_column_volume, water_column_overhead_volume):
    # transfer counter
    transfers = 0

    # counter to make sure there is enough stock
    required_stock_volume = 0
    # and solvent
    required_solvent_volume = 0

    # volume before passing over to the next column
    # derived this by reverse-engineering https://www.aatbio.com/tools/serial-dilution
    volume_before = target_volume / (1 - (1 / dilution_factor))

    # needs to be added in the first column only
    volume = volume_before - target_volume
    # safety check on volume
    if volume < 1:
        raise ValueError(f'Target volume '
                          'is below 1uL')

    # for each column
    solvent_volume = target_volume

    for plate in range(plates):
        for row in 'ABCDEFGHIJKLMNOP':
            # volume of stock to use for this plate

            # keep track of how much stock we have consumed
            # so far
            required_stock_volume += volume
            for column in range(1, 23):
                # and solvent
                required_solvent_volume += solvent_volume
                transfers += 1

            # last two columns just solvent
            required_solvent_volume += target_volume * 2
            transfers += 2

    # check how many columns we need
    n_columns = required_stock_volume // (stock_column_volume - stock_column_overhead_volume)
    n_columns += 1
    n_columns = int(n_columns)
    # total stock including overhead
    total_stock = n_columns * stock_column_volume

    # check how many columns we need (solvent)
    n_columns_solvent = required_solvent_volume // (water_column_volume - water_column_overhead_volume)
    n_columns_solvent += 1
    n_columns_solvent = int(n_columns_solvent)
    # total solvent including overhead
    total_solvent = n_columns_solvent * water_column_volume

    protocol.comment(f'Will perfom {transfers} tranfers over {plates} plates')
    protocol.comment(f'Will use {required_stock_volume} uL of stock solution')
    protocol.comment(f'Will use {required_solvent_volume} uL of media')
    protocol.comment('\n')

    protocol.comment(f'Please fill with stock the single-well reservoir')
    protocol.comment(f'Each column should have {stock_column_volume+stock_column_overhead_volume} uL of stock')
    protocol.comment(f'Total stock volume including overhead will be {total_stock}')

    protocol.comment('\n')
    protocol.comment(f'Please fill with media the single-well reservoir')
    protocol.comment(f'Each column should have at least {required_solvent_volume+water_column_overhead_volume} uL of media')
    protocol.comment(f'Total media volume including overhead will be {total_solvent}')
    if n_columns_solvent > 1:
        protocol.comment(f'More than 1 refill required for media (estimated: {n_columns_solvent} refills)')
    protocol.comment('\n')

    protocol.pause('When done click Resume')

    return volume, solvent_volume


def make_mic(protocol):
    volume, water_volume = check_volumes(
                  protocol, DILUTION_FACTOR,
                  TARGET_VOLUME, PLATES,
                  STOCK_COLUMN_VOLUME,
                  STOCK_COLUMN_OVERHEAD_VOLUME,
                  WATER_COLUMN_VOLUME,
                  WATER_COLUMN_OVERHEAD_VOLUME)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # right: p300 multiple

    # 384 well layout
    # 7, 9: 30uL tips
    # 4: stock reservoir
    # 11, 8, 5, 2, 1, 3: 384 plates
    # 6: water reservoir

    # tips
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', i)
               for i in [7, 9, 10]]

    stock_position = 4
    water_position = 6
    plate_labware = 'corning_384_wellplate_112ul_flat'

    plate_positions = [11, 8, 5, 2, 1, 3]
    finished_plates = 0

    # 1 - 20 uL
    p300 = protocol.load_instrument('p300_multi_gen2', 'right', tip_racks=tips300)
    p300.well_bottom_clearance.dispense = P300_CLEARANCE_MEDIA

    # stock reservoir
    stock_plate = protocol.load_labware('brand_1_reservoir_220000ul', stock_position)

    # A1 to A12
    used_stock = 0
    current_column = 1
    stock = stock_plate[f'A{current_column}']

    # water reservoir
    water_plate = protocol.load_labware('brand_1_reservoir_220000ul', water_position)

    # A1 to A12
    used_water = 0
    current_column_water = 1
    water = water_plate[f'A{current_column_water}']

    # do the actual transfers

    # 1. water (across all plates)
    # 2. drug (across all plates)

    # destination plates
    plates = []
    for plate_pos in plate_positions:
        plate = protocol.load_labware(plate_labware, plate_pos)
        plates.append(plate)

    while finished_plates < PLATES:
        _plates = [x for x in plates]
        if finished_plates + len(_plates) > PLATES:
            _plates = _plates[:PLATES - finished_plates]

        # water
        p300.pick_up_tip()
        _water = 0
        for plate in _plates:
            for row in ('A', 'B'):
                p300.aspirate(TARGET_VOLUME, water)
                p300.dispense(TARGET_VOLUME, plate.wells_by_name()[f'{row}24'])
                p300.aspirate(TARGET_VOLUME, water)
                p300.dispense(TARGET_VOLUME, plate.wells_by_name()[f'{row}23'])
                _water += TARGET_VOLUME * 2
                _water, current_column_water, water = check_column(_water,
                              WATER_COLUMN_VOLUME, WATER_COLUMN_OVERHEAD_VOLUME,
                              water, water_plate, current_column_water)
                for column in range(2, 23):
                    p300.aspirate(water_volume, water)
                    p300.dispense(water_volume, plate.wells_by_name()['%s%d' % (row, column)])
                    _water += water_volume
                    _water, current_column_water, water = check_column(_water,
                                  WATER_COLUMN_VOLUME, WATER_COLUMN_OVERHEAD_VOLUME,
                                  water, water_plate, current_column_water)
                p300.aspirate(TARGET_VOLUME, water)
                p300.dispense(TARGET_VOLUME, plate.wells_by_name()[f'{row}1'])
                _water += TARGET_VOLUME
                _water, current_column_water, water = check_column(_water,
                              WATER_COLUMN_VOLUME, WATER_COLUMN_OVERHEAD_VOLUME,
                              water, water_plate, current_column_water)
        p300.drop_tip()

        # drug
        p300.well_bottom_clearance.dispense = P300_CLEARANCE_DRUG
        p300.pick_up_tip()
        _drug = 0
        for plate in _plates:
            for row in ('A', 'B'):
                p300.aspirate(volume, stock)
                p300.dispense(volume, plate.wells_by_name()[f'{row}2'])
                _drug += volume
                _drug, current_column, stock = check_column(_drug,
                              STOCK_COLUMN_VOLUME, STOCK_COLUMN_OVERHEAD_VOLUME,
                              stock, stock_plate, current_column)
                previous_column = 2
                for column in range(3, 23):
                    p300.aspirate(volume, plate.wells_by_name()['%s%d' % (row, previous_column)])
                    p300.dispense(volume, plate.wells_by_name()['%s%d' % (row, column)])
                    previous_column = column
                # get rid of overhead drug + water in column 1
                p300.aspirate(volume, plate.wells_by_name()[f'{row}22'])
                p300.blow_out(p300.trash_container)
        # just drop it in the trash
        p300.drop_tip()

        finished_plates += len(_plates)

        if finished_plates < PLATES:
            protocol.comment('Please load the next batch of 6 plates')
            protocol.comment('Please refill the media plate as needed')
            protocol.pause('When done click Resume')


    if p300.has_tip:
        p300.drop_tip()

    protocol.home()
    protocol.cleanup()

    protocol.set_rail_lights(False)


def run(protocol: protocol_api.ProtocolContext):
    #try:
    make_mic(protocol)
    #except Exception as e:
    #    protocol.comment(f'Error during execution')
    #    protocol.comment(str(e))
    #    protocol.comment(f'Will cleanup and abort run')
    #    for pipette in protocol.loaded_instruments.values():
    #        if pipette.has_tip:
    #            pipette.drop_tip()
    #    protocol.home()
    #    protocol.cleanup()

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
# doesn't matter which units (uM or ug/mL)
# as long as it is the same as the one used
# in all the other variables
# should have the same dilution factor
# as in the plate
# so if dilutio factor is 2
# the stock concentration is double that
# of the firwst well (i.e. 40)
STOCK_CONC = 80
# by how much the drug gets diluted at each step
DILUTION_FACTOR = 1.4
# in uL
# assumed to be 1/10th of final volume for the MIC
TARGET_VOLUME = 15
# in uL, how much volume each column
# can hold, useful to tell the user how many
# columns need to be filled
STOCK_COLUMN_VOLUME = 5000
STOCK_COLUMN_OVERHEAD_VOLUME = 250
# same for water, in this case it's a single column
WATER_COLUMN_VOLUME = 220000
WATER_COLUMN_OVERHEAD_VOLUME = 5000
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
                 plate, current_column):
    if used_volume > column_volume - column_overhead_volume:
        used_volume = 0
        current_column += 1
        if current_column > maximum_columns:
            protocol.pause('WARNING: reservoir is estimated to have ran out, please refill and press resume')
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

    # needs to be added in the first column only
    volume = target_volume * (dilution_factor - 1)
    # safety check on volume
    if volume < 1:
        raise ValueError(f'Target volume '
                            'is below 1uL')

    # for each column
    solvent_volume = (dilution_factor - 1) * target_volume
    solvent_volume += target_volume
    solvent_volume -= volume

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
    if n_columns > 12:
        raise ValueError(f'More than 12 columns required for stock ({n_columns})')
    # total stock including overhead
    total_stock = n_columns * stock_column_volume

    # check how many columns we need (solvent)
    n_columns_solvent = required_solvent_volume // (water_column_volume - water_column_overhead_volume)
    n_columns_solvent += 1
    n_columns_solvent = int(n_columns_solvent)
    if n_columns_solvent > 1:
        protocol.comment(f'More than 1 refill required for solvent (estimated: {n_columns_solvent} refills)')
    # total solvent including overhead
    total_solvent = n_columns_solvent * water_column_volume

    protocol.comment(f'Will perfom {transfers} tranfers over {plates} plates')
    protocol.comment(f'Will use {required_stock_volume} uL of stock solution')
    protocol.comment(f'Will use {required_solvent_volume} uL of water')
    protocol.comment('\n')

    protocol.comment(f'Please fill with stock {n_columns} column(s) in 12-column reservoir in place 3')
    protocol.comment(f'Each column should have {stock_column_volume} uL of stock')
    protocol.comment(f'Total stock volume including overhead will be {total_stock}')

    protocol.comment('\n')
    protocol.comment(f'Please fill with water the single-well reservoir in place 5')
    protocol.comment(f'Each column should have at least {required_solvent_volume+water_column_overhead_volume} uL of water')
    protocol.comment(f'Total water volume including overhead will be {total_solvent}')
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

    # right: p20 multiple

    # 384 well layout
    # 7, 9: 20uL tips
    # 4: stock reservoir
    # 11, 8, 5, 2, 7, 9: 384 plates
    # 6: water reservoir

    # tips
    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', i)
              for i in [4, 6]]

    stock_position = 4
    water_position = 9
    plate_labware = 'corning_384_wellplate_240ul'

    plate_positions = [11, 8, 5, 2, 7, 9]
    loaded_plates = 0

    # 1 - 20 uL
    p20 = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)

    # stock reservoir
    stock_plate = protocol.load_labware('marcolifesciences12x6ml_12_reservoir_6000ul', stock_position)

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

    while loaded_plates < PLATES:
        # destination plates
        plates = []
        for plate_pos in plate_positions:
            plate = protocol.load_labware(plate_labware, plate_pos)
            plates.append(plate)
            loaded_plates += 1
            # we are done with the plates we intended to do
            if loaded_plates == PLATES:
                break

        # water
        p20.pick_up_tip()
        _water = 0
        for plate in plates:
            p20.aspirate(target_volume, water)
            p20.dispense(target_volume, plate.wells_by_name()['A24'])
            p20.aspirate(target_volume, water)
            p20.dispense(target_volume, plate.wells_by_name()['A23'])
            _water += target_volume * 2
            _water, current_column_water, water = check_column(_water,
                          WATER_COLUMN_VOLUME, WATER_COLUMN_OVERHEAD_VOLUME,
                          water, water_plate, current_column_water)
            for column in range(1, 23):
                p20.aspirate(water_volume, water)
                p20.dispense(water_volume, plate.wells_by_name()['A%02d' % column])
                _water += water_volume
                _water, current_column_water, water = check_column(_water,
                              WATER_COLUMN_VOLUME, WATER_COLUMN_OVERHEAD_VOLUME,
                              water, water_plate, current_column_water)
        p20.drop_tip()

        # drug
        p20.pick_up_tip()
        _drug = 0
        for plate in plates:
            p20.aspirate(volume, stock)
            p20.dispense(volume, plate.wells_by_name()['A1'])
            _drug += volume
            _drug, current_column, stock = check_column(_drug,
                          STOCK_COLUMN_VOLUME, STOCK_COLUMN_OVERHEAD_VOLUME,
                          stock, stock_plate, current_column)
            previous_column = 1
            for column in range(2, 23):
                p20.aspirate(volume, plate.wells_by_name()['A%02d' % previous_column])
                p20.dispense(volume, plate.wells_by_name()['A%02d' % column])
                previous_column = column
        # get rid of overhead drug + water in column 1
        p20.aspirate(volume, plate.wells_by_name()['A22'])
        # just drop it in the trash
        p20.drop_tip()

        protocol.comment('Please load the next batch of 6 plates')
        protocol.comment('Please refill the water plate as needed')
        protocol.pause('When done click Resume')

    if p20.has_tip:
        p20.drop_tip()

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

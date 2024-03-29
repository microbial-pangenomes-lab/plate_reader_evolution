#!/usr/bin/env python
# coding: utf-8


###############################################################################
# PARAMETERS
#
# change these values to change the protocol behavior
#
###############################################################################
# which deep-well plate to use
LAYOUT = 384
# doesn't matter which units (uM or ug/mL)
# as long as it is the same as the one used in
# the input csv file
STOCK_CONC = 80
# in uL, how much volume each column
# can hold, useful to tell the user how many
# columns need to be filled
STOCK_COLUMN_VOLUME = 5000
STOCK_COLUMN_OVERHEAD_VOLUME = 250
# same for water, in this case it's a single column
WATER_COLUMN_VOLUME = 220000
WATER_COLUMN_OVERHEAD_VOLUME = 5000
# when using 384 plate the 300 ul tips need to be higher
# to avoid overflows (in mm)
P300_CLEARANCE = 15
if LAYOUT == 96:
    # derived as follows:
    # final: 20uL in each well
    # times 2 to allow for serial dilution to subsequent plates
    # times 1 to allow for one passages at the same concentration
    # times 6 to allow up to 6 replicates
    # = 240uL, rounded to 270 for safety
    FINAL_VOLUME = 270
    # maximum volume for the deep-well plate
    MAXIMUM_VOLUME = 1950
elif LAYOUT == 384:
    # derived as follows:
    # final: 15uL in each well
    # times 2 to allow for serial dilution to subsequent plates
    # times 1 to allow for one passages at the same concentration
    # times 6 to allow up to 6 replicates
    # = 180uL, rounded to 200 for safety
    FINAL_VOLUME = 200
    # maximum volume for the deep-well plate
    MAXIMUM_VOLUME = 230
# NOTE: about the injected data file:
# should be a csv file with no header and 3 fields
# 1. row (A to H)
# 2. column (1 to 12)
# 3. desired concentration (same units as the STOCK_CONC above)
###############################################################################


import sys

from opentrons import protocol_api

metadata = {
    'protocolName': 'Drug ramp maker',
    'apiLevel': '2.11',
    'author': 'M. Galardini'
    }

HERE_INJECT_DATA

def read_transfers(protocol,
                   stock_conc, final_volume,
                   stock_column_volume, stock_column_overhead_volume,
                   water_column_volume, water_column_overhead_volume,
                   maximum_volume):
    # dictionary to keep track of transfers
    transfers = {}

    # counter to make sure there is enough stock
    required_stock_volume = 0
    # and solvent
    required_solvent_volume = 0

    for csv_row in DATA:
        csv_row = csv_row.split('\t')
        row, column, conc = csv_row[:3]
        column = int(column)
        well = f'{row}{column}'
        conc = float(conc)

        # volume of stock to use for this transfer
        volume = (conc * final_volume) / stock_conc

        # keep track of how much stock we have consumed
        # so far
        required_stock_volume += volume
        # and solvent
        required_solvent_volume += final_volume - volume

        # safety check 1 (concentration)
        if conc > stock_conc:
            raise ValueError(f'Target concentration for well {well} '
                                'is higher than the provided stock')

        # safety check 2 (volume)
        if volume < 1:
            raise ValueError(f'Target volume for well {well} '
                                'is below 1uL')

        transfers[well] = volume

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
        raise ValueError(f'More than 1 plate required for solvent ({n_columns})')
    # total solvent including overhead
    total_solvent = n_columns_solvent * water_column_volume

    # spell out transfers for double checking
    #protocol.comment('Planned transfers:')
    #for well in sorted(transfers, key=lambda x: (x[0], int(x[1:]))):
    #    protocol.comment(f'Well {well}: {transfers[well]} uL drug, {final_volume - transfers[well]} uL water')

    #protocol.comment('\n')
    protocol.comment(f'Will perfom {len(transfers)} tranfers')
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

    return transfers


def make_ramp(protocol):
    transfers = read_transfers(protocol,
                               STOCK_CONC,
                               FINAL_VOLUME,
                               STOCK_COLUMN_VOLUME,
                               STOCK_COLUMN_OVERHEAD_VOLUME,
                               WATER_COLUMN_VOLUME,
                               WATER_COLUMN_OVERHEAD_VOLUME,
                               MAXIMUM_VOLUME)

    protocol.set_rail_lights(True)
    protocol.home()

    # load labware and pipette arms

    # left: p300 single
    # right: p20 single

    if LAYOUT == 96:
        # 96 well layout
        # 1. 300uL tips
        # 2. 20uL tips
        # 4. stock reservoir
        # 5. 96 deep-well plate
        # 6. water reservoir

        # tips
        tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', 1), ]
        tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', 2), ]

        stock_position = 4
        plate_position = 5
        water_position = 6
        plate_labware = 'vwr_96_wellplate_2000ul'

    elif LAYOUT == 384:
        # 384 well layout
        # 1, 2, 4, 5: 300uL tips
        # 7, 8, 10, 11: 20uL tips
        # 3: stock reservoir
        # 6: 384 deep-well plate
        # 9: water reservoir

        # tips
        tips300 =[protocol.load_labware('opentrons_96_tiprack_300ul', i)
                 for i in [1, 2, 4, 5]]
        tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', i)
                 for i in [7, 8, 10, 11]]

        stock_position = 3
        plate_position = 6
        water_position = 9
        plate_labware = 'corning_384_wellplate_240ul'

    # pipette arms
    # 20 - 300 uL
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)
    if LAYOUT == 384:
        p300.well_bottom_clearance.dispense = P300_CLEARANCE
    # 1 - 20 uL
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=tips20)

    # stock reservoir
    stock_plate = protocol.load_labware('marcolifesciences12x6ml_12_reservoir_6000ul', stock_position)

    # A1 to A12
    used_stock = 0
    current_column = 1
    stock = stock_plate[f'A{current_column}']

    # destination plate
    plate = protocol.load_labware(plate_labware, plate_position)

    # water reservoir
    water_plate = protocol.load_labware('brand_1_reservoir_220000ul', water_position)

    # A1 to A12
    used_water = 0
    current_column_water = 1
    water = water_plate[f'A{current_column}']

    # do the actual transfers

    # 1. water
    # 2. drug

    # the "distribute" command is used to simplify the code

    # for the water a single tip is used

    # for the drug one tip for each drug concentration bin
    # is used, just to be extra sure

    # distribute the water, using two tips at most
    large_water_transfers = {well for well, volume in transfers.items()
                            if FINAL_VOLUME - volume >= 20}
    small_water_transfers = {well for well, volume in transfers.items()
                            if FINAL_VOLUME - volume < 20}

    for pipette, current_transfers in zip([p300, p20],
                                          [large_water_transfers,
                                           small_water_transfers]):
        volumes = [FINAL_VOLUME - transfers[well] for well in current_transfers]
        destinations = [plate[well] for well in current_transfers]
        _vol = []
        _dest = []
        for vol, dest in zip(volumes, destinations):
            if vol + used_water > WATER_COLUMN_VOLUME - WATER_COLUMN_OVERHEAD_VOLUME:
                # perform the current transfers,
                # then move pointer to next column
                if len(_vol) > 0:
                    pipette.distribute(_vol,
                                       water,
                                       _dest,
                                       blow_out=True,
                                       blowout_location='source well'
                                       )
                _vol = []
                _dest = []
                used_water = 0
                current_column_water += 1
                if current_column_water > 1:
                    raise ValueError('Water reservoir ran out of columns')
                water = water_plate[f'A{current_column_water}']

            _vol.append(vol)
            _dest.append(dest)
            used_water += vol

        if len(_vol) > 0:
            # perform the last transfers, if any
            pipette.distribute(_vol,
                                water,
                                _dest,
                                blow_out=True,
                                blowout_location='source well'
                                )


    # distributre the drug
    # since we are using MIC values
    # the volumes are quantised
    # and we can expect to have a handful of them
    drug_bins = {volume for well, volume in transfers.items()}
    for bin_volume in sorted(drug_bins):
        if bin_volume >= 20:
            pipette = p300
        else:
            pipette = p20
        volumes = [transfers[well] for well, volume in transfers.items()
                   if volume == bin_volume]
        destinations = [plate[well] for well, volume in transfers.items()
                        if volume == bin_volume]
        _vol = []
        _dest = []
        for vol, dest in zip(volumes, destinations):
            if vol + used_stock > STOCK_COLUMN_VOLUME - STOCK_COLUMN_OVERHEAD_VOLUME:
                # perform the current transfers,
                # then move pointer to next column
                if len(_vol) > 0:
                    pipette.distribute(_vol,
                                       stock,
                                       _dest,
                                       blow_out=True,
                                       blowout_location='source well'
                                       )
                _vol = []
                _dest = []
                used_stock = 0
                current_column += 1
                if current_column > 12:
                    raise ValueError('Stock reservoir ran out of columns')
                stock = stock_plate[f'A{current_column}']

            _vol.append(vol)
            _dest.append(dest)
            used_stock += vol

        if len(_vol) > 0:
            # perform the last transfers, if any
            pipette.distribute(_vol,
                                stock,
                                _dest,
                                blow_out=True,
                                blowout_location='source well'
                                )

    if p300.has_tip:
        p300.drop_tip()
    if p20.has_tip:
        p20.drop_tip()

    protocol.home()
    protocol.cleanup()

    protocol.set_rail_lights(False)


def run(protocol: protocol_api.ProtocolContext):
    #try:
    make_ramp(protocol)
    #except Exception as e:
    #    protocol.comment(f'Error during execution')
    #    protocol.comment(str(e))
    #    protocol.comment(f'Will cleanup and abort run')
    #    for pipette in protocol.loaded_instruments.values():
    #        if pipette.has_tip:
    #            pipette.drop_tip()
    #    protocol.home()
    #    protocol.cleanup()

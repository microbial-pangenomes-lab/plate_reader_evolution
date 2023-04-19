OD equalizer (384 wells)
========================

This protocol does a 1:100 dilution of a 1:10 ON deep well plate.
The resulting plate can be then used to do a 1:10 dilution into
a shallow 384 plate.

Usage
-----

Edit any parameters at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

The data from the plate reader of the 1:10 ON can be then injected into
the protocol:

    python3 inject.py protocol.ot2.py od_readings.xlsx > my_protocol.py

Upload the `my_protocol.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

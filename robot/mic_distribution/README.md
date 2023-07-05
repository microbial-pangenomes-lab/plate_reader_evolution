MIC distribution
=============

This protocol distributes strains from a source 384 well plate
to a series of 384 well plates, so that each row of the destination plates contains
a single strain.

The transfers are done in batches of 6 plates, with a pause to allow
the user to change plates and add a new tip box.

Usage
-----

Edit any parameters (such as transfer volume and pipette clearance) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Upload the `protocol.ot2.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

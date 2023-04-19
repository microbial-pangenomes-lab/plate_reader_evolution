MIC maker (384 wells)
=====================

This protocol creates a large number of 384 shallow plates to run
MIC tests. The highest concentration is in column 1, column 23 and 24
have only water.
Up to 6 plates at a time are prepared.

IMPORTANT: the stock concentration should be `DILUTION_FACTOR * concentration_column_1 * 2`.
So if the dilution factor is 2 and the concentration in column 1 is 10
the stock concentration should be 40.

Usage
-----

Edit any parameters (such as final volume and stock concentration) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Upload the `protocol.ot2.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

IMPORTANT: 6 plates at a time are done, the robot will then stop and wait
for the user to replace the plates with the new ones and press resume.

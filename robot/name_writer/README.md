Name writer
===========

This protocol creates a drawing on two 96 well plates, by taking
colored liquid from a reservoir plate.

Edit any parameters (such as transfer volume and source/destination existing volumes) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Create the final protocol python file by injecting the desired randomization data:

    python3 inject.py protocol.ot2.py data/wells.tsv > my_protocol.py

Upload the `my_protocol.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

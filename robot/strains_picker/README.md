Strain picker
=============

This protocol creates a new 384  well plate following a previously decided set
of samples to pick (potentially moving them to a different destination well).

Usage
-----

Edit `data/my_samples.tsv`
with the desired source plate/row/column list. The first column indicates the position of the source
plate in the OT-2 deck.

Edit any parameters (such as transfer volume and source/destination existing volumes) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Create the final protocol python file by injecting the desired randomization data:

    python3 inject.py protocol.ot2.py data/my_samples.tsv > my_protocol.py

Upload the `my_protocol.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

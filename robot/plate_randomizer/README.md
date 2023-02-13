Plate randomizer
================

This protocol creates a new 96 or 384  well plate following a previously decided randomization
(see the `random_plate` folder for the code used and if you want to make a new randomization)

Usage
-----

Edit `data/my_randomization.tsv` and `data/my_384_randomization.py`
with the desired randomization
(you can also leave it as is if you are using the default randomization).

Edit any parameters (such as transfer volume and source/destination existing volumes) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Create the final protocol python file by injecting the desired randomization data:

    python3 inject.py protocol.ot2.py data/my_384_randomization.py > my_protocol.py

Upload the `my_protocol.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

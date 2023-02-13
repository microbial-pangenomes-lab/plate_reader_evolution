Drug ramp master maker
======================

This protocol creates a master plate to be serially diluted in order to make
a drug ramp for evolution experiments.

Usage
-----

Edit `data/my_drug.tsv` or `data/my_384_drug.tsv` with the desired
concentration for each well in
a 96 or 384 well plate. Missing wells will not be filled with either water or drug.

Edit any parameters (such as final volume and stock concentration) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Create the final protocol python file by injecting the desired drug
concentration data:

    python3 inject.py protocol.ot2.py data/my_384_drug.py > my_protocol.py

Upload the `my_protocol.py` file in the Opentrons app.
The app will indicate which labware is needed and in which position.

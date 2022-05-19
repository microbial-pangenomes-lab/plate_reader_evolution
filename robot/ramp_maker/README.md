Drug ramp master maker
======================

This protocol creates a master plate to be serially diluted in order to make
a drug ramp for evolution experiments.

Usage
-----

Edit `data/my_drug.tsv` with the desired concentration for each well in
a 96 well plate. Missing wells will not be filled with either water or drug.

Edit any parameters (such as final volume and stock concentration) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Create a zipped archive that contains the `protocol.ot2.py` file and
the `data` and `labware` folders. You can use the following command from
the terminal: `zip -r ramp_maker.zip data labware protocol.ot2.py`

Using the 4.7 version of the opentrons app, upload the `ramp_maker.zip`
file, and follow the instructions as if it was a regular protocol. You may
need to enable developer tools through the app:
`More > App > Enable developer tools > __DEV__ Enable Bundle Upload`.

The app will indicate which labware is needed and in which position.

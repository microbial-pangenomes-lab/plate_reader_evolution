Plate randomizer
================

This protocol creates a new 96 well plate following a previously decided randomization
(see the `random_plate` folder for the code used and if you want to make a new randomization)

Usage
-----

Edit `data/my_randomization.tsv` with the desired randomization
(you can also leave it as is if you are using the default randomization).

Edit any parameters (such as transfer volume and source/destination existing volumes) at the
top of the `protocol.ot2.py` file and save the changes. Do not change
anything else unless you know what/why you are doing it.

Create a zipped archive that contains the `protocol.ot2.py` file and
the `data` and `labware` folders. You can use the following command from
the terminal: `zip -r plate_randomizer.zip data labware protocol.ot2.py`

Using the 4.7 version of the opentrons app, upload the `plate_randomizer.zip`
file, and follow the instructions as if it was a regular protocol. You may
need to enable developer tools through the app:
`More > App > Enable developer tools > __DEV__ Enable Bundle Upload`.

The app will indicate which labware is needed and in which position.

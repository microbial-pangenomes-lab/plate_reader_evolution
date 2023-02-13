Plate randomizer
================

This script generates a (reproducible) "smart" randomization for a 96-well plate.
The randomization scheme is deemed to be smart because it ensures that wells on
the border of the source plate are given a random spot in the middle of the
destination plate. This in turn should reduce plate border effects.
Border wells are those in rows A and H and columns 1 and 12.

Usage
-----

Choose a random seed (the seed allows the generation of exactly the same randomization
each time the script is invoked); then type:

    python3 randomize.py --seed 100 > my_randomization.tsv

The first two columns are the source well, the last two the destination wells

To randomize a 384-well plate layout, type the following:

    python3 randomize.py --seed 100 --plate-384 > my_384_randomization.tsv

You can use the `plate_checker.ipynb` to verify that the randomization worked as expected.

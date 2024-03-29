from setuptools import setup, find_packages
from codecs import open
from os import path
import os
import re
import io


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


here = path.abspath(path.dirname(__file__))


with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='plate_reader_evolution',
    version=find_version("plate_reader_evolution/__init__.py"),
    description='Evolution experiments in microplate format',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/microbial-pangenomes-lab/plate_reader_evolution',
    author='Marco Galardini',
    author_email='galardini.marco@mh-hannover.de',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    packages=['plate_reader_evolution'],
    entry_points={
        "console_scripts": [
            'pre-parse-folder = plate_reader_evolution.parse_folder:main',
            'pre-parse-ramp = plate_reader_evolution.parse_ramp:main',
            'pre-compute-mic = plate_reader_evolution.compute_mic:main',
            'pre-compute-grate = plate_reader_evolution.compute_grate:main',
            'pre-plot-evol = plate_reader_evolution.plot_evol:main',
            'pre-plot-plate = plate_reader_evolution.plot_plate:main',
            'pre-rename-readings = plate_reader_evolution.rename_readings:main',
            ]
    },
    install_requires=['numpy',
                      'scipy',
                      'pandas',
                      'matplotlib',
                      'seaborn',]
    #test_suite="tests",
)

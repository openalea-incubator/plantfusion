import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 0):
    print('ERROR: requires at least Python 3.0 to run.')
    sys.exit(1)

setup(
    name="CN-Wheat_and_l-egume",
    version="1.0.0",
    description="",
    url="",

    packages=find_packages('wheatfusion'),
)

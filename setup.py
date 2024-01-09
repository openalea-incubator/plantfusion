import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 0):
    print('ERROR: requires at least Python 3.0 to run.')
    sys.exit(1)

setup(
    name="PlantFusion",
    version="0.0.0",
    description="API for mixed crop modelling",
    url="https://github.com/mwoussen/plantfusion",

    packages=find_packages('plantfusion'),
)

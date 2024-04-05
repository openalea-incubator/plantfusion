# Plant Fusion: API for mixed crop modelling

![](doc/img/row_planter.png)

**Authors** : Maurane Woussen, Romain Barillot, Didier Combes, Gaëtan Louarn

**Institutes** : INRAE

**Status** : Python package 

**License** : [Cecill-C](https://cecill.info/licences/Licence_CeCILL-C_V1-en.html)

**URL** : https://github.com/openalea-incubator/plantfusion

**Documentation** : https://plantfusion.readthedocs.io/en/latest/

## Overview

This package provides an API for modelling mixing crops involving several functional-structural plant models (FSPM). Its aim is to simplify the building of such simulations. 
It takes place through the [MobiDiv](https://www6.inrae.fr/mobidiv/) research project, especially in the modelling of mixed crops with wheat and alfafa. 

Currently, this API recognizes two FSPM, [CN-Wheat](https://github.com/openalea-incubator/WheatFspm) and [l-egume](https://github.com/glouarn/l-egume).

## Modules required

Main packages used for the simulations:
- [CN-Wheat](https://github.com/openalea-incubator/WheatFspm): wheat modelling
- [l-egume](https://github.com/glouarn/l-egume): legume modelling
- [CARIBU](https://github.com/openalea-incubator/caribu): light modelling through surfacic meshes*
- [PyRATP](https://github.com/mwoussen/PyRATP): light modelling through volumic meshes
- [RiRi5](https://github.com/glouarn/riri5): compact version of RATP
- [LightVegeManager](https://github.com/mwoussen/lightvegemanager): Tool for managing lighting for plant modelling
- [soil3ds](https://github.com/glouarn/soil3ds)

Their dependencies:
- openalea.mtg
- openalea.plantgl
- openalea.lpy
- Adel wheat
- numpy
- pandas
- scipy
- gcc
- gfortran
- make

## Installation

We use [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/index.html) for managing our python environment. 

Note: `git` commands must be run in a git bash terminal (or linux terminal) and `python`, `conda`, `mamba`, in a powershell terminal (or linux terminal).

0. Recommended step: install mamba in your `base` conda environment:

```python
conda install mamba 
```

1. Create your conda environment (replace conda with mamba if installed):

```python
conda create -n myenvname openalea.mtg openalea.plantgl openalea.deploy openalea.lpy openalea.sconsx alinea.caribu alinea.astk numpy=1.22.4 pandas pytest sphinx sphinx-rtd-theme xlrd coverage nose statsmodels scipy=1.7.3 scons zipp=3.15.0 m2w64-gcc-fortran -c conda-forge -c openalea3
```

2. Convert CARIBU and Astk namespace in PEP 420. This step is required for installing other packages in the `alinea` namespace. To do so, you need to delete the `__init__.py` file in the `alinea` folder. For example, on a Windows computer, you could use this command:

```bash
del C:\Users\username\AppData\Local\miniconda3\envs\myenvname\Lib\site-packages\alinea.astk-2.3.2-py3.9.egg\alinea\__init__.py
del C:\Users\username\AppData\Local\miniconda3\envs\myenvname\Lib\site-packages\alinea.caribu-8.0.10-py3.9-win-amd64.egg\alinea\__init__.py
```

/!\ For all the following steps, run the commands inside the downloaded folders (commands after `git clone`).

3. Installation of Adel

    1. `git clone -b python3 https://github.com/rbarillot/adel`

    2. Convert the namespace package to PEP 420: 

        1. Delete the `__init__.py` in alinea folder

            ```bash
            del src/alinea/__init__.py
            ```
            
        2. Replace the `setup.py` with `setup_adel.py` in `plantfusion/installation_ressources`. Rename it `setup.py`.

    3. Installation : `python setup.py develop`

4. Installation of PyRATP. For this step, you need to have `gcc`, `gfortran` and `make` installed

    1. Download the package: `git clone -b update_mobidiv https://github.com/mwoussen/PyRATP`

    2. Installation: 

        ```bash
        make mode=develop
        make clean
        ``` 

    Note: `make` will compile the fortran part, then run the package installation with pip.

5. Installation of WheatFspm

    1. Create a WheatFspm folder and copy the `clone_wheatfspm.sh` and `setup_wheatfspm.py` files in it.

    2. Run `clone_wheatfspm.sh` in a git bash terminal. This step will download all the wheatfspm submodules.

    3. Rename `setup_wheatfspm.py` to `setup.py` and install the package with `python setup.py develop`

6. Installation of l-egume

    1. Download the package: `git clone -b Develop https://github.com/glouarn/l-egume`

    2. Install: `python setup.py develop`

7. Installation of LightVegeManager

    1. Download the package: `git clone https://github.com/mwoussen/lightvegemanager`

    2. Install: `python setup.py develop`

8. Installation of soil3ds

    1. Download the package: `git clone https://github.com/glouarn/soil3ds`

    2. Install: `python setup.py develop`

9. Installation of riri5

    1. Download the package: `git clone https://github.com/glouarn/riri5`
    
    2. Install: `python setup.py develop`


## Simulation Examples

- copy of l-egume default simulation with the API
- copy of fspmwheat default simulation with the API
- compare l-egume default with l-egume + RATP
- compare l-egume default with l-egume + CARIBU
- compare fspmwheat default with fspmwheat + RATP
- soil coupling fspmwheat + soil3ds
- light coupling l-egume + fspmwheat + CARIBU
- full coupling l-egume + fspmwheat + CARIBU + soil3ds

## Usage

In your conda environment run one the simulation scripts in `simulations`:

```python
python simulations/simulation_name.py
```
## Licence

This project is licensed under the CeCILL-C License - see file [LICENSE](LICENSE) for details


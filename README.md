# Plant Fusion: API for mixed crop modelling

## Introduction

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

0) Recommended step: install mamba in your `base` conda environment:

```python
conda install mamba 
```

1) Create your conda environment (replace conda with mamba if installed):

```python
conda create -n myenvname openalea.mtg openalea.plantgl openalea.deploy openalea.lpy openalea.sconsx alinea.caribu alinea.astk numpy=1.22.4 pandas pytest sphinx sphinx-rtd-theme xlrd coverage nose statsmodels scipy=1.7.3 scons zipp=3.15.0 m2w64-gcc-fortran -c conda-forge -c openalea3
```

2) Convert CARIBU and Astk namespace in PEP 420. This step is required for installing other packages in the `alinea` namespace. To do so, you need to delete the `__init__.py` file in the `alinea` folder. For example, on a Windows computer, you could use this command:

```bash
del C:\Users\username\AppData\Local\miniconda3\envs\myenvname\Lib\site-packages\alinea.astk-2.3.2-py3.9.egg\alinea\__init__.py
del C:\Users\username\AppData\Local\miniconda3\envs\myenvname\Lib\site-packages\alinea.caribu-8.0.10-py3.9-win-amd64.egg\alinea\__init__.py
```

For all the following steps, run the commands inside the downloaded folders (commands after `git clone`).

3) Installation of Adel
    a) `git clone -b python3 https://github.com/rbarillot/adel`
    b) Convert the namespace package to PEP 420: 
        i) Delete the `__init__.py` in alinea folder
            ```bash
            del src/alinea/__init__.py
            ```
        ii) Replace the `setup.py` with `setup_adel.py` in `plantfusion/installation_ressources`. Rename it `setup.py`.
    c) installation : `python setup.py develop`

4) Installation of PyRATP. For this step, you need to have `gcc`, `gfortran` and `make` installed
    a) download the package: `git clone -b update_mobidiv https://github.com/mwoussen/PyRATP`
    b) installation: 
        ```bash
        make mode=develop
        make clean
        ``` 
    `make` will compile the fortran part, then run the package installation with pip.

5) Installation of WheatFspm
    a) Create a WheatFspm folder and copy the `clone_wheatfspm.sh` and `setup_wheatfspm.py` files in it.
    b) Run `clone_wheatfspm.sh` in a git bash terminal. This step will download all the wheatfspm submodules.
    c) Rename `setup_wheatfspm.py` to `setup.py` and install the package with `python setup.py develop`

6) Installation of l-egume
    a) download the package: `git clone -b Develop https://github.com/glouarn/l-egume`
    b) install: `python setup.py develop`

7) Installation of LightVegeManager
    a) download the package: `git clone https://github.com/mwoussen/lightvegemanager`
    b) install: `python setup.py develop`

8) Installation of soil3ds
    a) download the package: `git clone https://github.com/glouarn/soil3ds`
    b) install: `python setup.py develop`

9) Installation of riri5
    a) download the package: `git clone https://github.com/glouarn/riri5`
    b) install: `python setup.py develop`


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


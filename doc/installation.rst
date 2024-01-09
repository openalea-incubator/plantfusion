.. _installation:

Installation
============

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
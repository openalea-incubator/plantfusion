# Containers for runing a python environment

## Singularity

Creating the container. You need to download the pre-built container with miniconda3 from https://forgemia.inra.fr/singularity/prebuilt/miniconda3-py37

```bash
sudo singularity build --force container_name.sif couplage_env_singularity.def
```

Using the container

```bash
singularity run container_name.sif <script_python.py>
```
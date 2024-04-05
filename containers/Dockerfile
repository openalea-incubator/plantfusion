FROM condaforge/mambaforge

COPY ./adel /adel
COPY ./WheatFspm /WheatFspm

RUN apt update
RUN apt upgrade -y
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install -y tzdata
RUN apt install -y build-essential wget bzip2 unzip git gfortran freeglut3-dev libxext-dev libxrender-dev libglib2.0-0 libqhull-dev
	
    # packages python fredboudon et conda-forge
RUN mamba install -v python=3.7 openalea.mtg openalea.plantgl openalea.lpy openalea.deploy openalea.sconsx alinea.astk alinea.caribu xlrd coverage nose sphinx pytest statsmodels numpy scipy=1.7.3 pandas sphinx_rtd_theme scons zipp=3.15.0 -c conda-forge -c fredboudon -y

RUN pip install notebook pgljupyter
    
    # cleanup
RUN conda clean -y --all
RUN apt autoremove --purge
RUN apt clean

    # conversion du namespace pour caribu et astk convention PEP 420
RUN rm /opt/conda/lib/python3.7/site-packages/alinea.caribu-8.0.7-py3.7.egg/alinea/__init__.py
RUN rm /opt/conda/lib/python3.7/site-packages/alinea.astk-2.2.0-py3.7.egg/alinea/__init__.py
    
    # debug soilmesh et virtualsensors
RUN wget https://raw.githubusercontent.com/mwoussen/caribu/master/src/alinea/caribu/CaribuScene.py
RUN	mv CaribuScene.py /opt/conda/lib/python3.7/site-packages/alinea.caribu-8.0.7-py3.7.egg/alinea/caribu/
RUN	wget https://raw.githubusercontent.com/mwoussen/caribu/master/src/alinea/caribu/caribu_shell.py
RUN	mv caribu_shell.py /opt/conda/lib/python3.7/site-packages/alinea.caribu-8.0.7-py3.7.egg/alinea/caribu/

    # adel
WORKDIR /adel/
RUN python setup.py develop

    # Wheat-Fspm
WORKDIR /WheatFspm/
RUN python setup.py develop

    # l-egume
WORKDIR /
RUN git clone -b Develop https://github.com/glouarn/l-egume.git
WORKDIR /l-egume/
RUN python setup.py develop

    # PyRATP
WORKDIR /
RUN git clone -b update_mobidiv https://github.com/mwoussen/PyRATP.git
WORKDIR /PyRATP/
RUN make
RUN make clean

    # lightvegemanager
WORKDIR /
RUN git clone https://github.com/openalea-incubator/lightvegemanager.git
WORKDIR /lightvegemanager/
RUN python setup.py develop

    # 3ds Soil
WORKDIR /
RUN git clone https://github.com/glouarn/soil3ds.git
WORKDIR /soil3ds/
RUN python setup.py develop

    # RiRi5
WORKDIR /
RUN git clone https://github.com/glouarn/riri5.git
WORKDIR /riri5/
RUN python setup.py develop

CMD ["jupyter", "notebook"]

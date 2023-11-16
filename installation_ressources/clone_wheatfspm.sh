#!/bin/bash

printf "\t Clone WheatFSPM\n" 
printf "\t ===============\n\n" 
git clone https://github.com/openalea-incubator/senesc-wheat
git clone https://github.com/openalea-incubator/farquhar-wheat
git clone https://github.com/openalea-incubator/respi-wheat
git clone https://github.com/openalea-incubator/growth-wheat
git clone https://github.com/openalea-incubator/elong-wheat
git clone -b mobidiv https://github.com/rbarillot/cn-wheat
git clone -b extsoil https://github.com/mwoussen/fspm-wheat
printf "\n\t installation done\n\n" 

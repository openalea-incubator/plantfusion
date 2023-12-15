from plantfusion.indexer import Indexer
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.planter import Planter

import openalea.plantgl.all as pgl

import random
import numpy


class fakeFSPM:
    def __init__(self, name=""):
        self.name = name
        self.scene = pgl.Scene(
            [pgl.Shape(pgl.Box(), pgl.Material(), 888), pgl.Shape(pgl.Cylinder(), pgl.Material(), 999)]
        )
        self.soil_parameters = {
            "Vmax1": 0.0006,
            "Vmax2": 0.016,
            "Kmax1": 50,
            "Kmax2": 25000,
            "treshminN": 0.8,
            "treshmaxN": 1.75,
            "WaterTreshGs": 0.4,
            "leafAlbedo": 0.15,
            "treshEffRootsN": 1000000,
        }

    def light_inputs(self):
        return self.scene

    def light_results(self, lighting):
        self.energy = lighting.results_organs().mean()["par Eabs"]

    def soil_inputs(self, soil_dimensions):
        nb_plants = 1

        N_content_roots_per_plant = [0.5] * nb_plants
        plants_light_interception = [0.4] * nb_plants

        roots_length = 6.0  # m
        roots_length_per_plant_per_soil_layer = []
        for i in range(nb_plants):
            # on répartit de manière homogène les racines à travers les couches du sol
            # convertit m en cm # --> peut etre en metre finalement
            rootLen_i = numpy.ones(soil_dimensions) * roots_length / numpy.prod(soil_dimensions)
            roots_length_per_plant_per_soil_layer.append(rootLen_i)

        return (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            [self.soil_parameters] * nb_plants,
            plants_light_interception,
        )

    def soil_results(self, uptakeN):
        pass

    def run(self):
        pass

    def end(self):
        print("--- END ---")


def simulation(iterations, out_folder="outputs/other_fspm", writegeo=False):
    indexer = Indexer(global_order=["fspm"], other_names=["fspm"])

    plane = ((-0.5, -0.5), (0.5, 0.5))
    planter = Planter(xy_plane=plane)

    fspm = fakeFSPM(name="fspm")

    light = Light_wrapper(lightmodel="caribu", planter=planter, out_folder=out_folder, writegeo=writegeo)
    soil = Soil_wrapper(in_folder="inputs_soil_legume", IDusm=1711, planter=planter, save_results=True)
    soil_dimensions = [len(soil.soil.dxyz[i]) for i in [2, 0, 1]]

    # meteo file follows soil3ds in "inputs_soil_legume/list_usms_exemple.xls"
    for i in range(60, 60 + iterations):
        # LIGHT #
        scene = fspm.light_inputs()
        light.run(scenes=[scene], day=i, energy=random.uniform(1, 500))
        fspm.light_results(light)

        # SOIL #
        (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            soil_plants_parameters,
            plants_light_interception,
        ) = fspm.soil_inputs(soil_dimensions)
        soil.run(
            day=i,
            N_content_roots_per_plant=[N_content_roots_per_plant],
            roots_length_per_plant_per_soil_layer=[roots_length_per_plant_per_soil_layer],
            soil_plants_parameters=[soil_plants_parameters],
            plants_light_interception=[plants_light_interception],
        )
        fspm.soil_results(soil.results[4])

        fspm.run()

    fspm.end()


if __name__ == "__main__":
    simulation(2)

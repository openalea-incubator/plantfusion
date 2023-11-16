import os

from lightvegemanager.tool import LightVegeManager
from lightvegemanager.stems import extract_stems_from_MTG
from plantfusion.utils import create_child_folder
from plantfusion.planter import Planter

class Light(object):
    def __init__(
        self,
        environment,
        position:Planter,
        lightmodel="",
        legume_facade=None,
        wheat_facade=None,
        caribu_opt={"par": (0.10, 0.07)},
        voxels_size=[1.0, 1.0, 1.0],
        angle_distrib_algo="compute voxel",
        nb_angle_class=9,
        mu=1.0,
        writegeo=False,
        out_folder="",
    ):
        self.transformations = position.transformations
        self.wheat_facade = wheat_facade
        self.writegeo = writegeo
        self.compute_sensors = False
        if writegeo:
            create_child_folder(out_folder, "light")
            self.out_folder = os.path.join(out_folder, "light")
            create_child_folder(self.out_folder, "vtk")
            create_child_folder(self.out_folder, "plantgl")

        self.lightmodel = lightmodel

        self.type_domain = position.type_domain
        self.domain = position.domain

        # calcul du nombre d'espèce
        self.number_of_species = 0

        # les instances de l-egume doivent suivre la même grille
        if legume_facade is not None:
            if isinstance(legume_facade, list):
                for leg in legume_facade:
                    self.number_of_species += leg.number_of_species()
                nxyz_legume = [
                    legume_facade[0].number_of_voxels()[3],
                    legume_facade[0].number_of_voxels()[2],
                    legume_facade[0].number_of_voxels()[1],
                ]
                dxyz_legume = [x * 0.01 for x in legume_facade[0].voxels_size()]  # conversion de cm à m
            else:
                self.number_of_species += legume_facade.number_of_species()
                nxyz_legume = [
                    legume_facade.number_of_voxels()[3],
                    legume_facade.number_of_voxels()[2],
                    legume_facade.number_of_voxels()[1],
                ]
                dxyz_legume = [x * 0.01 for x in legume_facade.voxels_size()]  # conversion de cm à m
        if wheat_facade is not None:
            if isinstance(wheat_facade, list):
                self.number_of_species += len(wheat_facade)
            else:
                self.number_of_species += 1

        lightmodel_parameters = {}

        if lightmodel == "caribu":
            lightmodel_parameters["caribu opt"] = caribu_opt
            lightmodel_parameters["sun algo"] = "caribu"
            if legume_facade is not None:
                self.compute_sensors = True
                orig = [self.domain[0][0], self.domain[0][1], 0.0]
                path = os.path.join(os.path.normpath(self.out_folder), "vtk", "sensors")
                if writegeo:
                    lightmodel_parameters["sensors"] = ["grid", dxyz_legume, nxyz_legume, orig, path, "vtk"]
                    create_child_folder(os.path.join(os.path.normpath(self.out_folder), "vtk"), "sensors")
                else:
                    lightmodel_parameters["sensors"] = ["grid", dxyz_legume, nxyz_legume, orig]

            lightmodel_parameters["debug"] = False
            lightmodel_parameters["soil mesh"] = 1

        elif lightmodel == "ratp" or lightmodel == "riri5":
            if legume_facade is not None:
                lightmodel_parameters["voxel size"] = dxyz_legume
                lightmodel_parameters["origin"] = [0.0, 0.0, 0.0]
                lightmodel_parameters["full grid"] = True
            else:
                lightmodel_parameters["voxel size"] = voxels_size
                lightmodel_parameters["full grid"] = False

            lightmodel_parameters["mu"] = [mu] * self.number_of_species
            lightmodel_parameters["reflectance coefficients"] = [[0.0, 0.0]] * self.number_of_species

            if "/" in angle_distrib_algo or "\\" in angle_distrib_algo:
                lightmodel_parameters["angle distrib algo"] = "file"
                lightmodel_parameters["angle distrib file"] = angle_distrib_algo
            else:
                lightmodel_parameters["angle distrib algo"] = angle_distrib_algo
                lightmodel_parameters["nb angle classes"] = nb_angle_class
                lightmodel_parameters["soil reflectance"] = [0.0, 0.0]

        else:
            print("lightmodel not recognize")
            raise

        self.light = LightVegeManager(
            environment=environment.light,
            lightmodel=lightmodel,
            lightmodel_parameters=lightmodel_parameters,
            main_unit="m",
        )

        self.i_vtk = 0


    def run(self, energy=1., scenes_wheat=[], scenes_l_egume=[], day=1, hour=12, parunit="RG", position=None):
        self.wheat_index = list(range(len(scenes_wheat)))
        self.l_egume_index = list(range(len(scenes_wheat), len(scenes_wheat) + len(scenes_l_egume)))
        stems = None
        if self.l_egume_index == []:
            self.l_egume_index = None
        if self.wheat_index == []:
            self.wheat_index = None
        else:
            for id in self.wheat_index:
                stems = extract_stems_from_MTG(self.wheat_facade.g, id)

        scenes = scenes_wheat + scenes_l_egume

        geometry = {"scenes": scenes, "domain" : self.domain, "transformations": self.transformations, "stems id": stems}

        self.light.build(geometry)
        self.light.run(energy=energy, day=day, hour=hour, truesolartime=True, parunit=parunit, id_sensors=self.l_egume_index)

        if self.writegeo:
            self.light.VTK_light(os.path.join(os.path.normpath(self.out_folder), "vtk", "scene_"), i=self.i_vtk)
            self.i_vtk += 1

    def results_organs(self):
        try:
            return self.light.elements_outputs
        except AttributeError:
            return []

    def results_voxels(self):
        return self.light.voxels_outputs

    def results_triangles(self):
        return self.light.triangles_outputs

    def results_sensors(self):
        return self.light.sensors_outputs

    def res_trans(self):
        return self.light.riri5_transmitted_light

    def res_abs_i(self):
        return self.light.riri5_intercepted_light

    def soil_energy(self):
        try:
            return self.light.soilenergy["Qi"]
        except AttributeError:
            return -1

    def nb_empty_z_layers(self):
        return self.light.legume_empty_layers
    
    def xydomain_lightvegemanager(self):
        return self.light.domain

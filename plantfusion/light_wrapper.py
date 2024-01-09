"""

    contains Light_wrapper class

"""

import os

from lightvegemanager.LVM import LightVegeManager
from plantfusion.utils import create_child_folder
from plantfusion.planter import Planter
from plantfusion.indexer import Indexer


class Light_wrapper(object):
    """Wrapper for LightVegeManager
    
    Sets pre-configured parameters following the inputs

    Parameters
    ----------
    planter : Planter, optional
        Object containing plant positions and/or number of plants and/or soil domain, by default Planter()
    indexer : Indexer, optional
        indexer for listing FSPM in the simulation, by default Indexer()
    lightmodel : str, optional
        select the light model, choose between "caribu", "ratp" or "riri5", by default ""
    sky : str, optional
        sky type, see sky in LightVegeManager for more info, by default "turtle46"
    direct : bool, optional
        activate direct radiation (sun), by default False
    diffuse : bool, optional
        activate diffuse radiation (sky), by default True
    reflected : bool, optional
        activate reflected radiation between plants, by default False
    coordinates : list, optional
        [latitude, longitude, timezone], by default [46.4, 0.0, 1.0]
    infinite : bool, optional
        activate infinite scene replication, by default True
    legume_wrapper : L_egume_wrapper or list of L_egume_wrapper, optional
        instance(s) of L_egume_wrapper in the simulation, by default None
    caribu_opt : dict, optional
        optical parameters for CARIBU, by default {"par": (0.10, 0.07)}
    voxels_size : list, optional
        input voxels size in m for each direction [dx, dy, dz], by default [1.0, 1.0, 1.0]
    angle_distrib_algo : str, optional
        computation type for leaf angle distribution, by default "compute global"
    nb_angle_class : int, optional
        number of leaf angle classes between 0 and 90°, by default 9
    mu : float, optional
        dispersion coefficient in voxels, by default 1.0
    writegeo : bool, optional
        activate write the scene in VTK and bgeom files, by default False
    out_folder : str, optional
        outputs folder path where to write geometric files if writegeo == True, by default ""

    """    
    def __init__(
        self,
        planter=Planter(),
        indexer=Indexer(),
        lightmodel="",
        sky="turtle46",
        direct=False,
        diffuse=True,
        reflected=False,
        coordinates=[46.4, 0.0, 1.0],
        infinite=True,
        legume_wrapper=None,
        caribu_opt={"par": (0.10, 0.07)},
        voxels_size=[1.0, 1.0, 1.0],
        angle_distrib_algo="compute global",
        nb_angle_class=9,
        mu=1.0,
        writegeo=False,
        out_folder="",
    ):
        """Constructor, create an instance of LightVegeManager

        """        
        self.transformations = planter.transformations
        self.indexer = indexer
        self.writegeo = writegeo
        self.compute_sensors = False
        self.direct=direct
        if writegeo:
            create_child_folder(os.path.normpath(out_folder), "light")
            self.out_folder = os.path.join(os.path.normpath(out_folder), "light")
            create_child_folder(self.out_folder, "vtk")
            create_child_folder(self.out_folder, "plantgl")

        self.lightmodel = lightmodel

        self.type_domain = planter.type_domain
        self.domain = planter.domain

        self.environment = {
            "coordinates": coordinates,
            "sky": sky,
            "direct": direct,
            "diffus": diffuse,
            "reflected": reflected,
            "infinite": infinite,
        }

        self.number_of_species = len(indexer.global_order)

        # get grid dimensions of l-egume instances
        dxyz_legume = [0.0] * 3
        nxyz_legume = [0] * 3
        if legume_wrapper is not None:
            if isinstance(legume_wrapper, list):
                nxyz_legume = []
                for wrap in legume_wrapper:
                    nxyz_legume.append([
                        wrap.number_of_voxels()[3],
                        wrap.number_of_voxels()[2],
                        wrap.number_of_voxels()[1],
                    ])
                nxyz_legume = [max(*x) for x in zip(*nxyz_legume)]
                dxyz_legume = [x * 0.01 for x in legume_wrapper[0].voxels_size()]  # conversion de cm à m
            else:
                nxyz_legume = [
                    legume_wrapper.number_of_voxels()[3],
                    legume_wrapper.number_of_voxels()[2],
                    legume_wrapper.number_of_voxels()[1],
                ]
                dxyz_legume = [x * 0.01 for x in legume_wrapper.voxels_size()]  # conversion de cm à m

        lightmodel_parameters = {}

        # CARIBU parameters
        if lightmodel == "caribu":
            lightmodel_parameters["caribu opt"] = caribu_opt
            lightmodel_parameters["sun algo"] = "caribu"
            # creates grids of virtual sensors if l-egume + CARIBU
            if legume_wrapper is not None:
                self.compute_sensors = True
                x_trans, y_trans = 0, 0
                if isinstance(legume_wrapper, list):
                    lightmodel_parameters["sensors"] = {}
                    for wrap in legume_wrapper:
                        if "translate" in planter.transformations:
                            if wrap.global_index in planter.transformations["translate"]:
                                x_trans, y_trans, z = planter.transformations["translate"][wrap.global_index]
                        orig = [self.domain[0][0]+x_trans, self.domain[0][1]+y_trans, 0.0]
                        nxyz_legume = [
                            wrap.number_of_voxels()[3],
                            wrap.number_of_voxels()[2],
                            wrap.number_of_voxels()[1],
                        ]
                        dxyz_legume = [x * 0.01 for x in wrap.voxels_size()]  # conversion de cm à m
                        lightmodel_parameters["sensors"][wrap.global_index] = ["grid", dxyz_legume, nxyz_legume, orig]
                else:                
                    if "translate" in planter.transformations:
                        if isinstance(legume_wrapper.global_index, list):
                            if any([i in planter.transformations["translate"] for i in legume_wrapper.global_index]) :
                                x_trans, y_trans, z = planter.transformations["translate"][legume_wrapper.global_index[0]]
                        else:
                            if legume_wrapper.global_index in planter.transformations["translate"] :
                                x_trans, y_trans, z = planter.transformations["translate"][legume_wrapper.global_index]
                    orig = [self.domain[0][0]+x_trans, self.domain[0][1]+y_trans, 0.0]   
                    lightmodel_parameters["sensors"] = ["grid", dxyz_legume, nxyz_legume, orig]

            lightmodel_parameters["debug"] = False
            lightmodel_parameters["soil mesh"] = 1

        # RATP/RiRi5 parameters
        elif lightmodel == "ratp" or lightmodel == "riri5":
            if legume_wrapper is not None:
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
        
        # instance create of LightVegeManager
        self.light = LightVegeManager(
            environment=self.environment,
            lightmodel=lightmodel,
            lightmodel_parameters=lightmodel_parameters,
            main_unit="m",
        )

        self.i_vtk = 0

    def run(self, energy=1.0, scenes=[], day=1, hour=12, parunit="RG", stems=None):
        """Run the lighting computation

        Parameters
        ----------
        energy : float, optional
            radiation input from meteo in W/m², by default 1.0
        scenes : list, optional
            lits of geometric scenes available with LightVegeManager, by default []
        day : int, optional
            day of the year, by default 1
        hour : int, optional
            timestep hour, by default 12
        parunit : str, optional
            possibility to precise the radiation unit, by default "RG"
        stems : list of tuple, optional
            precise if stems are among the input scenes. An element of the list is (specy ID, organ ID), by default None
        """        
        geometry = {"scenes": scenes, "domain": self.domain, "transformations": self.transformations, "stems id": stems}

        self.light.build(geometry)
        self.light.run(
            energy=energy,
            day=day,
            hour=hour,
            truesolartime=True,
            parunit=parunit,
        )

        if self.writegeo:
            file_project_name = os.path.join(os.path.normpath(self.out_folder), "vtk", "plantfusion_")
            
            if self.lightmodel == "ratp":
                printvoxels = True
            elif self.lightmodel == "caribu":
                printvoxels = True

            self.light.to_VTK(lighting=True, 
                                path=file_project_name, 
                                i=self.i_vtk, 
                                printtriangles=True, 
                                printvoxels=printvoxels, 
                                virtual_sensors=self.compute_sensors, 
                                sun=self.direct)
            scene_plantgl= self.light.to_plantGL(lighting=True, 
                                                    printtriangles=True, 
                                                    printvoxels=printvoxels, 
                                                    virtual_sensors=self.compute_sensors)
            
            if self.compute_sensors:
                scene_plantgl[0].save(
                    os.path.join(self.out_folder, "plantgl", "scene_light_plantgl_" + str(self.i_vtk)) + ".bgeom"
                )
                scene_plantgl[1].save(
                    os.path.join(self.out_folder, "plantgl", "sensors_plantgl_" + str(self.i_vtk)) + ".bgeom"
                )
            else:
                scene_plantgl.save(
                    os.path.join(self.out_folder, "plantgl", "scene_light_plantgl_" + str(self.i_vtk)) + ".bgeom"
                )

            self.i_vtk += 1

    def results_organs(self):
        """Return lighting results at organ scale

        Returns
        -------
        pandas.Dataframe
            lighting results at organ scale
        """        
        try:
            return self.light.elements_outputs
        except AttributeError:
            return None

    def results_voxels(self):
        """Return lighting results at voxels scale

        Returns
        -------
        pandas.Dataframe
            lighting results at voxels scale
        """         
        return self.light.voxels_outputs

    def results_triangles(self):
        """Return lighting results at triangles scale

        Returns
        -------
        pandas.Dataframe
            lighting results at triangles scale
        """         
        return self.light.triangles_outputs

    def results_sensors(self):
        """Return lighting results of virtual sensors

        Returns
        -------
        pandas.Dataframe
            lighting results of virtual sensors
        """         
        return self.light.sensors_outputs(dataframe=True)

    def res_trans(self):
        """Return transmitted energy per voxel

        Returns
        -------
        numpy.array
            transmitted energy per voxel dimensions [iz, iy, ix]
        """        
        return self.light.riri5_transmitted_light

    def res_abs_i(self):
        """Return absorbed energy per voxel per specy

        Returns
        -------
        numpy.array
            absorbed energy per voxel dimensions [specy id, iz, iy, ix]
        """        
        return self.light.riri5_intercepted_light

    def soil_energy(self):
        """Relative energy intercepted by soil

        Returns
        -------
        float
            Relative energy intercepted by soil [0-1]
        """        
        try:
            return self.light.soilenergy["Qi"]
        except AttributeError:
            return -1

    def nb_empty_z_layers(self):
        """Number of empty z layers in voxel grid

        Returns
        -------
        int
            Number of empty z layers in voxel grid
        """        
        return self.light.legume_empty_layers

    def xydomain_lightvegemanager(self):
        """Return soil domain computed by lightvegemanager

        Returns
        -------
        tuple of tuple
            ((xmin, ymin), (xmax, ymax))
        """        
        return self.light.domain
    
    def plantgl(self, lighting=False, printtriangles=True, printvoxels=False):
        """Return plantGL scene of LightVegeManager mesh

        Parameters
        ----------
        lighting : bool, optional
            activate lighting results or only geometry, by default False
        printtriangles : bool, optional
            print triangles in returned scene, by default True
        printvoxels : bool, optional
            print voxels in returned scene, by default False

        Returns
        -------
        plantgl.Scene
            plantgl scene of the current timestep
        """        
        return self.light.to_plantGL(lighting=lighting, 
                                        printtriangles=printtriangles, 
                                        printvoxels=printvoxels, 
                                        virtual_sensors=self.compute_sensors) 

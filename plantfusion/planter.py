import numpy
import pandas
import math

from alinea.adel.Stand import AgronomicStand
import openalea.plantgl.all as plantgl
import random


class Planter:
    def __init__(
        self,
        generation_type="default",
        plantmodels=[],
        inter_rows=0.15,
        plant_density={1: 250},
        xy_plane=None,
        xy_square_length=0.5,
        xy_translate=None,
        noise_plant_positions=0.,
        save_wheat_positions=False,
    ) -> None:
        self.generation_type = generation_type
        # plant_density = {"legume" : [n1, n2], "wheat" : [n1, n2] ...}
        self.plant_density = plant_density
        self.save_wheat_positions = save_wheat_positions
        self.noise_plant_positions = noise_plant_positions

        if generation_type == "default":
            self.__default_preconfigured(plantmodels, inter_rows, plant_density, xy_plane, xy_translate)

        elif generation_type == "random":
            self.__random(plantmodels, plant_density, xy_square_length)

        elif generation_type == "row":
            self.__row(plantmodels, plant_density, inter_rows)

    def __random(self, plantmodels, plant_density, xy_square_length):
        # fait un carré à partir de (0,0)
        # xy_plane = longueur d'un cote du carré du sol
        self.domain = ((0.0, 0.0), (xy_square_length, xy_square_length))

        if "legume" in plant_density:
            # on réajuste le domaine pour avoir 64 plantes
            if isinstance(plant_density["legume"], list):
                 self.legume_nbcote = plant_density["legume"][0]
                 self.legume_nbcote = [8] * len(plant_density["legume"])
            else:
                 self.legume_nbcote = plant_density["legume"]
                 self.legume_nbcote = [8]
            # xy_square_length = math.sqrt(64/legume_density)
            # self.domain = ((0.0, 0.0), (xy_square_length, xy_square_length))
            
            self.legume_typearrangement = "random8"
            # conversion m en cm
            self.legume_cote = xy_square_length * 100
            
            self.legume_optdamier = 8

        if "wheat" in plant_density:
            if isinstance(plant_density["wheat"], list):
                self.wheat_nbplants = [ int(xy_square_length * xy_square_length * wheat_density) for wheat_density in plant_density["wheat"] ]
            else:
                self.wheat_nbplants = [ int(xy_square_length * xy_square_length * plant_density["wheat"]) ]
            self.wheat_positions = []

        # les lsystem l-egume sont par défaut en cm et wheat en m
        self.index = {"wheat": [], "l-egume": []}
        self.transformations = {"scenes unit": {}}
        id_specy = 0
        for facade in plantmodels:
            if facade == "wheat":
                self.index["wheat"].append(id_specy)
                self.transformations["scenes unit"][id_specy] = "m"
            if facade == "legume":
                self.index["l-egume"].append(id_specy)
                self.transformations["scenes unit"][id_specy] = "cm"
                id_specy += 1
            id_specy += 1

    def __row(self, plantmodels, plant_density, inter_rows):
        if "legume" not in plant_density :
            plant_density["legume"] = []
        elif "wheat" not in plant_density :
            plant_density["wheat"] = []

        self.total_n_rows = 2 * ( len(plant_density["legume"]) + len(plant_density["wheat"]) )
        xy_square_length = inter_rows * self.total_n_rows
        self.domain = ((0.0, 0.0), (xy_square_length, xy_square_length))

        if "legume" in plant_density:
            self.legume_typearrangement = "row4_sp1"
            # conversion m en cm
            self.legume_cote = inter_rows * self.total_n_rows * 100
            if isinstance(plant_density["legume"], list):
                self.legume_nbcote = [int( xy_square_length * xy_square_length * d / 2) for d in plant_density["legume"] ]
            else:
                self.legume_nbcote = [int( xy_square_length * xy_square_length * plant_density["legume"] / 2 )]

            self.legume_optdamier = 2

        if "wheat" in plant_density:
            if isinstance(plant_density["wheat"], list):
                self.wheat_nbplants = [ int(xy_square_length * xy_square_length * wheat_density) for wheat_density in plant_density["wheat"] ]
            else:
                self.wheat_nbplants = [ int(xy_square_length * xy_square_length * plant_density["wheat"]) ]
            self.inter_rows = inter_rows
            self.wheat_positions = []

        # les lsystem l-egume sont par défaut en cm et wheat en m
        self.index = {"wheat": [], "l-egume": []}
        self.transformations = {"scenes unit": {}}
        id_specy = 0
        for facade in plantmodels:
            if facade == "wheat":
                self.index["wheat"].append(id_specy)
                self.transformations["scenes unit"][id_specy] = "m"
            if facade == "legume":
                self.index["l-egume"].append(id_specy)
                self.transformations["scenes unit"][id_specy] = "cm"
                id_specy += 1
            id_specy += 1
        
        self.transformations["translate"] = {}
        if len(plant_density["legume"]) + len(plant_density["wheat"]) > 2 :
            for i in range(len(plantmodels)):
                if plantmodels[i] == "legume" :
                    self.transformations["translate"][i] = (0., (i) * inter_rows, 0.)
                elif plantmodels[i] == "wheat" :
                    self.transformations["translate"][i] = (0., (i-0.5) * inter_rows, 0.)
        
        # il y a que deux espèces
        else:
            # 2 wheats
            if plantmodels.count("wheat") > 1 :
                self.transformations["translate"][0] = (0., - inter_rows, 0.)
            
            # 2 legume
            elif plantmodels.count("legume") > 1 :
                self.transformations["translate"][1] = (0., inter_rows, 0.)


    def __default_preconfigured(
        self, plantmodels=[], inter_rows=0.15, plant_density={1: 250}, xy_plane=None, xy_translate=None
    ):
        from plantfusion.l_egume_facade import L_egume_facade
        from plantfusion.wheat_facade import Wheat_facade

        self.plant_density = plant_density
        self.inter_rows = inter_rows

        legume_instances = [facade for facade in plantmodels if isinstance(facade, L_egume_facade)]
        wheat_instances = [facade for facade in plantmodels if isinstance(facade, Wheat_facade)]

        self.nb_plants = 0
        self.nb_wheat_plants = 50
        if wheat_instances != [] :
            self.type_domain = "create_heterogeneous_canopy"
            # pour mettre à jour self.domain
            setup_scene = self.create_heterogeneous_canopy(wheat_instances[0].adel_wheat, wheat_instances[0].g)
            self.nb_plants = self.nb_wheat_plants * len(wheat_instances)

        # les lsystem l-egume sont par défaut en cm et wheat en m
        self.index = {"wheat": [], "l-egume": []}
        self.transformations = {"scenes unit": {}}
        id_specy = 0
        for facade in plantmodels:
            if isinstance(facade, Wheat_facade):
                self.index["wheat"].append(id_specy)
                self.transformations["scenes unit"][id_specy] = "m"
            if isinstance(facade, L_egume_facade):
                # il peut y avoir plusieurs lsystem dans un legume
                for i in range(len(facade.idsimu)):
                    self.index["l-egume"].append(id_specy)
                    self.transformations["scenes unit"][id_specy] = "cm"
                    id_specy += 1
            id_specy += 1

        # temporaire : on applique les translations que aux instances l-egume
        if xy_translate is not None:
            self.transformations["translate"] = {}
            id_specy = 0
            for facade in plantmodels:
                if isinstance(facade, L_egume_facade):
                    # il peut y avoir plusieurs lsystem dans un legume
                    for i in range(len(facade.idsimu)):
                        # self.index["l-egume"].append(id_specy)
                        self.transformations["translate"][id_specy] = (xy_translate[0], xy_translate[1], 0)
                        id_specy += 1
                id_specy += 1

        # gestion du domain xy de définition
        if xy_plane is None:
            # si recalcul le domain via create_heterogeneous_canopy
            if legume_instances == []:
                self.type_domain = "create_heterogeneous_canopy"
            elif wheat_instances == []:
                self.type_domain = "l-egume"
                n = legume_instances[0].idsimu[0]
                # convertit domain cm en m
                self.domain = (
                    (0.0, 0.0),
                    (legume_instances[0].lsystems[n].cote * 0.01, legume_instances[0].lsystems[n].cote * 0.01),
                )
            else:
                n = legume_instances[0].idsimu[0]
                self.type_domain = "mix"
                legume_domain = (
                    (0.0, 0.0),
                    (legume_instances[0].lsystems[n].cote * 0.01, legume_instances[0].lsystems[n].cote * 0.01),
                )
                if xy_translate is not None:
                    legume_domain = (
                        (legume_domain[0][0] + xy_translate[0], legume_domain[0][1] + xy_translate[1]),
                        (legume_domain[1][0] + xy_translate[0], legume_domain[1][1] + xy_translate[1]),
                    )
                # a été calculé au-dessus à  l'appel de create_heterogeneous_canopy
                wheat_domain = self.domain
                self.domain = (
                    (min(legume_domain[0][0], wheat_domain[0][0]), min(legume_domain[0][1], wheat_domain[0][1])),
                    (max(legume_domain[1][0], wheat_domain[1][0]), max(legume_domain[1][1], wheat_domain[1][1])),
                )
        else:
            self.type_domain = "input"
            self.domain = xy_plane

        # transmets l'information aux l-egumes (pour éviter d'avoir planter en input de l-egume (temporaire))
        for facade in legume_instances:
            facade.set_domain(self.domain)

    def generate_random_wheat(self, adel_wheat, mtg, indice_wheat_instance=0, seed=None):  
        var_leaf_inclination = 0.157
        var_leaf_azimut = 1.57
        var_stem_azimut = 0.157

        if seed is not None:
            s = seed
        else:
            s = 1234
        random.seed(s)
        numpy.random.seed(s)

        initial_scene = adel_wheat.scene(mtg)

        # tirage des positions
        # list de 3-tuple des positions
        if self.wheat_positions != [] and self.save_wheat_positions:
            positions = self.wheat_positions
        else:
            positions = []
            for i in range(self.wheat_nbplants[indice_wheat_instance]):
                positions.append((numpy.random.uniform(0.0, self.domain[1][0]), numpy.random.uniform(0.0, self.domain[1][0]), 0.0))

        if self.save_wheat_positions:
            self.wheat_positions = positions

        generated_scene =  self.__generate_wheat_from_positions(initial_scene,
                                                                    mtg,
                                                                    positions, 
                                                                    var_leaf_inclination,
                                                                    var_leaf_azimut,
                                                                    var_stem_azimut)

        return generated_scene

    def generate_row_wheat(self, adel_wheat, mtg, indice_wheat_instance=0, seed=None):
        var_leaf_inclination = 0.157
        var_leaf_azimut = 1.57
        var_stem_azimut = 0.157

        if seed is not None:
            s = seed
        else:
            s = 1234
        random.seed(s)
        numpy.random.seed(s)

        initial_scene = adel_wheat.scene(mtg)

        if self.wheat_positions != [] and self.save_wheat_positions:
            positions = self.wheat_positions
        else:
            positions = []

            inter_plants = 2 * self.domain[1][1] / self.wheat_nbplants[indice_wheat_instance]
            nrows = 2
            self.total_n_rows

            # first row on left 1/2 interrow, then 1 out of 2 row is wheat
            rows_y = [ self.inter_rows * 1.5, ((self.total_n_rows / nrows) + 1.5) * self.inter_rows ]
            for y in rows_y:
                for ix in range(int(self.wheat_nbplants[indice_wheat_instance] / nrows)):
                    x = inter_plants * (0.5 + ix)
                    p = (random.uniform(x - self.noise_plant_positions, x + self.noise_plant_positions),
                            random.uniform(y - self.noise_plant_positions, y + self.noise_plant_positions),
                            0.)
                    positions.append(p)
        
        if self.save_wheat_positions:
            self.wheat_positions = positions

        generated_scene =  self.__generate_wheat_from_positions(initial_scene,
                                                                    mtg,
                                                                    positions, 
                                                                    var_leaf_inclination,
                                                                    var_leaf_azimut,
                                                                    var_stem_azimut)

        return generated_scene

    def create_heterogeneous_canopy(
        self,
        geometrical_model,
        mtg=None,
        var_leaf_inclination=0.157,
        var_leaf_azimut=1.57,
        var_stem_azimut=0.157,
        seed=None,
    ):
        """
        Duplicate a plant in order to obtain a heterogeneous canopy.

        :param int nplants: the desired number of duplicated plants
        :param float var_plant_position: variability for plant position (m)
        :param float var_leaf_inclination: variability for leaf inclination (rad)
        :param float var_leaf_azimut: variability for leaf azimut (rad)
        :param float var_stem_azimut: variability for stem azimut (rad)
        :param string id_type: precise how to set the shape id of the elements : None, plant or organ

        :return: duplicated heterogenous scene and its domain
        :rtype: openalea.plantgl.all.Scene, (float)
        """
        if seed is not None:
            random.seed(seed)
            numpy.random.seed(seed)

        # Planter
        stand = AgronomicStand(
            sowing_density=self.plant_density[1],
            plant_density=self.plant_density[1],
            inter_row=self.inter_rows,
            noise=self.noise_plant_positions,
        )
        _, domain, positions, _ = stand.smart_stand(nplants=self.nb_wheat_plants, at=self.inter_rows, convunit=1)

        random.seed(1234)

        generated_scene =  self.__generate_wheat_from_positions(geometrical_model,
                                                                    mtg,
                                                                    positions, 
                                                                    var_leaf_inclination,
                                                                    var_leaf_azimut,
                                                                    var_stem_azimut)

        if self.type_domain == "create_heterogeneous_canopy":
            self.domain = domain

        return generated_scene

    def __generate_wheat_from_positions(self, 
                                        geometrical_model,
                                        mtg=None,
                                        positions=[(0.,0.,0.)], 
                                        var_leaf_inclination=0.157,
                                        var_leaf_azimut=1.57,
                                        var_stem_azimut=0.157):

        # Load scene
        if not isinstance(geometrical_model, plantgl.Scene):
            initial_scene = geometrical_model.scene(mtg)
        else:
            initial_scene = geometrical_model

        alea_canopy = pandas.DataFrame()
        
        # Built alea table if does not exist yet
        if alea_canopy.empty and mtg is not None:
            elements_vid_list = []
            for mtg_plant_vid in mtg.components_iter(mtg.root):
                for mtg_axis_vid in mtg.components_iter(mtg_plant_vid):
                    for mtg_metamer_vid in mtg.components_iter(mtg_axis_vid):
                        for mtg_organ_vid in mtg.components_iter(mtg_metamer_vid):
                            for mtg_element_vid in mtg.components_iter(mtg_organ_vid):
                                if mtg.label(mtg_element_vid) == "LeafElement1":
                                    elements_vid_list.append(mtg_element_vid)

            elements_vid_df = pandas.DataFrame({"vid": elements_vid_list, "tmp": 1})
            positions_df = pandas.DataFrame(
                {"pos": range(len(positions)), "tmp": 1, "azimut_leaf": 0, "inclination_leaf": 0}
            )
            alea = pandas.merge(elements_vid_df, positions_df, on=["tmp"])
            alea = alea.drop("tmp", axis=1)
            for vid in elements_vid_list:
                numpy.random.seed(vid)
                alea.loc[alea["vid"] == vid, "azimut_leaf"] = numpy.random.uniform(
                    -var_leaf_azimut, var_leaf_azimut, size=len(positions)
                )
                alea.loc[alea["vid"] == vid, "inclination_leaf"] = numpy.random.uniform(
                    -var_leaf_inclination, var_leaf_inclination, size=len(positions)
                )
            alea_canopy = alea

        # Duplication and heterogeneity
        duplicated_scene = plantgl.Scene()
        position_number = 0
        for pos in positions:
            azimut_stem = random.uniform(-var_stem_azimut, var_stem_azimut)
            for shp in initial_scene:
                if mtg.label(shp.id) == "StemElement":
                    rotated_geometry = plantgl.EulerRotated(azimut_stem, 0, 0, shp.geometry)
                    translated_geometry = plantgl.Translated(plantgl.Vector3(pos), rotated_geometry)
                    new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=shp.id)
                    duplicated_scene += new_shape
                elif mtg.label(shp.id) == "LeafElement1":
                    # Add shp.id in alea_canopy if not in yet:
                    if shp.id not in list(alea_canopy["vid"]):
                        new_vid_df = pandas.DataFrame({"vid": shp.id, "pos": range(len(positions))})
                        numpy.random.seed(shp.id)
                        new_vid_df["azimut_leaf"] = numpy.random.uniform(
                            -var_leaf_azimut, var_leaf_azimut, size=len(positions)
                        )
                        new_vid_df["inclination_leaf"] = numpy.random.uniform(
                            -var_leaf_inclination, var_leaf_inclination, size=len(positions)
                        )
                        alea_canopy = alea_canopy.copy().append(new_vid_df, sort=False)
                    # Translation to origin
                    anchor_point = mtg.get_vertex_property(shp.id)["anchor_point"]
                    trans_to_origin = plantgl.Translated(-anchor_point, shp.geometry)
                    # Rotation variability
                    azimut = alea_canopy.loc[
                        (alea_canopy.pos == position_number) & (alea_canopy.vid == shp.id), "azimut_leaf"
                    ].values[0]
                    inclination = alea_canopy.loc[
                        (alea_canopy.pos == position_number) & (alea_canopy.vid == shp.id), "inclination_leaf"
                    ].values[0]
                    rotated_geometry = plantgl.EulerRotated(azimut, inclination, 0, trans_to_origin)
                    # Restore leaf base at initial anchor point
                    translated_geometry = plantgl.Translated(anchor_point, rotated_geometry)
                    # Translate leaf to new plant position
                    translated_geometry = plantgl.Translated(pos, translated_geometry)
                    new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=shp.id)
                    duplicated_scene += new_shape

            position_number += 1

        return duplicated_scene
import numpy
import pandas


class Planter:
    def __init__(
        self,
        plantmodels=[],
        inter_rows=0.15,
        plant_density={1: 250},
        xy_plane=None,
        xy_translate=None
    ) -> None:
        from plantfusion.l_egume_facade import L_egume_facade
        from plantfusion.wheat_facade import Wheat_facade
        
        self.plant_density = plant_density
        self.inter_rows = inter_rows
        
        legume_instances = [facade for facade in plantmodels if isinstance(facade, L_egume_facade)]
        wheat_instances = [facade for facade in plantmodels if isinstance(facade, Wheat_facade)]
                       
        self.nb_plants = 0
        self.nb_wheat_plants = 50
        if wheat_instances != []:
            self.type_domain = "create_heterogeneous_canopy"
            setup_scene = self.create_heterogeneous_canopy(wheat_instances[0].adel_wheat, wheat_instances[0].g)
            self.nb_plants = self.nb_wheat_plants * len(wheat_instances)

        # if legume_instances != []:
        #     for facade in legume_instances:
        #         self.nb_plants += sum([facade.lsystems[n].tag_loop_inputs[11] for n in facade.idsimu])

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
                for i in range(len(facade.idsimu)) :
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
                    for i in range(len(facade.idsimu)) :
                        self.index["l-egume"].append(id_specy)
                        self.transformations["translate"][id_specy] = (xy_translate[0], xy_translate[1], 0)
                        id_specy += 1
                id_specy += 1

        # gestion du domain xy de définition
        if xy_plane is None :
            # si recalcul le domain via create_heterogeneous_canopy
            if legume_instances == [] :
                self.type_domain = "create_heterogeneous_canopy"
            elif wheat_instances == [] :
                self.type_domain = "l-egume"
                n = legume_instances[0].idsimu[0]
                # convertit domain cm en m
                self.domain = ((0., 0.), (legume_instances[0].lsystems[n].cote * 0.01, legume_instances[0].lsystems[n].cote * 0.01))
            else :
                n = legume_instances[0].idsimu[0]
                self.type_domain = "mix"
                legume_domain = ((0., 0.), (legume_instances[0].lsystems[n].cote * 0.01, legume_instances[0].lsystems[n].cote * 0.01))
                if xy_translate is not None:
                    legume_domain = ((legume_domain[0][0] + xy_translate[0], legume_domain[0][1] + xy_translate[1]),
                                     (legume_domain[1][0] + xy_translate[0], legume_domain[1][1] + xy_translate[1]))
                # a été calculé au-dessus à  l'appel de create_heterogeneous_canopy
                wheat_domain = self.domain 
                self.domain = ((min(legume_domain[0][0], wheat_domain[0][0]), min(legume_domain[0][1], wheat_domain[0][1])),
                               (max(legume_domain[1][0], wheat_domain[1][0]), max(legume_domain[1][1], wheat_domain[1][1])))
        else:
            self.type_domain = "input"
            self.domain = xy_plane

        # transmets l'information aux l-egumes (pour éviter d'avoir planter en input de l-egume (temporaire))
        for facade in legume_instances :
            facade.set_domain(self.domain)


    def create_heterogeneous_canopy(
        self,
        geometrical_model,
        mtg=None,
        var_plant_position=0.03,
        var_leaf_inclination=0.157,
        var_leaf_azimut=1.57,
        var_stem_azimut=0.157,
        id_type=None,
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
        from alinea.adel.Stand import AgronomicStand
        import openalea.plantgl.all as plantgl
        import random

        if seed is not None:
            random.seed(seed)
            numpy.random.seed(seed)

        # Load scene
        if not isinstance(geometrical_model, plantgl.Scene):
            initial_scene = geometrical_model.scene(mtg)
        else:
            initial_scene = geometrical_model

        alea_canopy = pandas.DataFrame()

        # Planter
        stand = AgronomicStand(
            sowing_density=self.plant_density[1], plant_density=self.plant_density[1], inter_row=self.inter_rows, noise=var_plant_position
        )
        _, domain, positions, _ = stand.smart_stand(nplants=self.nb_wheat_plants, at=self.inter_rows, convunit=1)

        random.seed(1234)

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
        new_id = 0
        if id_type == "organ":
            new_id = max([sh.id for sh in initial_scene]) + 1

        for pos in positions:
            azimut_stem = random.uniform(-var_stem_azimut, var_stem_azimut)
            for shp in initial_scene:
                if mtg is not None:
                    if mtg.label(shp.id) == "StemElement":
                        rotated_geometry = plantgl.EulerRotated(azimut_stem, 0, 0, shp.geometry)
                        translated_geometry = plantgl.Translated(plantgl.Vector3(pos), rotated_geometry)
                        if id_type == "organ":
                            new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=new_id)
                        elif id_type == "plant":
                            new_shape = plantgl.Shape(
                                translated_geometry, appearance=shp.appearance, id=position_number
                            )
                        else:
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

                        if id_type == "organ":
                            new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=new_id)
                        elif id_type == "plant":
                            new_shape = plantgl.Shape(
                                translated_geometry, appearance=shp.appearance, id=position_number
                            )
                        else:
                            new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=shp.id)
                        duplicated_scene += new_shape

                else:
                    rotated_geometry = plantgl.EulerRotated(azimut_stem, 0, 0, shp.geometry)
                    translated_geometry = plantgl.Translated(plantgl.Vector3(pos), rotated_geometry)
                    if id_type == "organ":
                        new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=new_id)
                    elif id_type == "plant":
                        new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=position_number)
                    else:
                        new_shape = plantgl.Shape(translated_geometry, appearance=shp.appearance, id=shp.id)
                    duplicated_scene += new_shape
                new_id += 1
            position_number += 1

        if self.type_domain == "create_heterogeneous_canopy" :
            self.domain = domain

        return duplicated_scene

    # @property
    # def domain(self):
    #     return self.domain

    # @property
    # def nb_plants(self):
    #     return self.nb_plants

    # @property
    # def plant_density(self):
    #     return self.plant_density

    # @property
    # def transformations(self):
    #     return self.transformations

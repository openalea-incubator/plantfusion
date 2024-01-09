from openalea.lpy import *
import openalea.lpy as lpy
import numpy
import pandas
from soil3ds import soil_moduleN as solN

from plante_rampante_functions import *

from plantfusion.planter import Planter
from plantfusion.indexer import Indexer

class PlanteRampante_Wrapper:
    def __init__(self, name, planter=Planter(), indexer=Indexer()) -> None:
        """Initialisation de l'interface

        Parameters
        ----------
        name : string
            nom personnalisé de notre instance de PlanteRampante
        planter : Planter, optional
            un planter pour récupère les dimensions xy du sol, by default Planter()
        indexer : Indexer, optional
            un indexer pour anticiper des simulations avec d'autres FSPM, by default Indexer()
        """        
        self.name = name
        self.name_lsystem = 'plante_rampante_aerien.lpy' 
        self.lsystem = lpy.Lsystem(self.name_lsystem)

        self.indexer = indexer
        self.global_index = indexer.global_order.index(name)

        self.nb_plant = 1

        # transfert du domaine du sol
        self.soilsurf = (planter.domain[1][0] - planter.domain[0][0]) ** 2

        # transfert de la position de la plante
        if planter.generation_type != "default":
            self.lsystem.carto = planter.generate_random_other()
            self.nb_plant = len(self.lsystem.carto)
            a = AxialTree()
            for i in range(self.nb_plant):
                a.append(self.lsystem.plante(i))
                a.append(self.lsystem.A(0, 1., 0))
            self.lsystem.axiom = a
        
            self.lsystem.nb_plt = self.nb_plant
            self.lsystem.ParamPN = [solN.default_paramp()] * self.nb_plant
            self.lsystem.ls_N = [1.] * self.nb_plant

        # simulation avec couplage lumiere
        self.lsystem.opt_external_coupling = 1

        # initialize lstring
        self.lstring = self.lsystem.axiom

        self.data_results = {"dMS" : [], "dMSRoot" : [], "epsi" : [], "roots_length" : [], "t" : []}

    def derive(self, t):
        """Dérivation d'une itération

        Parameters
        ----------
        t : int
            pas de temps
        """        
        self.lstring = self.lsystem.derive(self.lstring, t, 1)
        self.data_results["t"].append(t)
    
    def light_inputs(self):
        """Renvoie une scène géométrique en plantGL Scene

        Returns
        -------
        plantgl.Scene
            représentation de la scène
        """        
        return self.lsystem.sceneInterpretation(self.lstring)
        
    def light_results(self, light_results_per_organ, energy):
        """Interprète les résultats de lumière

        Parameters
        ----------
        light_results_per_organ : pandas.Dataframe
            Résultats d'ensoleillement par organe
        energy : float
            valeur de rayonnement intercepté
        """        
        organs_par = { "default_band" : { "Eabs" : {} , "Ei" : {}, "area" : {} } }
        df_filtered = light_results_per_organ[light_results_per_organ.VegetationType == self.global_index]
        for i in range(len(df_filtered)):
            organs_par["default_band"]["Eabs"][df_filtered.loc[i, "Organ"]] = df_filtered.loc[i, "par Eabs"]
            organs_par["default_band"]["Ei"][df_filtered.loc[i, "Organ"]] = df_filtered.loc[i, "par Ei"]
            organs_par["default_band"]["area"][df_filtered.loc[i, "Organ"]] = df_filtered.loc[i, "Area"]
        
        self.lstring, self.cumlight, ls_par = update_light_lstring(self.lstring, organs_par)

        #Carbon assimilation and allocation
        self.dMS = CarbonAssimilation(self.cumlight, energy, self.lsystem.RUE, self.lsystem.FTSW, Soilsurf=self.soilsurf)

        # plant light interception
        epsi =  self.cumlight / self.soilsurf
        self.ls_epsi = [epsi] * self.nb_plant # partage identique entre plantes

    def soil_inputs(self, soil_wrapper):
        """Renvoie les entrées nécessaire à soil3ds

        Parameters
        ----------
        soil_wrapper : Soil_wrapper
            façade du sol

        Returns
        -------
        list
            - teneur en N dans les racines pour chaque plante ([0, 1])
            - longeur des racines (en m) par plante et par voxel du sol
            - paramètres variétaux
            - capacité d'interception de la lumière par plante en fonction du couvert ([0, 1])
        """        
        self.roots_length = self.lsystem.roots_length
        roots_length_per_plant_per_soil_layer = roots_length_repartition(self.roots_length, 
                                                                            self.lsystem.carto, 
                                                                            soil_wrapper.soil.dxyz[0][0], 
                                                                            soil_wrapper.soil.origin, 
                                                                            soil_wrapper.soil_dimensions)

        N_content_roots_per_plant = self.lsystem.ls_N
        plants_soil_parameters = self.lsystem.ParamPN
        plants_light_interception = self.ls_epsi

        return (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            plants_soil_parameters,
            plants_light_interception,
        )

    def soil_results(self, uptakeN_per_plant):
        """Interprète l'uptake d'azote

        Parameters
        ----------
        uptakeN_per_plant : list
            uptake d'azote par plante et par voxel
        """        
        self.uptakeN = numpy.sum(uptakeN_per_plant[0])
        self.roots_length = growth_roots(self.roots_length, self.uptakeN, self.dMS)

    def run(self):
        self.lsystem.MS += self.dMS
        self.dMSRoot = self.dMS * self.lsystem.AllocRoot

        self.lsystem.root_length = self.roots_length
        self.lsystem.ls_epsi = self.ls_epsi

        self.data_results["dMS"].append(self.dMS)
        self.data_results["dMSRoot"].append(self.dMSRoot)
        self.data_results["epsi"].append(numpy.sum(self.ls_epsi))
        self.data_results["roots_length"].append(self.roots_length)

    def end(self):
         print(pandas.DataFrame(self.data_results))

def simulation_planterampante(iterations):
    from plantfusion.indexer import Indexer
    from plantfusion.light_wrapper import Light_wrapper
    from plantfusion.soil_wrapper import Soil_wrapper
    from plantfusion.planter import Planter

    name = "planterampante"
    indexer = Indexer(global_order=["plantrampante"], other_names=["plantrampante"])

    plane = ((-1., -1.), (0.1, 0.1))
    planter = Planter(xy_plane=plane)

    rampante = PlanteRampante_Wrapper(name, planter, indexer)

    light = Light_wrapper(lightmodel="caribu", planter=planter, infinite=True)
    soil = Soil_wrapper(in_folder="soil3ds_inputs", IDusm=1, planter=planter)

    IncomingLight = 0.001 # MJ.m-2-degredays-1 (jour cumulant 10 degres days)
    doy_start = 60
    for i in range(iterations):
        print("t: ",i)

        rampante.derive(i)

        # LIGHT #
        scene = rampante.light_inputs()
        light.run(scenes=[scene], day=i)
        rampante.light_results(light.results_organs(), energy=IncomingLight)

        # SOIL #
        (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            soil_plants_parameters,
            plants_light_interception,
        ) = rampante.soil_inputs(soil)
        soil.run(
            day=doy_start+i,
            N_content_roots_per_plant=[N_content_roots_per_plant],
            roots_length_per_plant_per_soil_layer=[roots_length_per_plant_per_soil_layer],
            soil_plants_parameters=[soil_plants_parameters],
            plants_light_interception=[plants_light_interception],
        )
        rampante.soil_results(soil.results[4])

        rampante.run()
    
    rampante.end()

def simulation_planterampante_wheat(iterations, in_folder, out_folder, write_geo):
    from plantfusion.indexer import Indexer
    from plantfusion.light_wrapper import Light_wrapper
    from plantfusion.soil_wrapper import Soil_wrapper
    from plantfusion.planter import Planter
    from plantfusion.wheat_wrapper import Wheat_wrapper

    # initialisation des noms et de l'indexer
    name1 = "planterampante"
    name2 = "wheat"
    indexer = Indexer(global_order=[name1, name2], wheat_names=[name2], other_names=[name1])
    
    # plantation des plantes
    plantdensity = {name1 : 10, name2 : 150}
    xy_square_length = 0.5
    planter = Planter(generation_type="random", indexer=indexer, plant_density=plantdensity, xy_square_length=xy_square_length)
    planter.transformations["scenes unit"][0] = "cm"
    # instance de plante rampante
    rampante = PlanteRampante_Wrapper(name1, planter, indexer)

    # paramètres d'entrée pour WheatFSPM
    RERmax_vegetative_stages_example = {
        "elongwheat": {
            "RERmax": {5: 3.35e-06, 6: 2.1e-06, 7: 2.0e-06, 8: 1.83e-06, 9: 1.8e-06, 10: 1.65e-06, 11: 1.56e-06}
        }
    }
    tillers_replications = {"T1": 0.5, "T2": 0.5, "T3": 0.5, "T4": 0.5}
    senescwheat_timestep = 1
    light_timestep = 4

    # instance de WheatFspm
    wheat = Wheat_wrapper(
        in_folder=in_folder,
        name=name2,
        out_folder=out_folder,
        planter=planter,
        indexer=indexer,
        external_soil_model=True,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        tillers_replications=tillers_replications,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
        SOIL_PARAMETERS_FILENAME="inputs_soil_legume/Parametres_plante_exemple.xls"
    )

    # instance pour la lumière
    light = Light_wrapper(lightmodel="caribu", indexer=indexer, planter=planter, out_folder=out_folder, infinite=True, writegeo=write_geo)
    
    # instance pour le sol
    soil = Soil_wrapper(in_folder="soil3ds_inputs", IDusm=1, planter=planter)

    # énergie constante pour plante rampante
    IncomingLight = 0.001 # MJ.m-2-degredays-1 (jour cumulant 10 degres days)
    # itérations de plante rampante
    t_pr = 0
    doy_start = 60
    
    # RUN SIMULATION #
    for t_wheat in range(wheat.start_time, iterations, wheat.SENESCWHEAT_TIMESTEP):
        ## conditions pour calculer l'environnement
        # on change de jour
        activate_planterampante = wheat.doy(t_wheat) != wheat.next_day_next_hour(t_wheat)
        # la soleil est levé
        daylight = (t_wheat % light_timestep == 0) and (wheat.PARi_next_hours(t_wheat) > 0)

        if daylight or activate_planterampante:
            # derive le lsystem avant la lumière et le sol
            if activate_planterampante:
                rampante.derive(t_pr)

            # LIGHT #
            scene1 = rampante.light_inputs()
            scene2, stems = wheat.light_inputs(planter)
            scenes = indexer.light_scenes_mgmt({name1 : scene1, name2 : scene2})
            light.run(
                scenes=scenes,
                day=wheat.doy(t_wheat),
                hour=wheat.hour(t_wheat),
                parunit="RG",
                stems=stems
            )

            # transmets la lumière à wheat
            if daylight:
                wheat.light_results(energy=wheat.energy(t_wheat), lighting=light)

            if activate_planterampante:
                # transmets la lumière à plante rampante
                rampante.light_results(light.results_organs(), energy=IncomingLight)

                # SOIL #
                soil_wheat_inputs = wheat.soil_inputs(soil, planter, light)
                soil_planterampante_inputs = rampante.soil_inputs(soil)
                (
                    N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer,
                    plants_soil_parameters,
                    plants_light_interception,
                ) = indexer.soil_inputs({name1 : soil_planterampante_inputs, name2 : soil_wheat_inputs})
                soil.run(
                    day=doy_start+t_pr,
                    N_content_roots_per_plant=N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer=roots_length_per_plant_per_soil_layer,
                    soil_plants_parameters=plants_soil_parameters,
                    plants_light_interception=plants_light_interception,
                )
                rampante.soil_results(soil.results[4])
                wheat.soil_results(soil.results[4], planter=planter)

                rampante.run()
                t_pr += 1
        
        wheat.run(t_wheat)
    
    rampante.end()

if __name__ == "__main__":
    iterations = 1000
    in_folder_wheat = "inputs_fspmwheat"
    out_folder = "outputs"
    write_geo = True
    simulation_planterampante_wheat(iterations, in_folder_wheat, out_folder, write_geo)
from plantfusion.wheat_wrapper import Wheat_wrapper
from plantfusion.l_egume_wrapper import L_egume_wrapper
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.indexer import Indexer
from plantfusion.planter import Planter

import time
import datetime
import os


def simulation(
    in_folder_legume, in_folder_wheat, out_folder, simulation_length, id_usm, run_postprocessing=False, writegeo=False
):
    try:
        # Create target Directory
        os.mkdir(os.path.normpath(out_folder))
        print("Directory ", os.path.normpath(out_folder), " Created ")
    except FileExistsError:
        print("Directory ", os.path.normpath(out_folder), " already exists")

    ######################
    ### INITIALIZATION ###
    ######################

    wheat_name = "wheat"
    legume_name = "legume"
    indexer = Indexer(global_order=[legume_name, wheat_name], wheat_names=[wheat_name], legume_names=[legume_name])

    tillers_replications = {"T1": 0.5, "T2": 0.5, "T3": 0.5, "T4": 0.5}
    plant_density = {1: 250}
    sky = "turtle46"
    RERmax_vegetative_stages_example = {
        "elongwheat": {
            "RERmax": {5: 3.35e-06, 6: 2.1e-06, 7: 2.0e-06, 8: 1.83e-06, 9: 1.8e-06, 10: 1.65e-06, 11: 1.56e-06}
        }
    }
    senescwheat_timestep = 1
    light_timestep = 4

    generation_type = "random"
    plant_density = {wheat_name : 250, legume_name : 450}
    planter = Planter(generation_type=generation_type, indexer=indexer, plant_density=plant_density, save_wheat_positions=True)

    legume = L_egume_wrapper(
        name=legume_name, indexer=indexer, in_folder=in_folder_legume, out_folder=out_folder, IDusm=id_usm, planter=planter, caribu_scene=True
    )

    wheat = Wheat_wrapper(
        in_folder=in_folder_wheat,
        out_folder=out_folder,
        planter=planter,
        indexer=indexer,
        external_soil_model=True,
        nitrates_uptake_forced=False,
        tillers_replications=tillers_replications,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
        SOIL_PARAMETERS_FILENAME="inputs_soil_legume/Parametres_plante_exemple.xls"
    )

    lighting = Light_wrapper(
        lightmodel="caribu", 
        out_folder=out_folder, 
        sky=sky,
        planter=planter, 
        indexer=indexer,
        legume_wrapper=legume,
        writegeo=writegeo
    )

    soil = Soil_wrapper(in_folder=in_folder_legume, 
                        out_folder=out_folder, 
                        IDusm=id_usm, 
                        legume_wrapper=legume, 
                        planter=planter, 
                        opt_residu=0, 
                        save_results=True)
    soil_dimensions = [len(soil.soil.dxyz[i]) for i in [2,0,1] ]
    
    ##################
    ### SIMULATION ###
    ##################

    current_time_of_the_system = time.time()
    t_legume = 0
    nb_iter = int(wheat.meteo.loc[0, ["DOY"]].iloc[0] - legume.lsystem.DOYdeb)

    # onlylegume_index = 0
    # save_planter_nb_plants = planter.number_of_plants
    # planter.number_of_plants[onlylegume_index] = planter.number_of_plants[legume.global_index]
    
    for t in range(nb_iter):

        legume.derive(t)

        scene_legume = legume.light_inputs(elements="triangles")
        lighting.run(scenes=[scene_legume], day=legume.doy(), parunit="RG")
        legume.light_results(legume.energy(), lighting)

        (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            plants_soil_parameters,
            plants_light_interception,
        ) = legume.soil_inputs()
        soil.run(
            legume.doy(),
            [N_content_roots_per_plant],
            [roots_length_per_plant_per_soil_layer],
            [plants_soil_parameters],
            [plants_light_interception],
        )
        legume.soil_results(soil.results, planter)

        legume.run()

        t_legume += 1

    # planter.number_of_plants = save_planter_nb_plants

    lighting.i_vtk = lighting.i_vtk
    for t_wheat in range(wheat.start_time, simulation_length, wheat.SENESCWHEAT_TIMESTEP):
        activate_legume = wheat.doy(t_wheat) != wheat.next_day_next_hour(t_wheat)
        daylight = (t_wheat % light_timestep == 0) and (wheat.PARi_next_hours(t_wheat) > 0)

        if daylight or activate_legume:
            if activate_legume:
                legume.derive(t_legume)

            wheat_input, stems = wheat.light_inputs(planter)
            legume_input = legume.light_inputs(elements="triangles")
            scenes = indexer.light_scenes_mgmt({wheat_name : wheat_input, legume_name : legume_input})

            lighting.run(
                scenes=scenes,
                day=wheat.doy(t_wheat),
                hour=wheat.hour(t_wheat),
                parunit="RG",
                stems=stems
            )
            if daylight:
                wheat.light_results(energy=wheat.energy(t_wheat), lighting=lighting)

            if activate_legume:
                legume.light_results(legume.energy(), lighting)

                soil_wheat_inputs = wheat.soil_inputs(soil, planter, lighting)
                soil_legume_inputs = legume.soil_inputs()
                (
                    N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer,
                    plants_soil_parameters,
                    plants_light_interception,
                ) = indexer.soil_inputs({legume_name : soil_legume_inputs, wheat_name : soil_wheat_inputs})
                
                soil.run(
                    legume.doy(),
                    N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer,
                    plants_soil_parameters,
                    plants_light_interception
                )
                wheat.soil_results(soil.results[4], planter=planter)
                legume.soil_results(soil.results)

                legume.run()
                t_legume += 1

        wheat.run(t_wheat)

    execution_time = int(time.time() - current_time_of_the_system)
    print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))


    legume.end()
    wheat.end(run_postprocessing=run_postprocessing)
    soil.end()


if __name__ == "__main__":
    in_folder_legume = "inputs_soil_legume"
    in_folder_wheat = "inputs_fspmwheat"
    out_folder = "outputs/full_coupling_default"
    simulation_length = 2500
    id_usm = 9
    writegeo = True

    simulation(in_folder_legume, in_folder_wheat, out_folder, simulation_length, id_usm, writegeo=writegeo)

from plantfusion.wheat_wrapper import Wheat_wrapper
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.indexer import Indexer
from plantfusion.planter import Planter

import time
import datetime
import os


def simulation(
    in_folder, out_folder, simulation_length, run_postprocessing=False, writegeo=False
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

    wheat1_name = "wheat1"
    wheat2_name = "wheat2"
    indexer = Indexer(global_order=[wheat1_name, wheat2_name], wheat_names=[wheat1_name, wheat2_name])


    tillers_replications = {"T1": 0.5, "T2": 0.5, "T3": 0.5, "T4": 0.5}
    sky = "turtle46"
    RERmax_vegetative_stages_example = {
        "elongwheat": {
            "RERmax": {5: 3.35e-06, 6: 2.1e-06, 7: 2.0e-06, 8: 1.83e-06, 9: 1.8e-06, 10: 1.65e-06, 11: 1.56e-06}
        }
    }
    senescwheat_timestep = 1
    light_timestep = 4

    generation_type = "row"
    plant_density = {wheat1_name : 250, wheat2_name : 450} # plantes.m-2
    inter_rows = 0.10 # m
    planter = Planter(generation_type=generation_type, indexer=indexer, plant_density=plant_density, inter_rows=inter_rows, save_wheat_positions=True)


    wheat1 = Wheat_wrapper(
        name=wheat1_name,
        in_folder=in_folder,
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

    wheat2 = Wheat_wrapper(
        name=wheat2_name,
        in_folder=in_folder,
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
        writegeo=writegeo
    )

    soil = Soil_wrapper(in_folder="inputs_soil_legume", 
                        out_folder=out_folder, 
                        IDusm=1711, 
                        planter=planter, 
                        opt_residu=0, 
                        save_results=True)
    soil_dimensions = [len(soil.soil.dxyz[i]) for i in [2,0,1] ]
    
    ##################
    ### SIMULATION ###
    ##################

    current_time_of_the_system = time.time()
    for t_wheat in range(wheat1.start_time, simulation_length, wheat1.SENESCWHEAT_TIMESTEP):
        activate_soil = wheat1.doy(t_wheat) != wheat1.next_day_next_hour(t_wheat)
        daylight = (t_wheat % light_timestep == 0) and (wheat1.PARi_next_hours(t_wheat) > 0)

        if daylight or activate_soil:

            wheat_input1, stems1 = wheat1.light_inputs(planter)
            wheat_input2, stems2 = wheat2.light_inputs(planter)
            scenes = indexer.light_scenes_mgmt({wheat1_name : wheat_input1, wheat2_name : wheat_input2})

            lighting.run(
                scenes=scenes,
                day=wheat1.doy(t_wheat),
                hour=wheat1.hour(t_wheat),
                parunit="micromol.m-2.s-1",
                stems=stems1.extend(stems2)
            )
            if daylight:
                wheat1.light_results(energy=wheat1.energy(t_wheat), lighting=lighting)
                wheat2.light_results(energy=wheat2.energy(t_wheat), lighting=lighting)

            if activate_soil:
                soil_wheat_inputs1 = wheat1.soil_inputs(soil, planter, lighting)
                soil_wheat_inputs2 = wheat2.soil_inputs(soil, planter, lighting)
                (
                    N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer,
                    plants_soil_parameters,
                    plants_light_interception,
                ) = indexer.soil_inputs({wheat1_name : soil_wheat_inputs1, wheat2_name : soil_wheat_inputs2})
                
                soil.run(
                    wheat1.doy(t_wheat, soil3ds=True),
                    N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer,
                    plants_soil_parameters,
                    plants_light_interception
                )
                wheat1.soil_results(soil.results[4], planter=planter)
                wheat2.soil_results(soil.results[4], planter=planter)

        wheat1.run(t_wheat)
        wheat2.run(t_wheat)

    execution_time = int(time.time() - current_time_of_the_system)
    print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    wheat1.end(run_postprocessing=run_postprocessing)
    wheat2.end(run_postprocessing=run_postprocessing)
    soil.end()


if __name__ == "__main__":
    in_folder = "inputs_fspmwheat"
    out_folder = "outputs/two_wheats"
    simulation_length = 2500
    writegeo = True

    simulation(in_folder, out_folder, simulation_length, writegeo=writegeo)

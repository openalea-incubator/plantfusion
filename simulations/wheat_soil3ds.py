from plantfusion.wheat_wrapper import Wheat_wrapper
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.planter import Planter
from plantfusion.indexer import Indexer

import time
import datetime
import os


def simulation(in_folder, out_folder, simulation_length, write_geo=False, run_postprocessing=False):
    try:
        # Create target Directory
        os.mkdir(os.path.normpath(out_folder))
        print("Directory ", os.path.normpath(out_folder), " Created ")
    except FileExistsError:
        print("Directory ", os.path.normpath(out_folder), " already exists")

    tillers_replications = {"T1": 0.5, "T2": 0.5, "T3": 0.5, "T4": 0.5}
    plant_density = {1: 250}
    sky = [4, 5, "soc"]
    RERmax_vegetative_stages_example = {
        "elongwheat": {
            "RERmax": {5: 3.35e-06, 6: 2.1e-06, 7: 2.0e-06, 8: 1.83e-06, 9: 1.8e-06, 10: 1.65e-06, 11: 1.56e-06}
        }
    }
    senescwheat_timestep = 1
    light_timestep = 4

    plants_name = "wheat"
    index_log = Indexer(global_order=[plants_name], wheat_names=[plants_name])

    planter = Planter(generation_type="default", indexer=index_log, inter_rows=0.15, plant_density=plant_density)

    wheat = Wheat_wrapper(
        in_folder=in_folder,
        out_folder=out_folder,
        planter=planter,
        indexer=index_log,
        external_soil_model=True,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        tillers_replications=tillers_replications,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
        SOIL_PARAMETERS_FILENAME="inputs_soil_legume/Parametres_plante_exemple.xls"
    )


    lighting = Light_wrapper(
        lightmodel="caribu", 
        out_folder=out_folder, 
        sky=sky,
        planter=planter, 
        indexer=index_log,
        writegeo=write_geo
    )

    soil = Soil_wrapper(in_folder="inputs_soil_legume", out_folder=out_folder, IDusm=17111, planter=planter, save_results=True)

    current_time_of_the_system = time.time()
    for t in range(wheat.start_time, simulation_length, wheat.SENESCWHEAT_TIMESTEP):

        if ((t % light_timestep == 0) and (wheat.PARi_next_hours(t) > 0)) or (wheat.doy(t) != wheat.next_day_next_hour(t)):
            wheat_input, stems = wheat.light_inputs(planter)
            lighting.run(scenes=[wheat_input], day=wheat.doy(t), hour=wheat.hour(t), parunit="micromol.m-2.s-1", stems=stems)
            
            if ((t % light_timestep == 0) and (wheat.PARi_next_hours(t) > 0)) :
                wheat.light_results(energy=wheat.energy(t), lighting=lighting)

            if (wheat.doy(t)  != wheat.next_day_next_hour(t) ) :
                (
                    N_content_roots_per_plant,
                    roots_length_per_plant_per_soil_layer,
                    wheat_soil_parameters,
                    plants_light_interception,
                ) = wheat.soil_inputs(soil, planter, lighting)
                soil.run(
                    wheat.doy(t, soil3ds=True),
                    [N_content_roots_per_plant],
                    [roots_length_per_plant_per_soil_layer],
                    [wheat_soil_parameters],
                    [plants_light_interception],
                )
                wheat.soil_results(soil.results[4])

        wheat.run(t)

    execution_time = int(time.time() - current_time_of_the_system)
    print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))


    wheat.end(run_postprocessing=run_postprocessing)
    soil.end()


if __name__ == "__main__":
    in_folder = "inputs_fspmwheat"
    out_folder = "outputs/cnwheat_soil3ds"
    simulation_length = 2500
    write_geo = True

    simulation(in_folder, out_folder, simulation_length, write_geo)

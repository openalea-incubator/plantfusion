from plantfusion.wheat_wrapper import Wheat_wrapper, passive_lighting
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.indexer import Indexer
from plantfusion.planter import Planter
from plantfusion.utils import create_child_folder

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

    create_child_folder(out_folder, "passive")
    create_child_folder(out_folder, "active")

    plants_name = "wheat"
    index_log = Indexer(global_order=[plants_name], wheat_names=[plants_name])

    N_fertilizations = {2016: 357143, 2520: 1000000}
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
    planter = Planter(generation_type="default", indexer=index_log, inter_rows=0.15, plant_density=plant_density)

    # default
    wheat_default = Wheat_wrapper(
        in_folder=in_folder,
        out_folder=os.path.join(out_folder, "passive"),
        planter=planter,
        indexer=index_log,
        external_soil_model=False,
        nitrates_uptake_forced=False,
        N_fertilizations=N_fertilizations,
        tillers_replications=tillers_replications,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
    )

    lighting_default = Light_wrapper(
        lightmodel="caribu", 
        out_folder=out_folder, 
        sky=sky,
        planter=planter, 
        indexer=index_log,
        writegeo=write_geo
    )

    # RATP parameters
    dv = 0.05
    voxels_size = [dv, dv, dv]

    wheat_ratp = Wheat_wrapper(
        in_folder=in_folder,
        out_folder=os.path.join(out_folder, "active"),
        planter=planter,
        indexer=index_log,
        external_soil_model=False,
        nitrates_uptake_forced=False,
        N_fertilizations=N_fertilizations,
        tillers_replications=tillers_replications,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
    )

    lighting_ratp = Light_wrapper(
        lightmodel="ratp", 
        out_folder=out_folder, 
        sky=sky,
        planter=planter, 
        indexer=index_log,
        voxels_size=voxels_size,
        angle_distrib_algo="compute global",
        writegeo=write_geo
    )

    light_data = {"PARa": [], "t": []}


    current_time_of_the_system = time.time()
    for t in range(wheat_default.start_time, simulation_length, wheat_default.SENESCWHEAT_TIMESTEP):
        if (t % light_timestep == 0) and (wheat_default.PARi_next_hours(t) > 0):
            wheat_input, stems = wheat_default.light_inputs(planter)
            passive_lighting(light_data, t, wheat_default.doy(t), wheat_input, lighting_ratp, stems)
            
            start = time.time()
            lighting_default.run(scenes=[wheat_input], day=wheat_default.doy(t), hour=wheat_default.hour(t), parunit="micromol.m-2.s-1", stems=stems)
            caribu_time = time.time() - start

            wheat_default.light_results(energy=wheat_default.energy(t), lighting=lighting_default)

            wheat_input, stems = wheat_ratp.light_inputs(planter)
            start = time.time()
            lighting_ratp.run(scenes=[wheat_input], day=wheat_ratp.doy(t), hour=wheat_ratp.hour(t), parunit="micromol.m-2.s-1", stems=stems)
            ratp_time = time.time() - start
            
            wheat_ratp.light_results(energy=wheat_ratp.energy (t), lighting=lighting_ratp)

            print("Lighting running time | CARIBU: ",caribu_time,"RATP: ",ratp_time)

        wheat_default.run(t)
        wheat_ratp.run(t)

    execution_time = int(time.time() - current_time_of_the_system)
    print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    wheat_default.end(run_postprocessing=run_postprocessing)
    wheat_ratp.end(run_postprocessing=run_postprocessing)


if __name__ == "__main__":
    in_folder = "inputs_fspmwheat"
    out_folder = "outputs/cnwheat_ratp"
    simulation_length = 2500
    write_geo = True

    simulation(in_folder, out_folder, simulation_length, write_geo)

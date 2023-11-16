from plantfusion.wheat_facade import Wheat_facade, passive_lighting
from plantfusion.environment_tool import Environment
from plantfusion.light_facade import Light
from plantfusion.planter import Planter
from plantfusion.utils import create_child_folder

import time
import datetime
import os


def simulation(in_folder, out_folder, simulation_length, run_postprocessing=False):
    create_child_folder(out_folder, "passive")
    create_child_folder(out_folder, "active")

    # general parameters
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

    environment = Environment(
        sky=sky, N_fertilizations=N_fertilizations, tillers_replications=tillers_replications, external_soil=False
    )

    wheat_default = Wheat_facade(
        in_folder=in_folder,
        out_folder=os.path.join(out_folder, "passive"),
        environment=environment,
        plant_density=plant_density,
        external_soil_model=False,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
    )

    plants_positions_default = Planter(plantmodels=[wheat_default], inter_rows=0.15, plant_density=plant_density)

    lighting_default = Light(
        lightmodel="caribu",
        wheat_facade=wheat_default,
        position=plants_positions_default,
        environment=environment,
        writegeo=False,
    )

    # RATP parameters
    dv = 0.05
    voxels_size = [dv, dv, dv]

    wheat_ratp = Wheat_facade(
        in_folder=in_folder,
        out_folder=os.path.join(out_folder, "active"),
        environment=environment,
        plant_density=plant_density,
        external_soil_model=False,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
    )

    plants_positions_ratp = Planter(plantmodels=[wheat_ratp], inter_rows=0.15, plant_density=plant_density)

    lighting_ratp = Light(
        lightmodel="ratp",
        wheat_facade=wheat_ratp,
        position=plants_positions_ratp,
        environment=environment,
        voxels_size=voxels_size,
        angle_distrib_algo="compute global",
        writegeo=False,
    )

    light_data = {"PARa": [], "t": []}

    try:
        current_time_of_the_system = time.time()
        for t in range(wheat_default.start_time, simulation_length, wheat_default.SENESCWHEAT_TIMESTEP):
            if (t % light_timestep == 0) and (wheat_default.PARi_next_hours(t) > 0):
                wheat_input = wheat_default.light_inputs(plants_positions_default)
                passive_lighting(light_data, t, wheat_default.doy(t), wheat_input, lighting_ratp)
                
                start = time.time()
                lighting_default.run(scenes_wheat=wheat_input, day=wheat_default.doy(t), hour=wheat_default.hour(t), parunit="micromol.m-2.s-1")
                caribu_time = time.time() - start

                wheat_default.light_results(energy=wheat_default.energy(t), lighting=lighting_default)

                wheat_input = wheat_ratp.light_inputs(plants_positions_ratp)
                start = time.time()
                lighting_ratp.run(scenes_wheat=wheat_input, day=wheat_ratp.doy(t), hour=wheat_ratp.hour(t), parunit="micromol.m-2.s-1")
                ratp_time = time.time() - start
                
                wheat_ratp.light_results(energy=wheat_ratp.energy (t), lighting=lighting_ratp)

                print("Lighting running time | CARIBU: ",caribu_time,"RATP: ",ratp_time)

            wheat_default.run(t)
            wheat_ratp.run(t)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        wheat_default.end(run_postprocessing=run_postprocessing)
        wheat_ratp.end(run_postprocessing=run_postprocessing)


if __name__ == "__main__":
    in_folder = "inputs_fspmwheat"
    out_folder = "outputs/cnwheat_ratp"
    simulation_length = 50

    simulation(in_folder, out_folder, simulation_length)

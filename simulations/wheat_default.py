from plantfusion.wheat_wrapper import Wheat_wrapper
from plantfusion.environment_tool import Environment
from plantfusion.light_wrapper import Light
from plantfusion.planter import Planter

import time
import datetime


def simulation(in_folder, out_folder, simulation_length, write_geo=False, run_postprocessing=False):
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

    wheat = Wheat_wrapper(
        in_folder=in_folder,
        out_folder=out_folder,
        environment=environment,
        plant_density=plant_density,
        external_soil_model=False,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
    )

    plants_positions = Planter(plantmodels=[wheat], inter_rows=0.15, plant_density=plant_density)

    lighting = Light(
        lightmodel="caribu", 
        out_folder=out_folder, 
        position=plants_positions, 
        environment=environment, 
        wheat_wrapper=wheat, 
        writegeo=write_geo
    )

    try:
        current_time_of_the_system = time.time()
        for t in range(wheat.start_time, simulation_length, wheat.SENESCWHEAT_TIMESTEP):
            if (t % light_timestep == 0) and (wheat.PARi_next_hours(t) > 0):
                wheat_input = wheat.light_inputs(plants_positions)
                lighting.run(scenes_wheat=[wheat_input], day=wheat.doy(t), hour=wheat.hour(t), parunit="micromol.m-2.s-1")
                wheat.light_results(energy=wheat.energy(t), lighting=lighting)

            wheat.run(t)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        wheat.end(run_postprocessing=run_postprocessing)


if __name__ == "__main__":
    in_folder = "inputs_fspmwheat"
    out_folder = "outputs/cnwheat_default"
    simulation_length = 2500
    write_geo = True

    simulation(in_folder, out_folder, simulation_length, write_geo=write_geo)

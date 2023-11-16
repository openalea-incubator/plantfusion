from plantfusion.wheat_facade import Wheat_facade
from plantfusion.environment_tool import Environment
from plantfusion.light_facade import Light
from plantfusion.planter import Planter
from plantfusion.soil3ds_facade import Soil_facade

import time
import datetime


def simulation(in_folder, out_folder, simulation_length, run_postprocessing=False):
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

    environment = Environment(sky=sky, tillers_replications=tillers_replications, external_soil=True)

    wheat = Wheat_facade(
        in_folder=in_folder,
        out_folder=out_folder,
        environment=environment,
        plant_density=plant_density,
        external_soil_model=True,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
        SOIL_PARAMETERS_FILENAME="inputs_soil_legume/Parametres_plante_exemple.xls"
    )

    plants_positions = Planter(plantmodels=[wheat], inter_rows=0.15, plant_density=plant_density)

    lighting = Light(
        lightmodel="caribu", position=plants_positions, environment=environment, wheat_facade=wheat, writegeo=False
    )

    soil = Soil_facade(in_folder="inputs_soil_legume", out_folder=out_folder, IDusm=1714, position=plants_positions, save_results=True)
    soil_dimensions = [len(soil.soil.dxyz[i]) for i in [2,0,1] ]

    try:
        current_time_of_the_system = time.time()
        for t in range(wheat.start_time, simulation_length, wheat.SENESCWHEAT_TIMESTEP):

            if ((t % light_timestep == 0) and (wheat.PARi_next_hours(t) > 0)) or (wheat.doy(t) != wheat.next_day_next_hour(t)):
                wheat_input = wheat.light_inputs(plants_positions)
                lighting.run(scenes_wheat=wheat_input, day=wheat.doy(t), hour=wheat.hour(t), parunit="micromol.m-2.s-1")
                
                if ((t % light_timestep == 0) and (wheat.PARi_next_hours(t) > 0)) :
                    wheat.light_results(energy=wheat.energy(t), lighting=lighting)

                if (wheat.doy(t)  != wheat.next_day_next_hour(t) ) :
                    (
                        N_content_roots_per_plant,
                        roots_length_per_plant_per_soil_layer,
                        wheat_soil_parameters,
                        plants_light_interception,
                    ) = wheat.soil_inputs(soil_dimensions, lighting)
                    soil.run(
                        wheat.doy(t),
                        [N_content_roots_per_plant],
                        [roots_length_per_plant_per_soil_layer],
                        [wheat_soil_parameters],
                        [plants_light_interception],
                    )
                    wheat.soil_results(soil.results[4])

            wheat.run(t)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        wheat.end(run_postprocessing=run_postprocessing)
        soil.end()


if __name__ == "__main__":
    in_folder = "inputs_fspmwheat"
    out_folder = "outputs/cnwheat_soil3ds"
    simulation_length = 50

    simulation(in_folder, out_folder, simulation_length)

from wheatfusion.l_egume_facade import L_egume_facade
from wheatfusion.wheat_facade import Wheat_facade
from wheatfusion.environment_tool import Environment
from wheatfusion.light_facade import Light
from wheatfusion.soil3ds_facade import Soil_facade
from wheatfusion.planter import Planter

import time
import datetime


def simulation(in_folder_legume, in_folder_wheat, out_folder, simulation_length, run_postprocessing=False, writegeo=False):
    N_fertilizations = {2016: 357143, 2520: 1000000}
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

    environment = Environment(
        sky=sky, N_fertilizations=N_fertilizations, tillers_replications=tillers_replications, external_soil=False
    )

    wheat = Wheat_facade(
        in_folder=in_folder_wheat,
        out_folder=out_folder,
        environment=environment,
        plant_density=plant_density,
        external_soil_model=False,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
    )

    legume = L_egume_facade(in_folder=in_folder_legume, out_folder=out_folder, environment=environment)

    translate = (-0.21, -0.21)
    plants_positions = Planter(plantmodels=[wheat, legume], inter_rows=0.15, plant_density=plant_density, xy_translate=translate)

    soil = Soil_facade(in_folder=in_folder_legume, out_folder=out_folder, legume_facade=legume, position=plants_positions, legume_pattern=True)

    lighting = Light(
        out_folder=out_folder,
        lightmodel="caribu",
        position=plants_positions,
        environment=environment,
        wheat_facade=wheat,
        legume_facade=legume,
        writegeo=writegeo,
    )
  
    try:
        # start simulation
        t_legume = 0
        current_time_of_the_system = time.time()
        for t_wheat in range(wheat.start_time, simulation_length, wheat.SENESCWHEAT_TIMESTEP):

            activate_legume = wheat.doy(t_wheat) != wheat.next_day_next_hour(t_wheat)
            daylight = (t_wheat % light_timestep == 0) and (wheat.PARi_next_hours(t_wheat) > 0)

            if daylight or activate_legume:
                if activate_legume:
                    legume.derive(t_legume)

                wheat_input = wheat.light_inputs(plants_positions)
                legume_input = legume.light_inputs("caribu")
                lighting.run(
                    scenes_wheat=wheat_input,
                    scenes_l_egume=legume_input,
                    day=wheat.doy(t_wheat),
                    hour=wheat.hour(t_wheat),
                    parunit="RG",
                )
                if daylight:
                    wheat.light_results(energy=wheat.energy(t_wheat), lighting=lighting)

                if activate_legume:
                    legume.light_results(legume.energy(), lighting)

                    soil_legume_inputs = legume.soil_inputs()
                    soil.run(legume.doy(), legume_inputs=soil_legume_inputs)
                    legume.soil_results(soil.inputs, soil.results)

                    legume.run()

                    t_legume += 1

            wheat.run(t_wheat)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        legume.end()
        wheat.end(run_postprocessing=run_postprocessing)


if __name__ == "__main__":
    in_folder_legume = "inputs_soil_legume"
    in_folder_wheat = "inputs_fspmwheat"
    out_folder = "outputs/light_coupling"
    simulation_length = 2500
    writegeo = True

    simulation(in_folder_legume, in_folder_wheat, out_folder, simulation_length, writegeo=writegeo)

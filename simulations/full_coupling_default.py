from plantfusion.l_egume_facade import L_egume_facade
from plantfusion.wheat_facade import Wheat_facade
from plantfusion.environment_tool import Environment
from plantfusion.light_facade import Light
from plantfusion.soil3ds_facade import Soil_facade
from plantfusion.planter import Planter

import time
import datetime


def simulation(
    in_folder_legume, in_folder_wheat, out_folder, simulation_length, run_postprocessing=False, writegeo=False
):
    ######################
    ### INITIALIZATION ###
    ######################

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

    environment = Environment(sky=sky, tillers_replications=tillers_replications, external_soil=True)

    wheat = Wheat_facade(
        in_folder=in_folder_wheat,
        out_folder=out_folder,
        environment=environment,
        plant_density=plant_density,
        external_soil_model=True,
        nitrates_uptake_forced=False,
        update_parameters_all_models=RERmax_vegetative_stages_example,
        SENESCWHEAT_TIMESTEP=senescwheat_timestep,
        LIGHT_TIMESTEP=light_timestep,
        SOIL_PARAMETERS_FILENAME="inputs_soil_legume/Parametres_plante_exemple.xls",
    )

    legume = L_egume_facade(in_folder=in_folder_legume, out_folder=out_folder, IDusm=[9, 10])

    translate = (-0.21, -0.21)
    plants_positions = Planter(
        generation_type="default",
        plantmodels=[wheat, legume], 
        inter_rows=0.15, 
        plant_density=plant_density, 
        xy_translate=translate, 
        noise_plant_positions=0.03
    )

    soil = Soil_facade(
        in_folder=in_folder_legume,
        out_folder=out_folder,
        IDusm=9,
        legume_facade=legume,
        position=plants_positions,
        save_results=True,
    )
    soil_dimensions = [len(soil.soil.dxyz[i]) for i in [2, 0, 1]]

    lighting = Light(
        lightmodel="caribu",
        out_folder=out_folder,
        position=plants_positions,
        environment=environment,
        legume_facade=legume,
        writegeo=writegeo,
    )

    # pour legume seul
    plants_positions_legume = Planter(
        plantmodels=[legume]
    )
    lighting_legume = Light(
        lightmodel="caribu",
        out_folder=out_folder,
        position=plants_positions_legume,
        environment=environment,
        wheat_facade=wheat,
        legume_facade=legume,
        writegeo=writegeo,
    )
    soil_legume = Soil_facade(
        in_folder=in_folder_legume,
        out_folder=out_folder,
        IDusm=9,
        legume_facade=legume,
        position=plants_positions_legume,
        save_results=True,
    )
    
    ##################
    ### SIMULATION ###
    ##################

    current_time_of_the_system = time.time()
    t_legume = 0
    nb_iter = int(wheat.meteo.loc[0, ["DOY"]].iloc[0] - legume.lsystems[legume.idsimu[0]].DOYdeb)
    for t in range(nb_iter):
        legume.derive(t)

        scene_legume = legume.light_inputs(lightmodel="caribu")
        lighting_legume.run(scenes_l_egume=scene_legume, energy=1., day=legume.doy(), parunit="RG")
        legume.light_results(legume.energy(), lighting_legume)

        soil_legume_inputs = legume.soil_inputs()
        soil_legume.run(legume.doy(), legume_inputs=soil_legume_inputs)
        legume.soil_results(soil_legume.inputs, soil_legume.results)

        legume.run()
        t_legume += 1

    try:
        lighting.i_vtk = lighting_legume.i_vtk
        for t_wheat in range(wheat.start_time, simulation_length, wheat.SENESCWHEAT_TIMESTEP):
            activate_legume = wheat.doy(t_wheat) != wheat.next_day_next_hour(t_wheat)
            daylight = (t_wheat % light_timestep == 0) and (wheat.PARi_next_hours(t_wheat) > 0)

            if daylight or activate_legume:
                if activate_legume:
                    legume.derive(t_legume)

                wheat_input = wheat.light_inputs(plants_positions)
                legume_input = legume.light_inputs("caribu")
                lighting.run(
                    scenes_wheat=[wheat_input],
                    scenes_l_egume=legume_input,
                    day=wheat.doy(t_wheat),
                    hour=wheat.hour(t_wheat),
                    parunit="RG",
                )
                if daylight:
                    wheat.light_results(energy=wheat.energy(t_wheat), lighting=lighting)

                if activate_legume:
                    legume.light_results(legume.energy(), lighting)

                    (
                        N_content_roots_per_plant,
                        roots_length_per_plant_per_soil_layer,
                        wheat_soil_parameters,
                        plants_light_interception,
                    ) = wheat.soil_inputs(soil_dimensions, lighting)
                    soil_legume_inputs = legume.soil_inputs()
                    soil.run(
                        legume.doy(),
                        [N_content_roots_per_plant],
                        [roots_length_per_plant_per_soil_layer],
                        [wheat_soil_parameters],
                        [plants_light_interception],
                        legume_inputs=soil_legume_inputs,
                    )
                    wheat.soil_results(soil.results[4])
                    legume.soil_results(soil.inputs, soil.results)

                    legume.run()
                    t_legume += 1

            wheat.run(t_wheat)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        legume.end()
        wheat.end(run_postprocessing=run_postprocessing)
        soil.end()


if __name__ == "__main__":
    in_folder_legume = "inputs_soil_legume"
    in_folder_wheat = "inputs_fspmwheat"
    out_folder = "outputs/full_coupling_default"
    simulation_length = 2500
    writegeo = True

    simulation(in_folder_legume, in_folder_wheat, out_folder, simulation_length, writegeo=writegeo)

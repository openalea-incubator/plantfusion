from plantfusion.l_egume_wrapper import L_egume_wrapper, passive_lighting
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.planter import Planter
from plantfusion.indexer import Indexer
from plantfusion.utils import create_child_folder

import os
import time
import datetime
import pandas


def simulation(in_folder, out_folder, id_usm, write_geo=False):
    try:
        # Create target Directory
        os.mkdir(os.path.normpath(out_folder))
        print("Directory ", os.path.normpath(out_folder), " Created ")
    except FileExistsError:
        print("Directory ", os.path.normpath(out_folder), " already exists")

    create_child_folder(out_folder, "passive")
    create_child_folder(out_folder, "active")

    plants_name = "legume"
    index_log = Indexer(global_order=[plants_name], legume_names=[plants_name])


    # version par défaut
    planter = Planter(indexer=index_log, legume_cote={plants_name : 40.}, legume_number_of_plants={plants_name : 64})
    legume_default = L_egume_wrapper(
        name=plants_name, indexer=index_log, in_folder=in_folder, out_folder=os.path.join(out_folder, "passive"), IDusm=id_usm, caribu_scene=True, planter=planter
    )
    lighting_default = Light_wrapper(lightmodel="riri5", indexer=index_log, planter=planter, legume_wrapper=legume_default)
    soil_default = Soil_wrapper(out_folder=os.path.join(out_folder, "passive"), legume_wrapper=legume_default, legume_pattern=True, planter=planter)


    # lumiere avec caribu
    planter = Planter(indexer=index_log, legume_cote={plants_name : 40.}, legume_number_of_plants={plants_name : 64})
    legume_caribu = L_egume_wrapper(
        name=plants_name, indexer=index_log, in_folder=in_folder, out_folder=os.path.join(out_folder, "active"), IDusm=id_usm, caribu_scene=True, planter=planter
    )
    lighting_caribu = Light_wrapper(
        lightmodel="caribu",
        indexer=index_log, 
        planter=planter, 
        legume_wrapper=legume_caribu,
        sky="inputs_soil_legume/sky_5.data",
        writegeo=False,
    )
    soil_caribu = Soil_wrapper(out_folder=os.path.join(out_folder, "active"), legume_wrapper=legume_caribu,  legume_pattern=True, planter=planter)

    light_data = {"epsi": [], "parip": [], "t": []}


    try:
        current_time_of_the_system = time.time()
        for t in range(legume_default.lsystem.derivationLength):
            legume_default.derive(t)
            legume_caribu.derive(t)

            ### DEFAULT + PASSIVE
            scene_legume = legume_default.light_inputs(elements="triangles")
            passive_lighting(
                light_data, legume_default.energy(), legume_default.doy(), scene_legume, legume_default, lighting_caribu
            )

            scene_legume = legume_default.light_inputs(elements="voxels")
            start = time.time()
            lighting_default.run(
                scenes=[scene_legume], energy=legume_default.energy(), day=legume_default.doy(), parunit="RG"
            )
            riri5_time = time.time() - start
            legume_default.light_results(legume_default.energy(), lighting_default)

            (
                N_content_roots_per_plant,
                roots_length_per_plant_per_soil_layer,
                plants_soil_parameters,
                plants_light_interception,
            ) = legume_default.soil_inputs()
            soil_default.run(
                legume_default.doy(),
                [N_content_roots_per_plant],
                [roots_length_per_plant_per_soil_layer],
                [plants_soil_parameters],
                [plants_light_interception],
            )
            legume_default.soil_results(soil_default.results, planter)

            ### CARIBU
            scene_legume = legume_caribu.light_inputs(elements="triangles")
            start = time.time()
            lighting_caribu.run(
                scenes=[scene_legume], day=legume_caribu.doy(), parunit="RG"
            )
            caribu_time = time.time() - start
            legume_caribu.light_results(legume_caribu.energy(), lighting_caribu)

            (
                N_content_roots_per_plant,
                roots_length_per_plant_per_soil_layer,
                plants_soil_parameters,
                plants_light_interception,
            ) = legume_caribu.soil_inputs()
            soil_caribu.run(
                legume_caribu.doy(),
                [N_content_roots_per_plant],
                [roots_length_per_plant_per_soil_layer],
                [plants_soil_parameters],
                [plants_light_interception],
            )
            legume_caribu.soil_results(soil_caribu.results, planter)

            legume_default.run()
            legume_caribu.run()

            print("Lighting running time | RiRi5: ", riri5_time, "CARIBU: ", caribu_time)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        legume_default.end()
        legume_caribu.end()

        # write lighting passive RATP results
        filename = "lighting_results.csv"
        filepath = os.path.join(os.path.normpath(out_folder), "passive", "legume", "brut", filename)
        pandas.DataFrame(light_data).to_csv(filepath)


if __name__ == "__main__":
    in_folder = "inputs_soil_legume"
    out_folder = "outputs/legume_caribu"
    write_geo = False

    simulation(in_folder, out_folder, 1711, write_geo)

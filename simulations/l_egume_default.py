from plantfusion.indexer import Indexer
from plantfusion.l_egume_wrapper import L_egume_wrapper
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.planter import Planter

import time
import datetime
import os


def simulation(in_folder, out_folder, id_usm):
    try:
        # Create target Directory
        os.mkdir(os.path.normpath(out_folder))
        print("Directory ", os.path.normpath(out_folder), " Created ")
    except FileExistsError:
        print("Directory ", os.path.normpath(out_folder), " already exists")

    plants_name = "legume"
    index_log = Indexer(global_order=[plants_name], legume_names=[plants_name])

    legume = L_egume_wrapper(
        name=plants_name, indexer=index_log, in_folder=in_folder, out_folder=out_folder, IDusm=id_usm
    )

    planter = Planter(generation_type="default", indexer=index_log, legume_wrapper=legume)

    lighting = Light_wrapper(lightmodel="riri5", indexer=index_log, planter=planter, legume_wrapper=legume)

    soil = Soil_wrapper(in_folder=in_folder, out_folder=out_folder, legume_wrapper=legume, planter=planter)

    try:
        current_time_of_the_system = time.time()
        for t in range(legume.lsystem.derivationLength):
            legume.derive(t)

            scene_legume = legume.light_inputs(lightmodel="riri5")
            lighting.run(scenes=[scene_legume], energy=legume.energy(), day=legume.doy(), parunit="RG")
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
    
    finally:
        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

        legume.end()


if __name__ == "__main__":
    in_folder = "inputs_soil_legume"
    out_folder = "outputs/legume_default"
    id_usm = 1711

    simulation(in_folder, out_folder, id_usm)

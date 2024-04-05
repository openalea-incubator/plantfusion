from plantfusion.l_egume_wrapper import L_egume_wrapper
from plantfusion.light_wrapper import Light_wrapper
from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.indexer import Indexer
from plantfusion.planter import Planter

import time
import datetime
import os


def simulation(in_folder, out_folder, idusm1, idusm2, writegeo=False):
    try:
        # Create target Directory
        os.mkdir(os.path.normpath(out_folder))
        print("Directory ", os.path.normpath(out_folder), " Created ")
    except FileExistsError:
        print("Directory ", os.path.normpath(out_folder), " already exists")

    ######################
    ### INITIALIZATION ###
    ######################

    legume1_name = "legume1"
    legume2_name = "legume2"
    indexer = Indexer(global_order=[legume1_name, legume2_name], legume_names=[legume1_name, legume2_name])

    generation_type = "default"
    planter = Planter(generation_type=generation_type, 
                      indexer=indexer,  
                      legume_cote={legume1_name : 40., legume2_name : 40.}, 
                      legume_number_of_plants={legume1_name : 32, legume2_name : 32})

    legume1 = L_egume_wrapper(name=legume1_name, indexer=indexer, planter=planter, in_folder=in_folder, out_folder=out_folder, IDusm=idusm1)

    legume2 = L_egume_wrapper(name=legume2_name, indexer=indexer, planter=planter, in_folder=in_folder, out_folder=out_folder, IDusm=idusm2)


    sky = "turtle46"
    lighting = Light_wrapper(
        lightmodel="ratp", 
        out_folder=out_folder, 
        sky=sky,
        planter=planter, 
        indexer=indexer,
        legume_wrapper=[legume1, legume2],
        writegeo=writegeo
    )

    soil = Soil_wrapper(in_folder=in_folder, 
                        out_folder=out_folder, 
                        IDusm=1711, 
                        planter=planter, 
                        legume_wrapper=legume1,
                        opt_residu=0, 
                        save_results=True)
    
    ##################
    ### SIMULATION ###
    ##################

    current_time_of_the_system = time.time()
    for t in range(legume1.lsystem.derivationLength):
        legume1.derive(t)
        legume2.derive(t)

        scene_legume1 = legume1.light_inputs(elements="voxels")
        scene_legume2 = legume2.light_inputs(elements="voxels")
        lighting.run(scenes=[scene_legume1, scene_legume2], day=legume1.doy(), parunit="RG")
        legume1.light_results(legume1.energy(), lighting)
        legume2.light_results(legume2.energy(), lighting)

        soil_legume_inputs1 = legume1.soil_inputs()
        soil_legume_inputs2 = legume2.soil_inputs()
        (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            plants_soil_parameters,
            plants_light_interception,
        ) = indexer.soil_inputs({legume1_name : soil_legume_inputs1, legume2_name : soil_legume_inputs2})
        soil.run(
            legume1.doy(),
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            plants_soil_parameters,
            plants_light_interception,
        )
        legume1.soil_results(soil.results, planter)
        legume2.soil_results(soil.results, planter)

        legume1.run()
        legume2.run()

    execution_time = int(time.time() - current_time_of_the_system)
    print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    legume1.end()
    legume2.end()
    soil.end()


if __name__ == "__main__":
    in_folder = "inputs_soil_legume"
    out_folder = "outputs/two_legume_ratp"
    id1 = 17111
    id2 = 17112
    writegeo = False

    simulation(in_folder, out_folder, id1, id2, writegeo=writegeo)

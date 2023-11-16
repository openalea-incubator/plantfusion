from wheatfusion.l_egume_facade import L_egume_facade
from wheatfusion.environment_tool import Environment
from wheatfusion.light_facade import Light
from wheatfusion.soil3ds_facade import Soil_facade
from wheatfusion.planter import Planter

import time
import datetime


def simulation(in_folder, out_folder):
    environment = Environment(external_soil=False)

    legume = L_egume_facade(in_folder=in_folder, out_folder=out_folder, environment=environment)

    plants_positions = Planter(plantmodels=[legume])

    lighting = Light(lightmodel="riri5", position=plants_positions, environment=environment, legume_facade=legume)

    soil = Soil_facade(in_folder=in_folder, out_folder=out_folder, legume_facade=legume, position=plants_positions)

    nb_steps = max([legume.lsystems[n].derivationLength for n in legume.idsimu])

    try:
        current_time_of_the_system = time.time()
        for t in range(nb_steps):
            legume.derive(t)

            scene_legume = legume.light_inputs(lightmodel="riri5")
            lighting.run(scenes_l_egume=scene_legume, energy=legume.energy(), day=legume.doy(), parunit="RG")
            legume.light_results(legume.energy(), lighting)

            soil_legume_inputs = legume.soil_inputs()
            soil.run(legume.doy(), legume_inputs=soil_legume_inputs)
            legume.soil_results(soil.inputs, soil.results)

            legume.run()

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        legume.end()


if __name__ == "__main__":
    in_folder = "inputs_soil_legume"
    out_folder = "outputs/legume_default"

    simulation(in_folder, out_folder)

from plantfusion.l_egume_facade import L_egume_facade, passive_lighting
from plantfusion.environment_tool import Environment
from plantfusion.light_facade import Light
from plantfusion.soil3ds_facade import Soil_facade
from plantfusion.planter import Planter
from plantfusion.utils import create_child_folder

import os
import time
import datetime
import pandas


def simulation(in_folder, out_folder):
    create_child_folder(out_folder, "passive")
    create_child_folder(out_folder, "active")

    # version par défaut
    environment = Environment(external_soil=False)
    legume_default = L_egume_facade(in_folder=in_folder, out_folder=os.path.join(out_folder, "passive"))
    plants_positions = Planter(plantmodels=[legume_default])
    lighting_default = Light(
        lightmodel="riri5",
        position=plants_positions,
        environment=environment,
        writegeo=False,
        legume_facade=legume_default,
    )
    soil_default = Soil_facade(
        in_folder=in_folder,
        out_folder=os.path.join(out_folder, "passive"),
        legume_facade=legume_default,
        position=plants_positions,
    )

    # lumiere avec RATP
    environment = Environment(sky="inputs_soil_legume/sky_5.data", external_soil=False)
    legume_ratp = L_egume_facade(in_folder=in_folder, out_folder=os.path.join(out_folder, "active"))
    plants_positions = Planter(plantmodels=[legume_ratp])
    lighting_ratp = Light(
        lightmodel="ratp",
        position=plants_positions,
        environment=environment,
        angle_distrib_algo="compute global",
        writegeo=False,
        legume_facade=legume_ratp,
    )
    soil_ratp = Soil_facade(
        in_folder=in_folder,
        out_folder=os.path.join(out_folder, "active"),
        legume_facade=legume_ratp,
        position=plants_positions,
    )

    nb_steps = max([legume_default.lsystems[n].derivationLength for n in legume_default.idsimu])

    light_data = [{"epsi": [], "parip": [], "t": []} for n in legume_default.idsimu]

    try:
        current_time_of_the_system = time.time()
        for t in range(nb_steps):
            legume_default.derive(t)
            legume_ratp.derive(t)

            scene_legume = legume_default.light_inputs(lightmodel="riri5")
            passive_lighting(
                light_data, legume_default.energy(), legume_default.doy(), scene_legume, legume_default, lighting_ratp
            )

            start = time.time()
            lighting_default.run(
                scenes_l_egume=scene_legume, energy=legume_default.energy(), day=legume_default.doy(), parunit="RG"
            )
            riri5_time = time.time() - start
            legume_default.light_results(legume_default.energy(), lighting_default)

            soil_legume_inputs = legume_default.soil_inputs()
            soil_default.run(legume_default.doy(), legume_inputs=soil_legume_inputs)
            legume_default.soil_results(soil_default.inputs, soil_default.results)

            scene_legume = legume_ratp.light_inputs(lightmodel="ratp")
            start = time.time()
            lighting_ratp.run(
                scenes_l_egume=scene_legume, energy=legume_ratp.energy(), day=legume_ratp.doy(), parunit="RG"
            )
            ratp_time = time.time() - start
            legume_ratp.light_results(legume_ratp.energy(), lighting_ratp)

            soil_legume_inputs = legume_ratp.soil_inputs()
            soil_ratp.run(legume_ratp.doy(), legume_inputs=soil_legume_inputs)
            legume_ratp.soil_results(soil_ratp.inputs, soil_ratp.results)

            legume_default.run()
            legume_ratp.run()

            print("Lighting running time | RiRi5: ", riri5_time, "RATP: ", ratp_time)

        execution_time = int(time.time() - current_time_of_the_system)
        print("\n" "Simulation run in {}".format(str(datetime.timedelta(seconds=execution_time))))

    finally:
        legume_default.end()
        legume_ratp.end()

        # write lighting passive RATP results
        for i, n in enumerate(legume_default.idsimu):
            filename = "lighting_results" + "_" + n + ".csv"
            filepath = os.path.join(os.path.normpath(out_folder), "passive", "legume", "brut", filename)
            pandas.DataFrame(light_data[i]).to_csv(filepath)


if __name__ == "__main__":
    in_folder = "inputs_soil_legume"
    out_folder = "outputs/legume_ratp"

    simulation(in_folder, out_folder)

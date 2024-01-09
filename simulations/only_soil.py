from plantfusion.soil_wrapper import Soil_wrapper
from plantfusion.planter import Planter


def simulation(iterations, in_folder, out_folder, id_usm):
    plane = ((0.0, 0.0), (1.0, 1.0))
    planter = Planter(xy_plane=plane)
    soil = Soil_wrapper(in_folder=in_folder, out_folder=out_folder, IDusm=id_usm, planter=planter, save_results=True)

    for i in range(60, 60 + iterations):
        (
            N_content_roots_per_plant,
            roots_length_per_plant_per_soil_layer,
            soil_plants_parameters,
            plants_light_interception,
        ) = soil.bare_soil_inputs()
        soil.run(
            day=i,
            N_content_roots_per_plant=[N_content_roots_per_plant],
            roots_length_per_plant_per_soil_layer=[roots_length_per_plant_per_soil_layer],
            soil_plants_parameters=[soil_plants_parameters],
            plants_light_interception=[plants_light_interception],
        )
    
    soil.end()
    print("--- END ---")


if __name__ == "__main__":
    in_folder = "inputs_soil_legume"
    out_folder = "outputs/baresoil"
    simulation(10, in_folder, out_folder, 1711)

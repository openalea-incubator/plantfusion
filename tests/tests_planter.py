from plantfusion.l_egume_facade import L_egume_facade
from plantfusion.wheat_facade import Wheat_facade
from plantfusion.planter import Planter
import openalea.plantgl.all as pgl

plant_density = {1: 250}
xy_square_length = 0.5

generation_type = "random"

planter = Planter(
    generation_type=generation_type,
    plantmodels=["wheat", "legume"], 
    plant_density=plant_density, 
    xy_square_length=xy_square_length
)

wheat = Wheat_facade(in_folder="inputs_fspmwheat", planter=planter)
legume = L_egume_facade(in_folder="inputs_soil_legume", planter=planter)
legume.derive(0)


legume_scene = legume.light_inputs(lightmodel="caribu")
scene = []
for l in legume_scene :
    for s in l:
        scene.append(pgl.Shape(pgl.Scaled(0.01, s.geometry), s.appearance, s.id))

scene = wheat.light_inputs(planter) + legume.light_inputs(lightmodel="caribu")
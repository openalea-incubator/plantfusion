from plantfusion.l_egume_facade import L_egume_facade
from plantfusion.wheat_facade import Wheat_facade
from plantfusion.planter import Planter
import openalea.plantgl.all as pgl
import random

plant_density = {"legume": [250], "wheat" : [250]}
inter_rows = 0.15

generation_type = "row"

planter = Planter(
    generation_type=generation_type,
    plant_density=plant_density, 
    inter_rows=inter_rows
)

wheat = Wheat_facade(in_folder="inputs_fspmwheat", planter=planter)
legume = L_egume_facade(in_folder="inputs_soil_legume", planter=planter)
legume.derive(0)

legume_scene_cm = legume.light_inputs(lightmodel="caribu")
legume_scene = []
for l in legume_scene_cm :
    mat = pgl.Material((random.randint(0,255),random.randint(0,255),random.randint(0,255)))
    for s in l:
        legume_scene.append(pgl.Shape(pgl.Scaled(0.01, s.geometry), mat, s.id))

scene = wheat.light_inputs(planter) + legume_scene
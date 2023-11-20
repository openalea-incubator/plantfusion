from plantfusion.l_egume_facade import L_egume_facade
from plantfusion.wheat_facade import Wheat_facade
from plantfusion.planter import Planter
import openalea.plantgl.all as pgl
import random

def translate_scenes(scene, indice, transformations):
    if indice in transformations["translate"] :
        new_scene = []
        mat = pgl.Material((random.randint(0,255),random.randint(0,255),random.randint(0,255)))
        for shape in scene:
            new_scene.append(pgl.Shape(pgl.Translated(transformations["translate"][indice], shape.geometry), mat, shape.id))
        return pgl.Scene(new_scene)
    else:
        return scene
    
def scene_cm_tp_m(scenes_cm):
    scene_m = []
    for scene in scenes_cm :
        mat = pgl.Material((random.randint(0,255),random.randint(0,255),random.randint(0,255)))
        for shape in scene:
            scene_m.append(pgl.Shape(pgl.Scaled(0.01, shape.geometry), mat, shape.id))
    return scene_m

generation_type = "row"
plant_density = {"wheat" : [90, 150], "legume" : [100, 200]} # plantes.m-2
plantmodels = ["wheat", "legume", "wheat", "legume"]
inter_rows = 0.10 # m

planter = Planter(
    plantmodels=plantmodels,
    generation_type=generation_type,
    plant_density=plant_density, 
    inter_rows=inter_rows,
    noise_plant_positions=0.01
)

wheat1 = Wheat_facade(in_folder="inputs_fspmwheat", planter=planter)
wheat2 = Wheat_facade(in_folder="inputs_fspmwheat", planter=planter)
legume1 = L_egume_facade(in_folder="inputs_soil_legume", planter=planter, planter_index=0)
legume2 = L_egume_facade(in_folder="inputs_soil_legume", planter=planter, planter_index=1)
legume1.derive(0)
legume2.derive(0)

legume1_scene_cm = legume1.light_inputs(lightmodel="caribu")
legume1_scene = scene_cm_tp_m(legume1_scene_cm)
legume2_scene_cm = legume2.light_inputs(lightmodel="caribu")
legume2_scene = scene_cm_tp_m(legume2_scene_cm)

scenes = [wheat1.light_inputs(planter, planter_index=0)[0], 
          legume1_scene, 
          wheat2.light_inputs(planter, planter_index=1)[0], 
          legume2_scene]
final_scene = pgl.Scene()
for i, scene in enumerate(scenes):
    final_scene = final_scene + translate_scenes(scene, i, planter.transformations)

print("END")
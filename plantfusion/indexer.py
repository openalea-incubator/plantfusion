# legume : 1 wrapper = 1 usm = 1 espèce de plante


class Indexer:
    def __init__(self, global_order=[], wheat_names=[], legume_names=[], other_names=[]) -> None:
        self.global_order = global_order
        self.wheat_names = wheat_names
        self.legume_names = legume_names
        self.other_names = other_names

        self.legume_active = legume_names != []
        self.wheat_active = wheat_names != []

        self.wheat_index = [global_order.index(name) for name in wheat_names if name in global_order]
        self.legume_index = [global_order.index(name) for name in legume_names if name in global_order]
        self.other_index = [global_order.index(name) for name in other_names if name in global_order]

    def light_scenes_mgmt(self, scenes_dict):
        scenes = [0.] * len(self.global_order)
        for name, geo in scenes_dict.items():
            scenes[self.global_order.index(name)] = geo
        return scenes



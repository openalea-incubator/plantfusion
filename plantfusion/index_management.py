# legume : 1 wrapper = 1 usm = 1 espèce de plante


class IndexManagement:
    def __init__(self, global_order=[], wheat_names=[], legume_names=[]) -> None:
        self.global_order = global_order
        self.wheat_names = wheat_names
        self.legume_names = legume_names

        self.legume_active = legume_names != []
        self.wheat_active = wheat_names != []

        self.wheat_index = [global_order.index(name) for name in wheat_names if name in global_order]
        self.legume_index = [global_order.index(name) for name in legume_names if name in global_order]

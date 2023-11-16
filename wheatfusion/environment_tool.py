class Environment(object):
    def __init__(
        self,
        sky="turtle46",
        direct=False,
        diffuse=True,
        coordinates=[46.4, 0.0, 1.0],
        external_soil=False,
        N_fertilizations={2016: 357143, 2520: 1000000},
        tillers_replications={"T1": 0.5, "T2": 0.5, "T3": 0.5, "T4": 0.5},
    ) -> None:
        self.external_soil = external_soil
        if external_soil:
            self.N_fertilizations = {}
        else:
            self.N_fertilizations = N_fertilizations

        self.tillers_replications = tillers_replications

        lighting_environment = {
            "coordinates": coordinates,
            "sky": sky,
            "direct": direct,
            "diffus": diffuse,
            "reflected": False,
            "infinite": True,
        }

        self.light = lighting_environment

    # @property
    # def external_soil(self):
    #     return self.external_soil

    # @property
    # def light(self):
    #     return self.light

    # @property
    # def N_fertilization(self):
    #     return self.N_fertilization

    # @property
    # def tillers_replication(self):
    #     return self.tillers_replication

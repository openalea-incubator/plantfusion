class Environment(object):
    def __init__(
        self,
        sky="turtle46",
        direct=False,
        diffuse=True,
        coordinates=[46.4, 0.0, 1.0],
    ) -> None:
        lighting_environment = {
            "coordinates": coordinates,
            "sky": sky,
            "direct": direct,
            "diffus": diffuse,
            "reflected": False,
            "infinite": True,
        }

        self.light = lighting_environment


"""
"""

Config = {
    'pseudo_random': True,
    'pseudo_random_seed': 5454334,

    'camera': {
        'debug': False,
    },

    # Terrainc configuration
    "terrain_size":512,
    "terrain_maxheight":18,
    "terrain_width":512,

    "terrain": {
        "flat": False,               # do not generate noise
        "forest": True,             # display forest
        "city": True,               # generate a city
        "roads": True,
        "debug_flatness": False,     # help position procedural city by findind a flat place
        "download": True,
        "debug": {
            "normals": False,        # display normals of terrain meshes
            "boundingsphere": False,
            "wireframe": False,      # display terrain meshes as wireframe
            "lod": False,            # display meshes LOD as colored wireframe
            'uv': False              # use a standard shader with an UV texture
        },
        'display_scenary': True
    },

    "river": {
        "display": True,
        "debug": {
            "path": False
        }
    },

    "skybox": True,

    "player": {
        "debug": {
            "collision": False,
            "direction": False,
            "boundingsphere": False,
            "frustrum": False
        },
        "tps": True
    },

    'shadow': {
        'enabled': True,
        'size': 512,
        'debug': False
    }
}

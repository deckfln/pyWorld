"""
"""

Config = {
    'folder': 'd:/dev/pyworld',
    'pseudo_random': True,
    'pseudo_random_seed': 5454334,

    'camera': {
        'debug': False,
    },

    # Terrainc configuration
    "terrain_size": 512,
    "terrain_maxheight": 18,
    "terrain_width": 512,

    "terrain": {
        "flat": False,               # do not generate noise
        "forest": True,             # display forest
        "city": True,               # generate a city
        "roads": True,
        "debug_flatness": False,     # help position procedural city by findind a flat place
        "download": True,
        "debug": {
            "normals": False,        # display normals of terrain meshes
            "boundingsphere": False, # display the boundingSphere around the tiles
            "wireframe": False,      # display terrain meshes as wireframe
            "lod": False,            # display meshes LOD as colored wireframe
            'uv': False              # use a standard shader with an UV texture
        },
        'display_scenary': False,
        'display_grass': False,
        "indexmap": {
            "size": 32,
            "repeat": 128
        },
        "blendmap": {
            "size": 256
        }

    },

    "river": {
        "display": True,
        "debug": {
            "path": False
        }
    },

    "skybox": True,                 # display the skybox
    'time': False,                  # time passes

    "player": {
        "debug": {
            "collision": False,
            "direction": False,
            "boundingsphere": False,
            "frustrum": False
        },
        "tps": True,
        "position": [22.8510658816, -11.0726747753],
        "collision": False
    },

    'shadow': {
        'enabled': False,
        'size': 1024,
        'debug': False
    },

    "benchmark": False,

    "engine": {
        "player": "models/marie-jane.dae",
        "assets": {
            'evergreen': [
                "models/anime_tree/1/model",
                "models/anime_tree/2/model",
                "models/anime_tree/3/model",
                "models/anime_tree/4/model",
                "models/anime_tree/D0406452B11"
                ],
            "tree": [
                "models/old-tree/1/model",
                "models/old-tree/2/model",
                "models/old-tree/3/model",
                "models/old-tree/4/model",
                "models/old-tree/model"
                ],
            "house": [
                "models/wooden_house/wooden_house",
                "models/wooden_house/wooden_house",
                "models/wooden_house/wooden_house",
                "models/wooden_house/wooden_house",
                "models/wooden_house/wooden_house"
            ]
        },
        "dynamic_asset": {
            "grass": "models/grass/grass",
            'high grass': "models/grass2/grass",
            'prairie': "models/flower/obj__flow2",
            'forest': "models/forest/obj__fern3",
            'forest1': "models/forest1/obj__shr3",
            'forest2': "models/forest2/obj__fern2"
        },
        "skycube": [
            "img/skybox/front.png",
            'img/skybox/left.png',
            'img/skybox/right.png',
            'img/skybox/back.png',
            'img/skybox/top.png',
            'img/skybox/bottom.png'
        ]
    }
}

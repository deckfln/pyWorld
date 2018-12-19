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
    "terrain": {
        "size": 512,         # heightmap size
        "max_height": 18,
        "width": 512,        # terrain size onscreen
        "lods": 6,           # #level of details

        "flat": False,               # do not generate noise
        "forest": True,              # display forest
        "city": True,                # generate a city
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
        "direction": [0.3, 0],
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
        "shaders": {
            "terrain": {
                "vertex": "shaders/terrain/vertex.glsl",
                "fragment": "shaders/terrain/fragment.glsl",
                "textures": {
                    "indexmap": "img/indexmap.png",
                    "blendmap": "img/blendmap.png",
                    "terrain_d": "img/terrain_d.png",
                    "terrain_far_d": "img/terrain_far_d.png",
                    "terrain_very_far_d": "img/terrain_very_far_d.png",
                    "terrain_n": "img/terrain_n.png"
                }
            },
            "terrain_debug": {
                "vertex": "shaders/terrain/debug/vertex.glsl",
                "fragment": "shaders/terrain/debug/fragment.glsl",
                "textures": {
                    "uv": "img/UV_Grid_Sm.jpg"
                }
            },
            'asset': {
                'vertex': 'shaders/instances/vertex.glsl',
                'fragment': 'shaders/instances/fragment.glsl'
            },
            'asset_depth': {
                'vertex': 'shaders/instances/depth_vertex.glsl',
                'fragment': 'shaders/instances/depth_fragment.glsl'
            },
            'grass': {
                'vertex': 'shaders/dynamic_instances/vertex_grass.glsl',
                'fragment': 'shaders/dynamic_instances/fragment.glsl'
            },
            'skybox': {
                'vertex': 'shaders/skybox/vertex.glsl',
                'fragment': 'shaders/skybox/fragment.glsl'
            }
        },
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


def full_path(folder, file):
    if ':/' not in file:
        return folder + file


def update_config():
    folder = Config['folder'] + '/'

    skycube = Config["engine"]["skycube"]
    for i in range(len(skycube)):
        skycube[i] = full_path(folder, skycube[i])

    assets = Config["engine"]["assets"]
    for asset in assets.values():
        for i in range(len(asset)):
            asset[i] = full_path(folder, asset[i])

    assets = Config["engine"]["dynamic_asset"]
    for asset in assets:
        assets[asset] = full_path(folder, assets[asset])

    shaders = Config["engine"]["shaders"]
    for shader in shaders.values():
        shader["vertex"] = full_path(folder, shader["vertex"])
        shader["fragment"] = full_path(folder, shader["fragment"])
        if 'textures' in shader:
            textures = shader["textures"]
            for texture in textures:
                textures[texture] = full_path(folder, textures[texture])

    Config["engine"]["player"] = full_path(folder, Config["engine"]["player"])


update_config()

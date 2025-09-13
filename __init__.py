from .modules import straight_uvs

bl_info = {
    "name": "Straighten UVs Addon",
    "description": "Straightens UVs for Square UV Workflows",
    "author": "Liam D'Arcy",
    "version": (0, 0, 5),
    "blender": (4, 5, 2),
    "category": "UV"
}

modules = [
    straight_uvs,
]

def register():
    for m in modules:
        m.register()

def unregister():
    for m in reversed(modules):
        m.unregister()

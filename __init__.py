from .modules import straight_uvs

bl_info = {
    "name": "Lime Juice's Blender Toolkit",
    "description": "A Collection of NPR-Based 3D Tools",
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

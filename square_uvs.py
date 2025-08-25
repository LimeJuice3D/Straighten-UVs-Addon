bl_info = {
    "name": "Square UV Edges",
    "description": "Straightens the bordering edges of UV tiles",
    "author": "Liam D'Arcy",
    "version": (0, 0, 1),
    "blender": (4, 5, 1),
    "location": "UV Editor > Panel > Square UVs",
    "category": "UV"
}

import bpy
import bmesh
import math

NO_ALIGN = -1
ALIGN_X = 0
ALIGN_Y = 1

# UI class
class SquareUvsUi(bpy.types.Panel):
    """UI Interface for the Square UVs Addon"""
    bl_label = "Square UVs"
    bl_idname = "PT_SquareUvs"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Square UVs'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(SquareUvsMain.bl_idname)

class SquareUvsMain(bpy.types.Operator):
    """Main squaring method for square UVs"""
    bl_idname = "uv.square_uvs"
    bl_label = "Square UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):
        main(context, self)
        return {'FINISHED'}

def main(context, operator):
    me = bpy.context.object.data
    bm = bmesh.from_edit_mesh(me)
    uvLayer = bm.loops.layers.uv.verify()

    sel = GetSelected(bm)

    islands = FacesToIslands(sel)

    count = 0 # debug

    for isl in islands:
        print("Island " + str(count))
        count += 1 #debug

        border, inner = SplitIsland(isl)

        AlignBorder(border, uvLayer)

# Aligns the border of an island
def AlignBorder(border, uvLayer):
    fset = border

    # debug
    print("Entering AlignBorders")

    while len(fset):
        wall, align = GetWall(uvLayer, fset, fset.pop(0))

        print("Wall:")
        for f in wall:
            if f in fset:
                fset.remove(f)
            print("    " + str(f.index))

        AlignWall(uvLayer, wall, align)
    
    print("Exiting AlignBorders")

# Gets a wall, which is a part of the border that shares an alignment.
def GetWall(uvLayer, fset, start):
    print("Entering GetWall") #debug
    wall = []
    wall.append(start)
    align = GetAlignment(uvLayer, start)

    adj = GetAdjacentFaces(start, fset, wall, align, uvLayer)


    while len(adj):
        wall.extend(adj)

        for f in wall:
            if f in fset:
                fset.remove(f)

            adj = GetAdjacentFaces(f, fset, wall, align, uvLayer)

    print("Exiting GetWall")

    return wall, align

# Aligns a wall
def AlignWall(uvLayer, wall, align):
    uvWall = []

    for f in wall:
        for e in f.edges:
            if e.seam:
                for l in e.link_loops:
                    if l in f.loops:
                        uvWall.append(l[uvLayer])

    if align == ALIGN_X:
        AlignX(uvWall)
    else:
        AlignY(uvWall)

# Aligns a wall to the average x value
def AlignX(uvWall):
    sum = 0
    length = len(uvWall)

    for uv in uvWall:
        sum += uv.uv.y

    avg = sum/length

    for uv in uvWall:
        uv.uv.y = avg

# Aligns a wall to the average x value
def AlignY(uvWall):
    sum = 0
    length = len(uvWall)

    for uv in uvWall:
        sum += uv.uv.x

    avg = sum/length

    for uv in uvWall:
        uv.uv.x = avg

# Takes a face and returns the face corners of the face's edge with a seam
# must pass in a face with a seam
def GetSeamFaceCorners(face):
    print("Entering GetSeamFaceCorners") # debug

    for l in face.loops:
        if l.edge.seam:
            print("    face corner 0: " + str(l.index)) # debug
            print("    face corner 1: " + str(l.link_loop_next.index)) # debug
            print("Exiting GetSeamFaceCorners")
            return l, l.link_loop_next

    raise Exception("ERROR: GetSeamFaceCorners must pass in a face with at least 1 seam edge")
    return

# Returns whether a pair of face corners should be aligned to X or Y
def GetAlignment(uvLayer, face):
    print("Entering GetAlignment")
    fc = GetSeamFaceCorners(face)

    uv1 = fc[0][uvLayer]
    uv2 = fc[1][uvLayer]
    slope = (uv1.uv.y - uv2.uv.y) / (uv1.uv.x - uv2.uv.x)

    angle = math.atan(slope)

    if angle < math.pi/4 and angle > -math.pi/4:
        return ALIGN_X
    else:
        return ALIGN_Y

    print("Exiting GetAlignment")
    return

# Gets the adjacent faces. Used to traverse the border
# the adjacent face must be in bounds, and canoot be in exclude
def GetAdjacentFaces(face, bounds, exclude, align, uvLayer):
    print("Entering GetAdjacentFaces")
    adj = []

    for v in face.verts:
        for f in v.link_faces:
            if f not in bounds:
                continue
            if f in exclude:
                continue
            if f in adj:
                continue
            if GetAlignment(uvLayer, f) != align:
                continue

            adj.append(f)
            print("    Adjacent: " + str(f.index))

    print("Entering GetAdjacentFaces")
    return adj

# splits island into border and inner faces
def SplitIsland(isl):
    border = []
    inner = []
    fset = isl

    # debug
    print("Splitting island")
    border_count = 0
    inner_count = 0

    for f in fset:
        has_seam = False
        for e in f.edges:
            if e.seam:
                has_seam = True 
                break
        if has_seam:
            border.append(f)
            border_count += 1
        else:
            inner.append(f)
            inner_count += 1

    print("Number of border faces: " + str(border_count))
    print("Number of inner faces: " + str(inner_count))

    return border, inner

# Returns 2D array, faces in islands.
def FacesToIslands(sel):
    print("Entering FacesToIslands")

    islands = []
    fset = sel
    islcount = 0 # debug

    while len(fset):
        isl = []
        isl.append(fset.pop(0))

        count = 1 # debug

        for f in isl:
            for e in f.edges:
                if not e.seam:
                    for n in e.link_faces:
                        if n in isl:
                            continue
                        isl.append(n)
                        count += 1 # debug

        islands.append(isl)

        for f in isl:
            if f in fset:
                fset.remove(f)

        print("Island " + str(islcount) + ": Faces: " + str(count)) # debug
        islcount += 1 # debug

    print("Exiting FacesToIslands")
    return islands

# Returns all selected faces
def GetSelected(bm):
    print("Isolating selected") # debug
    sel = []
    count = 0 # debug

    for f in bm.faces:
        if f.select:
            sel.append(f)
            count += 1 # debug

    print("Number of selected faces: " + str(count)) # debug

    return sel

def register():
    bpy.utils.register_class(SquareUvsUi)
    bpy.utils.register_class(SquareUvsMain)

def unregister():
    bpy.utils.unregister_class(SquareUvsUi)
    bpy.utils.unregister_class(SquareUvsMain)

if __name__ == "__main__":
    register()

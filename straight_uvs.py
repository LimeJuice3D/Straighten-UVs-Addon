"""
This file is part of the Straighten UVs Addon.
the Straighten UVs Addon is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published 
by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.

the Straighten UVs Addon is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
General Public License for more details.

You should have received a copy of the GNU General Public License 
along with the Straighten UVs Addon. If not, see <https://www.gnu.org/licenses/>. 
"""

bl_info = {
    "name": "Straighten UV Edges",
    "description": "Straightens the bordering edges of UV tiles",
    "author": "Liam D'Arcy",
    "version": (0, 0, 2),
    "blender": (4, 5, 2),
    "location": "UV Editor > Panel > Straighten UVs",
    "category": "UV"
}

import bpy
import bmesh
import math

NO_ALIGN = -1
ALIGN_X = 0
ALIGN_Y = 1

# UI class
class StraightUvsUI(bpy.types.Panel):
    """UI Interface for the Straighten UVs Addon"""
    bl_label = "Straight UVs"
    bl_idname = "PT_StraightUvs"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Straight UVs'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(StraightUvsButton.bl_idname)

class StraightUvsButton(bpy.types.Operator):
    """Main squaring method for square UVs"""
    bl_idname = "uv.straight_uvs"
    bl_label = "Straighten UVs"
    bl_options = {'REGISTER', 'UNDO'}

    smooth_iter: bpy.props.IntProperty(
        name="Smooth Iterations",
        default=2,
        description="Number of smoothing iterations post-straightening"
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):
        main(context, self)
        return {'FINISHED'}

def main(context, operator):
    me = bpy.context.object.data
    bm = bmesh.from_edit_mesh(me)
    uv_layer = bm.loops.layers.uv.verify()

    sel = GetSelected(bm)
    islands = FacesToIslands(sel)

    for isl in islands:
        border, inner, fringe = SplitIsland(isl)
        AlignBorder(border, fringe, uv_layer)
        SmoothInner(uv_layer, inner, operator.smooth_iter)

    bmesh.update_edit_mesh(me)


def SmoothInner(uv_layer, inner, iter):
    for i in range(0, iter):
        for v in inner:
            x, y = GetAvgPos(uv_layer, v)

            for l in v.link_loops:
                l[uv_layer].uv.x = x
                l[uv_layer].uv.y = y

    return

def GetAvgPos(uv_layer, v):
    avg_x = 0
    avg_y = 0
    num_edges = 0.0

    for l in v.link_loops:
        w = l.link_loop_next
        uv = w[uv_layer].uv

        avg_x += uv.x
        avg_y += uv.y
        num_edges += 1.0

    if num_edges <= 0:
        # if num edges = 0, return verts own UV coordinates
        return v.link_loops[0][uv_layer].uv.x, v.link_loops[0][uv_layer].uv.y

    avg_x = avg_x / num_edges
    avg_y = avg_y / num_edges

    return avg_x, avg_y


# Aligns the border of an island
def AlignBorder(border, fringe, uv_layer):
    fset = fringe

    while len(fset):
        wall, align = GetWall(uv_layer, fset, fset.pop(0))

        for f in wall:
            if f in fset:
                fset.remove(f)

        AlignWall(border, uv_layer, wall, align)

# Gets a wall, which is a part of the border that shares an alignment.
def GetWall(uv_layer, fset,  start):
    wall = []
    wall.append(start)
    align = GetAlignment(uv_layer, start)

    adj = GetAdjacentFaces(start, fset, wall, align, uv_layer)

    while len(adj):
        wall.extend(adj)

        for f in wall:
            if f in fset:
                fset.remove(f)

        adj = GetAdjacentFaces(f, fset, wall, align, uv_layer)

    return wall, align

# Aligns a wall
def AlignWall(border, uv_layer, wall, align):
    uv_wall = []

    for f in wall:
        for e in f.edges:
            if e.seam:
                for v in e.verts:
                    for l in v.link_loops:
                        for b in border:
                            if l in b.loops:
                                uv_wall.append(l[uv_layer])

    if align == ALIGN_X:
        AlignX(uv_wall)
    else:
        AlignY(uv_wall)

# Aligns a wall to the average x value
def AlignX(uv_wall):
    sum = 0
    length = len(uv_wall)

    if length == 0:
        return

    for uv in uv_wall:
        sum += uv.uv.y

    avg = sum/length

    for uv in uv_wall:
        uv.uv.y = avg

# Aligns a wall to the average x value
def AlignY(uv_wall):
    sum = 0
    length = len(uv_wall)

    if length <= 0:
        return

    for uv in uv_wall:
        sum += uv.uv.x

    avg = sum/length

    for uv in uv_wall:
        uv.uv.x = avg

# Takes a face and returns the face corners of the face's edge with a seam
# must pass in a face with a seam
def GetSeamFaceCorners(face):

    for l in face.loops:
        if l.edge.seam:
            return l, l.link_loop_next

    return None

# Returns whether a pair of face corners should be aligned to X or Y
def GetAlignment(uv_layer, face):
    fc = GetSeamFaceCorners(face)

    if fc == None:
        return NO_ALIGN

    uv1 = fc[0][uv_layer]
    uv2 = fc[1][uv_layer]

    if (uv1.uv.x - uv2.uv.x) == 0:
        return ALIGN_Y

    slope = (uv1.uv.y - uv2.uv.y) / (uv1.uv.x - uv2.uv.x)

    angle = math.atan(slope)

    if angle < math.pi/4 and angle > -math.pi/4:
        return ALIGN_X
    else:
        return ALIGN_Y

# Gets the adjacent faces. Used to traverse the border
# the adjacent face must be in bounds, and canoot be in exclude
def GetAdjacentFaces(face, bounds, exclude, align, uv_layer):
    adj = []

    for v in face.verts:
        for f in v.link_faces:
            adj_align = GetAlignment(uv_layer, f)

            if adj_align != align:
                continue
            if f not in bounds:
                continue
            if f in exclude:
                continue
            if f in adj:
                continue

            adj.append(f)

    return adj

# splits island into border, inner and fringe faces
# fringe faces are faces with a seam as an edge, whereas 
# borders can either have a seam edge or a vert connected 
# to a seam edge
def SplitIsland(isl):
    border = []
    inner = []
    fringe = []

    fset = isl

    for f in fset:
        has_seam = False
        for v in f.verts:
            for e in v.link_edges:
                if e.seam:
                    has_seam = True
        if has_seam:
            border.append(f)
        else:
            for v in f.verts:
                inner.append(v)

        has_seam = False
        for e in f.edges:
            if e.seam:
                has_seam = True
                break
        if has_seam:
            fringe.append(f)

    return border, inner, fringe

# Returns 2D array, faces in islands.
def FacesToIslands(sel):
    islands = []
    fset = sel

    while len(fset):
        isl = []
        isl.append(fset.pop(0))

        for f in isl:
            for e in f.edges:
                if not e.seam:
                    for n in e.link_faces:
                        if n in isl:
                            continue
                        isl.append(n)

        islands.append(isl)

        for f in isl:
            if f in fset:
                fset.remove(f)

    return islands

# Returns all selected faces
def GetSelected(bm):
    sel = []

    for f in bm.faces:
        if f.select:
            sel.append(f)

    return sel

def register():
    bpy.utils.register_class(StraightUvsUI)
    bpy.utils.register_class(StraightUvsButton)

def unregister():
    bpy.utils.register_class(StraightUvsUI)
    bpy.utils.register_class(StraightUvsButton)

if __name__ == "__main__":
    register()

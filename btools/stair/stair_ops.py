import bpy
import bmesh

from ..utils import crash_safe, get_edit_mesh, popup_message
from .stair_types import compute_and_build_stairs

PROP_NAME = "stair_builder_props"


class BTOOLS_OT_add_stairs(bpy.types.Operator):
    """Create stairs connecting two selected vertical faces"""

    bl_idname = "btools.add_stairs"
    bl_label = "Add Stairs"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        prop = getattr(context.scene, PROP_NAME, None)
        if prop is None:
            return {"CANCELLED"}
        return build(context, prop)

    def draw(self, context):
        prop = getattr(context.scene, PROP_NAME, None)
        if prop is not None:
            prop.draw(context, self.layout)


@crash_safe
def build(context, prop):
    me = get_edit_mesh()
    bm = bmesh.from_edit_mesh(me)
    selected_faces = [f for f in bm.faces if f.select]

    if len(selected_faces) < 2:
        popup_message("Please select exactly 2 vertical faces (wall faces)")
        return {"CANCELLED"}

    if len(selected_faces) > 2:
        popup_message("Please select exactly 2 faces, not more")
        return {"CANCELLED"}

    face1, face2 = selected_faces[0], selected_faces[1]

    if not is_vertical_face(face1):
        popup_message("First face is not vertical - please select wall faces")
        return {"CANCELLED"}
    if not is_vertical_face(face2):
        popup_message("Second face is not vertical - please select wall faces")
        return {"CANCELLED"}

    if getattr(prop, "as_object", False):
        result = build_as_object(me, prop, face1, face2)
    else:
        result = compute_and_build_stairs(bm, face1, face2, prop)

    # Deselect everything to avoid accidental extrude after building
    for f in bm.faces:
        f.select = False
    for v in bm.verts:
        v.select = False
    for e in bm.edges:
        e.select = False

    bmesh.update_edit_mesh(me, loop_triangles=True)
    return {"FINISHED"} if result else {"CANCELLED"}


def build_as_object(me, prop, face1, face2):
    """Build the stairs+railing into a brand-new object (never touching the wall mesh).

    The reference faces are read-only (only their centers/normals are used), so the
    geometry is built in a fresh bmesh and transferred into a new object that shares
    the source object's world transform. The new object is left unselected so the
    edit-mode session of the wall is not disturbed.
    """
    src_obj = bpy.context.object
    src_mw = src_obj.matrix_world.copy()

    new_bm = bmesh.new()
    result = compute_and_build_stairs(new_bm, face1, face2, prop)
    if not result:
        new_bm.free()
        return False

    mesh = bpy.data.meshes.new("Stairs")
    new_bm.to_mesh(mesh)
    new_bm.free()
    mesh.update()

    stairs_obj = bpy.data.objects.new("Stairs", mesh)
    bpy.context.scene.collection.objects.link(stairs_obj)
    stairs_obj.matrix_world = src_mw
    return True


def is_vertical_face(face, threshold=0.05):
    return abs(face.normal.z) < threshold

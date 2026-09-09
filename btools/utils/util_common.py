import bpy
import enum
import bmesh
import traceback
from mathutils import Vector
from bpy.props import PointerProperty
from .util_constants import VEC_UP, VEC_RIGHT


def equal(a, b, eps=0.001):
    return a == b or (abs(a - b) <= eps)


def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)


def minmax(items, key=lambda val: val):
    _min = _max = None
    for val in items:
        if _min is None or key(val) < key(_min):
            _min = val
        if _max is None or key(val) > key(_max):
            _max = val
    return _min, _max


def popup_message(message, title="Error", icon="ERROR"):
    if bpy.app.background:
        print("{}: {}".format(title, message))
        return
    bpy.context.window_manager.popup_menu(
        lambda self, ctx: self.layout.label(text=message),
        title=title, icon=icon,
    )


def crash_safe(func):
    def crash_handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
            popup_message("See console for errors", title="Operator Failed!")
            if bpy.context.mode == "EDIT_MESH":
                bmesh.update_edit_mesh(bpy.context.edit_object.data, loop_triangles=True)
            return {"CANCELLED"}
    return crash_handler


def get_scaled_unit(value):
    try:
        scale = bpy.context.scene.unit_settings.scale_length
    except AttributeError:
        scale = 1.0
    return value / scale


def local_xyz(face):
    z = face.normal.copy()
    x = z.cross(VEC_RIGHT if z.to_tuple(1) == VEC_UP.to_tuple(1) else VEC_UP)
    y = x.cross(z)
    return x, y, z


def vec_equal(a, b):
    if a.length == 0.0 or b.length == 0.0:
        return False
    angle = a.angle(b)
    return angle < 0.001 and angle > -0.001


def is_horizontal_face(face, threshold=0.01):
    return abs(face.normal.z) < threshold


def is_vertical_face(face, threshold=0.01):
    return abs(face.normal.z) > (1.0 - threshold)


def get_selected_face_dimensions(context):
    bm = bmesh.from_edit_mesh(context.edit_object.data)
    wall = [f for f in bm.faces if f.select]
    if wall:
        return wall[0], calc_face_dimensions(wall[0])
    return None, (1, 1)


def calc_face_dimensions(face):
    horizontal_edges = [e for e in face.edges if is_horizontal_edge(e)]
    vertical_edges = [e for e in face.edges if is_vertical_edge(e)]
    width = sum(e.calc_length() for e in horizontal_edges) / 2 if horizontal_edges else face.calc_dimensions()[0]
    height = sum(e.calc_length() for e in vertical_edges) / 2 if vertical_edges else face.calc_dimensions()[1]
    return width, height


def is_horizontal_edge(edge):
    v1, v2 = edge.verts
    return abs(v1.co.z - v2.co.z) < 0.001


def is_vertical_edge(edge):
    v1, v2 = edge.verts
    return abs(v1.co.x - v2.co.x) < 0.001 and abs(v1.co.y - v2.co.y) < 0.001 or \
           abs(v1.co.z - v2.co.z) > 0.001 and (abs(v1.co.x - v2.co.x) < 0.001 or abs(v1.co.y - v2.co.y) < 0.001)


def vec_to_2d(v):
    return Vector((v.x, v.y))
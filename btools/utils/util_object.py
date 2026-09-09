from contextlib import contextmanager
import bmesh
import bpy
from .util_mesh import select, get_edit_mesh


def create_object(name, data=None):
    return bpy.data.objects.new(name, data)


def link_obj(obj):
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    select(bpy.context.view_layer.objects, False)
    obj.select_set(True)
    obj.location = bpy.context.scene.cursor.location


@contextmanager
def bmesh_from_active_object(context=None):
    context = context or bpy.context
    if context.mode == "EDIT_MESH":
        me = get_edit_mesh()
        bm = bmesh.from_edit_mesh(me)
    elif context.mode == "OBJECT":
        bm = bmesh.new()
        bm.from_mesh(context.object.data)
    yield bm
    if context.mode == "EDIT_MESH":
        bmesh.update_edit_mesh(me, loop_triangles=True)
    elif context.mode == "OBJECT":
        bm.to_mesh(context.object.data)
        bm.free()
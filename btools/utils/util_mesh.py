import bmesh
import bpy
from bmesh.types import BMVert, BMEdge, BMFace
from mathutils import Vector

from .util_common import local_xyz, vec_equal, is_horizontal_edge


def get_edit_mesh():
    return bpy.context.edit_object.data


def select(elements, val=True):
    for el in elements:
        el.select_set(val)


def filter_geom(geom, _type):
    return list(filter(lambda x: isinstance(x, _type), geom))


def sort_edges(edges, direction):
    return sorted(edges, key=lambda e: direction.dot(calc_edge_median(e)))


def sort_verts(verts, direction):
    return sorted(verts, key=lambda v: direction.dot(v.co))


def sort_faces(faces, direction):
    return sorted(faces, key=lambda f: direction.dot(f.calc_center_median()))


def calc_edge_median(edge):
    return sum(v.co for v in edge.verts) / len(edge.verts)


def calc_verts_median(verts):
    return sum(v.co for v in verts) / len(verts)


def calc_face_dimensions(face):
    return face.calc_dimensions()


def face_with_verts(bm, verts, default=None):
    for face in bm.faces:
        if len(face.verts) == len(verts):
            sorted_verts = sorted(verts, key=lambda v: v.index)
            sorted_face = sorted(face.verts, key=lambda v: v.index)
            if all(a == b for a, b in zip(sorted_verts, sorted_face)):
                return face
    return default


def extrude_face(bm, face, extrude_depth):
    extruded_face = bmesh.ops.extrude_discrete_faces(bm, faces=[face]).get("faces")[0]
    bmesh.ops.translate(bm, verts=extruded_face.verts, vec=extruded_face.normal * extrude_depth)
    surrounding_faces = list({
        f for edge in extruded_face.edges for f in edge.link_faces if f not in [extruded_face]
    })
    return extruded_face, surrounding_faces


def create_face(bm, size, offset, xyz):
    offset_vec = -offset.x * xyz[0] + offset.y * xyz[1]
    v1 = bmesh.ops.create_vert(bm, co=offset_vec + size.x * xyz[0] / 2 + size.y * xyz[1] / 2)["vert"][0]
    v2 = bmesh.ops.create_vert(bm, co=offset_vec + size.x * xyz[0] / 2 - size.y * xyz[1] / 2)["vert"][0]
    v3 = bmesh.ops.create_vert(bm, co=offset_vec - size.x * xyz[0] / 2 + size.y * xyz[1] / 2)["vert"][0]
    v4 = bmesh.ops.create_vert(bm, co=offset_vec - size.x * xyz[0] / 2 - size.y * xyz[1] / 2)["vert"][0]
    return bmesh.ops.contextual_create(bm, geom=[v1, v2, v3, v4])["faces"][0]


def get_bounding_verts(verts):
    min_z, max_z = min(verts, key=lambda v: v.co.z), max(verts, key=lambda v: v.co.z)
    top_verts = [v for v in verts if v.co.z == max_z.co.z]
    bot_verts = [v for v in verts if v.co.z == min_z.co.z]
    if len(top_verts) > 1:
        topleft = sorted(top_verts, key=lambda v: v.co.xy.to_tuple())[0]
        topright = sorted(top_verts, key=lambda v: v.co.xy.to_tuple())[-1]
    else:
        topleft = topright = top_verts[0]
    if len(bot_verts) > 1:
        botleft = sorted(bot_verts, key=lambda v: v.co.xy.to_tuple())[0]
        botright = sorted(bot_verts, key=lambda v: v.co.xy.to_tuple())[-1]
    else:
        botleft = botright = bot_verts[0]
    return (topleft, topright, botleft, botright)


def subdivide_edges(bm, edges, direction, widths):
    dir = direction.copy().normalized()
    cuts = len(widths) - 1
    res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts)
    inner_edges = filter_geom(res.get("geom_inner"), BMEdge)
    distance = sum(widths) / len(widths)
    for i, edge in enumerate(sort_edges(inner_edges, dir)):
        original_position = (i + 1) * distance
        final_position = sum(widths[:i+1])
        diff = final_position - original_position
        bmesh.ops.translate(bm, verts=edge.verts, vec=diff * dir)
    return inner_edges


def subdivide_face_vertically(bm, face, widths):
    edges = [e for e in face.edges if is_vertical_edge(e)]
    _, direction, _ = local_xyz(face)
    if edges:
        inner_edges = subdivide_edges(bm, edges, direction, widths)
        return sort_faces(list({f for e in inner_edges for f in e.link_faces}), direction)
    return [face]


def valid_ngon(face):
    horizontal_edges = [e for e in face.edges if is_horizontal_edge(e)]
    return len(horizontal_edges) == 2 and face.is_valid


def get_face_center(face):
    return face.calc_center_bounds()


def get_face_normal(face):
    return face.normal.copy()


def get_face_bounds(face):
    return face.calc_dimensions()
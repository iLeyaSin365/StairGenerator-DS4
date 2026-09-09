import bmesh
import bpy
from mathutils import Vector

from .stair_props import RailProperty


def create_railing(bm, railing_faces, rail_prop, normal):
    if not railing_faces:
        return []

    fill = rail_prop.fill
    if fill == "BALUSTERS":
        return create_baluster_railing(bm, railing_faces, rail_prop, normal)
    elif fill == "WALL":
        return create_wall_railing(bm, railing_faces, rail_prop, normal)
    else:
        return create_simple_railing(bm, railing_faces, rail_prop, normal)


def create_baluster_railing(bm, railing_faces, rail_prop, normal):
    posts = []
    rail_height = rail_prop.height
    rail_thickness = rail_prop.thickness
    post_count = rail_prop.post_count

    for face in railing_faces:
        f_cent = face.calc_center_bounds()
        bottom = Vector((f_cent.x, f_cent.y, f_cent.z))
        top = Vector((f_cent.x, f_cent.y, f_cent.z + rail_height))
        create_vertical_post(bm, bottom, top, rail_thickness)
        posts.append(top)

    return posts


def create_wall_railing(bm, railing_faces, rail_prop, normal):
    walls = []
    for face in railing_faces:
        walls.append(face)
    return walls


def create_simple_railing(bm, railing_faces, rail_prop, normal):
    rails = []
    for face in railing_faces:
        f_cent = face.calc_center_bounds()
        v1 = bmesh.ops.create_vert(bm, co=Vector((f_cent.x, f_cent.y, f_cent.z + rail_prop.height)))["vert"][0]
        rails.append(v1)
    return rails


def create_vertical_post(bm, bottom, top, thickness):
    v1 = bmesh.ops.create_vert(bm, co=bottom)["vert"][0]
    v2 = bmesh.ops.create_vert(bm, co=top)["vert"][0]
    return bmesh.ops.contextual_create(bm, geom=[v1, v2])["edges"][0]
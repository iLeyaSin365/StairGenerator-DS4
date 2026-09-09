import bmesh
from mathutils import Vector, Matrix, Quaternion
from math import pi, sqrt, atan2, sin, cos

from .util_common import local_xyz, vec_equal, VEC_UP, VEC_RIGHT
from .util_mesh import sort_verts, sort_edges, sort_faces, calc_edge_median, extrude_face


def create_plane(bm, size, position=Vector((0, 0, 0))):
    geom = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1, matrix=Matrix.Scale(size[0], 4, (1,0,0)) @ Matrix.Scale(size[1], 4, (0,1,0)))
    bmesh.ops.translate(bm, verts=geom["verts"], vec=position)
    return geom


def local_to_global(face, vec):
    x, y, z = local_xyz(face)
    return x * vec.x + y * vec.y + z * vec.z


def cross_2d(a, b):
    return a.x * b.y - a.y * b.x


def angle_between_faces(face1, face2):
    n1 = face1.normal
    n2 = face2.normal
    cos_angle = n1.dot(n2)
    return atan2(sqrt(1 - cos_angle * cos_angle), cos_angle)


def are_faces_parallel(face1, face2, threshold=0.01):
    n1 = face1.normal
    n2 = face2.normal
    return abs(abs(n1.dot(n2)) - 1.0) < threshold or abs(n1.dot(n2)) < threshold


def get_faces_relationship(face1, face2):
    n1 = face1.normal
    n2 = face2.normal
    dot = n1.dot(n2)
    if abs(dot) < 0.01:
        return "perpendicular"
    elif abs(abs(dot) - 1.0) < 0.01:
        return "parallel" if dot > 0 else "antiparallel"
    else:
        return "angled"


def compute_stair_path(face1, face2):
    c1 = face1.calc_center_bounds()
    c2 = face2.calc_center_bounds()
    n1 = face1.normal
    n2 = face2.normal
    delta = c2 - c1
    distance = delta.length
    height_diff = delta.z
    return c1, c2, n1, n2, delta, distance, height_diff


def compute_rotation_angle(face1, face2):
    n1 = face1.normal
    n2 = face2.normal
    axis = n1.cross(n2)
    if axis.length < 0.001:
        return 0, Vector((0, 0, 1))
    axis.normalize()
    angle = atan2(axis.length, n1.dot(n2))
    if n1.cross(n2).z < 0:
        angle = -angle
    return angle, axis


def create_rotation_matrix(angle, axis):
    return Matrix.Rotation(angle, 4, axis)
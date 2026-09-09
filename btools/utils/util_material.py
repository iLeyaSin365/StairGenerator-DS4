import bpy


def link_material(obj, mat):
    if not has_material(obj, mat.name):
        obj.data.materials.append(mat)


def has_material(obj, name):
    return name in obj.data.materials.keys()


def create_object_material(obj, mat_name):
    if not has_material(obj, mat_name):
        if bpy.data.materials.get(mat_name, None):
            mat_name += ".{}".format(obj.name)
        mat = bpy.data.materials.new(mat_name)
        link_material(obj, mat)
        return mat
    return obj.data.materials.get(mat_name)


def uv_map_active_editmesh_selection(faces, method):
    if not bpy.context.object.mode == "EDIT":
        return
    selection_state = [f.select for f in faces]
    for f in faces:
        f.select_set(True)
    if method == "UNWRAP":
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.001)
    elif method == "CUBE_PROJECTION":
        bpy.ops.uv.cube_project(cube_size=0.5)
    for f, sel in zip(faces, selection_state):
        f.select_set(sel)
import bpy


def print_scene_info():
    scene = bpy.context.scene
    print(f"Scene: {scene.name}")
    print(f"Active object: {bpy.context.active_object}")
    print(f"Mode: {bpy.context.mode}")
    if bpy.context.object:
        print(f"Object type: {bpy.context.object.type}")
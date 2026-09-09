import bpy
from .btools.stair import register_stairs, unregister_stairs, PROP_NAME

bl_info = {
    "name": "StairGenerator (DS4)",
    "author": "DeepSeek V4 Flash",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Toolshelf > Stair Builder",
    "description": "Build stairs between two selected vertical faces. Straight, curved, L-shape, U-shape. Written by the DeepSeek V4 Flash large language model.",
    "warning": "",
    "doc_url": "",
    "category": "Mesh",
}


class BTOOLS_PT_stair_builder(bpy.types.Panel):
    bl_label = "StairGenerator (DS4)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Stair Builder"

    def draw(self, context):
        layout = self.layout
        props = getattr(context.scene, PROP_NAME, None)
        if props is None:
            layout.operator("btools.add_stairs")
            layout.separator(factor=1)
            layout.label(text="Select 2 vertical faces", icon="INFO")
            return
        props.draw(context, layout)
        layout.separator(factor=1)
        layout.operator("btools.add_stairs", text="Add Stairs")


classes = (BTOOLS_PT_stair_builder,)

register_ui, unregister_ui = bpy.utils.register_classes_factory(classes)


def register():
    register_stairs()
    register_ui()


def unregister():
    unregister_ui()
    unregister_stairs()


if __name__ == "__main__":
    register()
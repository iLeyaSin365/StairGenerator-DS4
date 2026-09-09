import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty, PointerProperty
from mathutils import Vector


class SizeOffsetProperty(bpy.types.PropertyGroup):
    size: FloatVectorProperty(name="Size", subtype="XYZ", size=2, unit="LENGTH")
    offset: FloatVectorProperty(name="Offset", subtype="TRANSLATION", size=2, unit="LENGTH")

    def init(self, parent_dimensions, default_size=(1.0, 1.0), default_offset=(0.0, 0.0), restricted=True):
        self["parent_dimensions"] = parent_dimensions
        self["default_size"] = default_size
        self["default_offset"] = default_offset
        self["restricted"] = restricted
        self.size = Vector(default_size)
        self.offset = Vector(default_offset)

    def draw(self, context, layout):
        col = layout.column(align=True)
        col.label(text="Size:")
        col.prop(self, "size", text="")
        col.label(text="Offset:")
        col.prop(self, "offset", text="")
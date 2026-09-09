import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
)

from ..utils import get_scaled_unit


class RailProperty(bpy.types.PropertyGroup):
    height: FloatProperty(
        name="Rail Height",
        min=get_scaled_unit(0.1),
        max=get_scaled_unit(5.0),
        default=get_scaled_unit(1.0),
        unit="LENGTH",
        description="Height of the railing",
    )
    thickness: FloatProperty(
        name="Rail Thickness",
        min=get_scaled_unit(0.01),
        max=get_scaled_unit(0.5),
        default=get_scaled_unit(0.08),
        unit="LENGTH",
        description="Thickness of the rail bar",
    )
    baluster_thickness: FloatProperty(
        name="Baluster Thickness",
        min=get_scaled_unit(0.005),
        max=get_scaled_unit(0.3),
        default=get_scaled_unit(0.03),
        unit="LENGTH",
        description="Thickness of the slim balusters",
    )
    fill: EnumProperty(
        name="Fill",
        items=[
            ("NONE", "None (rail only)", "", 0),
            ("BALUSTERS", "Balusters", "", 1),
            ("WALL", "Wall", "", 2),
        ],
        default="BALUSTERS",
        description="Type of railing fill",
    )
    post_count: IntProperty(
        name="Post Count", min=1, max=60, default=6,
        description="Number of intermediate posts",
    )
    bottom_rail: BoolProperty(
        name="Bottom Rail", default=True, description="Add bottom rail"
    )


class StairsProperty(bpy.types.PropertyGroup):
    stair_type: EnumProperty(
        name="Type",
        items=[
            ("STRAIGHT", "Straight", "", 0),
            ("CURVED", "Curved (Arc)", "", 1),
            ("L", "L-Shape (Landing)", "", 2),
            ("U", "U-Shape (Switchback)", "", 3),
        ],
        default="STRAIGHT",
        description="Type of staircase",
    )

    step_count: IntProperty(
        name="Step Count", min=2, max=80, default=12,
        description="Number of steps (depth & rise are computed automatically)",
    )
    step_width: FloatProperty(
        name="Step Width", min=get_scaled_unit(0.1), max=get_scaled_unit(50.0),
        default=get_scaled_unit(2.0), unit="LENGTH",
        description="Width of the stair flight (across the treads)",
    )

    landing_length: FloatProperty(
        name="Landing Length", min=get_scaled_unit(0.5), max=get_scaled_unit(20.0),
        default=get_scaled_unit(2.0), unit="LENGTH",
        description="Length of the landing platform (along the turn)",
    )
    landing_width: FloatProperty(
        name="Landing Width", min=get_scaled_unit(0.5), max=get_scaled_unit(20.0),
        default=get_scaled_unit(2.0), unit="LENGTH",
        description="Width of the landing platform",
    )
    landing_thickness: FloatProperty(
        name="Landing Thickness", min=get_scaled_unit(0.05), max=get_scaled_unit(2.0),
        default=get_scaled_unit(0.3), unit="LENGTH",
        description="Thickness of the landing slab",
    )
    landing_rotation: FloatProperty(
        name="Landing Rotation", min=-180.0, max=180.0, default=90.0,
        unit="ROTATION", subtype="ANGLE",
        description="Absolute turn angle of the L-shape (angle between the two flights) around Z",
    )
    landing_slab_rotation: FloatProperty(
        name="Landing Slab Rotation", min=-180.0, max=180.0, default=0.0,
        unit="ROTATION", subtype="ANGLE",
        description="Rotate just the landing slab around Z (used by U-shape)",
    )
    has_landing: BoolProperty(
        name="Add Mid Landing", default=False,
        description="Insert a landing midway (used with Curved type)",
    )

    has_railing: BoolProperty(
        name="Add Railing", default=True, description="Whether the stairs have railing"
    )
    rail_height: FloatProperty(
        name="Rail Height", min=get_scaled_unit(0.1), max=get_scaled_unit(5.0),
        default=get_scaled_unit(1.0), unit="LENGTH", description="Height of the railing",
    )
    rail_thickness: FloatProperty(
        name="Rail Thickness", min=get_scaled_unit(0.01), max=get_scaled_unit(0.5),
        default=get_scaled_unit(0.08), unit="LENGTH", description="Thickness of the handrail",
    )
    rail_fill: EnumProperty(
        name="Rail Fill",
        items=[
            ("NONE", "None (rail only)", "", 0),
            ("BALUSTERS", "Balusters", "", 1),
            ("WALL", "Wall", "", 2),
        ],
        default="BALUSTERS", description="Type of railing fill",
    )
    rail_style: EnumProperty(
        name="Rail Style",
        items=[
            ("SLOPE", "Sloped", "One straight handrail along the ramp", 0),
            ("STEPPED", "Stepped", "Handrail with a turning point at each step", 1),
        ],
        default="SLOPE",
        description="How the handrail follows the stair profile",
    )
    baluster_thickness: FloatProperty(
        name="Baluster Thickness", min=get_scaled_unit(0.005), max=get_scaled_unit(0.3),
        default=get_scaled_unit(0.03), unit="LENGTH", description="Thickness of slim balusters",
    )
    baluster_type: EnumProperty(
        name="Baluster Style",
        items=[
            ("PLAIN", "Plain (Square)", "Straight square balusters", 0),
            ("TURNED", "Classical (Turned)", "Lathe profile with a bulged middle", 1),
        ],
        default="PLAIN",
        description="Shape of the balusters",
    )
    baluster_bulb: FloatProperty(
        name="Baluster Bulb", min=0.1, max=3.0, default=1.0,
        description="Size of the bulging (bowling-pin) middle",
    )
    baluster_waist: FloatProperty(
        name="Baluster Waist", min=0.05, max=2.0, default=0.55,
        description="Size of the narrow waist",
    )
    baluster_top: FloatProperty(
        name="Baluster Top", min=0.05, max=2.0, default=0.65,
        description="Size of the baluster top flare",
    )
    post_count: IntProperty(
        name="Post Count", min=1, max=60, default=6,
        description="Number of intermediate balusters",
    )
    bottom_rail: BoolProperty(
        name="Bottom Rail", default=True, description="Add bottom rail"
    )
    as_object: BoolProperty(
        name="Generate as Object", default=False,
        description="Build the stairs+railing as a new separate object instead of fusing into the current mesh",
    )

    def init(self, wall_dimensions):
        self["wall_dimensions"] = wall_dimensions

    def draw(self, context, layout):
        col = layout.column(align=True)
        col.label(text="Type")
        col.prop(self, "stair_type", text="")

        col = layout.column(align=True)
        col.label(text="Steps")
        col.prop(self, "step_count")
        col.prop(self, "step_width")
        layout.label(text="Depth & riser from gap & step count", icon="INFO")

        col = layout.column(align=True)
        col.label(text="Landing")
        col.prop(self, "landing_length")
        col.prop(self, "landing_width")
        col.prop(self, "landing_thickness")
        if self.stair_type == "L":
            col.prop(self, "landing_rotation", text="Turn")
        elif self.stair_type == "U":
            col.prop(self, "landing_slab_rotation", text="Slab Turn")
        col.prop(self, "has_landing")

        col = layout.column(align=True)
        col.label(text="Railing")
        col.prop(self, "has_railing")
        if self.has_railing:
            col.prop(self, "rail_fill", text="Fill")
            col.prop(self, "rail_style", text="Style")
            col.prop(self, "rail_height")
            col.prop(self, "rail_thickness")
            col.prop(self, "baluster_thickness")
            if self.rail_fill == "BALUSTERS":
                col.prop(self, "baluster_type", text="Baluster")
                if self.baluster_type == "TURNED":
                    row = layout.row(align=True)
                    row.prop(self, "baluster_bulb")
                    row.prop(self, "baluster_waist")
                    row = layout.row(align=True)
                    row.prop(self, "baluster_top")
            col.prop(self, "post_count")
            col.prop(self, "bottom_rail")

        col = layout.column(align=True)
        col.separator(factor=1)
        col.prop(self, "as_object")
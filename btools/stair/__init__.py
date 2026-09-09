import bpy
from .stair_ops import BTOOLS_OT_add_stairs, PROP_NAME
from .stair_props import StairsProperty, RailProperty

classes = (StairsProperty, RailProperty, BTOOLS_OT_add_stairs)


def register_stairs():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError:
            pass
    # Store the parameters on the Scene so the toolshelf panel can always draw them,
    # independent of the operator's transient redo/execution state.
    if not hasattr(bpy.types.Scene, PROP_NAME):
        try:
            setattr(bpy.types.Scene, PROP_NAME, bpy.props.PointerProperty(type=StairsProperty))
        except AttributeError:
            pass


def unregister_stairs():
    if hasattr(bpy.types.Scene, PROP_NAME):
        try:
            delattr(bpy.types.Scene, PROP_NAME)
        except (AttributeError, TypeError):
            pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
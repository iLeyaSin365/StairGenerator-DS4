import bpy


def register_event_handler(handler, event_type):
    bpy.app.handlers[event_type].append(handler)


def unregister_event_handler(handler, event_type):
    if handler in bpy.app.handlers[event_type]:
        bpy.app.handlers[event_type].remove(handler)
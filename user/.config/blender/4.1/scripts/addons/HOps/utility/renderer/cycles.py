from .. import object


def hide_preview(context, obj):
    object.hide_set(obj, True, viewport=False, render=False)


def show_preview(context, obj):
    object.hide_set(obj, False, viewport=False, render=False)

from ...... utility import addon

def shape(op, context, event):
    preference = addon.preference()

    #XXX:prevent unnecessary setting as update rebuilds the mesh
    if not preference.shape.box_grid:
        preference.shape.box_grid = True

from .. import lattice
from ...... utility import addon, screen


def shape(op, context, event):
    preference = addon.preference()

    preference.shape.taper = op.last['taper'] + ((op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True)) * 0.001

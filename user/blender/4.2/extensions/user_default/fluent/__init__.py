'''
Copyright (C) 2019
rudy.michau@gmail.com

Created by RUDY MICHAU

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from bpy.types import Operator, Menu, AddonPreferences
import bpy.utils.previews
import rna_keymap_ui
import urllib

from .operators import *
from .modal_editor import *
from .toolbox import *
from .Tools.helper import *
from .Tools.independant_helper import *
from .primitives import *
from .UI.menus import FLUENT_PT_Basic_Panel
try:
    from .power_trip.power_trip_panel import FLUENT_PT_PowerTrip_Panel
except:pass

from .properties import fluentProp
from .preferences import AddonKeymaps

from . import auto_load

TEMPS = 0

def vider_dossier_pycache(racine):
    import os
    import shutil

    for root, dirs, files in os.walk(racine):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            print(f"Vidage du dossier: {pycache_path}")
            for fichier in os.listdir(pycache_path):
                fichier_path = os.path.join(pycache_path, fichier)
                try:
                    if os.path.isfile(fichier_path) or os.path.islink(fichier_path):
                        os.unlink(fichier_path)
                    elif os.path.isdir(fichier_path):
                        shutil.rmtree(fichier_path)
                except Exception as e:
                    print(f"Erreur lors de la suppression {fichier_path}: {e}")
import os
# vider_dossier_pycache(os.path.dirname(os.path.realpath(__file__)))


auto_load.init()


def register():
    auto_load.register()

    if not get_addon_preferences().show_panel:
        from bpy.utils import unregister_class
        try:
            unregister_class(FLUENT_PT_PowerTrip_Panel)
        except:pass
        unregister_class(FLUENT_PT_Basic_Panel)

    bpy.types.Scene.fluentProp = bpy.props.PointerProperty(type=fluentProp)

    AddonKeymaps.new_keymap('Pie Menu', 'wm.call_menu_pie', 'FLUENT_MT_PieMenu',
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'F',
                            'PRESS', False, False, False, 'NONE'
                            )

    AddonKeymaps.new_keymap('Cut', 'fluent.cutstarter', None,
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'F',
                            'PRESS', False, False, True, 'NONE'
                            )

    AddonKeymaps.new_keymap('Slice', 'fluent.slicestarter', None,
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'F',
                            'PRESS', True, False, False, 'NONE'
                            )

    AddonKeymaps.new_keymap('Inset', 'fluent.insetstarter', None,
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'F',
                            'PRESS', False, True, False, 'NONE'
                            )

    AddonKeymaps.new_keymap('Show/Hide boolean', 'fluent.booleandisplay', None,
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'GRLESS',
                            'PRESS', False, False, False, 'NONE'
                            )

    AddonKeymaps.new_keymap('VG Cleaner', 'fluent.vgcleaner', None,
                            'Mesh', 'EMPTY', 'WINDOW', 'F',
                            'PRESS', False, True, False, 'NONE'
                            )

    AddonKeymaps.new_keymap('Edit', 'fluent.editor', None,
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'F',
                            'PRESS', True, False, True, 'NONE', ['operation', 'EDIT']
                            )

    AddonKeymaps.register_keymaps()

    if get_addon_preferences().fluent_primitive:
        bpy.types.VIEW3D_MT_mesh_add.prepend(primitive_add)

    load_icons(False)

def unregister():
    AddonKeymaps.unregister_keymaps()
    auto_load.unregister()

    clear_icons()

if __name__ == "__main__":
    register()

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from math import *
from bpy.props import *
import rna_keymap_ui
from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, BoolProperty
from bpy.types import (
		Operator,
		PropertyGroup,
		AddonPreferences
		)

class UI_PT_rflow_addon_pref(AddonPreferences):
	bl_idname = __package__

	font_size : IntProperty(
		description = "Helper font size when using modal operations",
		name        = "Helper Font Size",
		default     = 60,
		min         = 1,
		max         = 1000,
		step        = 1
		)
	font_size_1 : IntProperty(
		description = "Helper font size when using modal operations",
		name        = "Helper Font Size",
		default     = 12,
		min         = 1,
		max         = 1000,
		step        = 1
		)
	use_confirm : BoolProperty(
		default     = False,
		name        = "Use Confirm Menu",
		description = "Use confirm type adjust last action menu for random operators."
		)
	show_helper : BoolProperty(
		default     = False,
		name        = "Show Usage Info",
		description = "Show usage info button in add-on menu."
		)

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row(align=True)
		row.separator(factor=2.0)
		row.prop(self, 'font_size')
		row = col.row(align=True)
		row.separator(factor=2.0)
		row.prop(self, 'use_confirm')
		row = col.row(align=True)
		row.separator(factor=2.0)
		row.prop(self, 'show_helper')
		col.separator()
		wm = context.window_manager
		kc = wm.keyconfigs.user
		km = kc.keymaps['3D View Generic']
		kmi = get_hotkey_entry_item(km, 'wm.call_menu', 'UI_MT_random_flow')
		if kmi:
			col.context_pointer_set("keymap", km)
			rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
		else:
			col.label(text="No hotkey found!", icon="ERROR")
			col.operator("add_hotkey.rflow", text="Add hotkey")

def get_hotkey_entry_item(km, kmi_name, kmi_value):

	for i, km_item in enumerate(km.keymap_items):
		if km.keymap_items.keys()[i] == kmi_name:
			if km.keymap_items[i].properties.name == kmi_value:
				return km_item
	return None

def add_hotkey():

	addon_prefs = bpy.context.preferences.addons[__package__].preferences

	kc = bpy.context.window_manager.keyconfigs.addon
	if kc:
		km = kc.keymaps.new(name='3D View Generic', space_type='VIEW_3D', region_type='WINDOW')
		kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS', ctrl=False, shift=True, alt=False)
		kmi.properties.name = 'UI_MT_random_flow'
		kmi.active = True
		addon_keymaps.append((km, kmi))

def remove_hotkey():

	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)

	addon_keymaps.clear()

class USERPREF_OT_change_hotkey(Operator):
	'''Add hotkey'''
	bl_idname = "add_hotkey.rflow"
	bl_label = "Add Hotkey"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):

		add_hotkey()

		return {'FINISHED'}

addon_keymaps = []

class RFlow_Props(PropertyGroup):

	parent_result : BoolProperty(
		default     = True,
		name        = "Parent To Source",
		description = "Parent randomized objects to source mesh"
		)
	dynamic_scale : BoolProperty(
		default     = True,
		name        = "Dynamic Scale",
		description = "Adjust depth and scaling values based on source object dimensions"
		)
	scale_factor : FloatProperty(
		description = "Dynamic scale factor",
		name        = "Scale Factor",
		default     = 1.0,
		min         = 0.0,
		soft_max    = 2.0,
		step        = 0.1,
		precision   = 3
		)
	clear_select : BoolProperty(
		default     = False,
		name        = "Clear Selection",
		description = "Clear selection for some random operators after usage"
		)
	all_mods : BoolProperty(
		default     = False,
		name        = "Copy All Modifiers",
		description = "Copy all modifiers from source object to random objects"
		)
	link_angle : FloatProperty(
		name        = "Sharpness",
		description = "Select flat linked faces sharpness limit. Press alt then click on random operator button to use.",
		default     = radians(15),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	select_limit : IntProperty(
		name        = "Face Select Limit",
		description = "Number of faces selected before resetting subdivision cuts",
		default     = 50,
		min         = 0,
		soft_max    = 10000,
		step        = 1
		)
	select_influence : FloatProperty(
		description = "Select influence value for Extract Proxy",
		name        = "Select Influence",
		default     = 1.0,
		min         = 0,
		max         = 1.0
		)
	normal_guide : FloatVectorProperty(
		subtype     = 'TRANSLATION',
		description = "Normal guide for random animation mesh rotation"
		)

classes = (
	UI_PT_rflow_addon_pref,
	USERPREF_OT_change_hotkey,
	RFlow_Props,
	)

def register():

	from bpy.utils import register_class

	for cls in classes:
		register_class(cls)

	bpy.types.Scene.rflow_props = PointerProperty(
		type        = RFlow_Props,
		name        = "Random Flow Properties",
		description = ""
		)

	add_hotkey()

def unregister():

	from bpy.utils import unregister_class

	remove_hotkey()

	for cls in reversed(classes):
		unregister_class(cls)

	del bpy.types.Scene.rflow_props
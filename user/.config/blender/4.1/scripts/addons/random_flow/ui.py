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
from bpy.types import (
		Menu
		)

from .operators import *
from .preferences import *

class UI_MT_random_flow(Menu):
	bl_label = "Random Flow"
	bl_idname = "UI_MT_random_flow"

	def draw(self, context):

		obj = context.active_object

		props = context.scene.rflow_props
		prefs = context.preferences.addons[__package__].preferences

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("rand_loop_extr.rflow", icon="ORIENTATION_NORMAL")
		layout.operator("rand_panels.rflow", icon="MESH_GRID")
		layout.operator("rand_slice.rflow", icon="MOD_MULTIRES")
		layout.operator("rand_axis_extr.rflow", icon="SORTBYEXT")
		layout.operator("rand_cells.rflow", icon="MOD_MASK")
		layout.operator("rand_scatter.rflow", icon="OUTLINER_OB_POINTCLOUD")
		layout.operator("rand_tubes.rflow", icon="IPO_CONSTANT")
		layout.operator("rand_cables.rflow", icon="FORCE_CURVE")
		layout.operator("rand_vcol.rflow", icon="COLORSET_10_VEC")
		layout.operator("rand_anim.rflow", icon="RENDER_ANIMATION")
		layout.separator()
		if props.use_aux_mods:
			layout.menu("UI_MT_rflow_auxilliary")
			layout.separator()
		layout.operator("part_mesh.rflow", icon="IMGDISPLAY")
		layout.operator("n_picker.rflow", icon='SNAP_NORMAL')
		layout.separator()
		layout.menu("UI_MT_rflow_utility")
		layout.menu("UI_MT_rflow_shading")
		layout.separator()
		layout.menu("UI_MT_rflow_mesh")
		layout.separator()
		layout.menu("UI_MT_rflow_extras")
		layout.menu("UI_MT_rflow_settings")
		if prefs.show_helper:
			layout.separator()
			layout.operator("use_info.rflow", text="Usage Info", icon="INFO")

class UI_MT_rflow_auxilliary(Menu):
	bl_label = "Auxilliary Add-ons"
	bl_idname = "UI_MT_rflow_auxilliary"

	def draw(self, context):

		props = context.scene.rflow_props
		addon_list = list_aux_addons() if props.use_aux_mods else []

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		if "skin_vertex" in addon_list:
			layout.operator("skin_vertex.bga", text="Skin Vertex")
		if "panel_cutter" in addon_list:
			layout.operator("panel_cut.bga", text="Panel Cut")

class UI_MT_rflow_utility(Menu):
	bl_label = "Utility"
	bl_idname = "UI_MT_rflow_utility"

	def draw(self, context):

		obj = context.active_object

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		if obj:
			layout.operator("make_flanges.rflow", icon="GP_ONLY_SELECTED")
			layout.operator("panel_screws.rflow", icon="GRIP")
			layout.operator("panel_cloth.rflow", icon="MOD_CLOTH")
			layout.operator("plate_insets.rflow", icon="SELECT_EXTEND")
			layout.operator("quick_displ.rflow", icon="MOD_DISPLACE")
			layout.separator()
		layout.operator("img_browser.rflow", icon='FILE_FOLDER')

class UI_MT_rflow_shading(Menu):
	bl_label = "Shading"
	bl_idname = "UI_MT_rflow_shading"

	def draw(self, context):

		layout = self.layout
		layout.operator("bvl_node.rflow")
		layout.operator("append_mats.rflow")

class UI_MT_rflow_mesh(Menu):
	bl_label = "Mesh"
	bl_idname = "UI_MT_rflow_mesh"

	def draw(self, context):

		obj = context.active_object

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.menu("UI_MT_rflow_data")
		if obj \
			and obj.type == 'MESH' \
			and obj.data.is_editmode:
			layout.separator()
			layout.operator("tag_verts.rflow", icon="VERTEXSEL")
		layout.separator()
		if obj \
			and obj.type == 'MESH' \
			and obj.data.is_editmode:
			layout.operator("auto_mirror.rflow", icon="MOD_MIRROR")
			layout.operator("crease_sharp.rflow", icon="EDGESEL")
			layout.operator("smooth_sharp.rflow", icon="MOD_SMOOTH")
			layout.operator("sort_elem.rflow", icon="SORTBYEXT")
			layout.operator("filter_select.rflow", icon="FACE_MAPS")
			layout.separator()
			layout.operator("grid_project.rflow", icon="MESH_GRID")
			layout.operator("quad_slice.rflow", icon="GRID")
		if obj \
			and obj.type in { 'MESH', 'CURVE' } \
			and not obj.data.is_editmode:
			layout.operator("auto_mirror.rflow", icon="MOD_MIRROR")
			layout.operator("crease_sharp.rflow", icon="EDGESEL")
			layout.operator("smooth_sharp.rflow", icon="MOD_SMOOTH")
			layout.operator("extr_proxy.rflow", icon="FACESEL")
			layout.operator("apply_mesh.rflow", icon="IMPORT")
			layout.separator()
			layout.operator("clear_bands.rflow", icon="OUTLINER_OB_FORCE_FIELD")
			layout.operator("clear_dtobjs.rflow", icon="GROUP")

class UI_MT_rflow_data(Menu):
	bl_label = "Data"
	bl_idname = "UI_MT_rflow_data"

	def draw(self, context):

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("save_data.rflow", text="Save").mode = 'SAVE'
		layout.operator("save_data.rflow", text="Use").mode = 'USE'
		layout.operator("save_data.rflow", text="Clear").mode = 'CLEAR'

class UI_MT_rflow_extras(Menu):
	bl_label = "Extras"
	bl_idname = "UI_MT_rflow_extras"

	def draw(self, context):

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("join_objs.rflow", icon="STICKY_UVS_LOC")
		layout.operator("split_mesh.rflow", icon="STICKY_UVS_DISABLE")
		layout.operator("set_origin.rflow", icon="OBJECT_ORIGIN")
		layout.operator("clean_up.rflow", icon="MESH_DATA")
		layout.separator()
		layout.operator("merge_objs.rflow", icon="PIVOT_INDIVIDUAL")

class UI_MT_rflow_settings(Menu):
	bl_label = "Settings"
	bl_idname = "UI_MT_rflow_settings"

	def draw(self, context):

		props = context.scene.rflow_props
		prefs = context.preferences.addons[__package__].preferences

		layout = self.layout
		layout.prop(props, "parent_result")
		layout.prop(props, "dynamic_scale")
		layout.prop(props, "clear_select")
		layout.prop(props, "all_mods")
		layout.separator()
		layout.prop(props, "scale_factor")
		layout.prop(props, "link_angle")
		layout.prop(props, "select_limit")
		layout.separator()
		layout.prop(props, "use_aux_mods")
		layout.prop(prefs, "show_helper")

classes = (
	UI_MT_random_flow,
	UI_MT_rflow_auxilliary,
	UI_MT_rflow_utility,
	UI_MT_rflow_shading,
	UI_MT_rflow_mesh,
	UI_MT_rflow_data,
	UI_MT_rflow_extras,
	UI_MT_rflow_settings,
	)

def register():

	from bpy.utils import register_class

	for cls in classes:
		register_class(cls)

def unregister():

	from bpy.utils import unregister_class

	for cls in reversed(classes):
		unregister_class(cls)
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
import os
import colorsys
import numpy as np
from random import random, randint, sample, uniform, choice, choices, seed, shuffle, triangular
from collections import Counter
import bmesh
from math import *
from mathutils import *
from mathutils.bvhtree import BVHTree
from itertools import chain, groupby
from bpy.props import *
from bpy_extras.io_utils import ImportHelper
from addon_utils import check as mod_check, paths as mod_paths
from bpy.types import (
		Operator,
		)

from .utils import *
from .preferences import *

class OBJECT_OT_r_loop_extrude(Operator):
	'''Stack objects with randomized faces to create interesting shapes'''
	bl_idname = 'rand_loop_extr.rflow'
	bl_label = 'Random Loop Extrude'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	loop_objs : EnumProperty(
		name = "Loop Objects",
		description = "Loop objects 1-5",
		items = (
			('1', '1','Add loop object 1'),
			('2', '2','Add loop object 2'),
			('3', '3','Add loop object 3'),
			('4', '4','Add loop object 4'),
			('5', '5','Add loop object 5')),
		options = {"ENUM_FLAG"})
	lratio : FloatVectorProperty(
		name        = "Loop Ratio",
		description = "Number of randomized faces per loop",
		default     = (50,50,50,50,50),
		size        = 5,
		min         = 0.0,
		max         = 100,
		precision	= 0,
		step        = 100
		)
	lratio_seed : IntVectorProperty(
		name        = "Seed per loop ratio",
		description = "Randomize loop ration seed",
		default     = (1,1,1,1,1),
		size        = 5,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	size_mode : EnumProperty(
		name = 'Size Mode',
		description = "Size mode to use for loop ratio",
		items = (
			('PERCENT', 'Percent',''),
			('NUMBER', 'Number','')),
		default = 'PERCENT'
		)
	solver : EnumProperty(
		name = 'Solver',
		description = "Determines the method of generating islands",
		items = (
			('WALK', 'Walk','Chance to expand island by walking previous cells'),
			('RADIAL', 'Radial','Expand island by square area')),
			default = 'WALK'
		)
	path : EnumProperty(
		name = 'Path',
		description = "Determines what edge length to favor when generating new island cells",
		items = (
			('NONE', 'None','Do not favor any edge length when generating islands'),
			('SHORTEST', 'Shortest','Favor shorter edges when generating islands'),
			('LONGEST', 'Longest','Favor longer edges when generating islands')),
		default = 'NONE'
		)
	even_offset : EnumProperty(
		name = 'Even Offset',
		items = (
			('ON', 'On',''),
			('OFF', 'Off','')),
		default = 'ON'
		)
	clear_faces : EnumProperty(
		name = 'Clear Faces',
		items = (
			('NONE', 'None',''),
			('INNER', 'Inner',''),
			('OUTER', 'Outer','')),
		default = 'NONE'
		)
	lsolver_num : IntVectorProperty(
		name        = "Solver",
		description = "Solver per loop",
		default     = (1,1,1,1,1),
		size        = 5,
		min         = 1,
		max			= 3,
		step        = 1
		)
	lpath_num : IntVectorProperty(
		name        = "Path",
		description = "Path per loop",
		default     = (1,1,1,1,1),
		size        = 5,
		min         = 1,
		max			= 3,
		step        = 1
		)
	lshading_num : IntVectorProperty(
		name        = "Limit Smooth",
		description = "Limit smooth shading per loop",
		default     = (1,1,1,1,1),
		size        = 5,
		min         = 1,
		max			= 4,
		step        = 1
		)
	lbase_shading_num : IntVectorProperty(
		name        = "Shading",
		description = "Shading per loop",
		default     = (2,2,2,2,2),
		size        = 5,
		min         = 1,
		max			= 3,
		step        = 1
		)
	lsize01_min : FloatVectorProperty(
		name        = "Loop Panel Size %",
		description = "Minimum panel size per loop object",
		default     = (0,0,0,0,0),
		size        = 5,
		min         = 0,
		soft_min    = 1.0,
		max         = 100,
		precision	= 0,
		step        = 100
		)
	lsize01_max : FloatVectorProperty(
		name        = "Loop Panel Size %",
		description = "Maximum panel size per loop object",
		default     = (10,10,10,10,10),
		size        = 5,
		min         = 0,
		soft_min    = 1.0,
		max         = 100,
		precision	= 0,
		step        = 100
		)
	lsize02_min : IntVectorProperty(
		name        = "Loop Panel Size",
		description = "Minimum panel size per loop object",
		default     = (0,0,0,0,0),
		size        = 5,
		min         = 0,
		soft_min    = 0,
		soft_max    = 1000,
		step        = 1
		)
	lsize02_max : IntVectorProperty(
		name        = "Loop Panel Size",
		description = "Maximum panel size per loop object",
		default     = (100,100,100,100,100),
		size        = 5,
		min         = 0,
		soft_min    = 1,
		soft_max    = 1000,
		step        = 1
		)
	loop_subdv : IntVectorProperty(
		name        = "Loop Subdivision",
		description = "Subdivision per loop object",
		default     = (0,0,0,0,0),
		size        = 5,
		min         = 0,
		soft_max    = 6,
		step        = 1
		)
	lthick : FloatVectorProperty(
		name        = "Loop Thickness",
		description = "Inset thickness per loop",
		default     = (0.005,0.005,0.005,0.005,0.005),
		size        = 5,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	ldepth_max : FloatVectorProperty(
		name        = "Loop Depth",
		description = "Inset depth per loop",
		default     = (0.02,0.025,0.03,0.035,0.04),
		size        = 5,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	ldepth_min : FloatVectorProperty(
		name        = "Loop Depth",
		description = "Inset depth per loop",
		default     = (0.005,0.005,0.005,0.005,0.005),
		size        = 5,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	ldepth_seed : IntVectorProperty(
		name        = "Loop Depth Seed",
		description = "Inset depth random seed per loop",
		default     = (1,1,1,1,1),
		size        = 5,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	globl_seed1 : IntProperty(
		name        = "Ratio Global Seed",
		description = "Global seed for loop ratio",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	globl_seed2 : IntProperty(
		name        = "Depth Global Seed",
		description = "Global seed for loop inset depth",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for base object",
		default     = 0,
		min         = 0,
		soft_max    = 12,
		step        = 1
		)
	cuts_smooth : FloatProperty(
		name        = "Factor",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	smooth_iter : IntProperty(
		name        = "Repeat",
		description = "Number of times to repeat smoothing",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	base_smooth : BoolProperty(
		name        = "Base Smooth",
		description = "Smooth base instead of final mesh",
		default     = False
		)
	cut_method : EnumProperty(
		name = "Cut Method",
		description = "Determines how sharp edges will be cut",
		items = (
			('WRAP', 'Wrap',''),
			('SPLIT', 'Split','')),
		default = 'WRAP'
		)
	cut_threshold : FloatProperty(
		name        = "Cut Angle",
		description = "Maximum angle threshold for edges to be cut",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	tri_perc : FloatProperty(
		name        = "Triangulate",
		description = "Triangulate faces",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	tri_num : IntProperty(
		name        = "Triangulate",
		description = "Triangulate faces via number",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	rand_inset : BoolProperty(
		name        = "Individual Height",
		description = "Randomize face islands inset height",
		default     = True
		)
	orig_only : BoolProperty(
		name        = "Loop From Source",
		description = "Extrude loops from original/source object only",
		default     = True
		)
	indiv_sp : BoolProperty(
		name        = "Individual Solver/Path",
		description = "Give each loop its own unique solver and path",
		default     = True
		)
	inset_vgroup : BoolProperty(
		default     = False,
		name        = "Use Vertex Group",
		description = "Assign top inset faces to vertex group"
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = True
		)
	clip_dist : FloatProperty(
		name        = "Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	clip_axis : BoolVectorProperty(
		name        = "Clip Axis",
		description = "Clip axis toggles",
		default     = (True, True, True),
		size		= 3,
		subtype		= "XYZ"
		)
	use_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to remove subdivision from loop object (Slower)",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def execute(self, context):

		obj = context.active_object
		obj.update_from_editmode()

		mat = obj.matrix_world

		copy_data = None
		even_offset = self.even_offset == 'ON'

		mesh = obj.data

		if any(i for i in self.lshading_num if i != 1):
			copy_data = mesh.copy()
			mesh.set_sharp_from_angle(angle=radians(30))

		orig_mesh = cont_mesh = mesh if self.use_mirror else get_eval_mesh(obj)

		loop_objs = set()
		loop_count = [int(i) for i in self.loop_objs] \
			if self.loop_objs else [0]

		ret_idx = set()
		for i in range(0, max(loop_count)):
			limit_smooth = self.lshading_num[i] > 1

			bm = bmesh.new()
			temp_mesh = bpy.data.meshes.new(".temp")
			bm.from_mesh(cont_mesh if not self.orig_only else orig_mesh)

			if self.cuts_smooth \
				and self.base_smooth:
				mesh_smooth(bm, bm.verts, self.cuts_smooth, self.smooth_iter)

			if i == 0 or \
				self.orig_only:
				bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
				bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=self.cuts_base, use_grid_fill=True)
			else: bpy.data.meshes.remove(cont_mesh)

			if ret_idx:
				inset_faces = [f for f in bm.faces if f.index in ret_idx]
				bmesh.ops.delete(bm, geom=inset_faces, context='FACES')

			if limit_smooth:
				for e in bm.edges: e.smooth = True

			bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=self.loop_subdv[i], use_grid_fill=True)

			if self.tri_perc \
				or self.tri_num:
				tval = self.tri_perc if self.size_mode == 'PERCENT' else self.tri_num
				tris = get_tri_faces(bm.faces, tval, self.lratio_seed[i], mode=self.size_mode)
				bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))

			idx = set([f.index for f in bm.faces])
			if self.size_mode == 'PERCENT':
				size1 = int(len(idx) * self.lsize01_min[i]/100)
				size2 = int(len(idx) * self.lsize01_max[i]/100)
			else:
				size1 = self.lsize02_min[i]
				size2 = self.lsize02_max[i]

			min_size = min(size1, size2)
			max_size = max(size1, size2)

			solvers = ["WALK", "RADIAL", "SQUARE"]
			loop_solver = solvers[self.lsolver_num[i]-1]
			paths = ["NONE", "SHORTEST", "LONGEST"]
			loop_path = paths[self.lpath_num[i]-1]

			split_edg, cells = random_walk(bm, idx, min_size, max_size,(self.lratio_seed[i] + i) + self.globl_seed1, \
				sampling=loop_solver, path=loop_path, cut_threshold=self.cut_threshold, wrap_angle=self.cut_method == 'WRAP')

			if self.cut_method == 'WRAP':
				bmesh.ops.split_edges(bm, edges=split_edg)
			else:
				elist = [e for e in bm.edges if e in split_edg \
						or (e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)]

				bmesh.ops.split_edges(bm, edges=elist)

			seed(self.lratio_seed[i] + self.globl_seed1)
			rem_cells = sample(cells, int(len(cells) * (1 - self.lratio[i]/100)))
			bmesh.ops.delete(bm, geom=sum(rem_cells, []), context='FACES')

			ret_inset = []
			if self.rand_inset:
				for n, cell_faces in enumerate(cells):
					if not cell_faces in rem_cells:
						seed((self.ldepth_seed[i] + n) + self.globl_seed2)
						ldepth_random = uniform(self.ldepth_min[i], self.ldepth_max[i])
						ret = bmesh.ops.inset_region(bm, faces=cell_faces, use_boundary=True, use_even_offset=even_offset, \
							thickness=self.lthick[i] * self.mdv, depth=ldepth_random * self.mdv)['faces']

						if limit_smooth:
							inset_edges = set(sum([list(f.edges) for f in ret], []))

							if self.lshading_num[i] == 4:
								seed(n + i)
								shade_smooth = choice([2, 3])
							else:
								shade_smooth = self.lshading_num[i]

							for e in inset_edges:
								if shade_smooth == 2:
									if e.is_boundary: e.smooth = False

								if shade_smooth == 3:
									if not e.is_boundary \
										and len([lf for lf in e.link_faces if lf in ret]) == 1: e.smooth = False

						ret_inset.extend(ret)
			else:
				seed((self.ldepth_seed[i] + i) + self.globl_seed2)
				ldepth_uniform = uniform(self.ldepth_min[i], self.ldepth_max[i])
				loop_cells = sum([x for x in cells if not x in rem_cells], [])
				ret = bmesh.ops.inset_region(bm, faces=loop_cells, use_boundary=True, use_even_offset=even_offset, \
					thickness=self.lthick[i] * self.mdv, depth=ldepth_uniform * self.mdv)['faces']

				if limit_smooth:
					inset_edges = set(sum([list(f.edges) for f in ret], []))
					for e in inset_edges:
						if self.lshading_num[i] == 2:
							if e.is_boundary: e.smooth = False

						if self.lshading_num[i] == 3:
							if not e.is_boundary \
								and len([lf for lf in e.link_faces if lf in ret]) == 1: e.smooth = False

				ret_inset.extend(ret)

			if self.clear_faces != 'NONE':
				remf = list(set(bm.faces).difference(set(ret_inset))) if self.clear_faces == 'INNER' else ret_inset
				bmesh.ops.delete(bm, geom=remf, context='FACES')

			if not self.orig_only: ret_idx = [f.index for f in ret_inset if f in bm.faces]

			if self.cuts_smooth \
				and not self.base_smooth:
				mesh_smooth(bm, bm.verts, self.cuts_smooth, self.smooth_iter)

			if self.tri_perc or self.tri_num: bmesh.ops.join_triangles(bm, faces=bm.faces, \
				angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

			if self.use_clip: clip_center(bm, obj, self.clip_dist, self.clip_axis)

			list_co = [(mat @ v.co) for v in bm.verts if not all(f in ret_inset for f in v.link_faces)] \
				if self.inset_vgroup else []

			if self.lshading_num[i] == 2:
				temp_mesh.set_sharp_from_angle(angle=radians(30))

			if self.lshading_num[i] == 4:
				mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

				if mirror:
					for e in bm.edges:
						co = (e.verts[0].co + e.verts[1].co) / 2

						if check_center(mirror.use_axis, co):
							e.smooth = True; e.seam = False

			bm.to_mesh(temp_mesh)
			bm.free()

			if not self.orig_only:
				cont_mesh = temp_mesh.copy()
				cont_mesh.materials.clear()

			if str(i + 1) in self.loop_objs \
				and temp_mesh.polygons:
				new_obj = bpy.data.objects.new(filter_name(obj, "_RLExtr"), temp_mesh)
				orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
				new_obj.scale = orig_scale
				new_obj.rotation_euler = orig_rot.to_euler()
				new_obj.location = orig_loc

				assign_mat(self, obj, new_obj, self.mat_index)

				if not limit_smooth:
					new_obj.data.edges.foreach_set('use_edge_sharp', [False] * len(new_obj.data.edges))
					set_sharp(new_obj.data, self.lbase_shading_num[i])

				if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

				set_parent(obj, new_obj)

				refresh_vcolor(new_obj)

				inset_to_vgroup(new_obj, list_co, mat)
				loop_objs.add(new_obj)

		if self.use_dissolve:
			for i, o in enumerate(loop_objs):
				mesh = o.data
				bm = bmesh.new()
				bm.from_mesh(mesh)

				if self.use_dissolve:
					bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
						use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

					if 	self.lshading_num[i] > 2:
						bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

				bm.to_mesh(mesh)
				bm.free()

		if context.scene.rflow_props.clear_select: clear_select(obj)

		if copy_data: reset_data(obj, copy_data)

		return {'FINISHED'}

	def draw(self, context):

		props = context.scene.rflow_props
		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		col.label(text="Loops | Ratio | Seed" + (" " * 1) + "(shift+click to add multiple or remove)")
		col.row(align=True).prop(self, "loop_objs", expand=True)
		col.row(align=True).prop(self, "lratio", text="")
		col.row(align=True).prop(self, "lratio_seed", text="")
		col.row(align=True).prop(self, "globl_seed1")
		col.label(text="Loops Inset Depth Max | Min | Seed")
		col.row(align=True).prop(self, "ldepth_max", text="")
		col.row(align=True).prop(self, "ldepth_min", text="")
		col.row(align=True).prop(self, "ldepth_seed", text="")
		col.row(align=True).prop(self, "globl_seed2")
		col.label(text="Loops Inset Thickness")
		col.row(align=True).prop(self, "lthick", text="")
		col.label(text="Loops Subdivision")
		col.row(align=True).prop(self, "loop_subdv", text="")
		if self.size_mode == 'PERCENT':
			col.label(text="Loops Panel Size (Percent) Max | Min")
			col.row(align=True).prop(self, "lsize01_max", text="")
			col.row(align=True).prop(self, "lsize01_min", text="")
		else:
			col.label(text="Loops Panel Size (Number) Max | Min")
			col.row(align=True).prop(self, "lsize02_max", text="")
			col.row(align=True).prop(self, "lsize02_min", text="")
		col.label(text="Solver: 1. Walk 2. Radial 3. Square")
		col.row(align=True).prop(self, "lsolver_num", text="")
		col.label(text="Path: 1. None 2. Shortest 3. Longest (Walk Only)")
		col.row(align=True).prop(self, "lpath_num", text="")
		col.label(text="Limit Smooth: 1. None 2. Base 3. Top 4. Random")
		col.row(align=True).prop(self, "lshading_num", text="")
		col.label(text="Base Smooth: 1. Smooth 2. Angle 3. Flat")
		col.row(align=True).prop(self, "lbase_shading_num", text="")
		col.separator(factor=0.5)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size Mode:")
		row.row(align=True).prop(self, "size_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		row.row(align=True).prop(self, "cuts_base")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Smoothing:")
		split1 = row.split(factor=0.5, align=True)
		split1.row(align=True).prop(self, "cuts_smooth")
		split2 = split1.split(factor=0.8, align=True)
		split2.row(align=True).prop(self, "smooth_iter")
		split2.prop(self, "base_smooth", text="", icon="MESH_UVSPHERE")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Even Offset:")
		row.row(align=True).prop(self, "even_offset", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Method:")
		row.row(align=True).prop(self, "cut_method", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Angle:")
		row.row(align=True).prop(self, "cut_threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Clear Faces:")
		row.row(align=True).prop(self, "clear_faces", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Triangulate:")
		if self.size_mode == 'PERCENT':
			row.row(align=True).prop(self, "tri_perc", text="")
		else:
			row.row(align=True).prop(self, "tri_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "rand_inset")
		flow.prop(self, "orig_only")
		flow.prop(self, "inset_vgroup")
		row = col.row().split(factor=0.5, align=True)
		row.prop(self, "use_clip")
		if self.use_clip:
			row.row(align=True).prop(self, "clip_axis", text="", expand=True)
			col.prop(self, "clip_dist")
		col.prop(self, "use_dissolve")
		if self.use_dissolve:
			col.prop(self, "angle")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		dim = obj.dimensions.copy()
		self.mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

		self.loop_objs = set()
		self.lratio_seed = (1,1,1,1,1)
		self.ldepth_seed = (1,1,1,1,1)
		self.globl_seed1 = 1
		self.globl_seed2 = 1

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face:
			init_props(self, event, ops='rloop', force=has_face>=props.select_limit)
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_r_panels(Operator):
	'''Create randomized paneling details'''
	bl_idname = 'rand_panels.rflow'
	bl_label = 'Random Panels'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	type : EnumProperty(
		name = 'Type',
		description = "Determines the method of generating panel cuts",
		items = (
			('INSET', 'Inset','Generate panel cuts using inset with the ability to change height by section (non-destructive)'),
			('BEVEL', 'Bevel','Generate panel cuts using bevel with the advantage of not raising the mesh (destructive)')),
		default = 'INSET'
		)
	solver : EnumProperty(
		name = 'Solver',
		description = "Determines the method of generating islands",
		items = (
			('WALK', 'Walk','Expand island by walking previous cells'),
			('RADIAL', 'Radial','Expand island by radial expansion'),
			('SQUARE', 'Square','Expand island by square shapes')),
		default = 'WALK'
		)
	path : EnumProperty(
		name = 'Path',
		description = "Determines what edge length to favor when generating new island cells",
		items = (
			('NONE', 'None','Do not favor any edge length when generating islands'),
			('SHORTEST', 'Shortest','Favor shorter edges when generating islands'),
			('LONGEST', 'Longest','Favor longer edges when generating islands')),
		default = 'NONE'
		)
	size_mode : EnumProperty(
		name = 'Size Mode',
		items = (
			('PERCENT', 'Percent',''),
			('NUMBER', 'Number','')),
		default = 'PERCENT'
		)
	even_offset : EnumProperty(
		name = 'Even Offset',
		items = (
			('ON', 'On',''),
			('OFF', 'Off','')),
		default = 'ON'
		)
	panel_amount : FloatProperty(
		name        = "Panel Amount",
		description = "Total number of panel islands",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 100,
		subtype     = "PERCENTAGE"
		)
	panel_max_perc : FloatProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		min         = 0,
		max         = 100,
		soft_min    = 1,
		precision   = 0,
		default     = 5,
		subtype     = "PERCENTAGE"
		)
	panel_max_num : IntProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		default     = 100,
		min         = 0,
		soft_min    = 1,
		soft_max    = 1000,
		step        = 1
		)
	panel_min_perc : FloatProperty(
		name        = "Minimum Size",
		description = "Minimum panel size for radial sampling",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	panel_min_num : IntProperty(
		name        = "Minimum Size",
		description = "Minimum panel size for radial sampling",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	notch_count : IntProperty(
		name        = "Count",
		description = "Panel island notch count",
		default     = 0,
		min         = 0,
		max         = 10000,
		step        = 1
		)
	notch_size : IntProperty(
		name        = "Size",
		description = "Panel island notch size",
		default     = 0,
		min         = 0,
		max         = 10000,
		step        = 1
		)
	notch_seed : IntProperty(
		name        = "Seed",
		description = "Randomize panel notch random seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cuts_smooth : FloatProperty(
		name        = "Factor",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	smooth_iter : IntProperty(
		name        = "Repeat",
		description = "Number of times to repeat smoothing",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	base_smooth : BoolProperty(
		name        = "Base Smooth",
		description = "Smooth base instead of final mesh",
		default     = False
		)
	area_smooth : BoolProperty(
		name        = "Area Smooth",
		description = "Only smooth selected area in merge",
		default     = False
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		soft_max    = 12,
		step        = 1
		)
	edge_seed : IntProperty(
		name        = "Seed",
		description = "Randomize panel cuts",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	bvl_offset_min : FloatProperty(
		name        = "Min",
		description = "Minimum bevel offset/width",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	bvl_offset_max : FloatProperty(
		name        = "Max",
		description = "Maximum bevel offset/width",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	bvl_offset_uni : FloatProperty(
		name        = "Offset",
		description = "Uniform bevel offset/width",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	bvl_seg : IntProperty(
		name        = "Segments",
		description = "Bevel segments",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
	)
	bvl_angle : FloatProperty(
		name        = "Limit",
		description = "Maximum angle threshold for vertices to get beveled",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	bvl_seed : IntProperty(
		name        = "Bevel Seed",
		description = "Randomize bevel width",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Island margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	margin_indent : FloatProperty(
		name        = "In",
		description = "Idented island margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	margin_outdent : FloatProperty(
		name        = "Out",
		description = "Outdented island margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	thickness : FloatProperty(
		name        = "Thick",
		description = "Inset thickness",
		default     = 0.005,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	depth : FloatProperty(
		name        = "Depth",
		description = "Inset depth",
		default     = 0.005,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	cut_method : EnumProperty(
		name = "Cut Method",
		description = "Determines how sharp edges will be cut",
		items = (
			('WRAP', 'Wrap',''),
			('SPLIT', 'Split','')),
		default = 'WRAP'
		)
	cut_threshold : FloatProperty(
		name        = "Cut Angle",
		description = "Maximum angle threshold for edges to be cut",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	clear_faces : EnumProperty(
		name = 'Clear Faces',
		items = (
			('NONE', 'None',''),
			('INNER', 'Inner',''),
			('OUTER', 'Outer','')),
		default = 'NONE'
		)
	thickness_min : FloatProperty(
		name        = "Min",
		description = "Minimum randomized cell thickness",
		default     = 0.005,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	thickness_max : FloatProperty(
		name        = "Max",
		description = "Maximum randomized cell thickness",
		default     = 0.005,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	thickness_seed : IntProperty(
		name        = "Thickness Seed",
		description = "Inset thickness randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_thickness : BoolProperty(
		name        = "Uniform Thickness",
		description = "Use single property value for inset thickness",
		default     = True
		)
	depth_min : FloatProperty(
		name        = "Min",
		description = "Minimum randomized cell depth",
		default     = 0.005,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	depth_max : FloatProperty(
		name        = "Max",
		description = "Maximum randomized cell depth",
		default     = 0.005,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	depth_seed : IntProperty(
		name        = "Depth Seed",
		description = "Inset depth randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_depth : BoolProperty(
		name        = "Uniform Depth",
		description = "Use single property value for inset depth or height",
		default     = False
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	tri_perc : FloatProperty(
		name        = "Triangulate",
		description = "Triangulate faces via percentage",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	tri_num : IntProperty(
		name        = "Triangulate",
		description = "Triangulate faces via number",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	limit_smooth : EnumProperty(
		name = 'Limit SMooth',
		items = (
			('NONE', 'None','No limit on auto smooth'),
			('BASE', 'Base','Sharpen base plate area'),
			('TOP', 'Top','Sharpen top plate area'),
			('RANDOM', 'Random','Randomize between base and top')),
		default = 'NONE'
		)
	base_shading : EnumProperty(
		name = 'Shading',
		items = (
			('SMOOTH', 'Smooth','Faces are smooth shaded'),
			('ANGLE', 'By Angle','Faces are smooth shaded by angle'),
			('FLAT', 'Flat','Faces are flat shaded')),
		default = 'ANGLE'
		)
	shading_seed : IntProperty(
		name        = "Shading Seed",
		description = "Randomize smooth shading between limit smooth base and top",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_bevel : BoolProperty(
		name        = "Uniform Bevel",
		description = "Use single property value for bevel offset",
		default     = False
		)
	invert_panel_amount : BoolProperty(
		name        = "Invert Panel Amount",
		description = "Invert panel amount influence",
		default     = False
		)
	remove_panels : BoolProperty(
		name        = "Remove Panels",
		description = "Remove panels instead of flattening them",
		default     = False
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	merge_pnl : BoolProperty(
		name        = "Merge Panel",
		description = "Merge panel to original object",
		default     = False
		)
	floater_set : BoolProperty(
		name        = "Floater Mesh",
		description = "Set cycles render visibility to make it look like resulting mesh is part of source mesh",
		default     = False
		)
	inset_vgroup : BoolProperty(
		default     = False,
		name        = "Use Vertex Group",
		description = "Assign top inset faces to vertex group"
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = True
		)
	clip_dist : FloatProperty(
		name        = "Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	clip_axis : BoolVectorProperty(
		name        = "Clip Axis",
		description = "Clip axis toggles",
		default     = (True, True, True),
		size		= 3,
		subtype		= "XYZ"
		)
	use_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	only_msharp : BoolProperty(
		name        = "Marked Sharp Only",
		description = "Get marked sharp edges result only",
		default     = False
		)
	pnl_width : FloatProperty(
		name        = "Width",
		description = "Width of the outside panel edges",
		default     = 0.01,
		min         = 0,
		max         = 100,
		step        = 0.1,
		precision   = 4
		)
	pnl_offset : FloatProperty(
		name        = "Offset",
		description = "Offset of the middle panel edges",
		default     = 0.005,
		step        = 0.1,
		precision   = 4
		)
	margin_bounds : BoolProperty(
		name        = "Margin Boundary",
		description = "Use boundary when making margin for panel cut details",
		default     = True
		)
	split_borders : BoolProperty(
		name        = "Split Borders",
		description = "Split selection borders when using bevel type",
		default     = True
		)
	cut_symm : BoolProperty(
		name        = "Cut Symmetry",
		description = "Create panel cuts on mirror modifier symmetry lines",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def execute(self, context):

		obj = context.active_object
		obj.update_from_editmode()

		merge_pnl = False

		def randomize_edges(bm, faces):

			idx = set([f.index for f in faces])
			if self.size_mode == 'PERCENT':
				numf = len(idx)
				size1 = int(ceil(numf * (self.panel_min_perc/100)))
				size2 = int(ceil(numf * (self.panel_max_perc/100)))
			else:
				size1 = self.panel_min_num
				size2 = self.panel_max_num

			min_size = min(size1, size2)
			max_size = max(size1, size2)

			split_edg, cells = random_walk(bm, idx, min_size, max_size, self.edge_seed, sampling=self.solver, \
				notch_count=self.notch_count, notch_size=self.notch_size, notch_snum=self.notch_seed, path=self.path, \
				cut_threshold=self.cut_threshold, wrap_angle=self.cut_method == 'WRAP', mark_sharp=self.only_msharp)

			return split_edg, cells

		if self.type == 'INSET':
			even_offset = self.even_offset == 'ON'

			mat = obj.matrix_world
			list_co = []

			copy_data = None

			self.use_merge = self.clear_faces == 'NONE'
			limit_smooth = self.limit_smooth != 'NONE'

			orig_mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

			if limit_smooth:
				copy_data = orig_mesh.copy()
				if 'sharp_face' in orig_mesh.attributes:
					orig_mesh.set_sharp_from_angle(angle=radians(30))

			bm = bmesh.new()
			temp_mesh = bpy.data.meshes.new(".temp")
			bm.from_mesh(orig_mesh)

			if self.cuts_smooth \
				and self.base_smooth:
				mesh_smooth(bm, bm.verts, self.cuts_smooth, self.smooth_iter)

			bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
			bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

			bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=self.cuts_base, use_grid_fill=True)

			if self.tri_perc \
				or self.tri_num:
				tval = self.tri_perc if self.size_mode == 'PERCENT' else self.tri_num
				tris = get_tri_faces(bm.faces, tval, self.edge_seed, mode=self.size_mode)
				bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))

			split_edg, cells = randomize_edges(bm, bm.faces)

			if not self.only_msharp:
				if self.panel_amount < 100:
					tot = len(cells)
					amt = int(tot * (self.panel_amount/100))
					cells = cells[:amt] if not self.invert_panel_amount else cells[(tot-amt):]
					cells_flat = list(chain.from_iterable(cells))
					split_edg = [e for e in split_edg if any(f in cells_flat for f in e.link_faces)]
					if self.remove_panels: bmesh.ops.delete(bm, geom=list(set(bm.faces) - set(cells_flat)), context='FACES')

				if self.cut_method == 'WRAP':
					bmesh.ops.split_edges(bm, edges=split_edg)
				else:
					elist = [e for e in bm.edges if e in split_edg \
							or (e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)]

					bmesh.ops.split_edges(bm, edges=elist)

				if sum([self.bvl_offset_min, self.bvl_offset_max]) > 0 \
					if not self.uni_bevel else self.bvl_offset_uni > 0:
					self.use_merge = False
					for i, c in enumerate(cells):
						old_faces = []
						new_faces = []
						for x, f in enumerate(c):
							corner_verts = [v for v in f.verts if v.is_boundary and v.calc_edge_angle(None) \
								and v.calc_edge_angle(None) >= self.bvl_angle]
							if corner_verts:
								old_faces.append(f)
								for y, v in enumerate(corner_verts):
									seed(self.bvl_seed + i + x + y)
									bvl_offset = uniform(self.bvl_offset_min, self.bvl_offset_max) \
										if not self.uni_bevel else self.bvl_offset_uni
									bvl_verts = bmesh.ops.bevel(
										bm,
										geom            = [v],
										offset          = bvl_offset,
										offset_type     = 'OFFSET',
										segments        = self.bvl_seg,
										profile         = 0.5,
										affect          = 'VERTICES',
										clamp_overlap	= True
										)['verts']
									if bvl_verts:
										new_faces.append(bvl_verts[0].link_faces[0])

						for f in old_faces: cells[i].remove(f)
						cells[i].extend([f for f in new_faces if f in bm.faces])
						cells[i] = undupe((cells[i]))

				margin_faces = []
				merge_pnl = self.merge_pnl and self.use_merge

				if self.margin and not merge_pnl:
					margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
						use_even_offset=even_offset, thickness=self.margin)['faces']
					bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

				def merge_margins(height, faces):

					margin = self.margin_indent if height < 0 else self.margin_outdent
					margin_faces = bmesh.ops.inset_region(bm, faces=faces, use_boundary=True, \
						use_even_offset=even_offset, thickness=margin)['faces']

					return margin_faces

				ret_inset = []
				inset_faces = []

				for i, faces in enumerate(cells):
					if limit_smooth:
						fe = set(sum([list(f.edges) for f in faces], []))
						for e in fe:
							e.smooth = True

					seed(self.thickness_seed + i)
					inset_thickness = self.thickness if self.uni_thickness else uniform(self.thickness_min, self.thickness_max)

					seed(self.depth_seed + i)
					inset_depth = self.depth if self.uni_depth else uniform(self.depth_min, self.depth_max)

					if merge_pnl: margin_faces = merge_margins(inset_depth, faces)

					inset_faces = faces if not self.use_merge else [f for f in faces if not f in margin_faces]

					ret = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, use_even_offset=even_offset, \
						thickness=inset_thickness * self.mdv, depth=inset_depth * self.mdv)['faces']

					if limit_smooth:
						inset_edges = set(sum([list(f.edges) for f in ret], []))

						if self.limit_smooth  == 'RANDOM':
							seed(self.shading_seed + i)
							shade_smooth = choice(['BASE', 'TOP'])
						else:
							shade_smooth = self.limit_smooth

						for e in inset_edges:
							if shade_smooth == 'BASE':
								if e.is_boundary: e.smooth = False
							else:
								if not e.is_boundary \
									and len([lf for lf in e.link_faces if lf in ret]) == 1: e.smooth = False

					ret_inset.extend(ret)

				if self.clear_faces != 'NONE':
					remf = list(set(bm.faces).difference(set(ret_inset))) if self.clear_faces == 'INNER' else ret_inset
					bmesh.ops.delete(bm, geom=remf, context='FACES')

				if self.cuts_smooth \
					and not self.base_smooth \
					and not merge_pnl:
					mesh_smooth(bm, bm.verts, self.cuts_smooth, self.smooth_iter)

				if self.tri_perc or self.tri_num: bmesh.ops.join_triangles(bm, faces=bm.faces, \
					angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

				if self.use_dissolve and not self.merge_pnl:
					bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, use_dissolve_boundaries=False, \
						verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

					if limit_smooth:
						bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

				if self.use_clip: clip_center(bm, obj, self.clip_dist, self.clip_axis)

				list_co = [(mat @ v.co) for v in bm.verts if not all(f in ret_inset for f in v.link_faces)] \
					if self.inset_vgroup else []

				if self.limit_smooth == 'TOP':
					mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

					if mirror:
						for e in bm.edges:
							co = (e.verts[0].co + e.verts[1].co) / 2

							if check_center(mirror.use_axis, co):
								e.smooth = True; e.seam = False

			bm.to_mesh(temp_mesh)

			if not limit_smooth:
				smooth_type = ['SMOOTH', 'ANGLE', 'FLAT']
				set_sharp(temp_mesh, smooth_type.index(self.base_shading) + 1)

			link_obj = True

			if merge_pnl:
				bounds_co = []

				for e in bm.edges:
					if e.is_boundary:
						bounds_co.append((e.verts[0].co + e.verts[1].co) / 2)

					if not limit_smooth: e.smooth = True

					e.seam = False

				bm.to_mesh(temp_mesh)

				if not limit_smooth:
					smooth_type = ['SMOOTH', 'ANGLE', 'FLAT']
					set_sharp(temp_mesh, smooth_type.index(self.base_shading) + 1)

				if orig_mesh.is_editmode:
					bm_src = bmesh.from_edit_mesh(orig_mesh)
				else:
					bm_src = bmesh.new()
					bm_src.from_mesh(orig_mesh)

				if self.base_smooth:
					mesh_smooth(bm_src, [v for v in bm_src.verts if not v.is_boundary], self.cuts_smooth, self.smooth_iter)

				listf = [f for f in bm_src.faces if f.select]

				bmesh.ops.delete(bm_src, geom=listf, context='FACES')
				bmesh.ops.subdivide_edges(bm_src, edges=bm_src.edges, cuts=self.cuts_base, use_grid_fill=True)

				bm_src.from_mesh(temp_mesh)

				ref_vrt = []
				new_vrt = []

				for v in bm.verts:
					ref_vrt.append(v.co)
					if v.is_boundary: new_vrt.append(v.co)

				doubles = [ v for v in bm_src.verts if v.co in new_vrt ]

				bmesh.ops.remove_doubles(bm_src, verts=doubles, dist=1e-4)

				mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

				for e in bm_src.edges:
					co = (e.verts[0].co + e.verts[1].co) / 2
					if co in bounds_co:
						if self.limit_smooth == 'BASE' \
							or (not limit_smooth and self.base_shading == 'ANGLE'):
							e.smooth = False
						else:
							e.smooth = True

						e.seam = True

						if mirror:
							if not check_center(mirror.use_axis, co):
								e.seam = True
							else:
								e.smooth = True
								e.seam = False

				if not self.base_smooth:
					if self.area_smooth:
						mesh_smooth(bm_src, [v for v in bm_src.verts if v.co in ref_vrt and not v.is_boundary], self.cuts_smooth, self.smooth_iter)
					else:
						mesh_smooth(bm_src, [v for v in bm_src.verts if not v.is_boundary], self.cuts_smooth, self.smooth_iter)

				if self.use_dissolve:
					bmesh.ops.dissolve_limit(bm_src, angle_limit=self.angle, \
						use_dissolve_boundaries=False, verts=bm_src.verts, edges=bm_src.edges, delimit={'NORMAL'})

					if limit_smooth:
						bmesh.ops.triangulate(bm_src, faces=bm_src.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

				if orig_mesh.is_editmode:
					bmesh.update_edit_mesh(orig_mesh)
				else:
					bm_src.to_mesh(orig_mesh)
					bm_src.free()

				link_obj = False

			bm.free()

			if link_obj:
				new_obj = bpy.data.objects.new(filter_name(obj, "_RPanel"), temp_mesh)
				orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
				new_obj.scale = orig_scale
				new_obj.rotation_euler = orig_rot.to_euler()
				new_obj.location = orig_loc

				set_parent(obj, new_obj)

				refresh_vcolor(new_obj)

				assign_mat(self, obj, new_obj, self.mat_index)

				if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

				if not self.only_msharp:
					inset_to_vgroup(new_obj, list_co, mat)
					if self.floater_set \
						and self.clear_faces != 'NONE': set_floater_vis(new_obj)
				else:
					select_isolate(new_obj)

				if copy_data and not merge_pnl: reset_data(obj, copy_data)
			else:
				old_vgroup = obj.vertex_groups.get("panel_cut_faces")
				if old_vgroup: obj.vertex_groups.remove(old_vgroup)
				inset_to_vgroup(obj, list_co, mat)
		else:
			src_mesh = obj.data
			temp_obj = None

			if src_mesh.is_editmode:
				bm_src = bmesh.from_edit_mesh(src_mesh)
			else:
				bm_src = bmesh.new()
				bm_src.from_mesh(src_mesh)

			if self.cut_symm:
				temp_obj = duplicate_obj("temp_obj", obj, False, True)
				copy_modifiers([obj, temp_obj], mod_types=['MIRROR'])

				mesh = get_eval_mesh(temp_obj).copy()
			else:
				mesh = obj.data.copy()

			bm = bmesh.new()
			bm.from_mesh(mesh)

			if self.base_smooth:
				mesh_smooth(bm, bm.verts, self.cuts_smooth, self.smooth_iter)

			oldf = [f for f in bm.faces if f.select]

			if self.margin:
				bmesh.ops.inset_region(bm, faces=oldf, use_boundary=self.margin_bounds, use_even_offset=True, thickness=self.margin)

			ret = bmesh.ops.subdivide_edges(bm, edges=undupe(sum([list(f.edges) for f in oldf], [])), \
				cuts=self.cuts_base, use_grid_fill=True)['geom_inner']

			fsel = [f for f in ret if isinstance(f, bmesh.types.BMFace)] + oldf

			if self.tri_perc \
				or self.tri_num:
				tval = self.tri_perc if self.size_mode == 'PERCENT' else self.tri_num
				tris = get_tri_faces(fsel, tval, self.edge_seed, mode=self.size_mode)
				ret = bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))['faces']

				fsel += ret
				fsel = [f for f in fsel if f in bm.faces]

			split_edg, _ = randomize_edges(bm, fsel)
			sharp_edg = []

			if not self.split_borders:
				split_edg = [e for e in split_edg if all(f in fsel for f in e.link_faces)]

			if self.cut_method == 'SPLIT':
				fe = sum([list(f.edges) for f in fsel], [])
				fe = undupe(fe)

				sharp_edg = [e for e in fe if not e in split_edg and \
					(e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)]

			bvl_edges = undupe(split_edg + sharp_edg)

			for e in bvl_edges: e.smooth = False

			bvl = bmesh.ops.bevel(
				bm,
				geom            = bvl_edges,
				offset          = self.pnl_width,
				offset_type     = 'OFFSET',
				segments        = 2,
				profile         = 0.5,
				affect			= 'EDGES',
				)['faces']

			verts = sum([list(f.verts) for f in bvl], [])
			verts = list(dict.fromkeys(verts))
			split_vrt = [v for v in verts if all(f in bvl for f in v.link_faces)]

			for v in split_vrt:
				v.co += v.normal * (v.calc_shell_factor() * -self.pnl_offset)

				for e in v.link_edges:
					if all(v in split_vrt for v in e.verts):
						e.smooth = False
						e.seam = True

			if not self.base_smooth:
				mesh_smooth(bm, verts, self.cuts_smooth, self.smooth_iter)

			bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

			bm.to_mesh(mesh)

			if self.cut_symm:
				bisect_symmetry(bm, obj)

			bm.to_mesh(mesh)

			bm_src.clear()
			bm_src.from_mesh(mesh)

			bpy.data.meshes.remove(mesh)

			if src_mesh.is_editmode:
				bmesh.update_edit_mesh(src_mesh)
			else:
				bm_src.to_mesh(src_mesh)
				bm_src.free()

			if temp_obj: remove_obj(temp_obj)

		if context.scene.rflow_props.clear_select: clear_select(obj)

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		row.row(align=True).prop(self, "type", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Solver:")
		row.row(align=True).prop(self, "solver", expand=True)
		if not self.solver in ['RADIAL', 'SQUARE']:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Path:")
			row.row(align=True).prop(self, "path", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Notches:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "notch_count")
		split.row(align=True).prop(self, "notch_size")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Notch Seed:")
		row.row(align=True).prop(self, "notch_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size Mode:")
		row.row(align=True).prop(self, "size_mode", expand=True)
		if self.type == 'INSET':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Panel Amount:")
			split1 = row.split(factor=0.8, align=True)
			split1.row(align=True).prop(self, "panel_amount", text="")
			split2 = split1.split(factor=0.5, align=True)
			split2.prop(self, "invert_panel_amount", text="", icon="ARROW_LEFTRIGHT")
			split2.prop(self, "remove_panels", text="", icon="STICKY_UVS_DISABLE")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Panel Size:")
		split = row.split(factor=0.5, align=True)
		if self.size_mode == 'PERCENT':
			split.row(align=True).prop(self, "panel_min_perc", text="Min")
			split.row(align=True).prop(self, "panel_max_perc", text="Max")
		else:
			split.row(align=True).prop(self, "panel_min_num", text="Min")
			split.row(align=True).prop(self, "panel_max_num", text="Max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Panel Seed:")
		row.row(align=True).prop(self, "edge_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		row.row(align=True).prop(self, "cuts_base")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Smoothing:")
		split1 = row.split(factor=0.5, align=True)
		split1.row(align=True).prop(self, "cuts_smooth")
		split2 = split1.split(factor=0.58 if self.merge_pnl and not self.base_smooth else 0.8, align=True)
		split2.row(align=True).prop(self, "smooth_iter")
		if self.merge_pnl and not self.base_smooth:
			split3 = split2.split(factor=0.5, align=True)
			split3.prop(self, "area_smooth", text="", icon="AREA_SWAP")
			split3.prop(self, "base_smooth", text="", icon="MESH_UVSPHERE")
		else:
			split2.prop(self, "base_smooth", text="", icon="MESH_UVSPHERE")
		if self.type == 'INSET':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Margin:")
			if self.merge_pnl:
				split = row.split(factor=0.5, align=True)
				split.row(align=True).prop(self, "margin_indent")
				split.row(align=True).prop(self, "margin_outdent")
			else:
				row.row(align=True).prop(self, "margin", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Even Offset:")
			row.row(align=True).prop(self, "even_offset", expand=True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Thickness:")
			if self.uni_thickness:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "thickness", text="")
				split.prop(self, "uni_thickness", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "thickness_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "thickness_max")
				split2.prop(self, "uni_thickness", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Thickness Seed:")
				row.row(align=True).prop(self, "thickness_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Depth:")
			if self.uni_depth:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "depth", text="")
				split.prop(self, "uni_depth", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "depth_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "depth_max")
				split2.prop(self, "uni_depth", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Depth Seed:")
				row.row(align=True).prop(self, "depth_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cut Method:")
			row.row(align=True).prop(self, "cut_method", expand=True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cut Angle:")
			row.row(align=True).prop(self, "cut_threshold", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Bevel Offset:")
			if self.uni_bevel:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "bvl_offset_uni", text="")
				split.prop(self, "uni_bevel", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "bvl_offset_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "bvl_offset_max")
				split2.prop(self, "uni_bevel", text="", icon="UNLINKED")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Bvl Seg/Angle:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "bvl_seg")
			split.row(align=True).prop(self, "bvl_angle")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Bevel Seed:")
			row.row(align=True).prop(self, "bvl_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Clear Faces:")
			row.row(align=True).prop(self, "clear_faces", expand=True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Triangulate:")
			if self.size_mode == 'PERCENT':
				row.row(align=True).prop(self, "tri_perc", text="")
			else:
				row.row(align=True).prop(self, "tri_num", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Limit Smooth:")
			row.row(align=True).prop(self, "limit_smooth", expand=True)
			if self.limit_smooth == 'NONE':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Shading:")
				row.row(align=True).prop(self, "base_shading", expand=True)
			if self.limit_smooth == 'RANDOM':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Shading Seed:")
				row.row(align=True).prop(self, "shading_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Material Index:")
			row.row(align=True).prop(self, "mat_index", text="")
			col.separator(factor=0.5)
			flow = col.column_flow(columns=2, align=True)
			flow.prop(self, "use_mirror")
			if self.clear_faces != 'NONE' \
				and not self.use_merge:
				flow.prop(self, "floater_set")
			else:
				flow.prop(self, "merge_pnl")
			flow.prop(self, "only_msharp")
			flow.prop(self, "inset_vgroup")
			row = col.row().split(factor=0.5, align=True)
			row.prop(self, "use_clip")
			if self.use_clip:
				row.row(align=True).prop(self, "clip_axis", text="", expand=True)
				col.prop(self, "clip_dist")
			col.prop(self, "use_dissolve")
			if self.use_dissolve:
				col.prop(self, "angle")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Margin:")
			row.row(align=True).prop(self, "margin", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Width")
			row.row(align=True).prop(self, "pnl_width", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Offset:")
			row.row(align=True).prop(self, "pnl_offset", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cut Method:")
			row.row(align=True).prop(self, "cut_method", expand=True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cut Angle:")
			row.row(align=True).prop(self, "cut_threshold", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Triangulate:")
			if self.size_mode == 'PERCENT':
				row.row(align=True).prop(self, "tri_perc", text="")
			else:
				row.row(align=True).prop(self, "tri_num", text="")
			col.separator(factor=0.5)
			col.prop(self, "split_borders")
			col.prop(self, "margin_bounds")
			col.prop(self, "cut_symm")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		dim = obj.dimensions.copy()
		self.mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

		self.notch_seed = 1
		self.edge_seed = 1
		self.bvl_seed = 1
		self.thickness_seed = 1
		self.depth_seed = 1
		self.use_merge = True
		self.only_msharp = False

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face:
			init_props(self, event, ops='rpanels', force=has_face>=props.select_limit)
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_r_slice(Operator):
	'''Randomly slices faces recursively'''
	bl_idname = 'rand_slice.rflow'
	bl_label = 'Random Slice'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	solver : EnumProperty(
		name = 'Solver',
		items = (
			('RAND', 'Random','Cut from a random edge'),
			('SHORT', 'Shortest','Cut only from the shortest edge')),
		default = 'RAND'
		)
	direction : EnumProperty(
		name = "Direction",
		items = (
			('TANGENT', 'Tangent','Use face tangents from selected as direction'),
			('VIEW', 'View','Use view angle as direction')),
		default = 'TANGENT')
	origin : EnumProperty(
		name = 'Origin',
		items = (
			('EDGE', 'Edge','Longest edge from face is used for direction'),
			('XYZ', 'XYZ','Strict xyz values are used for direction')),
		default = 'EDGE'
		)
	mode : EnumProperty(
		name = 'Solver',
		items = (
			('MERGE', 'Merged','Resulting cuts are used on the source object'),
			('SPLIT', 'Separate','Resulting cuts are used on a new object')),
		default = 'MERGE'
		)
	cut_range : IntProperty(
		name        = "Cut Amount",
		description = "Number of random cuts or slices",
		default     = 100,
		min         = 0,
		soft_max    = 10000,
		step        = 1
		)
	cut_seed : IntProperty(
		name        = "Slice Seed",
		description = "Random seed for slicing selected faces",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	min_length : FloatProperty(
		name        = "Min Length",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 3
		)
	slide_min : FloatProperty(
		name        = "Min",
		description = "Minimum slide percentage",
		default     = 0.25,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	slide_max : FloatProperty(
		name        = "Max",
		description = "Maximum slide percentage",
		default     = 0.75,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	outer_margin : FloatProperty(
		name        = "Outer Margin",
		description = "Selection border margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	outer_margin_min : FloatProperty(
		name        = "Min",
		description = "Minimum face margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	outer_margin_max : FloatProperty(
		name        = "Max",
		description = "Maximum face margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	outer_margin_seed : IntProperty(
		name        = "Margin Seed",
		description = "Outer margin seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_outer_margin : BoolProperty(
		name        = "Uniform Outer Margin",
		description = "Use single property value for outer margin",
		default     = True
		)
	inner_margin : FloatProperty(
		name        = "Inner Margin",
		description = "Face margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	inner_margin_min : FloatProperty(
		name        = "Min",
		description = "Minimum face margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	inner_margin_max : FloatProperty(
		name        = "Max",
		description = "Maximum face margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	inner_margin_seed : IntProperty(
		name        = "Margin Seed",
		description = "Inner margin seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_inner_margin : BoolProperty(
		name        = "Uniform Inner Margin",
		description = "Use single property value for inner margin",
		default     = True
		)
	thickness : FloatProperty(
		name        = "Thickness",
		description = "Inset Thickness",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	thickness_min : FloatProperty(
		name        = "Min",
		description = "Minimum inset thickness",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	thickness_max : FloatProperty(
		name        = "Max",
		description = "Maximum inset thickness",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	thickness_seed : IntProperty(
		name        = "Thickness Seed",
		description = "Inset thickness randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_thickness : BoolProperty(
		name        = "Uniform Thickness",
		description = "Use single property value for inset thickness",
		default     = True
		)
	depth : FloatProperty(
		name        = "Depth",
		description = "Inset depth",
		default     = 0.1,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	depth_min : FloatProperty(
		name        = "Min",
		description = "Minimum depth",
		default     = 0.001,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	depth_max : FloatProperty(
		name        = "Max",
		description = "Maximum depth",
		default     = 0.1,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	depth_seed : IntProperty(
		name        = "Depth Seed",
		description = "Random seed for inset depth of faces",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_depth : BoolProperty(
		name        = "Uniform Depth",
		description = "Use single property value for inset depth",
		default     = False
		)
	scale : FloatProperty(
		name        = "Scale",
		description = "Face inset scale",
		default     = 1.0,
		min         = 0,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	scale_min : FloatProperty(
		name        = "Min",
		description = "Minimum scale",
		default     = 1.0,
		min         = 0,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	scale_max : FloatProperty(
		name        = "Max",
		description = "Minimum scale",
		default     = 1.0,
		min         = 0,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	scale_seed : IntProperty(
		name        = "Scale Seed",
		description = "Extrusion scale seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_scale : BoolProperty(
		name        = "Uniform Scale",
		description = "Use single property value for inset scale",
		default     = False
		)
	proc_perc : FloatProperty(
		name        = "Perc",
		description = "Percentage to determine if screw appears at this point",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 100,
		subtype     = "PERCENTAGE"
		)
	proc_seed : IntProperty(
		name        = "Seed",
		description = "Randomize seed for birth of screws",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	wire_thickness : FloatProperty(
		name        = "Thickness",
		description = "Wireframe modifier thickness",
		default     = 0.01,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	wire_offset : FloatProperty(
		name        = "Offset",
		description = "Wireframe modifier offset",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	use_bounds : BoolProperty(
		name        = "Use Boundary",
		description = "Wireframe modifier use boundary",
		default     = True
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	use_inset : BoolProperty(
		name        = "Inset",
		description = "Use inset on newly drawn faces",
		default     = False
		)
	use_wire : BoolProperty(
		name        = "Wireframe",
		description = "Use wireframe modifier",
		default     = False
		)
	floater_set : BoolProperty(
		name        = "Floater Mesh",
		description = "Set cycles render visibility to make it look like resulting mesh is part of source mesh",
		default     = False
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = False
		)
	clip_dist : FloatProperty(
		name        = "Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	clip_axis : BoolVectorProperty(
		name        = "Clip Axis",
		description = "Clip axis toggles",
		default     = (True, True, True),
		size		= 3,
		subtype		= "XYZ"
		)
	use_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def set_outer_margin(self, bm, listf=[], clear_margin=False):

		margin_faces = []

		if sum([self.outer_margin_min, self.outer_margin_max]) \
			and listf:
				i = 0
				while listf:
					linked_faces = []
					traversal_stack = [listf.pop()]

					while len(traversal_stack) > 0:
						f_curr = traversal_stack.pop()
						linked_faces.append(f_curr)

						for e in f_curr.edges:
							if e.is_contiguous and e.select:
								for f_linked in e.link_faces:
									if f_linked not in linked_faces and f_linked.select:
										traversal_stack.append(f_linked)
										if f_linked in listf: listf.remove(f_linked)

					i += 1

					seed(self.outer_margin_seed + i)
					outer_margin = self.outer_margin if self.uni_outer_margin \
						else uniform(self.outer_margin_min, self.outer_margin_max)
					ret_margin = bmesh.ops.inset_region(bm, faces=linked_faces, use_boundary=True, \
						use_even_offset=True, thickness=outer_margin)['faces']
					if clear_margin: bmesh.ops.delete(bm, geom=ret_margin, context='FACES')

					margin_faces.extend(linked_faces)

		return margin_faces

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		rv3d = context.region_data
		vrot = rv3d.view_rotation

		slice_faces = []

		if self.mode == 'MERGE' \
			and obj.data.is_editmode:
			mesh = obj.data
			bm = bmesh.from_edit_mesh(mesh)

			slice_faces = [f for f in bm.faces if f.select]

			if self.uni_outer_margin:
				bmesh.ops.inset_region(bm, faces=slice_faces, use_boundary=True, \
					use_even_offset=True, thickness=self.outer_margin)
			else:
				margin_faces = self.set_outer_margin(bm, slice_faces)
				if margin_faces: slice_faces = margin_faces
		else:
			mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

			bm = bmesh.new()
			temp_mesh = bpy.data.meshes.new(".temp")
			bm.from_mesh(mesh)

			bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
			bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

			if self.uni_outer_margin:
				outer_margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
					use_even_offset=True, thickness=self.outer_margin)['faces']
				bmesh.ops.delete(bm, geom=outer_margin, context='FACES')
			else:
				self.set_outer_margin(bm, bm.faces[:], clear_margin=True)

			slice_faces = bm.faces[:]

		if self.use_dissolve:
			ret = bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, use_dissolve_boundaries=False, \
				verts=[v for v in bm.verts if v.select and not any(e for e in v.link_edges if not e.select)], \
				edges=[e for e in bm.edges if e.select and not any(f for f in e.link_faces if not f.select)], \
				delimit={'NORMAL'})['region']
			slice_faces += ret

		orig_faces = bm.faces[:]

		cut_geo = []
		seed(self.cut_seed)
		shuffle(slice_faces)

		for i in range(self.cut_range):
			if slice_faces:
				f = slice_faces.pop()
			else: break

			if f in bm.faces:
				edg = None
				if self.solver == 'RAND':
					edges = [e for e in f.edges if e.calc_length() > self.min_length]
					if edges: edg = [choice(edges)]
				else:
					edg = sorted([e for e in f.edges], key=lambda o: o.calc_length())

				if edg:
					split = bmesh.ops.bisect_edges(bm, edges=[edg[-1]], cuts=1, \
						edge_percents={ e: uniform(self.slide_min, self.slide_max) for e in edg })['geom_split']

					co = split[0].co
					v1 = split[1].verts[0].co
					v2 = split[1].verts[1].co
					ini_geo = [f] + f.verts[:] + f.edges[:]

					if self.direction == 'TANGENT':
						if self.origin == 'EDGE':
							tangent = v1 - v2
							ret = bmesh.ops.bisect_plane(bm, geom=ini_geo, dist=0, plane_co=co, plane_no=tangent)
							cut_geo.extend(ret['geom'])
						else:
							axis = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]
							for n in axis:
								ret = bmesh.ops.bisect_plane(bm, geom=ini_geo, dist=0.0001, plane_co=co, plane_no=n)
								cut_geo.extend(ret['geom'])
					else:
						new_geo = ini_geo
						tangent = [vrot @ Vector((0,-1,0)), vrot @ Vector((-1,0,0))]
						for t in tangent:
							ret = bmesh.ops.bisect_plane(bm, geom=undupe(new_geo), dist=0.0001, plane_co=co, plane_no=t)
							new_geo.extend(ret['geom'])

						cut_geo.extend(undupe(new_geo))

			if not slice_faces:
				slice_faces = undupe([f for f in cut_geo if isinstance(f, bmesh.types.BMFace)])
				cut_geo.clear()

		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		def inset_face(f, i):

			remf = None

			seed(self.proc_seed + i)
			if random() < self.proc_perc/100:
				seed(self.inner_margin_seed + i)
				inner_margin = self.inner_margin if self.uni_inner_margin \
					else uniform(self.inner_margin_min, self.inner_margin_max)
				ret_inner = bmesh.ops.inset_region(bm, faces=[f], use_boundary=True, \
					use_even_offset=True, thickness=inner_margin)['faces']

				if not obj.data.is_editmode: bmesh.ops.delete(bm, geom=ret_inner, context='FACES')

				seed(self.thickness_seed + i)
				thickness = self.thickness if self.uni_thickness else uniform(self.thickness_min, self.thickness_max)
				seed(self.depth_seed + i)
				depth = self.depth if self.uni_depth else uniform(self.depth_min, self.depth_max)
				bmesh.ops.inset_region(bm, faces=[f], use_boundary=True, \
					use_even_offset=True, thickness=thickness * self.mdv, depth=depth * self.mdv)

				seed(self.scale_seed + i)
				sca = self.scale if self.uni_scale else uniform(self.scale_min, self.scale_max)
				bmesh.ops.scale(bm, vec=Vector((sca,sca,sca)), \
					space=Matrix.Translation(f.calc_center_median()).inverted(), verts=f.verts)
			else:
				remf = f

			return remf

		if self.mode == 'MERGE' \
			and obj.data.is_editmode:
			if self.use_inset:
				for i, f in enumerate(bm.faces[:]):
					if not f in orig_faces:	inset_face(f, i)

			if self.use_clip: clip_center(bm, obj, self.clip_dist, self.clip_axis)

			bmesh.update_edit_mesh(mesh)
			bpy.ops.mesh.select_all(action='DESELECT')
		else:
			bmesh.ops.split_edges(bm, edges=bm.edges)
			bmesh.ops.dissolve_limit(bm, angle_limit=radians(5), \
				use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

			add_wire = True
			if not self.use_wire:
				listf = []
				for i, f in enumerate(bm.faces[:]):
					remf = inset_face(f, i)
					if remf: listf.append(remf)

				bmesh.ops.delete(bm, geom=listf, context='FACES')
			else:
				bmesh.ops.wireframe(bm, faces=bm.faces, thickness=self.wire_thickness * self.mdv, \
					offset=self.wire_offset * self.mdv, use_replace=True, use_boundary=self.use_bounds)
				add_wire = False

			if self.use_clip: clip_center(bm, obj, self.clip_dist, self.clip_axis)

			bm.to_mesh(temp_mesh)

			new_obj = bpy.data.objects.new(filter_name(obj, "_RSlice"), temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc

			assign_mat(self, obj, new_obj, self.mat_index)

			if 'sharp_edge' in obj.data.attributes:
				new_obj.data.set_sharp_from_angle(angle=radians(30))

			if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			if self.use_wire and \
				self.floater_set: set_floater_vis(new_obj)

			set_parent(obj, new_obj)

			refresh_vcolor(new_obj)

		if (not obj.data.is_editmode or self.mode == 'SPLIT') and context.scene.rflow_props.clear_select: clear_select(obj)

		return {'FINISHED'}

	def draw(self, context):

		obj = context.active_object
		mesh = obj.data

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Solver:")
		row.row(align=True).prop(self, "solver", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Direction:")
		row.row(align=True).prop(self, "direction", expand=True)
		if self.direction == 'TANGENT':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Origin:")
			row.row(align=True).prop(self, "origin", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Amount:")
		row.row(align=True).prop(self, "cut_range", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Seed:")
		row.row(align=True).prop(self, "cut_seed", text="")
		if self.solver == 'RAND':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Min Length:")
			row.row(align=True).prop(self, "min_length", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Slide:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "slide_min")
		split.row(align=True).prop(self, "slide_max")
		if mesh.is_editmode:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mode:")
			row.row(align=True).prop(self, "mode", expand=True)
		if self.mode == 'SPLIT' \
			or not mesh.is_editmode:
			if not self.use_wire:
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Outer Margin:")
				if self.uni_outer_margin:
					split = row.split(factor=0.9, align=True)
					split.row(align=True).prop(self, "outer_margin", text="")
					split.prop(self, "uni_outer_margin", text="", icon="LINKED")
				else:
					split1 = row.split(factor=0.5, align=True)
					split1.row(align=True).prop(self, "outer_margin_min")
					split2 = split1.split(factor=0.8, align=True)
					split2.row(align=True).prop(self, "outer_margin_max")
					split2.prop(self, "uni_outer_margin", text="", icon="UNLINKED")
					row = col.row().split(factor=0.27, align=True)
					row.label(text="Margin Seed:")
					row.row(align=True).prop(self, "outer_margin_seed", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Inner Margin:")
				if self.uni_inner_margin:
					split = row.split(factor=0.9, align=True)
					split.row(align=True).prop(self, "inner_margin", text="")
					split.prop(self, "uni_inner_margin", text="", icon="LINKED")
				else:
					split1 = row.split(factor=0.5, align=True)
					split1.row(align=True).prop(self, "inner_margin_min")
					split2 = split1.split(factor=0.8, align=True)
					split2.row(align=True).prop(self, "inner_margin_max")
					split2.prop(self, "uni_inner_margin", text="", icon="UNLINKED")
					row = col.row().split(factor=0.27, align=True)
					row.label(text="Margin Seed:")
					row.row(align=True).prop(self, "inner_margin_seed", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Thickness:")
				if self.uni_thickness:
					split = row.split(factor=0.9, align=True)
					split.row(align=True).prop(self, "thickness", text="")
					split.prop(self, "uni_thickness", text="", icon="LINKED")
				else:
					split1 = row.split(factor=0.5, align=True)
					split1.row(align=True).prop(self, "thickness_min")
					split2 = split1.split(factor=0.8, align=True)
					split2.row(align=True).prop(self, "thickness_max")
					split2.prop(self, "uni_thickness", text="", icon="UNLINKED")
					row = col.row().split(factor=0.27, align=True)
					row.label(text="Thickness Seed:")
					row.row(align=True).prop(self, "thickness_seed", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Depth:")
				if self.uni_depth:
					split = row.split(factor=0.9, align=True)
					split.row(align=True).prop(self, "depth", text="")
					split.prop(self, "uni_depth", text="", icon="LINKED")
				else:
					split1 = row.split(factor=0.5, align=True)
					split1.row(align=True).prop(self, "depth_min")
					split2 = split1.split(factor=0.8, align=True)
					split2.row(align=True).prop(self, "depth_max")
					split2.prop(self, "uni_depth", text="", icon="UNLINKED")
					row = col.row().split(factor=0.27, align=True)
					row.label(text="Depth Seed:")
					row.row(align=True).prop(self, "depth_seed", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Scale:")
				if self.uni_scale:
					split = row.split(factor=0.9, align=True)
					split.row(align=True).prop(self, "scale", text="")
					split.prop(self, "uni_scale", text="", icon="LINKED")
				else:
					split1 = row.split(factor=0.5, align=True)
					split1.row(align=True).prop(self, "scale_min")
					split2 = split1.split(factor=0.8, align=True)
					split2.row(align=True).prop(self, "scale_max")
					split2.prop(self, "uni_scale", text="", icon="UNLINKED")
					row = col.row().split(factor=0.27, align=True)
					row.label(text="Scale Seed:")
					row.row(align=True).prop(self, "scale_seed", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Proc:")
				split = row.split(factor=0.5, align=True)
				split.row(align=True).prop(self, "proc_perc")
				split.row(align=True).prop(self, "proc_seed")
			else:
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Thickness:")
				row.row(align=True).prop(self, "wire_thickness", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Offset:")
				row.row(align=True).prop(self, "wire_offset", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Material Index:")
			row.row(align=True).prop(self, "mat_index", text="")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Outer Margin:")
			if self.uni_outer_margin:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "outer_margin", text="")
				split.prop(self, "uni_outer_margin", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "outer_margin_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "outer_margin_max")
				split2.prop(self, "uni_outer_margin", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Margin Seed:")
				row.row(align=True).prop(self, "outer_margin_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Inner Margin:")
			if self.uni_inner_margin:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "inner_margin", text="")
				split.prop(self, "uni_inner_margin", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "inner_margin_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "inner_margin_max")
				split2.prop(self, "uni_inner_margin", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Inner Margin Seed:")
				row.row(align=True).prop(self, "inner_margin_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Thickness:")
			if self.uni_thickness:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "thickness", text="")
				split.prop(self, "uni_thickness", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "thickness_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "thickness_max")
				split2.prop(self, "uni_thickness", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Thickness Seed:")
				row.row(align=True).prop(self, "thickness_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Depth:")
			if self.uni_depth:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "depth", text="")
				split.prop(self, "uni_depth", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "depth_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "depth_max")
				split2.prop(self, "uni_depth", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Depth Seed:")
				row.row(align=True).prop(self, "depth_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale:")
			if self.uni_scale:
				split = row.split(factor=0.9, align=True)
				split.row(align=True).prop(self, "scale", text="")
				split.prop(self, "uni_scale", text="", icon="LINKED")
			else:
				split1 = row.split(factor=0.5, align=True)
				split1.row(align=True).prop(self, "scale_min")
				split2 = split1.split(factor=0.8, align=True)
				split2.row(align=True).prop(self, "scale_max")
				split2.prop(self, "uni_scale", text="", icon="UNLINKED")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Scale Seed:")
				row.row(align=True).prop(self, "scale_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Proc:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "proc_perc")
			split.row(align=True).prop(self, "proc_seed")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		if not mesh.is_editmode:
			flow.prop(self, "use_mirror")
			if self.use_wire:
				flow.prop(self, "floater_set")
		if self.mode == 'SPLIT' \
			or not mesh.is_editmode:
			flow = col.column_flow(columns=2, align=True)
			flow.prop(self, "use_wire")
			if self.use_wire:
				flow.prop(self, "use_bounds")
			if self.use_wire \
				and mesh.is_editmode:
				flow.prop(self, "floater_set")
		if self.mode == 'MERGE' \
			and mesh.is_editmode: col.prop(self, "use_inset")
		if self.mirror:
			row = col.row().split(factor=0.5, align=True)
			row.prop(self, "use_clip")
			if self.use_clip:
				row.row(align=True).prop(self, "clip_axis", text="", expand=True)
				col.prop(self, "clip_dist")
		col.prop(self, "use_dissolve")
		if self.use_dissolve:
			col.prop(self, "angle")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		dim = obj.dimensions.copy()
		self.mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

		self.cut_range = 100 if self.cut_range > 100 else self.cut_range
		self.cut_seed = 1
		self.slide_seed = 1
		self.depth_seed = 1
		self.scale_seed = 1

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		self.mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

		if has_face:
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_r_axis_extrude(Operator):
	'''Extrude randomly in the xyz axis'''
	bl_idname = 'rand_axis_extr.rflow'
	bl_label = 'Random Axis Extrude'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for selected faces",
		default     = 0,
		min         = 0,
		soft_max    = 12,
		)
	loops_iter : IntProperty(
		name        = "Iteration",
		description = "Number of times to repeat the operation",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		)
	extr_offset : IntVectorProperty(
		name        = "Source Extrude",
		description = "Number of loops to extrude from original selection",
		default     = (5,5,5),
		size        = 3,
		min         = 0,
		soft_max    = 100,
		step        = 1,
		subtype		= "XYZ"
		)
	loop_offset : FloatVectorProperty(
		name        = "Loop Offset",
		description = "Minimum threshold to push extrusion for the next loop",
		default     = (0.5,0.5,0.5),
		size        = 3,
		min         = 0.0,
		max    		= 1.0,
		step        = 0.1,
		precision   = 3,
		subtype		= "XYZ"
		)
	axis_order1 : EnumProperty(
		name = 'Axis Order',
		description = "Order on which axis to loop first",
		items = (
			('X', 'X',''),
			('Y', 'Y',''),
			('Z', 'Z','')),
		default = 'X'
		)
	axis_order2 : EnumProperty(
		name = 'Axis Order',
		description = "Order on which axis to loop first",
		items = (
			('X', 'X',''),
			('Y', 'Y',''),
			('Z', 'Z','')),
		default = 'Y'
		)
	axis_order3 : EnumProperty(
		name = 'Axis Order',
		description = "Order on which axis to loop first",
		items = (
			('X', 'X',''),
			('Y', 'Y',''),
			('Z', 'Z','')),
		default = 'Z'
		)
	axis_loop : IntVectorProperty(
		name        = "Axis Loop",
		description = "Axis loop extrusion count",
		default     = (5,5,5),
		size        = 3,
		min         = 0,
		soft_max    = 100,
		step        = 1,
		subtype		= "XYZ"
		)
	loop_seed : IntVectorProperty(
		name        = "Loop Seed",
		description = "Axis loop seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	globl_seed : IntProperty(
		name        = "Global Seed",
		description = "Global seed for axis extrusions",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	min_length : FloatVectorProperty(
		name        = "Min Length",
		description = "Maximum size of faces by longest edge",
		default     = (1.0,1.0,1.0),
		size        = 3,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.5,
		precision   = 3,
		subtype		= "XYZ"
		)
	depth_max : FloatVectorProperty(
		name        = "Depth Max",
		description = "Maximum extrusion depth",
		default     = (0.5,0.5,0.5),
		size        = 3,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.5,
		precision   = 3,
		subtype		= "XYZ"
		)
	depth_min : FloatVectorProperty(
		name        = "Depth Min",
		description = "Minimum extrusion depth",
		default     = (0.1,0.1,0.1),
		size        = 3,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.5,
		precision   = 3,
		subtype		= "XYZ"
		)
	depth_seed : IntVectorProperty(
		name        = "Depth Seed",
		description = "Extrusion depth seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	inner_cut : IntVectorProperty(
		name        = "Inner Cut",
		description = "Number subdivisions on extrusion edges",
		default     = (2,2,2),
		size        = 3,
		min         = 0,
		soft_max    = 12,
		step        = 1,
		subtype		= "XYZ"
		)
	scale_max : FloatVectorProperty(
		name        = "Scale Max",
		description = "Minimum extrusion scale",
		default     = (1.0,1.0,1.0),
		size        = 3,
		min			= 0.0,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3,
		subtype		= "XYZ"
		)
	scale_min : FloatVectorProperty(
		name        = "Scale Min",
		description = "Minimum extrusion scale",
		default     = (1.0,1.0,1.0),
		size        = 3,
		min			= 0.0,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3,
		subtype		= "XYZ"
		)
	scale_seed : IntVectorProperty(
		name        = "Scale Seed",
		description = "Extrusion scale seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	threshold : FloatVectorProperty(
		name        = "Min",
		description = "Normal limit on faces in order to be extruded",
		default     = (0.5,0.5,0.5),
		size        = 3,
		min         = 0.0,
		soft_min    = 0.0001,
		soft_max    = 1.0,
		step        = 0.5,
		precision   = 3,
		subtype		= "XYZ"
		)
	scale_clipping : FloatProperty(
		name        = "Scale Clipping",
		description = "Clipping distance when scaling faces in the symmetry lines",
		default     = 0.0001,
		min			= 0.0,
		soft_min    = 0.0001,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	single_obj : BoolProperty(
		name        = "Single Object",
		description = "Make the extrusions part of the source mesh",
		default     = False
		)
	hit_self : BoolProperty(
		name        = "Hit Source",
		description = "Allows extrusion in faces that points to source mesh",
		default     = False
		)
	cut_symm : BoolProperty(
		name        = "Bisect Symmetry",
		description = "Bisect symmetry line if has mirror modifier",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def hit_source(self, context, obj, loc, norm):

		hit = False
		if not self.hit_self:
			depsgraph = context.evaluated_depsgraph_get()
			_, _, _, _, hit_obj, _ = context.scene.ray_cast(depsgraph, loc + norm, norm)
			if hit_obj == obj: hit = True

		return hit

	def remove_axis_faces(self, bm, obj):

		mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
		thresh = 1e-4; center_faces = set()
		if mirror:
			for f in bm.faces:
				for i in range(3):
					if mirror.use_axis[i]:
						if -thresh <= f.calc_center_median()[i] <= thresh: center_faces.add(f)

		bmesh.ops.delete(bm, geom=list(center_faces), context='FACES')

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

		split = obj.mode != 'OBJECT' or not self.single_obj
		mirror = self.mirror

		bm = bmesh.new()
		if split: temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(mesh)

		axis_vec = [Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
		iteration = self.loops_iter
		loops = self.axis_loop
		offset1 = self.extr_offset
		offset2 = self.loop_offset
		thresh = self.threshold
		loop_seed = self.loop_seed
		globl_seed = self.globl_seed
		min_length = self.min_length
		depth_seed = self.depth_seed
		depth_min = self.depth_min
		depth_max = self.depth_max
		inner_cut = self.inner_cut
		scale_max = self.scale_max
		scale_min = self.scale_min
		scale_seed = self.scale_seed

		orig_faces = []
		init_faces = [f for f in bm.faces if f.select]

		if self.cuts_base > 0:
			f_edges = sum([list(f.edges) for f in init_faces], [])
			ret_subd1 = bmesh.ops.subdivide_edges(bm, edges=undupe(f_edges), cuts=self.cuts_base, use_grid_fill=True)
			init_faces = [f for f in ret_subd1['geom_inner'] if isinstance(f, bmesh.types.BMFace)]

		if split: orig_faces = bm.faces[:]

		newf = []
		axis_refr = [self.axis_order1, self.axis_order2, self.axis_order3]
		axis_base = ["X", "Y", "Z"]
		for x in range(iteration):
			for axis in axis_refr:
				n = axis_base.index(axis)
				vec = Vector((axis_vec[n]))
				for i in range(loops[n]):
					if i < loops[n]:
						if i >= offset1[n]:
							extf = undupe(newf)
						else: extf = undupe(init_faces + newf)

						faces = [f for f in extf if \
							((vec - f.normal).length < thresh[n] \
							or (vec + f.normal).length < thresh[n])\
							and not any(e for e in f.edges if e.calc_length() > min_length[n])]

						if faces:
							seed(loop_seed[n] + i + globl_seed)
							face = choice(faces)

							hit = self.hit_source(context, obj, face.calc_center_median(), face.normal)

							if not hit \
								and not any(v for v in face.verts if len(v.link_faces) > 4):
								if i < offset1[n]:
									if split and face in orig_faces: orig_faces.remove(face)

								seed(depth_seed[n] + i)
								ret_inset = bmesh.ops.inset_region(bm, faces=[face], use_boundary=True, use_even_offset=True, \
								depth=uniform(depth_min[n], depth_max[n]))['faces']

								center = face.calc_center_median()
								if mirror:
									dist = self.scale_clipping
									midp = set()
									for v in face.verts:
										near_zeros = 0
										for x in range(3):
											if mirror.use_axis[x]:
												if -dist <= v.co[x] <= dist:
													midp.add(tuple(v.co))
													near_zeros += 1
										if near_zeros > 1:
											center = v.co
											midp.clear()
											break

									if midp: center = sum((Vector(co) for co in midp), Vector()) / len(midp)

								seed(scale_seed[n] + i)
								sca = uniform(scale_min[n], scale_max[n])
								bmesh.ops.scale(bm, vec=Vector((sca,sca,sca)), \
									space=Matrix.Translation(center).inverted(), verts=face.verts)

								if inner_cut[n] > 0:
									inner_edges = set()
									for f in ret_inset:
										for e in f.edges:
											if all(f in ret_inset for f in e.link_faces): inner_edges.add(e)

									inner_faces = []
									ret_subd2 = bmesh.ops.subdivide_edges(bm, edges=list(inner_edges), cuts=inner_cut[n])
									for e in ret_subd2['geom_inner']:
										for f in e.link_faces: inner_faces.append(f)

									newf.extend(inner_faces + [face])
								else: newf.extend(ret_inset + [face])

		if split:
			bmesh.ops.delete(bm, geom=orig_faces, context='FACES')
			mesh = temp_mesh

		if self.use_mirror:
			if self.cut_symm: bisect_symmetry(bm, obj)

			self.remove_axis_faces(bm, obj)

		bm.to_mesh(mesh)
		bm.free()

		if split and \
			temp_mesh.polygons:
			new_obj = bpy.data.objects.new(filter_name(obj, "_RAExtr"), temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc

			assign_mat(self, obj, new_obj, self.mat_index)

			if 'sharp_edge' in obj.data.attributes:
				new_obj.data.set_sharp_from_angle(angle=radians(30))

			if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			set_parent(obj, new_obj)

			refresh_vcolor(new_obj)

		if context.scene.rflow_props.clear_select: clear_select(obj)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Base Cut:")
		row.row(align=True).prop(self, "cuts_base", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Iteration:")
		row.row(align=True).prop(self, "loops_iter", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Source Extrude:")
		row.row(align=True).prop(self, "extr_offset", text="")
		row = col.row().split(factor=0.28, align=True)
		row.label(text="Axis Order:")
		row.row(align=True).prop(self, "axis_order1", text="")
		row.row(align=True).prop(self, "axis_order2", text="")
		row.row(align=True).prop(self, "axis_order3", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Axis Loop:")
		row.row(align=True).prop(self, "axis_loop", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Loop Seed:")
		row.row(align=True).prop(self, "loop_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Global Seed:")
		row.row(align=True).prop(self, "globl_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Min Length:")
		row.row(align=True).prop(self, "min_length", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth Max:")
		row.row(align=True).prop(self, "depth_max", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth Min:")
		row.row(align=True).prop(self, "depth_min", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth Seed:")
		row.row(align=True).prop(self, "depth_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Threshold:")
		row.row(align=True).prop(self, "threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Inner Cut:")
		row.row(align=True).prop(self, "inner_cut", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scale Max:")
		row.row(align=True).prop(self, "scale_max", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scale Min:")
		row.row(align=True).prop(self, "scale_min", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scale Seed:")
		row.row(align=True).prop(self, "scale_seed", text="")
		if self.mirror:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale Clipping:")
			row.row(align=True).prop(self, "scale_clipping", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "hit_self")
		if self.use_mirror:
			flow.prop(self, "cut_symm")
			if context.active_object.mode == 'OBJECT': flow.prop(self, "single_obj")
		else:
			flow.label(text="")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		self.loop_seed = (1,1,1)
		self.depth_seed = (1,1,1)
		self.scale_seed = (1,1,1)
		self.globl_seed = 1
		self.mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face:
			init_props(self, event, ops='raxis', force=has_face>=props.select_limit)
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_r_cells(Operator):
	'''Mask randomly generated face islands'''
	bl_idname = 'rand_cells.rflow'
	bl_label = 'Random Cells'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	size_mode : EnumProperty(
		name = 'Size Mode',
		items = (
			('PERCENT', 'Percent',''),
			('NUMBER', 'Number','')),
		default = 'PERCENT'
		)
	pool_size_perc : FloatProperty(
		name        = "Pool Size",
		description = "Initial number of faces randomized",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 5,
		subtype     = "PERCENTAGE"
		)
	pool_size_num : IntProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		default     = 50,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	pool_seed : IntProperty(
		name        = "Pool Seed",
		description = "Randomize initial faces",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	island_size : IntProperty(
		name        = "Island Size",
		description = "Random growth factor for the initial faces",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	proc_size : FloatProperty(
		name        = "Proc Size",
		description = "Chance that a face island will grow",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 100,
		subtype     = "PERCENTAGE"
		)
	proc_seed : IntProperty(
		name        = "Proc Seed",
		description = "Randomize proc",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cut_method : EnumProperty(
		name = "Cut Method",
		description = "Determines how edges will be cut",
		items = (
			('SHARP', 'Sharp',''),
			('INDIV', 'Individual','')),
		default = 'SHARP'
		)
	cut_threshold : FloatProperty(
		name        = "Cut Angle",
		description = "Maximum angle threshold for edges to be cut",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	offset_mode : EnumProperty(
		name = 'Offset Mode',
		description = "Determines the method of offsetting vertices",
		items = (
			('CONST', 'Constant',''),
			('INDIV', 'Individual','')),
		default = 'CONST'
		)
	offset : FloatProperty(
		name        = "Offset",
		description = "Offset value for faces",
		default     = 0.001,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	offset_seed : IntProperty(
		name        = "Offset Seed",
		description = "Randomize offset",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	thickness : FloatProperty(
		name        = "Thickness",
		description = "Inset thickness value for faces",
		default     = 0.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	inner_margin : FloatProperty(
		name        = "Inner",
		description = "Individual face margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	outer_margin : FloatProperty(
		name        = "Outer Margin",
		description = "Margin from the face selection boundary",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	depth : FloatProperty(
		name        = "Depth",
		description = "Inset depth value for faces",
		default     = 0.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	depth_seed : IntProperty(
		name        = "Thick Seed",
		description = "Randomize thickness",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cuts_smooth : FloatProperty(
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		soft_max    = 24,
		step        = 1
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	tri_perc : FloatProperty(
		name        = "Triangulate",
		description = "Triangulate faces",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	tri_num : IntProperty(
		name        = "Triangulate",
		description = "Triangulate faces via number",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	floater_set : BoolProperty(
		name        = "Floater Mesh",
		description = "Set cycles render visibility to make it look like resulting mesh is part of source mesh",
		default     = False
		)
	clear_adj : BoolProperty(
		name        = "Clear Adjacent Faces",
		description = "Clear adjacent faces from the original face pool",
		default     = False
		)
	use_emit : BoolProperty(
		name        = "Use Emission",
		description = "Use emission shader on resulting cells",
		default     = False
		)
	track_normal : BoolProperty(
		name        = "Track Picked Normal",
		description = "Extrude to the direction of picked normal",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def add_material(self, obj):

		new_mat = bpy.data.materials.get("rcells_emit") or bpy.data.materials.new(name="rcells_emit")

		mat = obj.data.materials
		mat.clear()
		mat.append(new_mat)

		new_mat.use_nodes = True
		ntree = new_mat.node_tree

		for node in ntree.nodes:
			ntree.nodes.remove(node)

		node0 = ntree.nodes.new("ShaderNodeEmission")
		node0.inputs[0].default_value = (1, 0.5, 0.2, 1)
		node0.inputs[1].default_value = 5.0

		node1 = ntree.nodes.new("ShaderNodeOutputMaterial")
		ntree.links.new(node0.outputs[0], node1.inputs[0])

		space = 0
		for node in ntree.nodes:
			node.location.x = space
			space += node.width + 100
			node.location.y = 0

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		props = context.scene.rflow_props

		orig_mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

		use_sharp = False

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		if self.outer_margin:
			bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if e.calc_face_angle(None) \
				and e.calc_face_angle(None) >= radians(5)])
			margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
				use_even_offset=True, thickness=self.outer_margin)['faces']
			bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, cuts=self.cuts_base, \
			use_grid_fill=True, use_smooth_even=True)

		if self.tri_perc \
			or self.tri_num:
			tval = self.tri_perc if self.size_mode == 'PERCENT' else self.tri_num
			tris = get_tri_faces(bm.faces, tval, self.pool_seed, mode=self.size_mode)
			bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))

		bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if not e.smooth \
			or (e.calc_face_angle(None) and e.calc_face_angle(None) > radians(30))])

		listf = bm.faces[:]
		totlf = len(listf)

		if self.size_mode == 'PERCENT':
			pool_size = int(len(listf) * (self.pool_size_perc/100))
		else:
			pool_size = self.pool_size_num if not self.pool_size_num > totlf \
				else totlf

		init_faces = []
		adj_faces = []

		seed(self.pool_seed)

		for i in range(pool_size):
			if not listf: break
			if len(listf) == 1:
				f = listf.pop(0)
			else:
				f = listf.pop(randint(0, len(listf) - 1))

			if self.clear_adj:
				if not f in adj_faces: init_faces.append(f)
				adj_faces.extend(sum([v.link_faces[:] for v in f.verts], []))
			else:
				init_faces.append(f)

		plus_faces = init_faces.copy()

		for i in range(self.island_size):
			list_copy = undupe(plus_faces); plus_faces.clear()
			for n, f in enumerate(list_copy):
				seed(self.proc_seed + i + n)
				if random() < self.proc_size / 100:
					e = choice(f.edges[:])
					plus_faces.append(choice(e.link_faces[:]))
			init_faces.extend(plus_faces)

		remf = list(set(bm.faces).difference(set(init_faces)))
		bmesh.ops.delete(bm, geom=remf, context='FACES')

		if self.inner_margin:
			margin_faces = bmesh.ops.inset_individual(bm, faces=bm.faces, \
				use_even_offset=True, thickness=self.inner_margin)['faces']
			bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

		if self.cut_method == 'INDIV':
			bmesh.ops.split_edges(bm, edges=bm.edges)

		def offset_verts(verts, offset):

			link_faces = []
			for v in verts:
				v.co += v.normal * (v.calc_shell_factor() * offset)
				link_faces.extend(v.link_faces)

			return link_faces

		if self.offset_mode == 'INDIV' or self.cut_method == 'INDIV':
			if self.offset_mode == 'CONST':
				seed(self.offset_seed)
				offset = uniform(0, self.offset)

			isles = [[bm.verts[i] for i in n] for n in get_islands(None, bm)] \
				if self.cut_method == 'SHARP' else [f.verts[:] for f in bm.faces]

			for i, verts in enumerate(isles):
				if self.track_normal:
					_, orig_rot, _ = obj.matrix_world.decompose()
					bmesh.ops.rotate(
						bm,
						verts   = verts,
						cent    = sum([v.co for v in verts], Vector()) / len(verts),
						matrix  = orig_rot.to_matrix().inverted() @ \
							guided_rot(obj, track="Z", normal=props.normal_guide) @ \
							guided_rot(obj, track="Z", normal=sum([v.normal for v in verts], Vector()) / len(verts)).inverted()
						)

				if self.offset_mode == 'INDIV':
					seed(self.offset_seed + i)
					offset = uniform(0, self.offset)

				link_faces = offset_verts(verts, offset)

				seed(self.depth_seed + i)
				depth = uniform(0, self.depth)
				bmesh.ops.inset_region(bm, faces=undupe(link_faces), use_boundary=True, \
					use_even_offset=True, thickness=self.thickness, depth=depth)
		else:
			offset_verts(bm.verts, self.offset)
			bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
				use_even_offset=True, thickness=self.thickness, depth=self.depth)

		if self.tri_perc or self.tri_num: bmesh.ops.join_triangles(bm, faces=bm.faces, \
			angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		bm.to_mesh(temp_mesh)
		bm.free()

		new_obj = bpy.data.objects.new(filter_name(obj, "_RCells"), temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc

		if self.use_emit:
			self.add_material(new_obj)
		else:
			assign_mat(self, obj, new_obj, self.mat_index)

		if 'sharp_edge' in obj.data.attributes:
			new_obj.data.set_sharp_from_angle(angle=radians(30))

		if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
		if self.floater_set: set_floater_vis(new_obj)

		set_parent(obj, new_obj)

		refresh_vcolor(new_obj)

		if context.scene.rflow_props.clear_select: clear_select(obj)

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size Mode:")
		row.row(align=True).prop(self, "size_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Pool Size:")
		if self.size_mode == 'PERCENT':
			row.row(align=True).prop(self, "pool_size_perc", text="")
		else:
			row.row(align=True).prop(self, "pool_size_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Pool Seed:")
		row.row(align=True).prop(self, "pool_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Island Size:")
		row.row(align=True).prop(self, "island_size", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Proc Size:")
		row.row(align=True).prop(self, "proc_size", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Proc Seed:")
		row.row(align=True).prop(self, "proc_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Inner Margin:")
		row.row(align=True).prop(self, "inner_margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Outer Margin:")
		row.row(align=True).prop(self, "outer_margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Thickness:")
		row.row(align=True).prop(self, "thickness", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Method:")
		row.row(align=True).prop(self, "cut_method", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Angle:")
		row.row(align=True).prop(self, "cut_threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth:")
		row.row(align=True).prop(self, "depth", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth Seed:")
		row.row(align=True).prop(self, "depth_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset Mode:")
		row.row(align=True).prop(self, "offset_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		row.row(align=True).prop(self, "offset", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset Seed:")
		row.row(align=True).prop(self, "offset_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Triangulate:")
		if self.size_mode == 'PERCENT':
			row.row(align=True).prop(self, "tri_perc", text="")
		else:
			row.row(align=True).prop(self, "tri_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "floater_set")
		flow.prop(self, "clear_adj")
		flow.prop(self, "use_emit")
		if self.offset_mode == 'INDIV' \
			or self.cut_method == 'INDIV':
			col.prop(self, "track_normal")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		self.pool_seed = 0
		self.offset_seed = 0
		self.depth_seed = 0

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face:
			init_props(self, event, ops='rcells', force=has_face>=props.select_limit)
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_r_scatter(Operator):
	'''Create randomized scatter details'''
	bl_idname = 'rand_scatter.rflow'
	bl_label = 'Random Scatter'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	scatter_type : EnumProperty(
		name = 'Type',
		description = "Scatter type",
		items = (
			('CUBE', 'Cube',''),
			('MESH', 'Mesh',''),
			('COLLECTION', 'Collection','')),
		default = 'CUBE'
		)
	mesh_name : StringProperty(
		name        = "Mesh",
		description = "Mesh object for scatter"
		)
	meshes : CollectionProperty(type=PropertyGroup)
	coll_name : StringProperty(
		name        = "Collections",
		description = "Collection objects for scatter"
		)
	collections : CollectionProperty(type=PropertyGroup)
	coll_seed : IntProperty(
		name        = "Object Seed",
		description = "Randomize seed for collection objects",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	scatter_seed : IntProperty(
		name        = "Scatter Seed",
		description = "Randomize scatter points",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	scatter_points : IntProperty(
		name        = "Scatter Points",
		description = "Number of scatter points",
		default     = 10,
		min         = 1,
		soft_max    = 1000,
		step        = 1
		)
	sca_mode : EnumProperty(
		name = 'Scale Mode',
		items = (
			('AXIS', 'Axis','Use individual xyz axis for scaling'),
			('UNIFORM', 'Uniform','Use uniform scaling')),
		default = 'AXIS'
		)
	uni_size : FloatProperty(
		name        = "Size",
		description = "Uniform scatter size",
		default     = 1.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	size_min : FloatProperty(
		name        = "Min",
		description = "Minimum scatter size",
		default     = 0.1,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	size_max : FloatProperty(
		name        = "Max",
		description = "Maximum scatter size",
		default     = 1.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	size_seed : IntProperty(
		name        = "Size Seed",
		description = "Randomize size of scatter object",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	scale_max : FloatVectorProperty(
		name        = "Scale Max",
		description = "Randomized maximum scatter scale",
		default     = (1.0,1.0,1.0),
		size        = 3,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 1.0,
		subtype		= "XYZ"
		)
	scale_min : FloatVectorProperty(
		name        = "Scale Min",
		description = "Randomized minimum scatter scale",
		default     = (0.1,0.1,0.1),
		size        = 3,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 1.0,
		subtype		= "XYZ"
		)
	scale_seed : IntVectorProperty(
		name        = "Scale Seed",
		description = "Scatter object scaling seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	rot_mode : EnumProperty(
		name = 'Rotation Mode',
		items = (
			('FREE', 'Free','Rotation is randomized using min/max values'),
			('STRICT', 'Strict','Rotation is randomized using quotient tuple of given angle')),
		default = 'FREE'
		)
	rot_axis : FloatVectorProperty(
		name        = "Rotation",
		description = "Rotate axis",
		default     = (0,0,0),
		size        = 3,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "EULER"
		)
	rot_seed : IntVectorProperty(
		name        = "Rotation Seed",
		description = "Scatter object rotation seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	explode_min : FloatProperty(
		name        = "Min",
		description = "Minimum explode offset",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	explode_max : FloatProperty(
		name        = "Max",
		description = "Maximum explode offset",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	explode_seed : IntProperty(
		name        = "Explode Seed",
		description = "Randomize explode offset of scatter object",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cluster : FloatProperty(
		name        = "Cluster",
		description = "Cluster offset relative to tri center",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Margin from boundary edges",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	offset : FloatProperty(
		name        = "Offset",
		description = "Offset source mesh by this amount to produce overlap",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	single_scatter : BoolProperty(
		name        = "Single Object",
		description = "Generate scatter objects as single mesh",
		default     = True
		)
	follow_normal : BoolProperty(
		name        = "Follow Normal",
		description = "Rotate scatter objects using face normals",
		default     = True
		)
	track_normal : BoolProperty(
		name        = "Track Picked Normal",
		description = "Extrude to the direction of picked normal",
		default     = False
		)
	no_overlap : BoolProperty(
		name        = "No Overlap",
		description = "Avoid overlaps in scatter objects",
		default     = False
		)
	use_convex_hull : BoolProperty(
		name        = "Use Convex Hull",
		description = "Use convex hull when detecting overlaps instead of mesh",
		default     = True
		)
	use_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def point_on_triangle(self, face):
		'''https://blender.stackexchange.com/a/221597'''

		a, b, c = map(lambda v: v.co, face.verts)
		a2b = b - a
		a2c = c - a
		height = triangular(low=0.0, high=1.0, mode=0.0)

		return a + a2c*height + a2b*(1-height) * random(), face.normal, face.calc_center_median()

	def get_nonintersect(self, bm1, bm2):

		bvh1 = BVHTree.FromBMesh(bm1)
		bvh2 = BVHTree.FromBMesh(bm2)

		return bool(bvh1.overlap(bvh2))

	def add_scatter(self, obj, data):

		if not data.polygons: return

		new_obj = bpy.data.objects.new(filter_name(obj, "_RScatter"), data)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc

		assign_mat(self, obj, new_obj, self.mat_index)

		if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

		set_parent(obj, new_obj)

		refresh_vcolor(new_obj)

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		props = context.scene.rflow_props

		orig_mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')

		if self.use_dissolve: bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
			use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

		if self.margin:
			bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if e.calc_face_angle(None) \
				and e.calc_face_angle(None) >= radians(5)])
			margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin)['faces']
			bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

		if self.offset:
			for v in bm.verts:
				v.co -= v.normal * (v.calc_shell_factor() * self.offset)

		seed(self.scatter_seed)
		triangles = bmesh.ops.triangulate(bm, faces=bm.faces)['faces']
		# surfaces = list(map(lambda t: t.calc_area(), triangles))
		surfaces = [t.calc_area() for t in triangles]
		listp = choices(population=triangles, weights=surfaces, k=self.scatter_points)
		points = map(self.point_on_triangle, listp)

		cont = True
		scatter_obj = None
		scatter_type = self.scatter_type
		matlist = []
		single_obj = self.single_scatter

		if self.no_overlap:
			bm_hit = bmesh.new()
			scatter_hit = bpy.data.meshes.new(".scatter_hit")

		for i, p in enumerate(list(points)):
			bm_scatter = bmesh.new()
			scatter_data = bpy.data.meshes.new(".temp_scatter")

			loc = p[0]
			normal = p[1]
			center = p[2]

			dir1 = normal if self.follow_normal or (not self.follow_normal and self.track_normal) else Vector()

			if scatter_type == 'CUBE':
				seed(self.size_seed + i)
				scatter_verts = bmesh.ops.create_cube(bm_scatter, size=uniform(self.size_min, self.size_max) \
					if not self.sca_mode == 'UNIFORM' else self.uni_size)['verts']
				rot = guided_rot(obj, '-Z', dir1)
			else:
				if scatter_type == 'MESH':
					scatter_obj = bpy.data.objects.get(self.mesh_name)
				elif scatter_type == 'COLLECTION':
					collection = bpy.data.collections.get(self.coll_name)
					if collection:
						mesh_objs = [o for o in bpy.data.collections.get(self.coll_name).all_objects \
							if o.type == 'MESH' and o != obj]
						if mesh_objs:
							seed(self.coll_seed + i)
							coll_obj = choice(mesh_objs)
							scatter_obj = bpy.data.objects.get(coll_obj.name)

				if scatter_obj:
					bm_scatter.from_mesh(scatter_obj.data)
					scatter_verts = bm_scatter.verts
					rot = guided_rot(scatter_obj, 'Z', dir1)
				else: cont = False

			if cont:
				loc += ((center-loc) * self.cluster)
				if sum([self.explode_min, self.explode_max]) > 0:
					seed(self.explode_seed + i)
					dir2 = props.normal_guide if self.track_normal else normal
					loc += dir2 * uniform(self.explode_min, self.explode_max)

				bmesh.ops.translate(
					bm_scatter,
					verts   = scatter_verts,
					vec     = loc
					)

				if self.sca_mode == 'UNIFORM':
					sz = self.uni_size
					bmesh.ops.scale(
						bm_scatter,
						vec     = Vector((sz, sz, sz)),
						space   = Matrix.Translation(loc).inverted(),
						verts   = scatter_verts
						)
				else:
					if scatter_type != 'CUBE':
						seed(self.size_seed + i)
						sz = uniform(self.size_min, self.size_max)
						bmesh.ops.scale(
							bm_scatter,
							vec     = Vector((sz, sz, sz)),
							space   = Matrix.Translation(loc).inverted(),
							verts   = scatter_verts
							)

					def sca_seed(min_sca, max_sca):

						scale = Vector()
						for n in range(3):
							if self.scale_seed[n] > 1:
								seed(self.scale_seed[n] + i)
								scale[n] = uniform(min_sca[n], max_sca[n])
							else: scale[n] = max(min_sca[n], max_sca[n])
							seed(0)

						return scale

					x0, y0, z0 = self.scale_min
					x1, y1, z1 = self.scale_max
					scale = sca_seed([x0, y0, z0], [x1, y1, z1])
					bmesh.ops.scale(
						bm_scatter,
						vec     = Vector(scale),
						space   = Matrix.Translation(loc).inverted(),
						verts   = scatter_verts
						)

				def rot_seed(x, y, z):

					axis = [x, y, z]
					for n, v in enumerate(axis):
						if self.rot_seed[n] > 1:
							seed(self.rot_seed[n] + i)
							if v == 0:
								axis[n] = uniform(radians(-360), radians(360))
							else:
								if self.rot_mode == 'FREE':
									axis[n] = uniform(-v, v)
								else:
									rot_quotient = []
									for x in range(abs(int(360/v))):
										rot_quotient.append(v * (x+1))
									axis[n] = choice(rot_quotient)
						else: axis[n] = v
						seed(0)

					return Euler(Vector(axis))

				x, y, z = self.rot_axis
				rot_axis = rot_seed(x, y, z)
				_, orig_rot, _ = obj.matrix_world.decompose()
				if not self.follow_normal and self.track_normal:
					bmesh.ops.rotate(
						bm_scatter,
						verts   = scatter_verts,
						cent    = loc,
						matrix  = orig_rot.to_matrix().inverted() @ guided_rot(obj, track="Z", \
								normal=props.normal_guide) @ rot_axis.to_matrix()
						)
				else:
					bmesh.ops.rotate(
						bm_scatter,
						verts   = scatter_verts,
						cent    = loc,
						matrix  = orig_rot.to_matrix().inverted() @ rot @ rot_axis.to_matrix()
						)

			if self.use_mirror: bisect_symmetry(bm_scatter, obj)

			if self.no_overlap and \
				self.get_nonintersect(bm_hit, bm_scatter):
				bm_scatter.clear()

			bm_scatter.to_mesh(scatter_data)

			if self.no_overlap:
				if self.use_convex_hull:
					ch = bmesh.ops.convex_hull(bm_scatter, input=bm_scatter.verts)
					bmesh.ops.delete(bm_scatter, geom=ch["geom_unused"] + ch["geom_interior"], context='VERTS')

				bm_scatter.to_mesh(scatter_hit)
				bm_hit.from_mesh(scatter_hit)

			bm_scatter.free()

			if not single_obj:
				if scatter_data.polygons: self.add_scatter(obj, scatter_data)
			else:
				bm.from_mesh(scatter_data)
				bpy.data.meshes.remove(scatter_data)

		if single_obj: bmesh.ops.delete(bm, geom=triangles, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		if self.no_overlap:
			bm_hit.free()
			bpy.data.meshes.remove(scatter_hit)

		if not single_obj:
			bpy.data.meshes.remove(temp_mesh)
		else:
			self.add_scatter(obj, temp_mesh)

		if context.scene.rflow_props.clear_select: clear_select(obj)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		row.row(align=True).prop(self, "scatter_type", expand=True)
		if self.scatter_type == 'MESH':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mesh:")
			row.prop_search(
				self,
				"mesh_name",
				self,
				"meshes",
				text="",
				icon = "MESH_DATA"
				)
		if self.scatter_type == 'COLLECTION':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Collection:")
			row.prop_search(
				self,
				"coll_name",
				self,
				"collections",
				text="",
				icon = "OUTLINER_COLLECTION"
				)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Object Seed:")
			row.row(align=True).prop(self, "coll_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Points:")
		row.row(align=True).prop(self, "scatter_points", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Point Seed:")
		row.row(align=True).prop(self, "scatter_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scale Mode:")
		row.row(align=True).prop(self, "sca_mode", expand=True)
		if self.sca_mode == 'UNIFORM':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Size:")
			row.row(align=True).prop(self, "uni_size", text="")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Size:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "size_min")
			split.row(align=True).prop(self, "size_max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Size Seed:")
			row.row(align=True).prop(self, "size_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale Max:")
			row.row(align=True).prop(self, "scale_max", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale Min:")
			row.row(align=True).prop(self, "scale_min", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale Seed:")
			row.row(align=True).prop(self, "scale_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation Mode:")
		row.row(align=True).prop(self, "rot_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "rot_axis", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation Seed:")
		row.row(align=True).prop(self, "rot_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Explode:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "explode_min")
		split.row(align=True).prop(self, "explode_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Explode Seed:")
		row.row(align=True).prop(self, "explode_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cluster:")
		row.row(align=True).prop(self, "cluster", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		row.row(align=True).prop(self, "offset", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "no_overlap")
		flow.prop(self, "single_scatter")
		flow.prop(self, "follow_normal")
		if self.no_overlap and not self.follow_normal:
			flow = col.column_flow(columns=2, align=True)
			flow.prop(self, "use_convex_hull")
			flow.prop(self, "track_normal")
		else:
			if self.no_overlap:
				col.prop(self, "use_convex_hull")
			if not self.follow_normal:
				col.prop(self, "track_normal")
		col.prop(self, "use_dissolve")
		if self.use_dissolve:
			col.prop(self, "angle")

	def invoke(self, context, event):

		obj = context.active_object

		self.coll_seed = 1
		self.scatter_seed = 1
		self.size_seed = 1
		self.scale_seed = (1,1,1)
		self.rot_seed = (1,1,1)

		self.mesh_name = ""
		self.meshes.clear()
		self.coll_name = ""
		self.collections.clear()

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = any(f for f in obj.data.polygons if f.select)

		if has_face:
			init_props(self, event, ops='rscatter')
			for o in context.scene.objects:
				if o.type == 'MESH' and \
					o != obj:
					newListItem = self.meshes.add()
					newListItem.name = o.name

			for c in bpy.data.collections:
				newListItem = self.collections.add()
				newListItem.name = c.name

			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_r_tubes(Operator):
	'''Create randomized tubes'''
	bl_idname = 'rand_tubes.rflow'
	bl_label = 'Random Tubes'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	mode : EnumProperty(
		name = 'Mode',
		items = (
			('FACE', 'Face',''),
			('EDGE', 'Edge','')),
		default = 'FACE'
		)
	path : EnumProperty(
		name = 'Path',
		items = (
			('NONE', 'None',''),
			('SHORTEST', 'Shortest',''),
			('LONGEST', 'Longest','')),
		default = 'NONE'
		)
	panel_num : IntProperty(
		name        = "Number",
		description = "Panel amount",
		default     = 5,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	turn_count : IntProperty(
		name        = "Segments",
		description = "Number of aligned segments to walk before turning",
		default     = 5,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	turn_angle : FloatProperty(
		name        = "Angle",
		description = "Minimum angle threshold for turning aligned segments",
		default     = radians(30),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	edg_length_max : IntProperty(
		name        = "Max",
		description = "Maximum edge length",
		default     = 5,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	edg_length_min : IntProperty(
		name        = "Min",
		description = "Minimum edge length",
		default     = 0,
		min         = 0,
		soft_max    = 100,
		step        = 1
		)
	edg_seed : IntProperty(
		name        = "Seed",
		description = "Random edge walk seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	edg_offset : FloatProperty(
		name        = "Offset",
		description = "Edge offset",
		default     = 0.1,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	edg_offset_min : FloatProperty(
		name        = "Min",
		description = "Minimum edge offset",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	edg_offset_max : FloatProperty(
		name        = "Max",
		description = "Maximum edge offset",
		default     = 0.1,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	offset_seed : IntProperty(
		name        = "Offset Seed",
		description = "Random offset seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cut_method : EnumProperty(
		name = "Cut Method",
		description = "Determines how sharp edges will be cut",
		items = (
			('WRAP', 'Wrap',''),
			('SPLIT', 'Split','')),
		default = 'WRAP'
		)
	cut_threshold : FloatProperty(
		name        = "Cut Angle",
		description = "Maximum angle threshold for edges to be cut",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	uni_offset : BoolProperty(
		name        = "Uniform Offset",
		description = "Use single property value for edge offset",
		default     = False
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Margin from boundary edges",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	width : FloatProperty(
		name        = "Depth",
		description = "Depth of curve object",
		default     = 0.025,
		min         = 0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	resnum : IntProperty(
		name        = "Resolution",
		description = "Bevel resolution of curve object",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
	)
	bvl_offset_min : FloatProperty(
		name        = "Min",
		description = "Minimum bevel offset/width",
		default     = 0.025,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	bvl_offset_max : FloatProperty(
		name        = "Max",
		description = "Maximum bevel offset/width",
		default     = 0.025,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	bvl_offset_uni : FloatProperty(
		name        = "Bevel Offset",
		description = "Uniform bevel offset/width",
		default     = 0.025,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 4
	)
	bvl_seg : IntProperty(
		name        = "Segments",
		description = "Bevel segments",
		default     = 2,
		min         = 1,
		soft_max    = 100,
		step        = 1
	)
	bvl_angle : FloatProperty(
		name        = "Angle Limit",
		description = "Maximum angle threshold for curve points to get beveled",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	bvl_seed : IntProperty(
		name        = "Bevel Seed",
		description = "Randomize bevel offset",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		soft_max    = 12,
		step        = 1
		)
	cuts_smooth : FloatProperty(
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	uni_bevel : BoolProperty(
		name        = "Uniform Bevel",
		description = "Use single property value for bevel offset",
		default     = False
		)
	tri_mode : EnumProperty(
		name = 'Size Mode',
		description = "Size mode to use for loop ratio",
		items = (
			('PERCENT', 'Percent',''),
			('NUMBER', 'Number','')),
		default = 'PERCENT'
		)
	tri_perc : FloatProperty(
		name        = "Triangulate",
		description = "Triangulate faces",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	tri_num : IntProperty(
		name        = "Triangulate",
		description = "Triangulate faces via number",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	limit_body : BoolProperty(
		name        = "Limit Body",
		description = "Prevent start/end points originating from other tube bodies",
		default     = False
		)
	use_fallback : BoolProperty(
		name        = "Use Fallback",
		description = "Use fallback edges if no edge is found to meet next segment condition",
		default     = True
		)
	smooth_shade : BoolProperty(
		name        = "Shade Smooth",
		description = "Smooth shade curve object",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def curve_convert(self, obj, width, resnum, smooth=True):

		bpy.ops.object.convert(target='CURVE')

		obj.data.fill_mode = 'FULL'
		obj.data.bevel_depth = width
		obj.data.bevel_resolution = resnum

		for spline in obj.data.splines:
			spline.use_smooth = smooth

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		orig_mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		if self.mode == 'FACE':
			list_f = [f for f in bm.faces if not f.select]
		else:
			link_f = set()
			for e in bm.edges:
				if e.select:
					e.smooth = False
					for f in e.link_faces: link_f.add(f)

			list_f = list(set(bm.faces).difference(link_f))

		bmesh.ops.delete(bm, geom=list_f, context='FACES')

		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		split_margin = 0

		if self.cut_method == 'SPLIT':
			list_e = [e for e in bm.edges if e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold]
			bmesh.ops.split_edges(bm, edges=list_e)
			split_margin = 1e-5

		if self.margin or split_margin:
			margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin + split_margin)['faces']
			bmesh.ops.delete(bm, geom=margin, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		bm = bmesh.new()
		bm.from_mesh(temp_mesh)

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, cuts=self.cuts_base, \
			use_grid_fill=True, use_smooth_even=True)

		if self.tri_perc \
			or self.tri_num:
			tval = self.tri_perc if self.tri_mode == 'PERCENT' else self.tri_num
			tris = get_tri_faces(bm.faces, tval, self.edg_seed, mode=self.tri_mode)
			bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))

		oldv = list(bm.verts)
		indices = [e.index for e in bm.edges] if self.mode == 'FACE' \
			else [e.index for e in bm.edges if not e.smooth]
		cells = []

		if not indices:
			self.report({'WARNING'}, "No selected faces or edges.")
			return {"CANCELLED"}

		def add_body_limit(edge, vert):

			ov = edge.other_vert(vert)
			for link_e in ov.link_edges:
				if not link_e in cell_e: cell_e.add(link_e)

		pnum = 0
		while indices and pnum < self.panel_num:
			seed(self.edg_seed + pnum)
			x = choice(indices)
			indices.remove(x)

			bm.edges.ensure_lookup_table()
			edg = bm.edges[x]
			cell = [x]

			cell_e = set()
			last_v = None

			walk = 0
			t_count = self.turn_count

			while walk < (self.edg_length_max - 1):
				curr_e = edg
				curr_v = choice(curr_e.verts) if walk == 0 else curr_e.other_vert(last_v)

				dir1 = curr_e.verts[0].co - curr_e.verts[1].co

				add_body_limit(curr_e, curr_v)

				lnk_edges = list(curr_v.link_edges); shuffle(lnk_edges)
				edge_list = { e.index: e.calc_length() for e in lnk_edges }

				fallback = []
				if len(set(list(edge_list.keys())).intersection(set(cell))) < 2:
					for n, e in enumerate(lnk_edges):
						dir2 = e.verts[0].co - e.verts[1].co
						angle = dir1.angle(dir2)

						edge_length = list(edge_list.values())
						length_solver = min(edge_length) if self.path == 'LONGEST' \
							else max(edge_length) if self.path == 'SHORTEST' else 0.0

						if e.index in indices and \
							e.calc_length() != length_solver:
							if not e in cell_e: fallback.append(e)

						if t_count == 0:
							t_angle = angle >= self.turn_angle
							t_count = self.turn_count
						else: t_angle = angle < self.turn_angle

						last_e = n + 1 == len(lnk_edges)

						if t_angle or last_e:
							if e.index in indices and \
								e.calc_length() != length_solver:
								if not e in cell_e:
									idx = e.index
									edg = bm.edges[idx]
									indices.remove(idx)
									cell.append(idx)
									last_v = curr_v
									walk += 1
									break
							else:
								if self.use_fallback:
									if fallback and last_e:
										idx = choice(fallback).index
										edg = bm.edges[idx]
										indices.remove(idx)
										cell.append(idx)
										last_v = curr_v
										walk += 1
										break

					t_count -= 1

				if curr_e.index == cell[-1]:
					break

			if cell:
				for i in cell:
					limit = False
					if not self.limit_body:
						if i == cell[0] or i == cell[-1]: limit = True
					else: limit = True

					if limit:
						set_v = set()
						for v in bm.edges[i].verts:
							if not v in set_v:
								for e in v.link_edges:
									if e.index in indices: indices.remove(e.index)
								set_v.add(v)

				cells.append(cell)
				pnum += 1

		for i, edges in enumerate(cells):
			if len(edges) > self.edg_length_min:
				ret = bmesh.ops.duplicate(bm, geom=[e for e in bm.edges if e.index in edges])['vert_map']
				newv = [v for v in ret if not v in oldv]
				ends = [v for v in newv if len(v.link_edges) < 2]
				bmesh.ops.extrude_vert_indiv(bm, verts=ends)

				seed(self.offset_seed + i)
				vrt_offset = self.edg_offset if self.uni_offset else uniform(self.edg_offset_min, self.edg_offset_max)
				for v in newv:
					origv = [v0 for v0 in oldv if v0.co == v.co]
					if origv:
						v1 = origv[0]
						v.co += (v1.normal * (v1.calc_shell_factor() * vrt_offset))
				seed(0)

		bmesh.ops.delete(bm, geom=oldv, context='VERTS')

		if sum([self.bvl_offset_min, self.bvl_offset_max]) > 0 \
			if not self.uni_bevel else self.bvl_offset_uni > 0:
			vnum = 0
			for v in bm.verts[:]:
				angle = v.calc_edge_angle(None)
				if angle and \
					angle >= self.bvl_angle:
					seed(self.bvl_seed + vnum)
					bvl_offset = uniform(self.bvl_offset_min, self.bvl_offset_max) \
						if not self.uni_bevel else self.bvl_offset_uni
					bmesh.ops.bevel(
						bm,
						geom            = [v],
						offset          = bvl_offset,
						offset_type     = 'OFFSET',
						segments        = self.bvl_seg,
						profile         = 0.5,
						affect          = 'VERTICES',
						clamp_overlap	= True
						)
					vnum += 1

			bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		bm.to_mesh(temp_mesh)
		bm.free()

		if temp_mesh.vertices:
			new_obj = bpy.data.objects.new(filter_name(obj, "_RPipes"), temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc

			set_parent(obj, new_obj)

			select_isolate(new_obj)

			self.curve_convert(new_obj, self.width * self.mdv, self.resnum, self.smooth_shade)

			assign_mat(self, obj, new_obj, self.mat_index)

			if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			select_isolate(obj)
		else:
			bpy.data.meshes.remove(temp_mesh)

		if context.scene.rflow_props.clear_select: clear_select(obj)

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Mode:")
		row.row(align=True).prop(self, "mode", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Path:")
		row.row(align=True).prop(self, "path", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Amount:")
		row.row(align=True).prop(self, "panel_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Align:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "turn_count")
		split.row(align=True).prop(self, "turn_angle")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Length:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "edg_length_min")
		split.row(align=True).prop(self, "edg_length_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Seed:")
		row.row(align=True).prop(self, "edg_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		if self.uni_offset:
			split = row.split(factor=0.9, align=True)
			split.row(align=True).prop(self, "edg_offset", text="")
			split.prop(self, "uni_offset", text="", icon="LINKED")
		else:
			split1 = row.split(factor=0.5, align=True)
			split1.row(align=True).prop(self, "edg_offset_min")
			split2 = split1.split(factor=0.8, align=True)
			split2.row(align=True).prop(self, "edg_offset_max")
			split2.prop(self, "uni_offset", text="", icon="UNLINKED")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Offset Seed:")
			row.row(align=True).prop(self, "offset_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Method:")
		row.row(align=True).prop(self, "cut_method", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Angle:")
		row.row(align=True).prop(self, "cut_threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Curve:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "width")
		split.row(align=True).prop(self, "resnum")
		if self.uni_bevel:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Bevel Offset:")
			split = row.split(factor=0.9, align=True)
			split.row(align=True).prop(self, "bvl_offset_uni", text="")
			split.prop(self, "uni_bevel", text="", icon="LINKED")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Bevel Offset:")
			split1 = row.split(factor=0.5, align=True)
			split1.row(align=True).prop(self, "bvl_offset_min")
			split2 = split1.split(factor=0.8, align=True)
			split2.row(align=True).prop(self, "bvl_offset_max")
			split2.prop(self, "uni_bevel", text="", icon="UNLINKED")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bvl Seg/Angle:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "bvl_seg")
		split.row(align=True).prop(self, "bvl_angle")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel Seed:")
		row.row(align=True).prop(self, "bvl_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Tri Mode:")
		row.row(align=True).prop(self, "tri_mode", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Triangulate:")
		if self.tri_mode == 'PERCENT':
			row.row(align=True).prop(self, "tri_perc", text="")
		else:
			row.row(align=True).prop(self, "tri_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "limit_body")
		flow.prop(self, "use_fallback")
		flow.prop(self, "smooth_shade")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		dim = obj.dimensions.copy()
		self.mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

		self.edg_seed = 1
		self.offset_seed = 1

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = any(f for f in obj.data.polygons if f.select)

		init_props(self, event, ops='rtubes', force=has_face>=props.select_limit)
		prefs = context.preferences.addons[__package__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_r_cables(Operator):
	'''Create randomized catenary cables'''
	bl_idname = 'rand_cables.rflow'
	bl_label = 'Random Cables'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	cable_type : EnumProperty(
		name		= "Cable Type",
		description = "Cable type",
		items		= [('CATN', "Catenary", "Connect start/end points using catenary effect"),
					('CURV', "Curve", "Connect start/end points using curve effect")],
		default		= 'CATN',
		)
	spline_type : EnumProperty(
		name		= "Spline Type",
		description = "Spline type",
		items		= [('BEZIER', "Bezier", "Bezier spline"),
					('POLY', "Poly", "Poly spline")],
		default		= 'BEZIER',
		)
	slack_min : FloatProperty(
		name		= "Min",
		description	= "Minimum cable slack",
		precision	= 4,
		default		= 0.1,
		min			= 0.0001,
		max			= 100.0
		)
	slack_max : FloatProperty(
		name		= "Max",
		description	= "Maximum cable slack",
		precision	= 4,
		default		= 2.0,
		min			= 0.0001,
		max			= 100.0
		)
	slack_seed : IntProperty(
		name        = "Seed",
		description = "Randomize cable slack or curve",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	manual_offset : FloatVectorProperty(
		name        = "Manual Offset",
		description = "Additional vector control for curve offset",
		default     = (0,0,0),
		size        = 3,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.5,
		precision   = 3,
		subtype		= "XYZ"
		)
	norm_offset_min : FloatProperty(
		name        = "Min",
		description = "Minimum normal offset for curve",
		default     = 0.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	norm_offset_max : FloatProperty(
		name        = "Max",
		description = "Maximum normal offset for curve",
		default     = 1.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	offset_noise : FloatProperty(
		name        = "Offset",
		description = "Offset noise",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	wiggle_noise : FloatProperty(
		name        = "Wiggle",
		description = "Wiggle noise",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	points_seed : IntProperty(
		name        = "Seed",
		description = "Randomize cable points",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cable_num : IntProperty(
		name        = "Number of Cables",
		description = "Number of cable to randomize",
		default     = 10,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	steps : IntProperty(
		name		= "Steps",
		description	= "Resolution of the curve",
		default		= 16,
		min			= 2,
		max			= 1024,
		)
	dist_thresh : FloatProperty(
		name        = "Min Distance",
		description = "Minimum distance between start/end of cable for removal",
		default     = 0.0,
		min    		= 0.0,
		soft_max    = 1000.0,
		step        = 0.1,
		precision   = 4
		)
	res_u : IntProperty(
		name		= "Resolution U",
		description = "Curve resolution u",
		default		= 8,
		min			= 0,
		max			= 64
		)
	bvl_depth : FloatProperty(
		name		= "Radius",
		description	= "Bevel depth",
		default		= 0.01,
		min			= 0.0,
		step        = 0.01,
		precision	= 3
		)
	bvl_res : IntProperty(
		name		= "Resolution",
		description	= "Bevel resolution",
		default		= 0,
		min			= 0,
		max			= 32
		)
	extrude : FloatProperty(
		name		= "Extrude",
		description	= "Extrude amount",
		default		= 0.0,
		min			= 0.0,
		precision	= 3
		)
	twist_mode : EnumProperty(
		name		= "Twisting",
		description	= "Twist method, type of tilt calculation",
		items		= [('Z_UP', 'Z-Up', 'Z Up'),
					('MINIMUM', 'Minimum', 'Minimum'),
					('TANGENT', 'Tangent', 'Tangent')],
		default		= 'MINIMUM',
		)
	twist_smooth : FloatProperty(
		name		= "Smooth",
		description	= "Twist smoothing amount for tangents",
		default		= 0.0,
		min			= 0.0,
		precision	= 3
		)
	tilt : FloatProperty(
		name		= "Tilt",
		description	= "Spline handle tilt",
		default		= 0.0,
		precision	= 3
		)
	r_radius : FloatProperty(
		name		= "Radius",
		description	= "Randomise radius of spline controlpoints",
		default		= 0.0,
		min			= 0.0,
		precision	= 3
		)
	radius_seed : IntProperty(
		name        = "Radius Seed",
		description = "Randomize cable radius",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	offset : FloatProperty(
		name        = "Offset",
		description = "Offset source mesh by this amount to produce overlap",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	island_limit : EnumProperty(
		name		= "Island Limit",
		description	= "Method of limiting start and end points to islands",
		items		= [('NONE', 'None', 'No limit'),
					('LIMITED', 'Limited', 'Limit start and end points from the same island'),
					('FULL', 'Full', 'Limit start and end points to sequential islands')],
		default		= 'NONE',
		)
	island_seed : IntProperty(
		name        = "Island Seed",
		description = "Randomize face island sequence",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	sort_method : EnumProperty(
		name = 'Sort Method',
		items = (
			('NONE', 'None','No sorting'),
			('X', 'X','Sort indices by X axis direction'),
			('Y', 'Y','Sort indices by Y axis direction'),
			('Z', 'Z','Sort indices by Z axis direction')),
		default = 'NONE'
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Margin from boundary edges",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	join_curves : BoolProperty(
		name        = "Join Curves",
		description = "Join curves into one object",
		default     = True
		)
	no_overlap : BoolProperty(
		name        = "No Overlap",
		description = "Avoid overlaps on visible mesh/curve objects",
		default     = False
		)
	overlap_self : BoolProperty(
		name        = "Overlap Self",
		description = "Overlap cables generated in this instance",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def point_on_triangle(self, face):
		'''https://blender.stackexchange.com/a/221597'''

		a, b, c = map(lambda v: v.co, face.verts)
		a2b = b - a
		a2c = c - a
		height = triangular(low=0.0, high=1.0, mode=0.0)

		return a + a2c*height + a2b*(1-height) * random(), face

	def catenary_curve(
				self,
				start=[-2, 0, 2],
				end=[2, 0, 2],
				steps=24,
				a=2.0
				):

		points = []
		lx = end[0] - start[0]
		ly = end[1] - start[1]
		lr = sqrt(pow(lx, 2) + pow(ly, 2))
		lv = lr / 2 - (end[2] - start[2]) * a / lr
		zv = start[2] - pow(lv, 2) / (2 * a)
		slx = lx / steps
		sly = ly / steps
		slr = lr / steps
		i = 0

		while i <= steps:
			x = start[0] + i * slx
			y = start[1] + i * sly
			z = zv + pow((i * slr) - lv, 2) / (2 * a)
			points.append([x, y, z])
			i += 1

		return points

	def get_curve_points(self, spline):

		points = []

		if len(spline.bezier_points) >= 2:
			r = self.steps
			segments = len(spline.bezier_points)
			if not spline.use_cyclic_u: segments -= 1

			for i in range(segments):
				inext = (i + 1) % len(spline.bezier_points)

				knot1 = spline.bezier_points[i].co
				handle1 = spline.bezier_points[i].handle_right
				handle2 = spline.bezier_points[inext].handle_left
				knot2 = spline.bezier_points[inext].co

				_points = geometry.interpolate_bezier(knot1, handle1, handle2, knot2, r)
				if i != segments - 1:
					_points.pop()

				points.extend(_points)

		return points

	def add_temp_curve(self, coords):

		curve = bpy.data.curves.new('_temp', 'CURVE')
		curve.dimensions = '3D'
		spline = curve.splines.new(type='BEZIER')
		spline.bezier_points.add(int(len(coords) - 1))
		for i in range(len(coords)):
			spline.bezier_points[i].co = coords[i]
			spline.bezier_points[i].handle_right_type = 'AUTO'
			spline.bezier_points[i].handle_left_type = 'AUTO'

		return curve

	def get_nonintersect(self, obj1, obj2):

		mat1 = obj1.matrix_world
		mat2 = obj2.matrix_world

		obj1 = get_eval_mesh(obj1)
		obj2 = get_eval_mesh(obj2)

		bm1 = bmesh.new()
		bm2 = bmesh.new()

		bm1.from_mesh(obj1)
		bm2.from_mesh(obj2)

		bm1.transform(mat1)
		bm2.transform(mat2)

		bvh1 = BVHTree.FromBMesh(bm1)
		bvh2 = BVHTree.FromBMesh(bm2)

		return bool(bvh1.overlap(bvh2))

	def add_curve_object(
				self,
				obj,
				coords,
				matrix,
				spline_name="Spline",
				spline_type='BEZIER',
				resolution_u=12,
				bevel=0.0,
				bevel_resolution=0,
				extrude=0.0,
				spline_radius=0.0,
				twist_mode='MINIMUM',
				twist_smooth=0.0,
				tilt=0.0
				):

		cur_data = bpy.data.curves.new(spline_name, 'CURVE')
		cur_data.dimensions = '3D'
		if self.cable_type == 'CATN':
			spline = cur_data.splines.new(spline_type)
		else: spline = cur_data.splines.new('BEZIER')
		curve = bpy.data.objects.new(spline_name, cur_data)
		spline.radius_interpolation = 'BSPLINE'
		spline.tilt_interpolation = 'BSPLINE'

		if spline_type == 'BEZIER' or self.cable_type == 'CURV':
			spline.bezier_points.add(int(len(coords) - 1))
			for i in range(len(coords)):
				spline.bezier_points[i].co = coords[i]
				spline.bezier_points[i].handle_right_type = 'AUTO'
				spline.bezier_points[i].handle_left_type = 'AUTO'
				spline.bezier_points[i].radius += spline_radius * random()
				spline.bezier_points[i].tilt = radians(tilt)
		else:
			spline.points.add(int(len(coords) - 1))
			for i in range(len(coords)):
				spline.points[i].co = coords[i][0], coords[i][1], coords[i][2], 1

		set_parent(obj, curve)

		curve.data.resolution_u = resolution_u
		curve.data.fill_mode = 'FULL'
		curve.data.bevel_depth = bevel
		curve.data.bevel_resolution = bevel_resolution
		curve.data.extrude = extrude
		curve.data.twist_mode = twist_mode
		curve.data.twist_smooth = twist_smooth
		curve.matrix_world = matrix

		if self.no_overlap:
			for o in bpy.context.visible_objects:
				if o.type in ['MESH', 'CURVE'] \
					and not o in self.sel_objs and o != curve:
					overlap = self.get_nonintersect(o, curve)
					if overlap:
						remove_obj(curve)
						curve = None
						break

		if curve and self.overlap_self: self.sel_objs.append(curve)

		return curve

	def make_hit_source(self, dup_objs):

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")

		for o in dup_objs:
			_data = get_eval_mesh(o)

			for v in _data.vertices:
				v.co = o.matrix_world @ v.co

			bm.from_mesh(_data)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.select], context='FACES')

		bm.to_mesh(temp_mesh)

		source_hit = bpy.data.objects.new("_temp", temp_mesh)
		bpy.context.scene.collection.objects.link(source_hit)

		return source_hit

	def execute(self, context):

		obj = context.active_object

		hit_objs = []
		source_hit = None
		self.sel_objs = sel_objs = context.selected_objects

		limit = self.island_limit != 'NONE'
		props = context.scene.rflow_props

		def set_data_origin(obj, data, origin):

			pivot = obj.matrix_world.inverted() @ origin
			data.transform(Matrix.Translation(-pivot))

		bm = bmesh.new()

		sel_objs = sorted(sel_objs, key=lambda o: o.name)
		for o in sel_objs:
			o.update_from_editmode()
			clone_data = o.data.copy() if self.use_mirror else get_eval_mesh(o).copy()
			set_data_origin(o, clone_data, obj.matrix_world.translation)
			bm.from_mesh(clone_data)
			bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
			bpy.data.meshes.remove(clone_data)

			hit_objs.append(o)

		if hit_objs and self.no_overlap:
			source_hit = self.make_hit_source(hit_objs)

		if not bm.faces:
			self.report({'WARNING'}, "No faces selected.")
			bm.free()
			return {"FINISHED"}

		if self.offset:
			for v in bm.verts:
				v.co -= v.normal * (v.calc_shell_factor() * self.offset)

		if self.margin:
			margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin)['faces']
			bmesh.ops.delete(bm, geom=margin, context='FACES')

		sort_elements(bm.verts, self.sort_method, False)

		triangles = bmesh.ops.triangulate(bm, faces=bm.faces)['faces']
		surfaces = map(lambda t: t.calc_area(), triangles)
		seed(self.points_seed)
		listp = choices(population=triangles, weights=surfaces, k=self.cable_num*4)
		points = list(map(self.point_on_triangle, listp))

		islands = []
		unique_pairs = []

		if limit:
			islands = get_islands(obj, bm)
			isle_count = len(islands)
			if isle_count > 1:
				if self.island_seed > 1:
					seed(self.island_seed); shuffle(islands)
				unique_pairs = [[i, i+1] for i in range(isle_count)]

		amount = self.cable_num
		pairs = []

		def island_index(l1, l2):

			idx = 0
			for i, p in enumerate(l2):
				if all(x in p for x in l1): idx = i

			return idx

		while amount > 0:
			start = choice(points)
			points.remove(start)
			end = choice(points)
			points.remove(end)

			if limit:
				vl1 = island_index([v.index for v in start[1].verts], islands)
				vl2 = island_index([v.index for v in end[1].verts], islands)

			if start[0] != end[0]:
				delta = (start[0] - end[0]).length_squared
				if delta > self.dist_thresh:
					if limit:
						pairing = vl1 != vl2 if self.island_limit == 'LIMITED' else [vl1, vl2] in unique_pairs
						if pairing:
							pairs.append([start[0], end[0]])
					else: pairs.append([start[0], end[0]])

			amount -= 1
			if not points: break

		bm.free()

		new_curves = []
		for i, p in enumerate(pairs):
			try:
				seed(self.slack_seed + i)
				if self.cable_type == 'CATN':
					coords = self.catenary_curve(
							obj.matrix_world @ p[0],
							obj.matrix_world @ p[1],
							self.steps,
							uniform(self.slack_min, self.slack_max)
							)
				else:
					p1 = obj.matrix_world @ p[0]
					p2 = obj.matrix_world @ p[1]
					o = (p1 + p2) / 2 + Vector([uniform(-self.offset_noise,self.offset_noise) for n in range(3)])

					offset = uniform(self.norm_offset_min, self.norm_offset_max)
					points = [p1, o + self.manual_offset + (props.normal_guide * offset), p2]

					temp_curve = self.add_temp_curve(points)
					coords = self.get_curve_points(temp_curve.splines[0])
					bpy.data.curves.remove(temp_curve)

					for n, v in enumerate(coords):
						if n != 0 and n != len(coords) - 1:
							coords[n] = v + Vector([uniform(-self.wiggle_noise,self.wiggle_noise) for n in range(3)])

				seed(self.radius_seed)
				curve = self.add_curve_object(
						obj,
						coords,
						Matrix(),
						'RCables',
						self.spline_type,
						self.res_u,
						self.bvl_depth * self.mdv,
						self.bvl_res,
						self.extrude,
						self.r_radius,
						self.twist_mode,
						self.twist_smooth,
						self.tilt
						)
				if curve:
					new_curves.append(curve)
					set_origin(curve, obj.matrix_world.translation)
					if self.use_mirror: copy_modifiers([obj, curve], mod_types=['MIRROR'])
					assign_mat(self, obj, curve, self.mat_index)
			except:
				pass

		if new_curves:
			save_mode = obj.mode
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.select_all(action='DESELECT')

			for o in new_curves:
				o.select_set(True)
				if o == new_curves[0]: context.view_layer.objects.active = o

			if self.join_curves: bpy.ops.object.join()

			bpy.ops.object.select_all(action='DESELECT')

			for o in sel_objs:
				o.select_set(True)
				if o == sel_objs[-1]:
					context.view_layer.objects.active = o

				if context.scene.rflow_props.clear_select: clear_select(o)

			bpy.ops.object.mode_set(mode=save_mode)

		if source_hit: remove_obj(source_hit)

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cable Type:")
		row.row(align=True).prop(self, "cable_type", expand = True)
		if self.cable_type == 'CATN':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Spline Type:")
			row.row(align=True).prop(self, "spline_type", expand = True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Slack:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "slack_min")
			split.row(align=True).prop(self, "slack_max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Slack Seed:")
			row.row(align=True).prop(self, "slack_seed", text="")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Manual Offset:")
			row.row(align=True).prop(self, "manual_offset", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Normal Offset:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "norm_offset_min")
			split.row(align=True).prop(self, "norm_offset_max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Noise:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "offset_noise")
			split.row(align=True).prop(self, "wiggle_noise")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Curve Seed:")
			row.row(align=True).prop(self, "slack_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cable Amount:")
		row.row(align=True).prop(self, "cable_num", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Origin Seed:")
		row.row(align=True).prop(self, "points_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Island Limit:")
		row.row(align=True).prop(self, "island_limit", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Island Seed:")
		row.row(align=True).prop(self, "island_seed", text="")
		if self.island_limit != 'NONE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Sort Method:")
			row.row(align=True).prop(self, "sort_method", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		row.row(align=True).prop(self, "offset", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Min Distance:")
		row.row(align=True).prop(self, "dist_thresh", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "bvl_depth")
		split.row(align=True).prop(self, "bvl_res")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Resolution U:")
		row.row(align=True).prop(self, "res_u", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Steps:")
		row.row(align=True).prop(self, "steps", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Extrude:")
		row.row(align=True).prop(self, "extrude", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Twist Mode:")
		row.row(align=True).prop(self, "twist_mode", expand = True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Twist Smooth:")
		row.row(align=True).prop(self, "twist_smooth", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Tilt:")
		row.row(align=True).prop(self, "tilt", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Radius:")
		row.row(align=True).prop(self, "r_radius", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Radius Seed:")
		row.row(align=True).prop(self, "radius_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "join_curves")
		flow.prop(self, "no_overlap")
		if self.no_overlap:
			flow.prop(self, "overlap_self")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		dim = obj.dimensions.copy()
		self.mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

		self.points_seed = 1
		self.slack_seed = 1
		self.offset_vector = (0,0,0)
		self.sel_objs = []

		if event.alt:
			for o in context.selected_objects:
				get_linked_flat_faces(o)

		prefs = context.preferences.addons[__package__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_r_vertex_color(Operator):
	'''Randomize vertex color fill for selected objects'''
	bl_idname = 'rand_vcol.rflow'
	bl_label = 'Random VColor'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	vcname : StringProperty(
		name        = "Vertex Color Name",
		description = "Name of vertex color",
		default		= "Vertex Color"
		)
	vclist : StringProperty(
		name        = "Vertex Color List",
		description = "Vertex color group list from all selected objects"
		)
	vcolors : CollectionProperty(type=PropertyGroup)
	color_max : FloatVectorProperty(
		name        = "Color Max",
		description = "Vertex color maximum rgb values",
		subtype     = 'COLOR_GAMMA',
		default     = (1.0,1.0,1.0),
		size        = 3,
		min         = 0.0,
		max         = 1.0
		)
	color_min : FloatVectorProperty(
		name        = "Color Min",
		description = "Vertex color minimum rgb values",
		subtype     = 'COLOR_GAMMA',
		default     = (0.0,0.0,0.0),
		size        = 3,
		min         = 0.0,
		max         = 1.0
		)
	limit : EnumProperty(
		name = 'Limit',
		items = (
			('OBJECT', 'Object',''),
			('ISLAND', 'Island',''),
			('SELECT', 'Select',''),
			('SHARP', 'Sharp','')),
		default = 'OBJECT'
		)
	col_seed : IntProperty(
		name        = "H",
		description = "Color rgb randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	sat_min : FloatProperty(
		name        = "Min",
		description = "Minimum random value for saturation factor of hsv color",
		default     = 0,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
	)
	sat_max : FloatProperty(
		name        = "Max",
		description = "Maximum random value for saturation factor of hsv color",
		default     = 1.0,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
	)
	sat_seed : IntProperty(
		name        = "S",
		description = "Color saturation randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	val_min : FloatProperty(
		name        = "Min",
		description = "Minimum random value for value factor of hsv color",
		default     = 0,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
	)
	val_max : FloatProperty(
		name        = "Max",
		description = "Maximum random value for value factor of hsv color",
		default     = 1.0,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
	)
	val_seed : IntProperty(
		name        = "V",
		description = "Color value randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	offset : IntProperty(
		name        = "Island Offset",
		description = "Number offset before changing island color",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	obj_offset : IntProperty(
		name        = "Object Offset",
		description = "Number offset before changing object color",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	single_color : BoolProperty(
		name        = "Single Color",
		description = "Assign single color for faces selected per object",
		default     = False
		)
	use_hg : EnumProperty(
		name = "Hard Gradient",
		description = "Use hard gradient for HSV",
		items = (
			('COL', 'Hue','Use hard gradient for color or hue'),
			('SAT', 'Saturation','Use hard gradient for saturation'),
			('VAL', 'Value','Use hard gradient for value')),
		options = {"ENUM_FLAG"})
	col_hg_stops : IntProperty(
		name        = "H",
		description = "Number of stops for hard gradient hue set at even spacing",
		default     = 2,
		min         = 2,
		soft_max    = 100,
		step        = 1
	)
	sat_hg_stops : IntProperty(
		name        = "S",
		description = "Number of stops for hard gradient saturation set at even spacing",
		default     = 2,
		min         = 2,
		soft_max    = 100,
		step        = 1
	)
	val_hg_stops : IntProperty(
		name        = "V",
		description = "Number of stops for hard gradient value set at even spacing",
		default     = 2,
		min         = 2,
		soft_max    = 100,
		step        = 1
	)
	mark_sharp : BoolProperty(
		name        = "Mark Sharp",
		description = "Mark sharp edges based on angle threshold",
		default     = False
		)
	sharpness : FloatProperty(
		name        = "Sharpness",
		description = "Sharpness",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	dirty_vc : BoolProperty(
		name        = "Dirty Vertex Color",
		description = "Generate a dirt map gradient based on cavity",
		default     = False
		)
	blur_str : FloatProperty(
		name        = "Blur Strength",
		description = "Blur strength per iteration",
		default     = 1.0,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 2
	)
	blur_iter : IntProperty(
		name        = "Blur Iterations",
		description = "Number of times to blur the colors (higher blurs more)",
		default     = 1,
		min         = 0,
		max         = 40,
		step        = 1
		)
	hi_angle : FloatProperty(
		name        = "Highlight Angle",
		description = "Less than 90 limits the angle used in the tonal range",
		default     = radians(90),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 2,
		subtype     = "ANGLE"
		)
	drt_angle : FloatProperty(
		name        = "Dirt Angle",
		description = "Less than 90 limits the angle used in the tonal range",
		default     = 0,
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 2,
		subtype     = "ANGLE"
		)
	drt_only : BoolProperty(
		name        = "Dirt Only",
		description = "Don't calculate cleans for convex areas",
		default     = False
		)
	normalize : BoolProperty(
		name        = "Normalize",
		description = "Normalize the colors, increasing the contrast",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH" \
			and context.active_object.mode == "OBJECT"

	def get_random_color(self, var):

		col_hgs = self.col_hg_stops - 1
		sat_hgs = self.sat_hg_stops - 1
		val_hgs = self.val_hg_stops - 1

		def make_stops(minv, maxv, nstops):

			d = abs(maxv - minv)
			stop_value = round(d/nstops, 3)
			val = min(minv, maxv) + (stop_value * randint(0, nstops))

			return val

		seed(var + self.col_seed)
		if not "COL" in self.use_hg:
			r, g, b = [uniform(self.color_min[i], n) for i, n in enumerate(self.color_max)]
		else:
			r, g, b = [make_stops(self.color_min[i], n, col_hgs) for i, n in enumerate(self.color_max)]
		h, s, v = colorsys.rgb_to_hsv(r, g, b)

		seed(var + self.sat_seed)
		if not "SAT" in self.use_hg:
			s = uniform(self.sat_min, self.sat_max)
		else:
			s = make_stops(self.sat_min, self.sat_max, sat_hgs)

		seed(var + self.val_seed)
		if not "VAL" in self.use_hg:
			v = uniform(self.val_min, self.val_max)
		else:
			v = make_stops(self.val_min, self.val_max, val_hgs)

		return colorsys.hsv_to_rgb(h, s, v) + (1.0,)

	def sharpen_edges(self, edges):

		new_sharp = set()

		for e in edges:
			if e.smooth:
				angle = e.calc_face_angle(None)
				if angle and \
					angle > self.sharpness:
					e.smooth = False
					new_sharp.add(e)

		return new_sharp

	def execute(self, context):

		act_obj = context.active_object

		if act_obj: act_obj.select_set(True)

		objs = context.selected_objects

		def loops_color_layer(face, color):

			for loop in face.loops:
				loop[color_layer] = color

		x = 0
		obj_offset = 0
		for o in objs:
			context.view_layer.objects.active = o
			if o.type == 'MESH':
				mesh = o.data

				if self.vclist:
					layer = self.vclist
				else:
					layer = self.vcname if len(self.vcname) else "Vertex Color"

				bm = bmesh.new()
				bm.from_mesh(mesh)

				color_layer = bm.loops.layers.color.get(layer) \
					or bm.loops.layers.color.new(layer)

				bm.to_mesh(mesh)

				mesh.attributes.active_color = mesh.attributes[layer]

				if self.limit == 'OBJECT':
					vertex_color = self.get_random_color(x)
					for f in bm.faces:
						loops_color_layer(f, vertex_color)

				elif self.limit == 'ISLAND':
					listf = list(bm.faces)
					if listf != None:
						i = x
						offset = 0
						islands = get_islands(o, bm)

						for lp in islands:
							vertex_color = self.get_random_color(i)
							faces = [bm.verts[idx].link_faces for idx in lp]
							faces = undupe(list(chain.from_iterable(faces)))
							loops = [f.loops for f in faces]
							loops = undupe(list(chain.from_iterable(loops)))
							for l in loops:
								l[color_layer] = vertex_color

							offset += 1
							if offset == self.offset:
								i += 1
								offset = 0

				elif self.limit == 'SELECT':
					listf = [f for f in bm.faces if f.select]

					if self.single_color:
						vertex_color = self.get_random_color(x)
						for f in listf:
							loops_color_layer(f, vertex_color)
					else:
						linked_faces = set()

						if listf != None:
							i = x
							offset = 0
							while listf:
								traversal_stack = [listf.pop()]

								vertex_color = self.get_random_color(i)
								loops_color_layer(traversal_stack[0], vertex_color)

								while len(traversal_stack) > 0:
									f_curr = traversal_stack.pop()
									linked_faces.add(f_curr)

									for e in f_curr.edges:
										if e.is_contiguous and e.select:
											for f_linked in e.link_faces:
												if f_linked not in linked_faces and f_linked.select:
													traversal_stack.append(f_linked)
													loops_color_layer(f_linked, vertex_color)
													if f_linked in listf: listf.remove(f_linked)

								offset += 1
								if offset == self.offset:
									i += 1
									offset = 0

				else:
					if self.mark_sharp:
						new_sharp = self.sharpen_edges(bm.edges)

					listf = bm.faces[:]
					linked_faces = set()

					if listf != None:
						i = x
						offset = 0
						while listf:
							traversal_stack = [listf.pop()]

							vertex_color = self.get_random_color(i)
							loops_color_layer(traversal_stack[0], vertex_color)

							while len(traversal_stack) > 0:
								f_curr = traversal_stack.pop()
								linked_faces.add(f_curr)

								for e in f_curr.edges:
									if e.is_contiguous and e.smooth:
										for f_linked in e.link_faces:
											if f_linked not in linked_faces:
												traversal_stack.append(f_linked)
												loops_color_layer(f_linked, vertex_color)
												if f_linked in listf: listf.remove(f_linked)

							offset += 1
							if offset == self.offset:
								i += 1
								offset = 0

					if self.mark_sharp:
						for e in new_sharp: e.smooth = True

				bm.to_mesh(mesh)
				bm.free()

			obj_offset += 1
			if obj_offset == self.obj_offset:
				x += 1
				obj_offset = 0

			if self.dirty_vc:
				bpy.ops.paint.vertex_color_dirt(blur_strength=self.blur_str, blur_iterations=self.blur_iter, \
					clean_angle=self.hi_angle, dirt_angle=self.drt_angle, dirt_only=self.drt_only, normalize=self.normalize)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		col.separator()
		col.template_color_picker(self, "color_max", value_slider=False)
		col.separator()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="New Layer:")
		row.row(align=True).prop(self, "vcname", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Use Saved:")
		row.prop_search(
			self,
			"vclist",
			self,
			"vcolors",
			text="",
			icon = "GROUP_VCOL"
			)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limit:")
		flow = row.column_flow(columns=2, align=True)
		flow.prop(self, "limit", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Hue Max:")
		row.row(align=True).prop(self, "color_max", text="", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Hue Min:")
		row.row(align=True).prop(self, "color_min", text="", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Saturation:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "sat_min")
		split.row(align=True).prop(self, "sat_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Value:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "val_min")
		split.row(align=True).prop(self, "val_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Random Seeds:")
		split = row.split(factor=0.33, align=True)
		split.row(align=True).prop(self, "col_seed")
		split.row(align=True).prop(self, "sat_seed")
		split.row(align=True).prop(self, "val_seed")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Hard Gradient:")
		row.row(align=True).prop(self, "use_hg", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text=" ")
		row.label(text=(" " * 2) + "(shift+click to add multiple or remove)")
		if self.use_hg != set():
			row = col.row().split(factor=0.27, align=True)
			row.label(text="HG Stops:")
			split = row.split(factor=0.33, align=True)
			split.row(align=True).prop(self, "col_hg_stops")
			split.row(align=True).prop(self, "sat_hg_stops")
			split.row(align=True).prop(self, "val_hg_stops")
		if self.limit != 'OBJECT':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Island Offset:")
			row.row(align=True).prop(self, "offset", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Object Offset:")
		row.row(align=True).prop(self, "obj_offset", text="")
		if self.limit == 'SELECT':
			col.separator(factor=0.5)
			col.prop(self, "single_color")
		col.separator(factor=0.5)
		if self.limit == 'SHARP':
			col.prop(self, "mark_sharp")
			if self.mark_sharp: col.prop(self, "sharpness")
		col.prop(self, "dirty_vc")
		if self.dirty_vc:
			col.separator(factor=0.5)
			col.prop(self, "blur_str")
			col.prop(self, "blur_iter")
			col.prop(self, "hi_angle")
			col.prop(self, "drt_angle")
			col.separator(factor=0.5)
			col.prop(self, "drt_only")
			col.prop(self, "normalize")

	def invoke(self, context, event):

		self.color_seed = 1
		self.sat_seed = 1
		self.val_seed = 1
		self.vclist = ""

		init_props(self, event, ops='rvcol')
		context.space_data.shading.color_type = 'VERTEX'

		for o in context.selected_objects:
			if o.type == 'MESH':
				for vc in o.data.vertex_colors:
					if vc.name not in self.vcolors:
						newListItem = self.vcolors.add()
						newListItem.name = vc.name

		prefs = context.preferences.addons[__package__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_r_animation(Operator):
	'''Create randomized animation in move/scale/rotate transforms'''
	bl_idname = 'rand_anim.rflow'
	bl_label = 'Random Animation'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	anim_type : EnumProperty(
		name = 'Type',
		items = (
			('AXIS', 'Axis','Animate tranforms of selected objects in the xyz axis'),
			('PATH', 'Path','Animate objects to follow selected paths')),
		default = 'AXIS'
		)
	dpath : EnumProperty(
		name = 'Animation',
		items = (
			('ROTATE', 'Rotate',''),
			('MOVE', 'Move',''),
			('SCALE', 'Scale','')),
		default = 'ROTATE'
		)
	mode : EnumProperty(
		name = 'Mode',
		items = (
			('REPEAT', 'Repetitive',''),
			('REPEAT_OFFSET', 'Continuous',''),
			('MIRROR', 'Mirrored','')),
		default = 'REPEAT'
		)
	pivot : EnumProperty(
		name = 'Pivot',
		items = (
			('ORIGIN', 'Origin',''),
			('GEOMETRY', 'Geometry',''),
			('CURSOR', 'Cursor','')),
		default = 'ORIGIN'
		)
	axis : EnumProperty(
		name = 'Axis',
		description = 'Animation axis',
		items = (
			('0', 'X',''),
			('1', 'Y',''),
			('2', 'Z','')),
		options = {"ENUM_FLAG"}
		)
	start_frame : IntProperty(
		name        = "Start",
		description = "Start frame of the animation",
		default     = 0,
		min         = 0,
		soft_max    = 10000,
		step        = 1
		)
	end_frame : IntProperty(
		name        = "End",
		description = "Maximum randomized end frame of the animation",
		default     = 100,
		min         = 0,
		soft_max    = 10000,
		step        = 1
		)
	val_min : FloatProperty(
		name        = "Min",
		description = "Minimum move value for the animation",
		default     = -5.0,
		soft_min    = -5.0,
		soft_max    = 5.0,
		step        = 0.1,
		precision   = 3
	)
	val_max : FloatProperty(
		name        = "Max",
		description = "Maximum move value for the animation",
		default     = 5.0,
		soft_min    = -5.0,
		soft_max    = 5.0,
		step        = 0.1,
		precision   = 3
	)
	rot_min : FloatProperty(
		name        = "Min",
		description = "Minimum rotation value for the animation",
		default     = radians(-360),
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	rot_max : FloatProperty(
		name        = "Max",
		description = "Maximum rotation value for the animation",
		default     = radians(360),
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	anim_seed : IntProperty(
		name        = "Animation Seed",
		description = "Randomized seed for the animation fcurve value",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	frame_seed : IntProperty(
		name        = "Frame Seed",
		description = "Randomized seed for the animation start and end frames",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	type_empty : EnumProperty(
		name = 'Empty Draw Type',
		items = (
			('PLAIN_AXES', 'Plain Axes',''),
			('ARROWS', 'Arrow',''),
			('SINGLE_ARROW', 'SIngle Arrow',''),
			('CIRCLE', 'Circle',''),
			('CUBE', 'Cube',''),
			('SPHERE', 'Sphere',''),
			('CONE', 'Cone','')),
		default = 'PLAIN_AXES')
	loc_empty : EnumProperty(
		name = 'Empty Location',
		items = (
			('ACTIVE', 'Active','Use active object position as empty location'),
			('CURSOR', 'Cursor','Use 3D cursor position as empty location'),
			('AVERAGE', 'Average','Use average position of selected objects as empty location')),
		default = 'ACTIVE'
		)
	size_empty : FloatProperty(
		name        = "Empty Size",
		description = "Size of array offset object",
		default     = 2.0,
		min         = 0.01,
		soft_max    = 2.0,
		step        = 0.1,
		precision   = 3
	)
	use_cycles : BoolProperty(
		name        = "Use Cycles Modifier",
		description = "Use fcurve cycles modifier",
		default     = True
		)
	clear_anim : BoolProperty(
		name        = "Clear Animation",
		description = "Clear previous animations",
		default     = True
		)
	reset_transform : BoolProperty(
		name        = "Reset Transform",
		description = "Reset transformation of selected objects",
		default     = True
		)
	rem_parent : BoolProperty(
		name        = "Remove Initial Parent",
		description = "Unparent from current parent object",
		default     = False
		)
	add_parent : BoolProperty(
		name        = "Add Parent Empty",
		description = "Add parent empty to objects",
		default     = False
		)
	face_normal : BoolProperty(
		name        = "Align To Picked Normal",
		description = "Align parent empty to normal vector",
		default     = False
		)
	even_frames : BoolProperty(
		name        = "Even Frames",
		description = "Randomize only from even divisors of max frame",
		default     = False
		)
	coll_name : StringProperty(
		name        = "Collections",
		description = "Collection objects for scatter"
		)
	collections : CollectionProperty(type=PropertyGroup)
	coll_seed : IntProperty(
		name        = "Object Seed",
		description = "Randomize seed for collection objects",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	precision : FloatProperty(
		name        = "Precision",
		description = "Number of possible frames per spline",
		default     = 0.1,
		min         = 0.001,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
	)
	limit_frames : IntProperty(
		name        = "Limit Frames",
		description = "Frame limit for the path animation",
		default     = 250,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	offset_min : IntProperty(
		name        = "Min",
		description = "Minimum frame offset (Lower is faster)",
		default     = 10,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	offset_max : IntProperty(
		name        = "Max",
		description = "Maximum frame offset  (Lower is faster)",
		default     = 50,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	offset_seed : IntProperty(
		name        = "Offset Seed",
		description = "Randomized seed for frame offset",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "OBJECT" \
			and context.active_object in context.selected_objects

	def set_mod_vis(self, obj, list_mod=[], hide=True):

		if hide:
			hidden = []
			for m in obj.modifiers:
				if m.type != 'MIRROR' \
					and m.show_viewport:
					m.show_viewport = False
					hidden.append(m)

			return hidden
		else:
			for m in obj.modifiers:
				if m in list_mod:
					m.show_viewport = True

	def clear_parent(self, child):

		matrix_copy = child.matrix_world.copy()
		child.parent = None
		child.matrix_world = matrix_copy

	def set_parent(self, context, list_obj):

		act_obj = context.active_object
		props = context.scene.rflow_props

		empty = bpy.data.objects.new("RA_Parent", None)

		empty.empty_display_size = self.size_empty
		empty.empty_display_type = self.type_empty

		empty.rotation_euler = act_obj.rotation_euler.copy()

		global_loc = act_obj.matrix_world.translation if self.loc_empty == 'ACTIVE' \
			else context.scene.cursor.location if self.loc_empty == 'CURSOR' \
			else sum([o.matrix_world.translation for o in list_obj], Vector()) / len(list_obj)

		target_local_loc = empty.matrix_world.inverted() @ global_loc
		empty.matrix_world.translation = global_loc

		for col in act_obj.users_collection:
			if not empty.name in col.objects: col.objects.link(empty)

		for o in list_obj:
			old_parent = o.parent

			self.clear_parent(o)
			reset_transforms(o, False, self.reset_transform, self.reset_transform)

			o.parent = empty
			o.matrix_parent_inverse.translation -= target_local_loc

			if old_parent is not None \
				and not old_parent.children \
				and old_parent.type == 'EMPTY': remove_obj(old_parent)

		if self.face_normal:
			normal = props.normal_guide
			if normal != Vector:
				quat = normal.to_track_quat('Z', 'Y')
				mat = quat.to_matrix().to_4x4()
				rot = mat.to_3x3().normalized()
				empty.rotation_euler = rot.to_euler()

		if not empty.children: remove_obj(empty)

	def even_divisors(self, start_frame, end_frame):

		list_frame = []

		for i in range(start_frame, end_frame+1):
			if i > 0 \
				and end_frame % i == 0:
				if i > start_frame:
					list_frame.append(i)

		return sorted(list_frame)

	def execute(self, context):

		def create_animation_data(o):

			o.animation_data_create()
			o.animation_data.action = bpy.data.actions.new(name="RandomAction")

		if self.anim_type == 'AXIS':
			list_obj = []
			for i, o in enumerate(context.selected_objects):
				if self.rem_parent:
					self.clear_parent(o)

				if o.type == 'MESH':
					if self.pivot == 'GEOMETRY':
						list_mod = self.set_mod_vis(o)
						o_data = get_eval_mesh(o)
						set_origin(o, sum([o.matrix_world @ v.co for v in o_data.vertices], Vector()) / len(o_data.vertices))
						self.set_mod_vis(o, list_mod, False)

					if self.pivot == 'CURSOR':
						set_origin(o, context.scene.cursor.location)

				frames = [self.start_frame, self.end_frame]
				frames.sort()

				if self.clear_anim:
					reset_transforms(o, False, self.reset_transform, self.reset_transform)
					o.animation_data_clear()
					create_animation_data(o)
				else:
					if not o.animation_data \
						or not o.animation_data.action:
						create_animation_data(o)

				dpath = "rotation_euler" if self.dpath == 'ROTATE' else 'location' \
					if self.dpath == 'MOVE' else 'scale'

				for n, axis in enumerate(self.axis):
					fcurve = o.animation_data.action.fcurves.find(dpath, index=int(axis))

					if fcurve:
						o.animation_data.action.fcurves.remove(fcurve)

					if self.anim_seed > 1:
						seed(self.anim_seed + i)

						rot_deg = [self.rot_min, self.rot_max]; shuffle(rot_deg)
						loc_sca = [self.val_min, self.val_max]; shuffle(loc_sca)

						rot1 = rot_deg[0] if self.even_frames else uniform(self.rot_min, self.rot_max)
						val1 = loc_sca[0] if self.even_frames else uniform(self.val_min, self.val_max)

						kval1 = rot1 if self.dpath == 'ROTATE' \
							else o.matrix_world.translation[int(axis)] + val1 \
							if self.dpath == 'MOVE' else val1
					else:
						kval1 = self.rot_min if self.dpath == 'ROTATE' \
							else o.matrix_world.translation[int(axis)] + min(self.val_min, self.val_max) \
							if self.dpath == 'MOVE' else min(self.val_min, self.val_max)

					fcurve = o.animation_data.action.fcurves.new(data_path=dpath, index=int(axis))

					k1 = fcurve.keyframe_points.insert(frame=0 if self.even_frames else frames[0], value=kval1)
					k1.interpolation = "LINEAR"

					if self.frame_seed > 1:
						use_uneven = True

						seed(self.frame_seed + (i+n))

						if self.even_frames:
							list_frames = self.even_divisors(frames[0], frames[1])
							if list_frames:
								end_frame = choice(list_frames)
								use_uneven = False

						if use_uneven:
							end_frame = randint(frames[0], frames[1])
					else:
						end_frame = frames[1]

					if self.anim_seed > 1:
						seed((self.anim_seed + 1) + i)

						rot2 = rot_deg[1] if self.even_frames else uniform(self.rot_min, self.rot_max)
						val2 = loc_sca[1] if self.even_frames else uniform(self.val_min, self.val_max)

						kval2 = rot2 if self.dpath == 'ROTATE' \
							else o.matrix_world.translation[int(axis)] + val2 \
							if self.dpath == 'MOVE' else val2
					else:
						kval2 = self.rot_max if self.dpath == 'ROTATE' \
							else o.matrix_world.translation[int(axis)] + max(self.val_min, self.val_max) \
							if self.dpath == 'MOVE' else max(self.val_min, self.val_max)

					k2 = fcurve.keyframe_points.insert(frame=end_frame,	value=kval2)
					k2.interpolation = "LINEAR"

					if self.use_cycles:
						m = fcurve.modifiers.new('CYCLES')
						m.mode_before = self.mode
						m.mode_after = self.mode

				list_obj.append(o)

			if self.add_parent and list_obj:
				self.set_parent(context, list_obj)
		else:
			collection = self.coll_name
			objs = bpy.data.collections.get(collection)
			if objs:
				anim_objs = [o for o in bpy.data.collections.get(collection).all_objects \
					if o.type == 'MESH']
				if anim_objs:
					act_obj = context.active_object

					def set_data_origin(obj, data, origin):

						pivot = obj.matrix_world.inverted() @ origin
						data.transform(Matrix.Translation(-pivot))

					if act_obj.type != 'CURVE':
						sel_objs = context.selected_objects

						temp_mesh = bpy.data.meshes.new(".temp")
						bm = bmesh.new()

						sel_objs = sorted(sel_objs, key=lambda o: o.name)
						for o in sel_objs:
							o.update_from_editmode()
							o_data = get_eval_mesh(o).copy()
							set_data_origin(o, o_data, Vector())
							bm.from_mesh(o_data)
							bpy.data.meshes.remove(o_data)

						bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.select], context='EDGES')
						bmesh.ops.delete(bm, geom=bm.faces, context='FACES_ONLY')

						bm.to_mesh(temp_mesh)
						bm.free()

						anim_curve = bpy.data.objects.new("AnimPath", temp_mesh)
						context.scene.collection.objects.link(anim_curve)

						select_isolate(anim_curve)
						bpy.ops.object.convert(target='CURVE')
					else:
						anim_curve = act_obj

					points_on_curve = []
					for n, spline in enumerate(anim_curve.data.splines):
						spline.type = 'BEZIER'
						bez_points = spline.bezier_points
						bez_len = len(bez_points)

						i_range = range(1, bez_len, 1)
						for i in i_range:
							curr_point = bez_points[i-1]
							next_point = bez_points[i]

							delta = (curr_point.co - next_point.co).length
							count = int(max(1, delta/self.precision)) + 1

							calc_points = geometry.interpolate_bezier(
								curr_point.co,
								curr_point.handle_right,
								next_point.handle_left,
								next_point.co,
								count)

							if i != bez_len - 1:
								calc_points.pop()

							points_on_curve += calc_points

					total_points = len(points_on_curve)
					p_range = range(1, total_points, 1)

					for x, o in enumerate(anim_objs):
						dup = duplicate_obj("Path_Obj", o, get_eval=True, link=True)
						dup.rotation_mode = 'QUATERNION'

						seed(self.offset_seed + x)
						min_offset = min(self.offset_min, self.offset_max)
						max_offset = max(self.offset_min, self.offset_max)
						fnum = randint(min_offset, max_offset)

						fr = fnum

						for i in p_range:
							if i % fnum == 0 or i == 1 or i == total_points-1:
								p1 = points_on_curve[i-1]
								p2 = points_on_curve[i]
								tangent = p1 - p2
								tangent.normalize()

								fr += 1

								dup.location = p1 if act_obj.type != 'CURVE' else act_obj.matrix_world @ p1
								dup.keyframe_insert(data_path='location', frame=fr)

								rotation = tangent.to_track_quat('Y', 'Z')
								dup.rotation_quaternion = rotation
								dup.keyframe_insert(data_path='rotation_quaternion', frame=fr)

							if fr >= self.limit_frames: break

						fcurves = dup.animation_data.action.fcurves
						for f in fcurves:
							m = f.modifiers.new('CYCLES')
							m.mode_before = "REPEAT"
							m.mode_after = "REPEAT"

		return {"FINISHED"}

	def draw(self, context):

		act_obj = context.active_object

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		row.row(align=True).prop(self, "anim_type", expand=True)
		if self.anim_type == 'AXIS':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Animation:")
			row.row(align=True).prop(self, "dpath", expand=True)
			if self.use_cycles:
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Mode:")
				row.row(align=True).prop(self, "mode", expand=True)
			if act_obj.type == 'MESH':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Pivot:")
				row.row(align=True).prop(self, "pivot", expand=True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Axis:")
			row.row(align=True).prop(self, "axis", expand=True)
			row = col.row().split(factor=0.27, align=True)
			row.label(text=" ")
			row.label(text=(" " * 2) + "(shift+click to add multiple or remove)")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Frames:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "start_frame")
			split.row(align=True).prop(self, "end_frame")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Seed:")
			row.row(align=True).prop(self, "frame_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			if self.dpath == 'ROTATE':
				row.label(text="Rotation:")
				split = row.split(factor=0.5, align=True)
				split.row(align=True).prop(self, "rot_min")
				split.row(align=True).prop(self, "rot_max")
			else:
				if self.dpath == 'MOVE':
					txt = "Move:"
				elif self.dpath == 'SCALE': txt = "Scale:"
				row.label(text=txt)
				split = row.split(factor=0.5, align=True)
				split.row(align=True).prop(self, "val_min")
				split.row(align=True).prop(self, "val_max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Seed:")
			row.row(align=True).prop(self, "anim_seed", text="")
			if self.add_parent:
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Empty Type:")
				row.row(align=True).prop(self, "type_empty", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Location:")
				row.row(align=True).prop(self, "loc_empty", expand=True)
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Size:")
				row.row(align=True).prop(self, "size_empty", text="")
			col.separator(factor=0.5)
			flow = col.column_flow(columns=2, align=True)
			flow.prop(self, "use_cycles")
			flow.prop(self, "clear_anim")
			flow.prop(self, "add_parent")
			flow.prop(self, "reset_transform")
			flow.prop(self, "even_frames")
			flow.prop(self, "rem_parent")
			if self.add_parent: col.prop(self, "face_normal")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Collection:")
			row.prop_search(
				self,
				"coll_name",
				self,
				"collections",
				text="",
				icon = "OUTLINER_COLLECTION"
				)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Precision:")
			row.row(align=True).prop(self, "precision", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Limit Frames:")
			row.row(align=True).prop(self, "limit_frames", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Offset:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "offset_min")
			split.row(align=True).prop(self, "offset_max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Offset Seed:")
			row.row(align=True).prop(self, "offset_seed", text="")

	def invoke(self, context, event):

		self.frame_seed = 1
		self.value_seed = 1
		self.axis = set()
		self.add_parent = False
		self.coll_name = ""
		self.collections.clear()

		for c in bpy.data.collections:
			newListItem = self.collections.add()
			newListItem.name = c.name

		prefs = context.preferences.addons[__package__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_bevel_node(Operator):
	'''Adds and edit a bevel shader node to the active material of selected objects'''
	bl_idname = 'bvl_node.rflow'
	bl_label = 'Add Bevel Node'
	bl_options = {'REGISTER', 'UNDO'}

	mode : EnumProperty(
		name = 'Mode',
		description = "Determines whether to replace or add the bevel node",
		items = (
			('ADD', 'Add','Add the bevel node to the normal links of the BSDF shader'),
			('REPLACE', 'Replace','Disconnect all normal links from the BSDF shader and replace it with the bevel node')),
		default = 'ADD'
		)
	mat_mode : EnumProperty(
		name = 'Material',
		description = "Add bevel node to active material or all materials in selected objects",
		items = (
			('ACTIVE', 'Active','Add the bevel node to the active material'),
			('ALL', 'All','Add the bevel node to all materials')),
		default = 'ACTIVE'
		)
	samples : IntProperty(
		name        = "Samples",
		description = "Number of rays to trace per shader evaluation",
		default     = 4,
		min         = 2,
		soft_max    = 16,
		step        = 1
		)
	radius : FloatProperty(
		name        = "Radius",
		description = "Bevel offset or width",
		default     = 0.05,
		min         = 0,
		soft_max    = 1000,
		step        = 0.1,
		precision   = 3
		)
	nloc : FloatVectorProperty(
		name        = "Location",
		description = "Location of bevel node when added to material shaders",
		default     = (200,200),
		size        = 2,
		soft_min    = -1000,
		soft_max    = 1000,
		step        = 10.0,
		precision   = 3,
		subtype		= "XYZ"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None

	def bvl_inputs(self, bvl_node, val1, val2):

		bvl_node.samples = val1
		bvl_node.inputs[0].default_value = val2

	def get_link(self, ntree, node):

		from_node = None
		to_node = None

		for l in ntree.links:
			if l.to_node == node \
				and l.to_socket.name == 'Normal':
				from_node = l.from_node
			if l.from_node == node \
				and l.from_socket.name == 'Normal':
				to_node = l.to_node

		return from_node, to_node

	def add_bevel(self, ntree, link_to):

		bvl_node = ntree.nodes.new('ShaderNodeBevel')
		self.bvl_inputs(bvl_node, self.samples, self.radius)
		ntree.links.new(bvl_node.outputs[0], link_to.inputs['Normal'])

		bvl_node.location.x = link_to.location.x - self.nloc[0]
		bvl_node.location.y = link_to.location.y - self.nloc[1]

		return bvl_node

	def execute(self, context):

		list_mat = set()

		for o in context.selected_objects:
			mat = [o.active_material] if self.mat_mode == 'ACTIVE' else o.data.materials
			for m in mat:
				if not m in list_mat:
					ntree = m.node_tree

					for node in ntree.nodes:
						if node.type == 'BEVEL':
							bvl_node = node
							from_node, to_node = self.get_link(ntree, bvl_node)
							ntree.nodes.remove(bvl_node)
							if from_node and to_node:
								ntree.links.new(from_node.outputs[0], to_node.inputs['Normal'])

					for node in ntree.nodes:
						if node.type.find("BSDF") != -1:
							for inputs in node.inputs:
								if inputs.name == "Normal":
									if self.mode == 'ADD':
										from_node, _ = self.get_link(ntree, node)
										if from_node:
											bvl_node = self.add_bevel(ntree, node)
											ntree.links.new(from_node.outputs[0], bvl_node.inputs['Normal'])
										else:
											self.add_bevel(ntree, node)
									else:
										self.add_bevel(ntree, node)

									break

					list_mat.add(m)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Mode:")
		row.row(align=True).prop(self, "mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material:")
		row.row(align=True).prop(self, "mat_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Samples:")
		row.row(align=True).prop(self, "samples")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Radius:")
		row.row(align=True).prop(self, "radius")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Location:")
		row.row(align=True).prop(self, "nloc", text="")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_normal_picker(Operator):
	'''Pick normal data from active object'''
	bl_idname = 'n_picker.rflow'
	bl_label = 'Normal Picker'
	bl_options = {'REGISTER', 'UNDO'}

	def pick_material(self, context, co):

		hit, normal, face_index, obj = scene_ray_hit(context, co, ray_obj=self.pick_obj, scene_ray=True)

		return hit, normal, face_index, obj

	def clear_mesh_list(self):

		for o in bpy.data.meshes:
			if o not in self.mesh_list \
				and o.users == 0:
				bpy.data.meshes.remove(o)

	def clear_op(self, context):

		context.window.cursor_modal_restore()
		remove_obj(self.pick_obj)
		self.clear_mesh_list()

		self.orig_obj.select_set(True)
		context.view_layer.objects.active = self.orig_obj

	def modal(self, context, event):

		sce = context.scene
		props = sce.rflow_props

		self.mouse_co = event.mouse_region_x, event.mouse_region_y
		addon_prefs = bpy.context.preferences.addons[__package__].preferences

		if event.type in {
			'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
			'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_6',
			'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_5'}:
			return {'PASS_THROUGH'}

		if event.type == 'LEFTMOUSE':
				if event.value == 'PRESS':
					hit, normal, index, obj = self.pick_material(context, self.mouse_co)

					if hit:
						mesh_eval = get_eval_mesh(obj)
						bm = bmesh.new()
						bm.from_mesh(mesh_eval)

						bm.faces.ensure_lookup_table()
						props.normal_guide = bm.faces[index].normal @ context.active_object.matrix_world.inverted()

						bm.free()
					else:
						props.normal_guide = context.region_data.view_rotation @ Vector((0,0,1))
						self.report({'WARNING'}, ("Face normal not found. Using view direction instead."))

					self.clear_op(context)

					return {'FINISHED'}

		if event.type in {'RIGHTMOUSE', 'ESC'}:
			self.clear_op(context)

			return {'CANCELLED'}

		return {'RUNNING_MODAL'}

	def invoke(self, context, event):

		if context.area.type == 'VIEW_3D':
			args = (self, context)

			obj = self.orig_obj = context.active_object
			self.mesh_list = [o for o in bpy.data.meshes]

			self.pick_obj = duplicate_obj('pick_obj', obj, get_eval=True, link=False)
			self.mouse_co = []

			context.window.cursor_modal_set("EYEDROPPER")
			context.window_manager.modal_handler_add(self)

			return {'RUNNING_MODAL'}
		else:
			self.report({'WARNING'}, "View3D not found, cannot run operator.")

			return {'CANCELLED'}

class OBJECT_OT_make_flanges(Operator):
	'''Generate flanges and couplings for curve objects'''
	bl_idname = 'make_flanges.rflow'
	bl_label = 'Flanges/Couplings'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	mesh_type : EnumProperty(
		name = 'Type',
		description = "Type",
		items = (
			('BASIC', 'Basic',''),
			('MESH', 'Mesh',''),
			('CUSTOM', 'Custom',''),
			('COLLECTION', 'Collection','')),
		default = 'BASIC'
		)
	mesh_name : StringProperty(
		name        = "Mesh",
		description = "Use mesh object as cap design"
		)
	meshes : CollectionProperty(type=PropertyGroup)
	import_name : StringProperty(
		name        = "Import Mesh",
		description = "Use selected for cap design"
		)
	import_meshes : CollectionProperty(type=PropertyGroup)
	coll_name : StringProperty(
		name        = "Collections",
		description = "Collection objects for scatter"
		)
	collections : CollectionProperty(type=PropertyGroup)
	coll_seed : IntProperty(
		name        = "Object Seed",
		description = "Randomize seed for collection objects",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	amount : IntProperty(
		name        = "Amount",
		description = "Number of flanges/couplings to generate",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	spacing : FloatProperty(
		name        = "Spacing",
		description = "Edge spacing to determine the number of flanges/couplings to make",
		default     = 1,
		min			= 0,
		soft_min    = 0.1,
		soft_max    = 10.0,
		step        = 0.01,
		precision   = 3
		)
	cap_offset : FloatProperty(
		name        = "Caps",
		description = "Offset generated cap flanges/couplings",
		default     = 0,
		soft_min	= -100.0,
		soft_max	= 100.0,
		step        = 0.01,
		precision   = 3
		)
	bod_offset : FloatProperty(
		name        = "Body",
		description = "Offset generated body flanges/couplings",
		default     = 0,
		soft_min	= -100.0,
		soft_max	= 100.0,
		step        = 0.01,
		precision   = 3
		)
	radius : FloatProperty(
		name        = "Radius",
		description = "Radius of flanges/couplings",
		default     = 0.05,
		min			= 0,
		step        = 0.01,
		precision   = 3
		)
	rot_z : FloatProperty(
		name        = "Rotation",
		description = "Rotation of flanges/couplings",
		default     = 0,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	rot_seed : IntProperty(
		name        = "Rotation Seed",
		description = "Randomize seed for rotation of flanges/couplings",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	depth : FloatProperty(
		name        = "Depth",
		description = "Depth of flanges/couplings",
		default     = 0.005,
		min			= 0,
		step        = 0.01,
		precision   = 3
		)
	segment : IntProperty(
		name        = "Segment",
		description = "Total segment of flanges/couplings",
		default     = 6,
		min         = 3,
		max         = 500
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	limit : EnumProperty(
		name = 'Limit',
		description = "Limit to caps, body or none",
		items = (
			('NONE', 'None',''),
			('CAPS', 'Caps',''),
			('BODY', 'Body','')),
		default = 'NONE'
		)
	even_count : BoolProperty(
		name        = "Even Count",
		description = "Even count of flanges/couplings along tube body",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "OBJECT" \
			and context.active_object.type == "CURVE"

	def make_fittings(self, curve_objs):

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")

		def add_fittings(curve, bm, pos, tangent, idx):

			context = bpy.context
			type = self.mesh_type

			cont = True

			props = context.scene.rflow_props

			dim = context.active_object.dimensions.copy()
			mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

			def orient_to_curve(bm_cont, listv=[]):

				if not listv: listv = bm_cont.verts

				if type != 'BASIC':
					bmesh.ops.scale(
						bm_cont,
						vec     = Vector(tuple([self.radius * mdv] * 3)),
						space   = Matrix(),
						verts   = listv
						)

				z = self.rot_z
				if self.rot_seed > 1:
					seed(self.rot_seed + idx)
					z = uniform(360-z, z)

				rot_axis = [0 , 0, z]

				bmesh.ops.rotate(
					bm_cont,
					verts   = listv,
					cent    = Vector(),
					matrix  = Euler(Vector(rot_axis)).to_matrix()
					)

				bmesh.ops.translate(
						bm_cont,
						verts   = listv,
						vec     = pos
						)

				quat = tangent.to_track_quat('-Z', 'Y')
				mat = curve.matrix_world @ quat.to_matrix().to_4x4()
				rot = mat.to_3x3().normalized()

				_, orig_rot, _ = curve.matrix_world.decompose()
				bmesh.ops.rotate(
						bm_cont,
						verts   = listv,
						cent    = pos,
						matrix  = orig_rot.to_matrix().inverted() @ rot
						)

			def orient_bmesh_data(data):

				bm_temp = bmesh.new()
				temp_mesh = bpy.data.meshes.new(".temp")
				bm_temp.from_mesh(data)

				orient_to_curve(bm_temp)

				bm_temp.to_mesh(temp_mesh)
				bm_temp.free()

				bm.from_mesh(temp_mesh)
				bpy.data.meshes.remove(temp_mesh)

			if type == 'BASIC':
				listv = bmesh.ops.create_cone(
					bm,
					cap_ends    = True,
					segments    = self.segment,
					radius1     = self.radius * mdv,
					radius2     = self.radius * mdv,
					depth       = self.depth
					)['verts']

				orient_to_curve(bm, listv)

			if type == 'MESH':
				mesh = bpy.data.objects.get(self.mesh_name)
				if mesh: orient_bmesh_data(mesh.data)

			if type == 'CUSTOM':
				if self.import_name:
					file_name = self.import_name
					custom_data = bpy.data.meshes.get(file_name + "_rflow_mesh", None)
					if not custom_data:
						if file_name.find(".stl") == -1: file_name += ".stl"
						filepath = os.path.join(os.path.dirname(
							os.path.abspath(__file__)), "./flanges/" + file_name)

						try:
							bpy.ops.import_mesh.stl(filepath=filepath, global_scale=1.0)

							import_obj = context.selected_objects[0]
							custom_data = import_obj.data
							custom_data.name += "_rflow_mesh"

							curve.select_set(True)
							context.view_layer.objects.active = curve

							bpy.data.objects.remove(import_obj)
						except:
							self.report({'ERROR'}, 'STL Format add-on must be enabled!')
							cont = False

					if custom_data: orient_bmesh_data(custom_data)

			if type == 'COLLECTION':
				collection = bpy.data.collections.get(self.coll_name)
				if collection:
					mesh_objs = [o for o in bpy.data.collections.get(self.coll_name).all_objects \
						if o.type == 'MESH']
					if mesh_objs:
						seed(self.coll_seed + idx)
						rand_obj = choice(mesh_objs)
						coll_obj = bpy.data.objects.get(rand_obj.name)

						orient_bmesh_data(coll_obj.data)

			return cont

		cont = True

		for o in curve_objs:
			curve = o
			for spline in curve.data.splines:
				save_type = spline.type
				spline.type = 'BEZIER'

				bez_points = spline.bezier_points
				bez_len = len(bez_points)

				if bez_len >= 2:
					if not self.limit in ['BODY']:
						cap_points = [[bez_points[0], bez_points[1]], \
								[bez_points[-1], bez_points[-2]]]
						for n, i in enumerate(cap_points):
							p1 = i[0].co; p2 = i[1].co
							tangent = p1 - p2
							tangent.normalize()
							p3 = p1 - (tangent * self.cap_offset)
							cont = add_fittings(curve, bm, p3, tangent, n)
							if not cont: break

					if not cont: break

					if not self.limit in ['CAPS']:
						points_on_curve = []; total_length = []
						i_range = range(1, bez_len, 1)
						for i in i_range:
							curr_point = bez_points[i-1]
							next_point = bez_points[i]

							delta = (curr_point.co - next_point.co).length
							count = int(max(1, delta/0.01)) + 1

							calc_points = geometry.interpolate_bezier(
								curr_point.co,
								curr_point.handle_right,
								next_point.handle_left,
								next_point.co,
								count)

							if i != bez_len - 1:
								calc_points.pop()

							points_on_curve += calc_points
							total_length.append(delta)

						spline.type = save_type

						total_points = len(points_on_curve)
						p_range = range(1, total_points, 1)

						if not self.even_count:
							tl = ceil(sum(total_length) / max(0.01, self.spacing))
							fnum = int(ceil(total_points/tl))
						else:
							fnum = int(ceil(total_points/(self.amount + 1)))

						for i in p_range:
							x = i + int(ceil(total_points*self.bod_offset))
							if x % fnum == 0:
								p1 = points_on_curve[i-1]
								p2 = points_on_curve[i]
								tangent = p1 - p2
								tangent.normalize()
								cont = add_fittings(curve, bm, p1, tangent, x)
								if not cont: break

		bm.to_mesh(temp_mesh)
		bm.free()

		obj = curve_objs[0]
		new_obj = bpy.data.objects.new(filter_name(obj, "_Flanges"), temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc

		new_obj.data.set_sharp_from_angle(angle=radians(30))
		new_obj.data.update()

		assign_mat(self, obj, new_obj, self.mat_index)

		set_parent(obj, new_obj)

		copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

	def execute(self, context):

		act_obj = context.active_object

		if act_obj: act_obj.select_set(True)

		curve_objs = []
		for o in context.selected_objects:
			if o.type == 'CURVE':
				curve_objs.append(o)

		self.make_fittings(curve_objs)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		flow = row.column_flow(columns=2, align=True)
		flow.prop(self, "mesh_type", expand=True)
		if self.mesh_type == 'MESH':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mesh:")
			row.prop_search(
				self,
				"mesh_name",
				self,
				"meshes",
				text="",
				icon = "MESH_DATA"
				)
		if self.mesh_type == 'CUSTOM':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Import Mesh:")
			row.prop_search(
				self,
				"import_name",
				self,
				"import_meshes",
				text="",
				icon = "IMPORT"
				)
		if self.mesh_type == 'COLLECTION':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Collection:")
			row.prop_search(
				self,
				"coll_name",
				self,
				"collections",
				text="",
				icon = "OUTLINER_COLLECTION"
				)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Object Seed:")
			row.row(align=True).prop(self, "coll_seed", text="")
		if self.even_count:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Amount:")
			row.row(align=True).prop(self, "amount", text="")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Spacing:")
			row.row(align=True).prop(self, "spacing", text="")
		if self.mesh_type != 'BASIC':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Radius:")
			row.row(align=True).prop(self, "radius", text="")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Radius:")
			row.row(align=True).prop(self, "radius", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Depth:")
			row.row(align=True).prop(self, "depth", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Segments:")
			row.row(align=True).prop(self, "segment", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cap_offset")
		split.row(align=True).prop(self, "bod_offset")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "rot_z", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation Seed:")
		row.row(align=True).prop(self, "rot_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limit:")
		row.row(align=True).prop(self, "limit", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		col.prop(self, "even_count")

	def invoke(self, context, event):

		obj = context.active_object

		self.mesh_name = ""
		self.meshes.clear()
		self.import_name = ""
		self.import_meshes.clear()
		self.coll_name = ""
		self.collections.clear()

		path =  os.path.join(os.path.dirname(
			os.path.abspath(__file__)), "./flanges/")
		files = os.listdir(path)

		if files:
			for f in files:
				newListItem = self.import_meshes.add()
				file_name = f.split(".")[0]
				newListItem.name = file_name

		for c in bpy.data.collections:
			newListItem = self.collections.add()
			newListItem.name = c.name

		for o in context.scene.objects:
			if o.type == 'MESH' and \
				o != obj:
				newListItem = self.meshes.add()
				newListItem.name = o.name

		prefs = context.preferences.addons[__package__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_panel_screws(Operator):
	'''Generate panel screws on selected island faces'''
	bl_idname = 'panel_screws.rflow'
	bl_label = 'Panel Screws'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	mesh_type : EnumProperty(
		name = 'Type',
		description = "Type",
		items = (
			('BASIC', 'Basic',''),
			('MESH', 'Mesh',''),
			('CUSTOM', 'Custom',''),
			('COLLECTION', 'Collection','')),
		default = 'BASIC'
		)
	mesh_name : StringProperty(
		name        = "Mesh",
		description = "Use mesh object as cap design"
		)
	meshes : CollectionProperty(type=PropertyGroup)
	import_name : StringProperty(
		name        = "Import Mesh",
		description = "Use selected for cap design"
		)
	import_meshes : CollectionProperty(type=PropertyGroup)
	coll_name : StringProperty(
		name        = "Collections",
		description = "Collection objects for scatter"
		)
	collections : CollectionProperty(type=PropertyGroup)
	coll_seed : IntProperty(
		name        = "Object Seed",
		description = "Randomize seed for collection objects",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Margin of screws from island boundary",
		default     = 0.01,
		step        = 0.1,
		precision   = 3
		)
	offset : FloatProperty(
		name        = "Offset",
		description = "Offset generated screws",
		default     = 0,
		step        = 0.1,
		precision   = 3
		)
	origin : EnumProperty(
		name = 'Origin',
		items = (
			('FACES', 'Faces','Screws are generated on face vertices'),
			('VERTS', 'Verts','Screws are generated for each selected verts')),
		default = 'FACES'
		)
	mode : EnumProperty(
		name = 'Mode',
		items = (
			('ANGLE', 'Angle','Screws are generated based on max angle threshold of corner verts'),
			('VERTS', 'All Verts','Screws are generated for each boundary verts')),
		default = 'ANGLE'
		)
	threshold : FloatProperty(
		name        = "Max Angle",
		description = "Maximum vert angle threshold for screws to appear",
		default     = radians(30),
		min         = radians(0),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	spacing : FloatProperty(
		name        = "Spacing",
		description = "Edge spacing to determine the number of screws to make",
		default     = 0.5,
		min			= 0,
		soft_min    = 0.01,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 3
		)
	radius : FloatProperty(
		name        = "Radius",
		description = "Radius of screws",
		default     = 0.025,
		min			= 0,
		step        = 0.01,
		precision   = 3
		)
	rot_z : FloatProperty(
		name        = "Rotation",
		description = "Rotation of flanges/couplings",
		default     = 0,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	rot_seed : IntProperty(
		name        = "Rotation Seed",
		description = "Randomize seed for rotation of flanges/couplings",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	depth : FloatProperty(
		name        = "Depth",
		description = "Depth of flanges/couplings",
		default     = 0.025,
		min			= 0,
		step        = 0.01,
		precision   = 3
		)
	segment : IntProperty(
		name        = "Segments",
		description = "Total segment of flanges/couplings",
		default     = 6,
		min         = 3,
		max         = 500
		)
	bvl_offset : FloatProperty(
		name        = "Offset",
		description = "Bevel offset/width",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.01,
		precision   = 4
	)
	bvl_seg : IntProperty(
		name        = "Segments",
		description = "Bevel segments",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
	)
	birth_perc : FloatProperty(
		name        = "Perc",
		description = "Percentage to determine if screw appears at this point",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 100,
		subtype     = "PERCENTAGE"
		)
	birth_seed : IntProperty(
		name        = "Seed",
		description = "Randomize seed for birth of screws",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	per_face : BoolProperty(
		name        = "Per Face",
		description = "Generate screws per face instead of selection boundary",
		default     = False
		)
	use_split : BoolProperty(
		name        = "Split Sharp",
		description = "Split sharp edges using angle threshold ",
		default     = False
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	tagged_only : BoolProperty(
		name        = "Tagged Verts Only",
		description = "Generate screws from tagged verts only",
		default     = False
		)
	use_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def add_screw(self, context, obj, bm, pos, normal, idx):

		M = obj.matrix_world

		cont = True

		props = context.scene.rflow_props

		dim = obj.dimensions.copy()
		mdv = sum(d for d in dim)/len(dim) * props.scale_factor if props.dynamic_scale else 1

		bm_temp = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")

		mesh_type = self.mesh_type
		save_mode = obj.mode

		if mesh_type == 'BASIC':
			listv = bmesh.ops.create_cone(
				bm_temp,
				cap_ends    = True,
				segments    = self.segment,
				radius1     = self.radius * mdv,
				radius2     = self.radius * mdv,
				depth       = self.depth
				)['verts']

			faces = sorted(bm_temp.faces, key=lambda f: (M @ f.calc_center_median())[2])

			if faces:
				basis = (M @ faces[-1].calc_center_median())[2]
				top_face = [f for f in faces if abs((M @ f.calc_center_median())[2] - basis) < 0.0001]

				bmesh.ops.bevel(
					bm_temp,
					geom            = [e for e in top_face[0].edges],
					offset          = self.bvl_offset,
					offset_type     = 'OFFSET',
					segments        = self.bvl_seg,
					profile         = 0.5,
					affect			= 'EDGES',
					clamp_overlap	= True
					)

		if mesh_type == 'MESH':
			mesh = bpy.data.objects.get(self.mesh_name)
			if mesh: bm_temp.from_mesh(mesh.data)

		if mesh_type == 'CUSTOM':
			if self.import_name:
				file_name = self.import_name
				custom_data = bpy.data.meshes.get(file_name + "_rflow_mesh", None)
				if not custom_data:
					if file_name.find(".stl") == -1: file_name += ".stl"
					filepath = os.path.join(os.path.dirname(
						os.path.abspath(__file__)), "./screws/" + file_name)

					try:
						bpy.ops.import_mesh.stl(filepath=filepath, global_scale=1.0)

						import_obj = context.selected_objects[0]
						custom_data = import_obj.data
						custom_data.name += "_rflow_mesh"

						obj.select_set(True)
						context.view_layer.objects.active = obj
						bpy.ops.object.mode_set(mode=save_mode)

						bpy.data.objects.remove(import_obj)
					except:
						self.report({'ERROR'}, 'STL Format add-on must be enabled!')
						cont = False

				if custom_data:
					bm_temp.from_mesh(custom_data)

		if mesh_type == 'COLLECTION':
			collection = self.coll_name
			objs = bpy.data.collections.get(collection)
			if objs:
				mesh_objs = [o for o in bpy.data.collections.get(collection).all_objects \
					if o.type == 'MESH']
				if mesh_objs:
					seed(self.coll_seed + idx)
					rand_obj = choice(mesh_objs)
					coll_obj = bpy.data.objects.get(rand_obj.name)

					if coll_obj:
						bm_temp.from_mesh(coll_obj.data)

		if mesh_type != 'BASIC':
			bmesh.ops.scale(
				bm_temp,
				vec     = Vector(tuple([self.radius * mdv] * 3)),
				space   = Matrix(),
				verts   = bm_temp.verts
				)

		z = self.rot_z
		if self.rot_seed > 1:
			seed(self.rot_seed + idx)
			z = uniform(360-z, z)

		rot_axis = [0 , 0, z]

		bmesh.ops.rotate(
			bm_temp,
			verts   = bm_temp.verts,
			cent    = Vector(),
			matrix  = Euler(Vector(rot_axis)).to_matrix()
			)

		bmesh.ops.translate(
				bm_temp,
				verts   = bm_temp.verts,
				vec     = pos
				)

		quat = normal.to_track_quat('Z', 'Y')
		mat = obj.matrix_world @ quat.to_matrix().to_4x4()
		rot = mat.to_3x3().normalized()

		_, orig_rot, _ = obj.matrix_world.decompose()
		bmesh.ops.rotate(
				bm_temp,
				verts   = bm_temp.verts,
				cent    = pos,
				matrix  = orig_rot.to_matrix().inverted() @ rot
				)

		bm_temp.to_mesh(temp_mesh)
		bm.from_mesh(temp_mesh)
		bm_temp.free()

		bpy.data.meshes.remove(temp_mesh)

		return cont

	def flip_face_normals(self, bm, list_idx):

		bm.faces.ensure_lookup_table()

		avg_normal = Vector()
		for i in list_idx: avg_normal += bm.faces[i].normal
		avg_normal = avg_normal / max(len(list_idx), 1)

		dots = [avg_normal.dot(bm.faces[i].normal) for i in list_idx]
		flipped_faces = [i for i, dot in zip(list_idx, dots) if dot < 0]

		for i in flipped_faces:
			bm.faces[i].normal_flip()

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		orig_mesh = obj.data if self.use_mirror else get_eval_mesh(obj)

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		if self.origin == 'FACES':
			list_f = [f for f in bm.faces if not f.select]
			bmesh.ops.delete(bm, geom=list_f, context='FACES')

			if self.use_split:
				bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if e.calc_face_angle(None) \
					and e.calc_face_angle(None) >= radians(5)])
				margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
					use_even_offset=True, thickness=self.margin)['faces']
				bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

			if self.use_dissolve:
				bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
					use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

			saved_idx = [f.index for f in bm.faces if f.select]

			if not self.per_face:
				margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
					thickness=self.margin, depth=self.offset)['faces']
			else:
				margin = bmesh.ops.inset_individual(bm, faces=bm.faces, use_even_offset=True, \
					thickness=self.margin, depth=self.offset)['faces']

			bmesh.ops.delete(bm, geom=margin, context='FACES')

			self.flip_face_normals(bm, saved_idx)

			tagged_only = False
			if self.tagged_only:
				vgroup = "tagged_verts"
				vg = obj.vertex_groups.get(vgroup)
				if vg:
					deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()
					tagged_only = True

			if self.mode == 'VERTS':
				for e in bm.edges:
					tagged = len([v for v in e.verts if vg.index in v[deform_layer]]) == len(e.verts) if tagged_only else True
					if e.is_boundary or tagged:
						length_e = e.calc_length()
						segments = length_e / max(0.001, self.spacing)
						cut_x_times = int(floor(segments - (segments / 2 )))
						bmesh.ops.subdivide_edges(bm, edges=[e], cuts=cut_x_times)

			origin_faces = bm.faces[:]
			origin_verts = [v for v in bm.verts if vg.index in v[deform_layer]] if tagged_only else bm.verts

			for i, v in enumerate(origin_verts):
				cc = v.is_boundary if not tagged_only else True
				if cc:
					proc = True
					if self.mode == 'ANGLE':
						angle = v.calc_edge_angle(None)
						proc = angle and angle > self.threshold

					seed(self.birth_seed + i)
					if random() > self.birth_perc/100: proc = False

					if proc:
						normal = sum([f.normal for f in v.link_faces], Vector()) / len(v.link_faces)
						cont = self.add_screw(context, obj, bm, v.co, normal, i)
						if not cont: break

			bmesh.ops.delete(bm, geom=origin_faces, context='FACES')
		else:
			list_v = { v: v.co for v in bm.verts if v.select }
			v1 = list(list_v.keys())
			v2 = list(list_v.values())

			link_f = sum([list(v.link_faces) for v in v1], [])
			list_f = list(set(bm.faces[:]) - set(link_f))
			bmesh.ops.delete(bm, geom=list_f, context='FACES')

			coords = [(v.co, v.normal) for v in v1]

			for e in bm.edges:
				cc = all(v.co in v2 for v in e.verts)
				if cc:
					length_e = e.calc_length()
					segments = length_e / max(0.001, self.spacing)
					cut_x_times = int(floor(segments - (segments / 2 )))
					ret = bmesh.ops.subdivide_edges(bm, edges=[e], cuts=cut_x_times)['geom']
					coords += [(v.co, v.normal) for v in ret if isinstance(v, bmesh.types.BMVert)]

			origin_faces = bm.faces[:]
			origin_verts = coords

			vv = []
			for i, v in enumerate(origin_verts):
				seed(self.birth_seed + i)
				if random() < self.birth_perc/100 \
					and not v in vv:
					cont = self.add_screw(context, obj, bm, v[0], v[1], i)
					if cont:
						vv.append(v)
					else:
						break

			bmesh.ops.delete(bm, geom=origin_faces, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		new_obj = bpy.data.objects.new(filter_name(obj, "_Screws"), temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc

		if new_obj.data.polygons:
			assign_mat(self, obj, new_obj, self.mat_index)

			if self.mesh_type in ['BASIC', 'CUSTOM']: set_sharp(new_obj.data)

			set_parent(obj, new_obj)

			refresh_vcolor(new_obj)

			if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			if context.scene.rflow_props.clear_select: clear_select(obj)
		else:
			remove_obj(new_obj)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		flow = row.column_flow(columns=2, align=True)
		flow.prop(self, "mesh_type", expand=True)
		if self.mesh_type == 'MESH':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mesh:")
			row.prop_search(
				self,
				"mesh_name",
				self,
				"meshes",
				text="",
				icon = "MESH_DATA"
				)
		if self.mesh_type == 'CUSTOM':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Import Mesh:")
			row.prop_search(
				self,
				"import_name",
				self,
				"import_meshes",
				text="",
				icon = "IMPORT"
				)
		if self.mesh_type == 'COLLECTION':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Collection:")
			row.prop_search(
				self,
				"coll_name",
				self,
				"collections",
				text="",
				icon = "OUTLINER_COLLECTION"
				)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Object Seed:")
			row.row(align=True).prop(self, "coll_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Origin:")
		row.row(align=True).prop(self, "origin", expand=True)
		if self.origin == 'FACES':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mode:")
			row.row(align=True).prop(self, "mode", expand=True)
			if self.mode == 'ANGLE':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Threshold:")
				row.row(align=True).prop(self, "threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Radius:")
		row.row(align=True).prop(self, "radius", text="")
		if self.origin == 'FACES':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Margin:")
			row.row(align=True).prop(self, "margin", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Offset:")
			row.row(align=True).prop(self, "offset", text="")
		if self.mode == 'VERTS' \
			or self.origin == 'VERTS':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Spacing:")
			row.row(align=True).prop(self, "spacing", text="")
		if self.mesh_type == 'BASIC':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Shape:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "depth")
			split.row(align=True).prop(self, "segment")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Bevel:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "bvl_offset")
			split.row(align=True).prop(self, "bvl_seg")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "rot_z", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation Seed:")
		row.row(align=True).prop(self, "rot_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Proc:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "birth_perc")
		split.row(align=True).prop(self, "birth_seed")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		if self.origin == 'FACES':
			flow.prop(self, "use_split")
			flow.prop(self, "per_face")
			flow.prop(self, "tagged_only")
			col.prop(self, "use_dissolve")
			if self.use_dissolve:
				col.prop(self, "angle")

	def invoke(self, context, event):

		obj = context.active_object

		self.mesh_name = ""
		self.meshes.clear()
		self.import_name = ""
		self.import_meshes.clear()
		self.coll_name = ""
		self.collections.clear()
		self.per_face = False
		self.birth_seed = 0

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = any(f for f in obj.data.polygons if f.select)

		path =  os.path.join(os.path.dirname(
			os.path.abspath(__file__)), "./screws/")
		files = os.listdir(path)

		if files:
			for f in files:
				newListItem = self.import_meshes.add()
				file_name = f.split(".")[0]
				newListItem.name = file_name

		for c in bpy.data.collections:
			newListItem = self.collections.add()
			newListItem.name = c.name

		for o in context.scene.objects:
			if o.type == 'MESH' and \
				o != obj:
				newListItem = self.meshes.add()
				newListItem.name = o.name

		prefs = context.preferences.addons[__package__].preferences

		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_panel_cloth(Operator):
	'''Generate cloth effects on selected island faces'''
	bl_idname = 'panel_cloth.rflow'
	bl_label = 'Panel Cloth'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	split_mode : EnumProperty(
		name = 'Split Mode',
		description = "Determines how to split selected faces",
		items = (
			('NONE', 'None','Do not cut any edges'),
			('SEAM', 'Seam','Cut edges by seams'),
			('ANGLE', 'Angle','Cut edges by angle threshold')),
		default = 'NONE'
		)
	cut_threshold : FloatProperty(
		name        = "Cut Angle",
		description = "Maximum angle threshold for edges to be cut",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	rand_seed : IntProperty(
		name        = "Seed",
		description = "Cloth settings randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Face island margin",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	bake_frames : IntProperty(
		name        = "Bake Frames",
		description = "Number of frames for physics to bake",
		default     = 10,
		min         = 1,
		soft_max    = 100000,
		step        = 1
		)
	qual_steps : IntProperty(
		name        = "Quality Steps",
		description = "Quality of the simulation in steps per frame (higher is better quality but slower)",
		default     = 5,
		min         = 1,
		soft_max    = 80,
		step        = 1
		)
	prop_mode : EnumProperty(
		name = "Mode",
		description = "Randomize or use uniform values for cloth settings",
		items = (
			('RANDOM', 'Random',''),
			('UNIFORM', 'Uniform','')),
		default = 'RANDOM'
		)
	mass_min : FloatProperty(
		name        = "Vertex Mass",
		description = "The mass of each vertex on the cloth material",
		default     = 0.15,
		min         = 0,
		step        = 0.1,
		precision   = 3
		)
	mass_max : FloatProperty(
		name        = "Vertex Mass",
		description = "The mass of each vertex on the cloth material",
		default     = 0.15,
		min         = 0,
		step        = 0.1,
		precision   = 3
		)
	up_force_min : FloatProperty(
		name        = "Pressure",
		description = "Uniform pressure force",
		default     = 1.0,
		min         = -10000.0,
		max         = 10000.0,
		step        = 0.1,
		precision   = 3
		)
	up_force_max : FloatProperty(
		name        = "Pressure",
		description = "Uniform pressure force",
		default     = 1.0,
		min         = -10000.0,
		max         = 10000.0,
		step        = 0.1,
		precision   = 3
		)
	shrink_min_min : FloatProperty(
		name        = "Shrinking Factor",
		description = "Factor by which to shrink cloth",
		default     = -0.1,
		min         = -1.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	shrink_min_max : FloatProperty(
		name        = "Shrinking Factor",
		description = "Factor by which to shrink cloth",
		default     = -0.1,
		min         = -1.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	gravity_min : FloatProperty(
		name        = "Gravity",
		description = "Amount of gravity to affect cloth",
		default     = 0,
		min         = 0,
		soft_max    = 1.0,
		max         = 200.0,
		step        = 0.1,
		precision   = 3
		)
	gravity_max : FloatProperty(
		name        = "Gravity",
		description = "Amount of gravity to affect cloth",
		default     = 0,
		min         = 0,
		soft_max    = 1.0,
		max         = 200.0,
		step        = 0.1,
		precision   = 3
		)
	cuts_smooth : FloatProperty(
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		soft_max    = 50,
		step        = 1
		)
	fractal : FloatProperty(
		name        = "Fractal",
		default     = 0.0,
		min         = 0.0,
		step        = 0.1,
		precision   = 3
		)
	along_normal : FloatProperty(
		name        = "Normal",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	noise_seed : IntProperty(
		name        = "Seed",
		description = "Cut randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	subd_lvl : IntProperty(
		name        = "Subdivision",
		description = "Number of subdivision modifier levels",
		default     = 0,
		min         = 0,
		soft_max    = 6,
		step        = 1
		)
	col_quality : IntProperty(
		name        = "Collision Quality",
		description = "How many collision iterations should be done. (higher is better quality but slower)",
		default     = 2,
		min         = 1,
		max         = 32767,
		step        = 1
		)
	col_distance : FloatProperty(
		name        = "Collision Distance",
		description = "Minimum distance between collision objects before collision response takes effect",
		default     = 0.015,
		min         = 0.001,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	col_distance_self : FloatProperty(
		name        = "Distance",
		description = "Minimum distance between cloth faces before collision response takes effect",
		default     = 0.015,
		min         = 0.001,
		max         = 0.1,
		step        = 0.1,
		precision   = 3
		)
	col_thickness : FloatProperty(
		name        = "Thickness",
		description = "Outer face thickness",
		default     = 0.02,
		min         = 0.001,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	mat_index : IntProperty(
		name        = "Material Index",
		description = "Material assigned to duplicates",
		default     = -1,
		min         = -1,
		max         = 32767,
		step        = 1
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)
	flip_normal : BoolProperty(
		name        = "Flip Normals",
		description = "Flip normals of selected faces",
		default     = False
		)
	smooth_shade : BoolProperty(
		name        = "Shade Smooth",
		description = "Smooth shade panel cloth object",
		default     = False
		)
	remove_sel : BoolProperty(
		name        = "Remove Faces",
		description = "Remove selected faces from source object",
		default     = False
		)
	indiv_effect : BoolProperty(
		name        = "Individual Seed",
		description = "Individual random effects for separate face islands",
		default     = False
		)
	obj_collisions : BoolProperty(
		name        = "Object Collisions",
		description = "Enable collisions with other objects",
		default     = False
		)
	collide_source : BoolProperty(
		name        = "Collide To Source",
		description = "Use collision on source object",
		default     = True
		)
	collision_self : BoolProperty(
		name        = "Self Collision",
		description = "Enable collision self",
		default     = False
		)
	pin_cloth : BoolProperty(
		name        = "Pin",
		description = "Use pin group to hold cloth in place",
		default     = True
		)
	keep_corners : BoolProperty(
		name        = "Preserve Corner Pin",
		description = "Preserve pinning on sharp corner verts based on angle",
		default     = True
		)
	pin_threshold : FloatProperty(
		name        = "Angle",
		description = "Maximum angle threshold for vertices to keep pinning",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def get_collision_list(self, act_obj=None):

		collision_list = []
		for o in bpy.context.selected_objects:
			o.select_set(False)
			if not self.collide_source:
				if o == act_obj: continue
			if self.obj_collisions:
				md = o.modifiers.new('Collision_pcloth', 'COLLISION')
				o.collision.use_culling = False
				o.collision.use_normal = True
				o.collision.thickness_outer = self.col_thickness
				collision_list.append(o)

		return collision_list

	def set_modifier_vis(self, obj, hide=False):

		mod = obj.modifiers
		for m in mod:
			if hide:
				if m.type != 'MIRROR' \
					and m.show_viewport:
					m.show_viewport = False
					if hide: self.hidden_mods.append(m)
			else:
				if m in self.hidden_mods: m.show_viewport = True

	def assign_pin_group(self, obj, mat=Matrix(), list_co=[]):

		if self.pin_cloth:
			mesh = obj.data
			vg_name = "pcloth_pin"

			bm = bmesh.new()
			bm.from_mesh(mesh)

			old_vgroup = obj.vertex_groups.get(vg_name)
			if old_vgroup: obj.vertex_groups.remove(old_vgroup)

			new_vgroup = obj.vertex_groups.new(name=vg_name)
			idx = new_vgroup.index

			deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()

			for v in bm.verts:
				if v.is_boundary or any(e for e in v.link_edges if not e.smooth): v[deform_layer][idx] = 1
				if v.is_boundary and len([e for e in v.link_edges if not e.smooth]) == 2: v[deform_layer][idx] = 0
				if self.keep_corners:
					if v.is_boundary and v.calc_edge_angle(None) and v.calc_edge_angle(None) >= self.pin_threshold: v[deform_layer][idx] = 1

			bm.to_mesh(mesh)
			bm.free()

	def remove_selected_faces(self, obj):

		mesh = obj.data
		fcount = 0

		if mesh.is_editmode:
			bm = bmesh.from_edit_mesh(mesh)
		else:
			bm = bmesh.new()
			bm.from_mesh(mesh)

		remf = [f for f in bm.faces if f.select]
		bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.select], context='FACES')

		fcount = len(bm.faces)

		if mesh.is_editmode:
			bmesh.update_edit_mesh(mesh)
		else:
			bm.to_mesh(mesh)
			mesh.update()

		return fcount

	def add_cloth_effect(self, obj, rs=0):

		context = bpy.context
		frames_curr = context.scene.frame_current

		bake_frames = self.bake_frames
		qual_steps = self.qual_steps

		seed(rs)
		mass = uniform(self.mass_min, self.mass_max) if self.prop_mode == 'RANDOM' else self.mass_max
		up_force = uniform(self.up_force_min, self.up_force_max) if self.prop_mode == 'RANDOM' else self.up_force_max
		shrink_min = uniform(self.shrink_min_min, self.shrink_min_max) if self.prop_mode == 'RANDOM' else self.shrink_min_max
		gravity = uniform(self.gravity_min, self.gravity_max) if self.prop_mode == 'RANDOM' else self.gravity_max

		col_quality = self.col_quality
		col_distance = self.col_distance
		col_dist_self = self.col_distance_self

		mod = obj.modifiers
		md = mod.new('Cloth', 'CLOTH')
		md.settings.vertex_group_mass = "pcloth_pin"
		md.settings.use_pressure = True
		md.settings.uniform_pressure_force = up_force
		md.settings.shrink_min = shrink_min
		md.settings.effector_weights.gravity = gravity
		md.point_cache.frame_start = frames_curr
		md.point_cache.frame_end = frames_curr + bake_frames
		md.show_expanded = False

		# silk preset
		md.settings.quality = qual_steps
		md.settings.mass = mass
		md.settings.tension_stiffness = 5
		md.settings.compression_stiffness = 5
		md.settings.shear_stiffness = 5
		md.settings.bending_stiffness = 0.05
		md.settings.tension_damping = 0
		md.settings.compression_damping = 0
		md.settings.shear_damping = 0
		md.settings.air_damping = 1
		md.settings.use_dynamic_mesh = True

		md.collision_settings.use_collision = self.obj_collisions
		md.collision_settings.use_self_collision = self.collision_self
		md.collision_settings.collision_quality = col_quality
		md.collision_settings.distance_min = col_distance
		md.collision_settings.self_distance_min = col_dist_self

		bpy.ops.ptcache.bake_all(bake=True)
		context.scene.frame_current += bake_frames

		obj.data = get_eval_mesh(obj).copy()
		obj.modifiers.clear()
		obj.vertex_groups.clear()

		context.scene.frame_current = frames_curr

		if self.use_mirror: copy_modifiers([self.obj, obj], mod_types=['MIRROR'])

		md = mod.new('Subdivision', 'SUBSURF')
		md.levels = self.subd_lvl
		md.render_levels = self.subd_lvl
		md.boundary_smooth = 'PRESERVE_CORNERS'

		if self.smooth_shade:
			bpy.ops.object.shade_smooth()
		else:
			bpy.ops.object.shade_flat()

	def execute(self, context):

		self.obj = obj = context.active_object
		keep_obj = True

		if self.use_mirror:
			orig_mesh = obj.data
		else:
			self.set_modifier_vis(obj, hide=True)
			orig_mesh = get_eval_mesh(obj)

		collision_list = self.get_collision_list(obj)

		obj.update_from_editmode()

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		fsel = []
		ftri = []

		for f in bm.faces:
			if not f.select:
				fsel.append(f)
			else:
				if len(f.edges) > 4: ftri.append(f)

		bmesh.ops.delete(bm, geom=fsel, context='FACES')

		if self.flip_normal:
			bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
			bmesh.ops.reverse_faces(bm, faces=bm.faces)

		if self.split_mode != 'NONE':
			bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if (e.seam if self.split_mode == 'SEAM' else \
				e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)])

		if self.margin:
			margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin)['faces']
			bmesh.ops.delete(bm, geom=margin, context='FACES')

		ret = bmesh.ops.triangulate(bm, faces=ftri, quad_method='BEAUTY', ngon_method='BEAUTY')
		bmesh.ops.join_triangles(bm, faces=ret['faces'], angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, fractal=self.fractal, along_normal=self.along_normal, \
			cuts=self.cuts_base, seed=self.noise_seed, use_grid_fill=True, use_smooth_even=True)

		bm.to_mesh(temp_mesh)
		bm.free()

		new_obj = bpy.data.objects.new(obj.name + "_PCloth", temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc

		refresh_vcolor(new_obj)

		if self.remove_sel:
			fcount = self.remove_selected_faces(obj)
			if fcount == 0:	keep_obj = False

		use_indiv_effect = False
		if self.indiv_effect:
			mesh = new_obj.data.copy()
			islands = get_islands(new_obj, bm=None)

			list_objs = []
			if len(islands) > 1:
				use_indiv_effect = True
				for i in islands:
					bm_split = bmesh.new()
					split_mesh = bpy.data.meshes.new(".split")
					bm_split.from_mesh(mesh)

					verts = [v for v in bm_split.verts if not v.index in i]
					bmesh.ops.delete(bm_split, geom=verts, context='VERTS')

					bm_split.to_mesh(split_mesh)
					bm_split.free()

					split_obj = bpy.data.objects.new(filter_name(obj, "_PCloth"), split_mesh)
					orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
					split_obj.scale = orig_scale
					split_obj.rotation_euler = orig_rot.to_euler()
					split_obj.location = orig_loc
					context.scene.collection.objects.link(split_obj)
					list_objs.append(split_obj)

				for n, o in enumerate(list_objs):
					o.select_set(True)
					context.view_layer.objects.active = o
					self.assign_pin_group(o)
					self.add_cloth_effect(o, rs=n+self.rand_seed)

				context.view_layer.objects.active = list_objs[0]
				bpy.ops.object.join()

				assign_mat(self, obj, context.active_object, self.mat_index)
				select_isolate(obj)

				bpy.data.objects.remove(new_obj)

		if not use_indiv_effect:
			set_parent(obj, new_obj)

			select_isolate(new_obj)
			self.assign_pin_group(new_obj)
			self.add_cloth_effect(new_obj, rs=self.rand_seed)
			if keep_obj: select_isolate(obj)

		if collision_list:
			for o in collision_list:
				cm = o.modifiers.get("Collision_pcloth")
				if cm: o.modifiers.remove(cm)

		if not self.use_mirror and keep_obj: self.set_modifier_vis(obj, hide=False)

		if context.scene.rflow_props.clear_select: clear_select(obj)

		if not keep_obj: remove_obj(obj, clear_data=False)

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Split Mode:")
		row.row(align=True).prop(self, "split_mode", expand=True)
		if self.split_mode == 'ANGLE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cut Angle:")
			row.row(align=True).prop(self, "cut_threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cloth Seed:")
		row.row(align=True).prop(self, "rand_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bake Frames:")
		row.row(align=True).prop(self, "bake_frames", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Quality:")
		row.row(align=True).prop(self, "qual_steps", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Mode:")
		row.row(align=True).prop(self, "prop_mode", expand=True)
		if self.prop_mode == 'RANDOM':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mass:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "mass_min", text="Min")
			split.row(align=True).prop(self, "mass_max", text="Max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Pressure:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "up_force_min", text="Min")
			split.row(align=True).prop(self, "up_force_max", text="Max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Shrink:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "shrink_min_min", text="Min")
			split.row(align=True).prop(self, "shrink_min_max", text="Max")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Gravity:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "gravity_min", text="Min")
			split.row(align=True).prop(self, "gravity_max", text="Max")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mass:")
			row.row(align=True).prop(self, "mass_max", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Pressure:")
			row.row(align=True).prop(self, "up_force_max", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Shrink:")
			row.row(align=True).prop(self, "shrink_min_max", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Gravity:")
			row.row(align=True).prop(self, "gravity_max", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Noise:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "fractal")
		split.row(align=True).prop(self, "along_normal")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Noise Seed:")
		row.row(align=True).prop(self, "noise_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subsurf Level:")
		row.row(align=True).prop(self, "subd_lvl", text="")
		if self.obj_collisions or self.collision_self:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Collision:")
			row.row(align=True).prop(self, "col_quality", text="Quality")
		if self.obj_collisions:
			row = col.row().split(factor=0.27, align=True)
			row.label(text=" ")
			row.row(align=True).prop(self, "col_distance", text="Object: Distance")
			row = col.row().split(factor=0.27, align=True)
			row.label(text=" ")
			row.row(align=True).prop(self, "col_thickness", text="Object: Thickness")
		if self.collision_self:
			row = col.row().split(factor=0.27, align=True)
			row.label(text=" ")
			row.row(align=True).prop(self, "col_distance_self", text="Self: Distance")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "use_mirror")
		flow.prop(self, "flip_normal")
		flow.prop(self, "smooth_shade")
		flow.prop(self, "indiv_effect")
		flow.prop(self, "remove_sel")
		flow.prop(self, "obj_collisions")
		if self.obj_collisions: flow.prop(self, "collide_source")
		flow.prop(self, "collision_self")
		flow = col.column_flow(columns=2, align=True)
		flow.prop(self, "pin_cloth")
		flow.prop(self, "keep_corners")
		if self.keep_corners:
			col.prop(self, "pin_threshold")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		self.cuts_base = 0
		self.rand_seed = 1
		self.noise_seed = 1
		self.hidden_mods = []

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face:
			init_props(self, event, ops='pcloth', force=has_face>=props.select_limit)
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_plate_insets(Operator):
	'''Generate random plating insets'''
	bl_idname = 'plate_insets.rflow'
	bl_label = 'Plate Insets'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	cuts_base : IntProperty(
		name        = "Base Cut",
		description = "Number of subdivision cuts for base mesh",
		default     = 0,
		min         = 0,
		soft_max    = 12,
		step        = 1
		)
	mesh_smooth : FloatProperty(
		name        = "Smooth",
		description = "Smoothing factor for the mesh",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pool_size : IntProperty(
		name        = "Amount",
		description = "Number of hull faces to be extruded",
		default     = 500,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	plating_size_min : IntProperty(
		name        = "Min",
		description = "Minimum random growth factor for hull extrusions",
		default     = 2,
		min         = 1,
		soft_max    = 1000,
		step        = 1
		)
	plating_size_max : IntProperty(
		name        = "Max",
		description = "Maximum random growth factor for hull extrusions",
		default     = 5,
		min         = 1,
		soft_max    = 1000,
		step        = 1
		)
	ptol : FloatProperty(
		name        = "Tolerance",
		description = "Tolerance value for selecting faces for plating extrusion",
		default     = 0.5,
		min         =  0.001,
		soft_max    = 2.0,
		step        = 0.1,
		precision   = 3
		)
	adj_mode : EnumProperty(
		name = 'Adjacent Faces',
		items = (
			('CLEAR', 'Clear',''),
			('FILL', 'Fill','')),
		default = 'CLEAR'
		)
	even_offset : EnumProperty(
		name = 'Even Offset',
		items = (
			('ON', 'On',''),
			('OFF', 'Off','')),
		default = 'ON'
		)
	pl_thick : FloatProperty(
		name        = "Thickness",
		description = "Inset thickness value for faces",
		default     = 0.01,
		soft_min    = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pl_depth : FloatProperty(
		name        = "Depth",
		description = "Inset depth value for faces",
		default     = 0.025,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pl_thick_min : FloatProperty(
		name        = "Min",
		description = "Minimum inset thickness value for faces",
		default     = 0.01,
		soft_min    = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pl_thick_max : FloatProperty(
		name        = "Max",
		description = "Maximum inset thickness value for faces",
		default     = 0.01,
		soft_min    = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	thickness_seed : IntProperty(
		name        = "Thickness Seed",
		description = "Inset thickness randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_thickness : BoolProperty(
		name        = "Uniform Thickness",
		description = "Use single property value for inset thickness",
		default     = True
		)
	pl_depth_min : FloatProperty(
		name        = "Min",
		description = "Minimum inset depth value for faces",
		default     = 0.025,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pl_depth_max : FloatProperty(
		name        = "Max",
		description = "Maximum inset depth value for faces",
		default     = 0.025,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	depth_seed : IntProperty(
		name        = "Seed",
		description = "Inset depth randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	uni_depth : BoolProperty(
		name        = "Uniform Depth",
		description = "Use single property value for inset depth or height",
		default     = False
		)
	margin_type : EnumProperty(
		name = 'Inner Margin',
		description = "Inner margin type",
		items = (
			('ALL', 'All','Creates margin for all plate insets'),
			('INDENT', 'Indent Only','Creates margin only for indented plate insets')),
		default = 'ALL'
		)
	pl_margin_outer : FloatProperty(
		name        = "Outer",
		description = "Outer plate margin",
		default     = 0.0,
		soft_min    = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pl_margin_inner : FloatProperty(
		name        = "Inner",
		description = "Inner plate margin",
		default     = 0.0,
		soft_min    = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	rev_depth : FloatProperty(
		name        = "Reverse Depth",
		description = "Percentage to determine if plating depth is reversed",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 50,
		subtype     = "PERCENTAGE"
		)
	rev_seed : IntProperty(
		name        = "Seed",
		description = "Reverse depth random seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	tri_perc : FloatProperty(
		name        = "Triangulate",
		description = "Triangulate faces via percentage",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	limit_smooth : EnumProperty(
		name = 'Limit SMooth',
		items = (
			('NONE', 'None','No limit on auto smooth'),
			('BASE', 'Base','Sharpen base plate area'),
			('TOP', 'Top','Sharpen top plate area')),
		default = 'NONE'
		)
	base_smooth : EnumProperty(
		name = 'Shading',
		items = (
			('SMOOTH', 'Smooth','Faces are smooth shaded'),
			('ANGLE', 'By Angle','Faces are smooth shaded by angle'),
			('FLAT', 'Flat','Faces are flat shaded')),
		default = 'ANGLE'
		)
	pl_seed : IntProperty(
		name        = "Seed",
		description = "Hull extras random seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	use_clip : BoolProperty(
		name        = "Clip Center",
		description = "Clip center verts when using mirror modifier",
		default     = True
		)
	clip_dist : FloatProperty(
		name        = "Distance",
		description = "Distance within which center vertices are clipped",
		default     = 0.001,
		min         = 0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	clip_axis : BoolVectorProperty(
		name        = "Clip Axis",
		description = "Clip axis toggles",
		default     = (True, True, True),
		size		= 3,
		subtype		= "XYZ"
		)
	use_dissolve : BoolProperty(
		name        = "Limited Dissolve",
		description = "Use limited dissolve to unify faces",
		default     = False
		)
	angle : FloatProperty(
		name        = "Max Angle",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def unsharp_symmetry_edges(self, obj, edges=[], center=Vector(), dist=1e-4):

		mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

		if mirror:
			axis = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]
			for e in [e for e in edges if e.is_boundary]:
				for i in range(3):
					if mirror.use_axis[i]:
						v1 = geometry.distance_point_to_plane(e.verts[0].co, center, axis[i]) < dist
						v2 = geometry.distance_point_to_plane(e.verts[1].co, center, axis[i]) < dist
						if v1 and v2: e.smooth = True

	def execute(self, context):

		obj = context.active_object

		obj.update_from_editmode()

		even_offset = self.even_offset == 'ON'
		limit_smooth = self.limit_smooth != 'NONE'
		use_mirror = self.use_mirror
		mirror_vec = Vector()

		mesh = obj.data

		if self.limit_smooth != 'NONE':
			mesh.edges.foreach_set('use_edge_sharp', [False for e in mesh.edges])
			mesh.shade_smooth()

		mesh_copy = obj.data if use_mirror else get_eval_mesh(obj)

		if mesh.is_editmode:
			bm_src = bmesh.from_edit_mesh(mesh)
		else:
			bm_src = bmesh.new()
			bm_src.from_mesh(mesh)

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(mesh_copy)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')

		bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if not e.smooth])

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=self.cuts_base, use_grid_fill=True)

		if self.tri_perc:
			tris = get_tri_faces(bm.faces, self.tri_perc, self.pl_seed)
			bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))

		margin_outer = []
		if self.pl_margin_outer:
			save_faces = bm.faces[:].copy()
			margin_outer = bmesh.ops.inset_region(bm, faces=save_faces, use_boundary=True, \
				use_even_offset=even_offset, thickness=self.pl_margin_outer)['faces']
			listf = save_faces
		else:
			listf = bm.faces[:]

		totlf = len(listf)

		pool_size = self.pool_size if not self.pool_size > totlf else totlf

		hull_faces = []
		adj_faces = set()

		for i in range(pool_size):
			seed(self.pl_seed + i)
			if not listf: break
			if len(listf) == 1:
				f = listf.pop(0)
			else:
				f = listf.pop(randint(0, len(listf) - 1))

			if self.adj_mode == 'CLEAR':
				if not f in adj_faces: hull_faces.append(f)
				adj_faces.update(set(sum([v.link_faces[:] for v in f.verts], [])))
			else:
				hull_faces.append(f)

		seed_counter = 0
		plating = set(margin_outer)
		while hull_faces:
			seed(self.pl_seed + seed_counter)
			f = hull_faces.pop()
			plus_faces = {f}
			fverts = set(f.verts)
			r_min = min(self.plating_size_min, self.plating_size_max) - 1
			r_max = max(self.plating_size_min, self.plating_size_max) - 1
			for i in range(randint(r_min, r_max)):
				link_faces = list(dict.fromkeys(sum([list(v.link_faces) for v in fverts], [])))
				fverts.clear()
				for lf in link_faces:
					angle = f.normal.angle(lf.normal, None)
					if not lf in plating \
						and angle != None and angle < self.ptol:
						plus_faces.add(lf)
						fverts.update(set(lf.verts))
						if lf in hull_faces: hull_faces.remove(lf)

				if not fverts: break

			inset_faces = list(plus_faces)

			seed(self.depth_seed + seed_counter)
			inset_depth = self.pl_depth if self.uni_depth else uniform(self.pl_depth_min, self.pl_depth_max)

			if self.rev_depth:
				seed(self.rev_seed + seed_counter)
				inset_depth = inset_depth if int(ceil(random() * 100)) > self.rev_depth else -inset_depth

			margin_inner = []
			if self.pl_margin_inner:
				if (inset_depth < 0 and self.margin_type == 'INDENT') \
					or self.margin_type == 'ALL':
					margin_inner = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, \
						use_even_offset=even_offset, thickness=self.pl_margin_inner)['faces']

			seed(self.thickness_seed + seed_counter)
			inset_thickness = self.pl_thick if self.uni_thickness else uniform(self.pl_thick_min, self.pl_thick_max)
			ret_inset = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, \
				use_even_offset=even_offset, thickness=inset_thickness, depth=inset_depth)['faces']

			inset_edges = set(sum([list(f.edges) for f in ret_inset], []))

			for e in inset_edges:
				e.smooth = True; e.seam = False

				inset_count1 = len([lf for lf in e.link_faces if lf in ret_inset])
				inset_count2 = len([lf for lf in e.link_faces if lf in inset_faces])

				if inset_count1 == 1 \
					and inset_count2 == 0: e.seam = True

				if limit_smooth:
					limit_area = inset_depth < 0 if self.limit_smooth == 'BASE' else inset_depth > 0
					if limit_area:
						if inset_count1 == 1: e.smooth = False
					else:
						if inset_count1 == 1 \
							and inset_count2 == 0: e.smooth = False

			plating.update(set(inset_faces + margin_inner + ret_inset))

			seed_counter += 1

		if self.tri_perc: bmesh.ops.join_triangles(bm, faces=bm.faces, \
			angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

		if not use_mirror: bisect_symmetry(bm, obj)

		if self.use_clip:
			clip_center(bm, obj, self.clip_dist, self.clip_axis)
			if limit_smooth: self.unsharp_symmetry_edges(obj, bm.edges)

		bm.to_mesh(temp_mesh)

		listf = [f for f in bm_src.faces if f.select]

		if limit_smooth:
			edges = set(sum([list(f.edges) for f in listf], []))
			for e in edges:
				if not all(f in listf for f in e.link_faces): e.smooth = False

		bmesh.ops.delete(bm_src, geom=listf, context='FACES')
		bmesh.ops.subdivide_edges(bm_src, edges=bm_src.edges, cuts=self.cuts_base, use_grid_fill=True)

		bm_src.from_mesh(temp_mesh)

		double_verts = [ v for v in bm_src.verts if not any(e for e in v.link_edges if not e.smooth) ]

		bmesh.ops.remove_doubles(bm_src, verts=double_verts, dist=1e-4)
		bmesh.ops.smooth_vert(bm_src, verts=[v for v in bm_src.verts if not v.is_boundary], factor=self.mesh_smooth, use_axis_x=True, \
			use_axis_y=True, use_axis_z=True)

		if self.use_dissolve: bmesh.ops.dissolve_limit(bm_src, angle_limit=self.angle, \
			use_dissolve_boundaries=False, verts=bm_src.verts, edges=bm_src.edges, delimit={'NORMAL'})

		if mesh.is_editmode:
			bmesh.update_edit_mesh(mesh)
		else:
			bm_src.to_mesh(mesh)
			mesh.update()

		bm_src.free()
		bm.free()

		if not limit_smooth:
			if self.base_smooth == 'SMOOTH':
				mesh.shade_smooth()

			if self.base_smooth == 'ANGLE':
				mesh.set_sharp_from_angle(angle=radians(30))

			if self.base_smooth == 'FLAT':
				mesh.shade_flat()

		if context.scene.rflow_props.clear_select: clear_select(obj)

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		row.row(align=True).prop(self, "cuts_base", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Plating Seed:")
		row.row(align=True).prop(self, "pl_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Smooth:")
		row.row(align=True).prop(self, "mesh_smooth", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Plates:")
		row.row(align=True).prop(self, "pool_size", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "plating_size_min")
		split.row(align=True).prop(self, "plating_size_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Tolerance:")
		row.row(align=True).prop(self, "ptol", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Adj Faces:")
		row.row(align=True).prop(self, "adj_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Even Offset:")
		row.row(align=True).prop(self, "even_offset", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Thickness:")
		if self.uni_thickness:
			split = row.split(factor=0.9, align=True)
			split.row(align=True).prop(self, "pl_thick", text="")
			split.prop(self, "uni_thickness", text="", icon="LINKED")
		else:
			split1 = row.split(factor=0.5, align=True)
			split1.row(align=True).prop(self, "pl_thick_min")
			split2 = split1.split(factor=0.8, align=True)
			split2.row(align=True).prop(self, "pl_thick_max")
			split2.prop(self, "uni_thickness", text="", icon="UNLINKED")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Thickness Seed:")
			row.row(align=True).prop(self, "thickness_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth:")
		if self.uni_depth:
			split = row.split(factor=0.9, align=True)
			split.row(align=True).prop(self, "pl_depth", text="")
			split.prop(self, "uni_depth", text="", icon="LINKED")
		else:
			split1 = row.split(factor=0.5, align=True)
			split1.row(align=True).prop(self, "pl_depth_min")
			split2 = split1.split(factor=0.8, align=True)
			split2.row(align=True).prop(self, "pl_depth_max")
			split2.prop(self, "uni_depth", text="", icon="UNLINKED")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height Seed:")
		row.row(align=True).prop(self, "depth_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Inner Margin:")
		row.row(align=True).prop(self, "margin_type", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margins:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "pl_margin_outer")
		split.row(align=True).prop(self, "pl_margin_inner")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Reverse:")
		row.row(align=True).prop(self, "rev_depth", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Reverse Seed:")
		row.row(align=True).prop(self, "rev_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Triangulate:")
		row.row(align=True).prop(self, "tri_perc", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limit Smooth:")
		row.row(align=True).prop(self, "limit_smooth", expand=True)
		if self.limit_smooth == 'NONE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Shading:")
			row.row(align=True).prop(self, "base_smooth", expand=True)
		col.separator(factor=0.5)
		col.prop(self, "use_mirror")
		row = col.row().split(factor=0.5, align=True)
		row.prop(self, "use_clip")
		if self.use_clip:
			row.row(align=True).prop(self, "clip_axis", text="", expand=True)
			col.prop(self, "clip_dist")
		col.prop(self, "use_dissolve")
		if self.use_dissolve:
			col.prop(self, "angle")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		self.pl_seed = 1
		self.thickness_seed = 1
		self.depth_seed = 1
		self.rev_seed = 1

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face:
			init_props(self, event, ops='p_insets', force=has_face>=props.select_limit)
			self.has_mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
			prefs = context.preferences.addons[__package__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_quick_displace(Operator):
	'''Generate noise displacement using mesh'''
	bl_idname = 'quick_displ.rflow'
	bl_label = 'Quick Displacement'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	displ_type : EnumProperty(
		name = "Type",
		description = "Displacement type",
		items = (
			('CLOUDS', 'Clouds',''),
			('IMAGE', 'Image','')),
		default = 'CLOUDS')
	displ_mode : EnumProperty(
		name = "Mode",
		description = "Displacement mode",
		items = (
			('ALL', 'All Faces',''),
			('SELECTION', 'Selection','')),
		default = 'ALL')
	coords : EnumProperty(
		name = "Coordinates",
		description = "Displacement mode",
		items = (
			('OBJECT', 'Object',''),
			('UV', 'UV','')),
		default = 'OBJECT')
	img_name : StringProperty(
		name        = "Image",
		description = "Image for displacement texture"
		)
	images : CollectionProperty(type=PropertyGroup)
	noise_basis : EnumProperty(
		name = "Noise Basis",
		description = "Noise algorithm",
		items = (
			('BLENDER_ORIGINAL', 'Blender Original',''),
			('ORIGINAL_PERLIN', 'Original Perlin',''),
			('IMPROVED_PERLIN', 'Improved Perlin',''),
			('VORONOI_F1', 'Voronoi F1',''),
			('VORONOI_F2', 'Voronoi F2',''),
			('VORONOI_F3', 'Voronoi F3',''),
			('VORONOI_F4', 'Voronoi F4',''),
			('VORONOI_F2_F1', 'Voronoi F2-F1',''),
			('VORONOI_CRACKLE', 'Voronoi Crackle',''),
			('CELL_NOISE', 'Cell Noise','')),
		default = 'BLENDER_ORIGINAL')
	subtract_sel : IntProperty(
		name        = "Size",
		description = "Reduces selection area used for displacement",
		default     = 0,
		min         = 0,
		soft_max    = 50,
		step        = 1
		)
	expand_subtr : IntProperty(
		name        = "Expand",
		description = "Expand border smoothing",
		default     = 0,
		min         = 0,
		soft_max    = 50,
		step        = 1
		)
	strength : FloatProperty(
		name        = "Strength",
		description = "Amount to displace geometry",
		default     = 0.2,
		min         = -100.0,
		max         = 100.0,
		step        = 0.1,
		precision   = 3
		)
	mid_level : FloatProperty(
		name        = "Midlevel",
		description = "Material value that gives no displacement",
		default     = 0.5,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	noise_scale : FloatProperty(
		name        = "Size",
		description = "Scaling for noise input",
		default     = 0.25,
		min         = 0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	noise_depth : IntProperty(
		name        = "Depth",
		description = "Depth of the cloud calculation",
		default     = 3,
		min         = 0,
		max         = 24,
		step        = 1
		)
	intensity : FloatProperty(
		name        = "Brightness",
		description = "Adjust the brightness of the texture",
		default     = 1.0,
		min         = 0,
		max         = 2.0,
		step        = 0.1,
		precision   = 3
		)
	contrast : FloatProperty(
		name        = "Contrast",
		description = "Adjust the contrast of the texture",
		default     = 1.0,
		min         = 0,
		max         = 5.0,
		step        = 0.1,
		precision   = 3
		)
	smooth_factor : FloatProperty(
		name        = "Smooth Factor",
		description = "Strength of smoothing",
		default     = 0.5,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	smooth_iter : IntProperty(
		name        = "Smooth Iteration",
		description = "Smooth iteration",
		default     = 0,
		min         = 0,
		soft_max    = 100,
		step        = 1
		)
	location : FloatVectorProperty(
		name        = "Location",
		description = "Displacement object location",
		default     = (0.0,0.0,0.0),
		size        = 3,
		step        = 1.0,
		subtype		= "XYZ"
		)
	loc_seed : IntVectorProperty(
		name        = "Location Seed",
		description = "Cloud texture location seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	rotation : FloatVectorProperty(
		name        = "Rotation",
		description = "Displacement object rotation",
		default     = (0,0,0),
		size        = 3,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "EULER"
		)
	rotation_seed : IntVectorProperty(
		name        = "Rotation Seed",
		description = "Cloud texture rotation seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	scale : FloatVectorProperty(
		name        = "Scale",
		description = "Displacement object scale",
		default     = (1.0,1.0,1.0),
		size        = 3,
		soft_min    = 0.01,
		soft_max    = 10.0,
		step        = 1.0,
		subtype		= "XYZ"
		)
	scale_seed : IntVectorProperty(
		name        = "Scale Seed",
		description = "Cloud texture scale seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	img_pos : FloatVectorProperty(
		name        = "Location",
		description = "Image location",
		default     = (0.0,0.0),
		size        = 2,
		step        = 1.0,
		subtype		= "XYZ"
		)
	pos_seed : IntVectorProperty(
		name        = "Location Seed",
		description = "Image location seed",
		default     = (1,1),
		size        = 2,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	img_size : FloatProperty(
		name        = "Size",
		description = "Image size",
		default     = 1.0,
		step        = 0.1,
		precision   = 3
		)
	img_rotation : FloatProperty(
		name        = "Rotation",
		description = "Image rotation",
		default     = 0,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	filter_size : FloatProperty(
		name        = "Filter Size",
		description = "Filter size",
		default     = 1.0,
		min         = 0.1,
		max         = 50.0,
		step        = 1.0,
		precision   = 3
		)
	cuts_smooth : FloatProperty(
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
		)
	cuts_base : IntProperty(
		name        = "Cuts",
		description = "Number of subdivision cuts for panel object",
		default     = 0,
		min         = 0,
		soft_max    = 100,
		step        = 1
		)
	fractal : FloatProperty(
		name        = "Fractal",
		default     = 0.0,
		min         = 0.0,
		step        = 0.1,
		precision   = 3
		)
	along_normal : FloatProperty(
		name        = "Normal",
		default     = 0.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3
		)
	noise_seed : IntProperty(
		name        = "Seed",
		description = "Cut randomize seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	subd_lvl : IntProperty(
		name        = "Subdivision",
		description = "Number of subdivision modifier levels",
		default     = 0,
		min         = 0,
		soft_max    = 6,
		step        = 1
		)
	obj_rot : FloatVectorProperty(
		name        = "Rotation",
		description = "Object rotation",
		default     = (0,0,0),
		size        = 3,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "EULER"
		)
	rot_seed : IntVectorProperty(
		name        = "Rotation Seed",
		description = "Object rotation seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)
	obj_sca_max : FloatVectorProperty(
		name        = "Scale",
		description = "Maximum object scale",
		default     = (1.0,1.0,1.0),
		size        = 3,
		min         = 0,
		soft_max    = 10.0,
		step        = 1.0,
		subtype		= "XYZ"
		)
	obj_sca_min : FloatVectorProperty(
		name        = "Scale",
		description = "Minimum object scale",
		default     = (0.1,0.1,0.1),
		size        = 3,
		min         = 0,
		soft_max    = 10.0,
		step        = 1.0,
		subtype		= "XYZ"
		)
	sca_seed : IntVectorProperty(
		name        = "Scale Seed",
		description = "Object scaling seed",
		default     = (1,1,1),
		size        = 3,
		min         = 1,
		soft_max	= 10000,
		step        = 1
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH" \
			and context.active_object.mode == 'OBJECT'

	def rand_pos(self, sdr=1, val=0, n=1, type='None'):

		if sdr > 1:
			seed(sdr + n)
			if val == 0:
				if type != 'None':
					val = uniform(radians(-360), radians(360))
				else:
					val = uniform(-1, 1)
			else:
				val = uniform(-val, val)

		return val

	def move_uv(self, obj, n=1):

		def make_rotation_transformation(angle, origin=(0.5, 0.5)):

			cos_theta, sin_theta = cos(angle), sin(angle)
			x0, y0 = origin

			def xform(point):

				x, y = point[0] - x0, point[1] - y0
				return (x * cos_theta - y * sin_theta + x0,
						x * sin_theta + y * cos_theta + y0)

			return xform

		rot = make_rotation_transformation(self.img_rotation)

		uv_map = obj.data.uv_layers.active
		for v in obj.data.loops :
			for i in range(2):
				uv_map.data[v.index].uv[i] += self.rand_pos(self.pos_seed[i], self.img_pos[i], n)
			uv_map.data[v.index].uv = rot(uv_map.data[v.index].uv)

	def set_displacement(self, obj, n=1):

		empty = None

		mod = obj.modifiers.new("Smooth", type='SMOOTH')
		mod.factor = self.smooth_factor
		mod.iterations = self.smooth_iter

		if self.displ_mode == 'SELECTION': mod.vertex_group = self.vg_name

		if self.coords == 'OBJECT': empty = self.add_empty(obj.location)

		height_img = bpy.data.textures.new('Noise_RFlow', type='IMAGE')
		if self.displ_type == 'CLOUDS':
			height_img.type = 'CLOUDS'
			bpy.data.textures[height_img.name].noise_basis = self.noise_basis
			bpy.data.textures[height_img.name].noise_scale = self.noise_scale
			bpy.data.textures[height_img.name].noise_depth = self.noise_depth
		else:
			height_img.type = 'IMAGE'
			if self.img_name: bpy.data.textures[height_img.name].image = bpy.data.images[self.img_name]
			height_img.crop_max_x = self.img_size
			height_img.crop_max_y = self.img_size
			height_img.filter_size = self.filter_size
			if self.img_name: bpy.data.textures[height_img.name].image = bpy.data.images[self.img_name]
		bpy.data.textures[height_img.name].intensity = self.intensity
		bpy.data.textures[height_img.name].contrast = self.contrast

		mod = obj.modifiers.new("Displace", type='DISPLACE')
		mod.texture = height_img
		if self.displ_mode == 'SELECTION': mod.vertex_group = self.vg_name
		mod.strength = self.strength
		mod.mid_level = self.mid_level
		mod.texture_coords = 'OBJECT' if self.coords == 'OBJECT' else 'UV'

		if empty:
			mod.texture_coords_object = empty
			for i in range(3):
				empty.location[i] += self.rand_pos(self.loc_seed[i], self.location[i], n)
				empty.rotation_euler[i] = self.rand_pos(self.rotation_seed[i], self.rotation[i], n, type='Angle')
				empty.scale[i] = self.rand_pos(self.scale_seed[i], self.scale[i], n)

		obj.data = get_eval_mesh(obj).copy()
		obj.modifiers.clear()
		obj.vertex_groups.clear()

		if empty: bpy.data.objects.remove(empty)
		bpy.data.textures.remove(height_img)

		if self.subd_lvl > 0:
			md = obj.modifiers.new('Subdivision', 'SUBSURF')
			md.levels = self.subd_lvl
			md.render_levels = self.subd_lvl
			md.boundary_smooth = 'PRESERVE_CORNERS'

	def add_empty(self, loc=Vector()):

		o = bpy.data.objects.new( "RFlow_Empty", None )
		bpy.context.scene.collection.objects.link(o)
		o.empty_display_size = 2
		o.empty_display_type = 'PLAIN_AXES'
		o.location = loc

		return o

	def assign_vgroup(self, obj, bm):

		listv = []

		old_vgroup = obj.vertex_groups.get(self.vg_name)
		if old_vgroup: obj.vertex_groups.remove(old_vgroup)

		new_vgroup = obj.vertex_groups.new(name=self.vg_name)
		idx = new_vgroup.index

		deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()

		for v in bm.verts:
			if v.select:
				v[deform_layer][idx] = 1
				listv.append(v)

		return listv

	def remove_subsurf(self, obj):

		for m in obj.modifiers:
			if m.type == 'SUBSURF': obj.modifiers.remove(m)

	def rot_sca(self, obj, bm, listv=[], i=0):

		pivot = sum([v.co for v in listv], Vector()) / len(listv)

		def rand_sca(min_sca, max_sca):

			scale = Vector()
			for n in range(3):
				if self.sca_seed[n] > 1:
					seed(self.sca_seed[n] + i)
					scale[n] = uniform(min_sca[n], max_sca[n])
				else: scale[n] = max(min_sca[n], max_sca[n])
				seed(0)

			return scale

		x0, y0, z0 = self.obj_sca_min
		x1, y1, z1 = self.obj_sca_max
		scale = rand_sca([x0, y0, z0], [x1, y1, z1])
		bmesh.ops.scale(
			bm,
			vec     = Vector(scale),
			space   = Matrix.Translation(pivot).inverted(),
			verts   = listv
			)

		def rand_rot(x, y, z):

			axis = [x, y, z]
			for n, v in enumerate(axis):
				if self.rot_seed[n] > 1:
					seed(self.rot_seed[n] + i)
					if v == 0:
						axis[n] = uniform(radians(-360), radians(360))
					else:
						axis[n] = uniform(-v, v)
				else: axis[n] = v
				seed(0)

			return Euler(Vector(axis))

		x, y, z = self.obj_rot
		rot_axis = rand_rot(x, y, z)
		_, orig_rot, _ = obj.matrix_world.decompose()
		bmesh.ops.rotate(
			bm,
			verts   = listv,
			cent    = pivot,
			matrix  = orig_rot.to_matrix().inverted() @ rot_axis.to_matrix()
			)

	def execute(self, context):

		for i, obj in enumerate(context.selected_objects):
			if obj.type == 'MESH':
				self.remove_subsurf(obj)
				if self.coords == 'UV': self.move_uv(obj, i)

				listv = []
				mesh = obj.data

				bm = bmesh.new()
				bm.from_mesh(mesh)

				if self.displ_mode == 'SELECTION':
					listv = self.assign_vgroup(obj, bm)
				else: listv = bm.verts

				if listv:
					self.rot_sca(obj, bm, listv, i)

					bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, fractal=self.fractal, \
						along_normal=self.along_normal, cuts=self.cuts_base, seed=self.noise_seed, use_grid_fill=True, \
						use_smooth_even=True)

					if self.displ_mode == 'SELECTION':
						vgroup = obj.vertex_groups.get(self.vg_name, None)
						if vgroup:
							idx = vgroup.index
							deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()

							for n in range(self.subtract_sel):
								border_verts = [v for v in bm.verts if idx in v[deform_layer] and \
									any(e for e in v.link_edges if not idx in e.other_vert(v)[deform_layer])]

								for v in border_verts:
									del v[deform_layer][idx]

							expansion_verts = set()
							for n in range(self.expand_subtr):
								if n == 0:
									expansion_line = [v for v in bm.verts if idx in v[deform_layer] and \
										any(e for e in v.link_edges if not e.other_vert(v)[deform_layer])]
								else:
									expansion_line = [v for v in bm.verts if idx in v[deform_layer] and \
										any(e for e in v.link_edges if e.other_vert(v) in expansion_verts) and \
										not v in expansion_verts]

								for v in expansion_line:
									v[deform_layer][idx] = (1 * (1 / self.expand_subtr)) * n
									expansion_verts.add(v)

					bm.to_mesh(mesh)
					mesh.update()

					self.set_displacement(obj, i)
				else:
					bm.free()
					self.report({'WARNING'}, "No face selection detected.")

		return {"FINISHED"}

	def draw(self, context):

		props = context.scene.rflow_props

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Type:")
		row.row(align=True).prop(self, "displ_type", text="")
		if self.displ_type == 'IMAGE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Image:")
			row.prop_search(
				self,
				"img_name",
				self,
				"images",
				text="",
				icon = "IMAGE_DATA"
				)
		if self.displ_type == 'CLOUDS':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Noise Basis:")
			row.row(align=True).prop(self, "noise_basis", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Mode:")
		row.row(align=True).prop(self, "displ_mode", expand=True)
		if self.displ_mode == 'SELECTION':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Smoothing:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "subtract_sel")
			split.row(align=True).prop(self, "expand_subtr")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Coordinates:")
		row.row(align=True).prop(self, "coords", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Strength:")
		row.row(align=True).prop(self, "strength", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Midlevel:")
		row.row(align=True).prop(self, "mid_level", text="")
		if self.displ_type == 'CLOUDS':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Size:")
			row.row(align=True).prop(self, "noise_scale", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Depth:")
			row.row(align=True).prop(self, "noise_depth", text="")
		if self.coords == 'UV':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Location:")
			row.row(align=True).prop(self, "img_pos", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Seed:")
			row.row(align=True).prop(self, "pos_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Rotation:")
			row.row(align=True).prop(self, "img_rotation", text="")
		if self.displ_type == 'IMAGE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Size:")
			row.row(align=True).prop(self, "img_size", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Filter Size:")
			row.row(align=True).prop(self, "filter_size", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Brightness:")
		row.row(align=True).prop(self, "intensity", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Contrast:")
		row.row(align=True).prop(self, "contrast", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Smooth:")
		row.row(align=True).prop(self, "smooth_factor", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Repeat:")
		row.row(align=True).prop(self, "smooth_iter", text="")
		if self.coords == 'OBJECT':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Location:")
			row.row(align=True).prop(self, "location", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Location Seed:")
			row.row(align=True).prop(self, "loc_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Rotation:")
			row.row(align=True).prop(self, "rotation", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Rotation Seed:")
			row.row(align=True).prop(self, "rotation_seed", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale:")
			row.row(align=True).prop(self, "scale", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Scale Seed:")
			row.row(align=True).prop(self, "scale_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Noise:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "fractal")
		split.row(align=True).prop(self, "along_normal")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Noise Seed:")
		row.row(align=True).prop(self, "noise_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subsurf Level:")
		row.row(align=True).prop(self, "subd_lvl", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Obj Scale Max:")
		row.row(align=True).prop(self, "obj_sca_max", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Obj Scale Min:")
		row.row(align=True).prop(self, "obj_sca_min", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Scale Seed:")
		row.row(align=True).prop(self, "sca_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Obj Rotation:")
		row.row(align=True).prop(self, "obj_rot", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation Seed:")
		row.row(align=True).prop(self, "rot_seed", text="")

	def invoke(self, context, event):

		obj = context.active_object
		props = context.scene.rflow_props

		self.location = [0,0,0]
		self.rotation = [0,0,0]
		self.scale = [1,1,1]
		self.pos_seed = [1,1]
		self.loc_seed = [1,1,1]
		self.rotation_seed = [1,1,1]
		self.scale_seed = [1,1,1]
		self.noise_seed = 1
		self.sca_seed = [1,1,1]
		self.rot_seed = [1,1,1]
		self.img_name = ""
		self.images.clear()
		self.vg_name = "displ_rflow"

		if event.alt: get_linked_flat_faces(obj)

		for img in bpy.data.images:
			newListItem = self.images.add()
			newListItem.name = img.name

		init_props(self, event, ops='ndispl', force=len(obj.data.polygons)>=props.select_limit)
		prefs = context.preferences.addons[__package__].preferences

		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_partition_mesh(Operator):
	'''Randomly partition mesh. Ctrl+click to merge'''
	bl_idname = 'part_mesh.rflow'
	bl_label = 'Partition Mesh'
	bl_options = {'REGISTER', 'UNDO'}

	mode : EnumProperty(
		name = 'Mode',
		description = "Use random solver or capture sharp edge for splitting",
		items = (
			('RANDOM', 'Random','Split edges using random solvers'),
			('SHARP', 'Sharp','Split edges from sharp edges'),
			('SELECT', 'Selection','Split edges from selection borders')),
		default = 'RANDOM'
		)
	solver : EnumProperty(
		name = 'Solver',
		description = "Determines the method of generating islands",
		items = (
			('WALK', 'Walk','Expand island by walking previous cells'),
			('RADIAL', 'Radial','Expand island by radial expansion'),
			('SQUARE', 'Square','Expand island by square shapes')),
		default = 'WALK'
		)
	path : EnumProperty(
		name = 'Path',
		description = "Determines what edge length to favor when generating new island cells",
		items = (
			('NONE', 'None','Do not favor any edge length when generating islands'),
			('SHORTEST', 'Shortest','Favor shorter edges when generating islands'),
			('LONGEST', 'Longest','Favor longer edges when generating islands')),
		default = 'NONE'
		)
	size_mode : EnumProperty(
		name = 'Size Mode',
		items = (
			('PERCENT', 'Percent',''),
			('NUMBER', 'Number','')),
		default = 'PERCENT'
		)
	panel_amount : FloatProperty(
		name        = "Panel Amount",
		description = "Total number of panel islands",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 100,
		subtype     = "PERCENTAGE"
		)
	panel_max_perc : FloatProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		min         = 0,
		max         = 100,
		soft_min    = 1,
		precision   = 0,
		default     = 5,
		subtype     = "PERCENTAGE"
		)
	panel_max_num : IntProperty(
		name        = "Panel Size",
		description = "Randomized panel size",
		default     = 100,
		min         = 0,
		soft_min    = 1,
		soft_max    = 1000,
		step        = 1
		)
	panel_min_perc : FloatProperty(
		name        = "Minimum Size",
		description = "Minimum panel size for radial sampling",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 0,
		subtype     = "PERCENTAGE"
		)
	panel_min_num : IntProperty(
		name        = "Minimum Size",
		description = "Minimum panel size for radial sampling",
		default     = 0,
		min         = 0,
		soft_max    = 1000,
		step        = 1
		)
	edge_seed : IntProperty(
		name        = "Seed",
		description = "Randomize panel cuts",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	angle_sharp : FloatProperty(
		name        = "Sharpness",
		description = "Maximum angle threshold for edges to be cut",
		default     = radians(15),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	cut_method : EnumProperty(
		name = "Cut Method",
		description = "Determines how sharp edges will be cut",
		items = (
			('WRAP', 'Wrap',''),
			('SPLIT', 'Split','')),
		default = 'WRAP'
		)
	merge_dist : FloatProperty(
		name        = "Merge Distance",
		description = "Merge vertices based on their proximity",
		default     = 0.0001,
		min         = 0.00001,
		soft_max    = 10.0,
		step        = 0.01,
		precision   = 4
		)
	dissolve_dist : FloatProperty(
		name        = "Degenerate Dissolve Distance",
		description = "Maximum distance between elements to merge",
		default     = 0.0001,
		min         = 0.00001,
		soft_max    = 10.0,
		step        = 0.01,
		precision   = 4
		)
	dissolve_count : IntProperty(
		name        = "Degenerate Dissolve Count",
		description = "Number of times the mesh will use degenerate dissolve to get rid of zero area faces",
		default     = 100,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	only_similar : BoolProperty(
		name        = "Only Similar",
		description = "Merge only meshes that share even a single vertex location. (Slower)",
		default     = False
		)
	clear_fill : BoolProperty(
		name        = "Clear Fill Faces",
		description = "Remove faces resulting from filling holes by maximum area",
		default     = True
		)
	max_face_area : FloatProperty(
		name        = "Max Area",
		description = "Maximum face area to keep when removing fill faces",
		default     = 0.0001,
		min         = 0,
		soft_max    = 10.0,
		step        = 0.01,
		precision   = 4
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def use_data(self, mesh, data_copy):

		if mesh.is_editmode:
			bm = bmesh.from_edit_mesh(mesh)
		else:
			bm = bmesh.new()
			bm.from_mesh(mesh)

		bm.clear()
		bm.from_mesh(data_copy)

		for f in bm.faces: f.select = True

		if mesh.is_editmode:
			bmesh.update_edit_mesh(mesh)
		else:
			bm.to_mesh(mesh)
			mesh.update()

	def execute(self, context):

		obj = context.active_object

		def randomize_edges(bm, faces):

			idx = set([f.index for f in faces])
			if self.size_mode == 'PERCENT':
				numf = len(idx)
				size1 = int(ceil(numf * (self.panel_min_perc/100)))
				size2 = int(ceil(numf * (self.panel_max_perc/100)))
			else:
				size1 = self.panel_min_num
				size2 = self.panel_max_num

			min_size = min(size1, size2)
			max_size = max(size1, size2)

			split_edg, cells = random_walk(bm, idx, min_size, max_size, self.edge_seed, sampling=self.solver, \
				notch_count=0, notch_size=0, notch_snum=1, path=self.path, cut_threshold=radians(30), wrap_angle=self.cut_method == 'WRAP')

			return split_edg, cells

		if obj.data.is_editmode:
			bpy.ops.object.editmode_toggle()

		if self.merge:
			adopted = []
			adopted_parents = []

			init_sel = context.selected_objects[:]

			for o in init_sel:
				if o != obj:
					o.select_set(False)
					adopted.append(o)
					if o.parent:
						adopted_parents.append(o.parent)

			family = []
			clan = []

			grand_parent = []
			orphans = []

			parent_src = None
			children_src = []

			if obj.children:
				parent_src = obj
				children_src = obj.children
			else:
				if obj.parent:
					parent_src = obj.parent
					children_src = parent_src.children

			if parent_src:
				for c in parent_src.children:
					if c.name.find("PMesh") == -1: orphans.append(c)

				if parent_src.parent: grand_parent = parent_src.parent

			def add_family(o):

				parent = o.parent

				if parent \
					and not parent in clan:
					family.append(parent)
					clan.append(parent)

			family.append(obj)

			while family:
				p = family.pop()
				p.select_set(True)

				add_family(p)

				for ch in p.children_recursive:
					ch.select_set(True)
					add_family(ch)

			sel_objs = context.selected_objects[:]

			for o in sel_objs:
				if len(init_sel) == 1 and o.name.find("PMesh") == -1: o.select_set(False)
				if o.children and o != parent_src: o.select_set(False)
				if not o in children_src and o != parent_src: o.select_set(False)
				if o.parent and o.parent == parent_src: orphans.append(o)

			if adopted:
				for o in adopted: o.select_set(True)
				obj.select_set(True)

			if self.only_similar:
				while sel_objs:
					obj1 = sel_objs.pop()
					for obj2 in context.selected_objects:
						if obj2 != obj1 \
							and get_similarity(obj1, obj2.data, obj1.matrix_world, obj2.matrix_world, use_matrix=True) > 0:
							break
					else: obj1.select_set(False)

			if context.selected_objects:
				context.view_layer.objects.active = context.selected_objects[-1]

				bpy.ops.object.join()

				join_obj = context.active_object
				mesh = join_obj.data

				bm = bmesh.new()
				bm.from_mesh(mesh)

				bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=self.merge_dist)
				ret = bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)['faces']

				if self.clear_fill:
					nonzero_areas = [f for f in ret if f.calc_area() > self.max_face_area]
					bmesh.ops.delete(bm, geom=nonzero_areas, context='FACES')

				for n in range(self.dissolve_count):
					for f in bm.faces:
						if f.calc_area() == 0:
							bmesh.ops.dissolve_degenerate(bm, dist=self.dissolve_dist, edges=bm.edges)
							break
					else: break

				bm.to_mesh(mesh)
				mesh.update()

				areas = np.zeros(len(mesh.polygons), dtype=float)
				mesh.polygons.foreach_get('area', areas)

				self.report({'INFO'}, "Operation completed with " + str(np.count_nonzero(areas == 0)) + " zero area faces remaining.")

				join_obj.name = join_obj.name.split("_PMesh")[0]

				refresh_vcolor(join_obj)

				for o in orphans:
					if o in list(bpy.data.objects) and o != join_obj: set_parent(join_obj, o)

				if grand_parent \
					and grand_parent in list(bpy.data.objects):
					set_parent(grand_parent, join_obj)
				else:
					if adopted_parents \
						and grand_parent in list(bpy.data.objects):
						set_parent(adopted_parents[-1], join_obj)
		else:
			select_isolate(obj)

			mesh = obj.data

			bm = bmesh.new()
			bm.from_mesh(mesh)

			split_edg = []

			if self.mode == 'RANDOM':
				faces = [f for f in bm.faces if f.select]
				split_edg, _ = randomize_edges(bm, faces)
			elif self.mode == 'SHARP':
				edges = [e for e in bm.edges if e.select]
				for e in edges:
					append_edge = False

					angle = e.calc_face_angle(None)
					if angle and angle > self.angle_sharp: append_edge = True

					if len(edges) != len(bm.edges):
						if len([f for f in e.link_faces if f.select]) == 1: append_edge = True

					if append_edge: split_edg.append(e)
			else:
				for e in bm.edges:
					if e.select:
						if len([f for f in e.link_faces if f.select]) == 1: split_edg.append(e)

			bmesh.ops.split_edges(bm, edges=split_edg)

			bm.to_mesh(mesh)
			mesh.update()

			islands = get_islands(obj, bm=None)

			list_objs = []
			if len(islands) > 1:
				obj.name = filter_name(obj, "_PMesh")
				for i, isle in enumerate(islands):
					if i == 0:
						orig_mesh = obj.data.copy()

						bm = bmesh.new()
						bm.from_mesh(orig_mesh)

						verts = [v for v in bm.verts if not v.index in isle]
						bmesh.ops.delete(bm, geom=verts, context='VERTS')

						bm.to_mesh(orig_mesh)
						orig_mesh.update()
					else:
						bm_split = bmesh.new()
						split_mesh = bpy.data.meshes.new(".split")
						bm_split.from_mesh(mesh)

						verts = [v for v in bm_split.verts if not v.index in isle]
						bmesh.ops.delete(bm_split, geom=verts, context='VERTS')

						bm_split.to_mesh(split_mesh)
						bm_split.free()

						split_obj = bpy.data.objects.new(filter_name(obj, "_PMesh"), split_mesh)
						orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
						split_obj.scale = orig_scale
						split_obj.rotation_euler = orig_rot.to_euler()
						split_obj.location = orig_loc

						for col in obj.users_collection: col.objects.link(split_obj)

						list_objs.append(split_obj)

						refresh_vcolor(split_obj)

				self.use_data(obj.data, orig_mesh)
				list_objs.append(obj)

				for new_obj in list_objs:
					if new_obj != obj:
						new_obj.parent = obj
						new_obj.matrix_parent_inverse = obj.matrix_world.inverted()

						if "sharp_edge" in obj.data.attributes:
							new_obj.data.set_sharp_from_angle(angle=radians(30))

						copy_modifiers([obj, new_obj])
						new_obj.data.polygons.foreach_set('select', [True] * len(new_obj.data.polygons))

				context.view_layer.objects.active = list_objs[0]

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		if self.merge:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Merge:")
			row.row(align=True).prop(self, "merge_dist", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Dissolve:")
			row.row(align=True).prop(self, "dissolve_dist", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Count:")
			row.row(align=True).prop(self, "dissolve_count", text="")
			col.separator(factor=0.5)
			col.prop(self, "only_similar")
			col.prop(self, "clear_fill")
			if self.clear_fill:
				col.prop(self, "max_face_area")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mode:")
			row.row(align=True).prop(self, "mode", expand=True)
			if self.mode == 'RANDOM':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Solver:")
				row.row(align=True).prop(self, "solver", expand=True)
				if not self.solver in ['RADIAL', 'SQUARE']:
					row = col.row().split(factor=0.27, align=True)
					row.label(text="Path:")
					row.row(align=True).prop(self, "path", expand=True)
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Size Mode:")
				row.row(align=True).prop(self, "size_mode", expand=True)
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Panel Size:")
				split = row.split(factor=0.5, align=True)
				if self.size_mode == 'PERCENT':
					split.row(align=True).prop(self, "panel_min_perc", text="Min")
					split.row(align=True).prop(self, "panel_max_perc", text="Max")
				else:
					split.row(align=True).prop(self, "panel_min_num", text="Min")
					split.row(align=True).prop(self, "panel_max_num", text="Max")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Panel Seed:")
				row.row(align=True).prop(self, "edge_seed", text="")
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Cut Method:")
				row.row(align=True).prop(self, "cut_method", expand=True)
			if self.mode == 'SHARP':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Sharpness:")
				row.row(align=True).prop(self, "angle_sharp", text="")

	def invoke(self, context, event):

		obj = context.active_object

		self.merge = False

		if event.alt: get_linked_flat_faces(obj)

		if event.ctrl:
			self.merge = True
			return self.execute(context)
		else:
			obj.update_from_editmode()
			has_face = count_selected_faces(obj)

			if has_face:
				prefs = context.preferences.addons[__package__].preferences
				if prefs.use_confirm:
					return context.window_manager.invoke_props_dialog(self)
				else:
					return context.window_manager.invoke_props_popup(self, event)
			else:
				self.report({'WARNING'}, "No faces selected.")
				return {"FINISHED"}

class FILES_OT_append_materials(Operator):
	'''Append materials to the scene'''
	bl_idname = 'append_mats.rflow'
	bl_label = 'Append Materials'
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):

		mat_count = len(bpy.data.materials)

		path =  os.path.join(os.path.dirname(
			os.path.abspath(__file__)), "./materials/")
		files = os.listdir(path)

		blend_files = []
		for file in files:
			if file.endswith(".blend"):
				 blend_files.append(os.path.join(path, file))

		for filepath in blend_files:
			with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
				data_to.materials = data_from.materials

		self.report({'INFO'}, "Appended " + str(len(bpy.data.materials) - mat_count) + " materials.")

		return {'FINISHED'}

	def draw(self, context): None

class FILES_OT_image_browser(Operator, ImportHelper):
	'''Import multiple images'''
	bl_idname = 'img_browser.rflow'
	bl_label = 'Load Image(s)'
	bl_options = {'REGISTER', 'UNDO'}

	filter_glob: StringProperty(
		default     = '*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp',
		options     = {'HIDDEN'}
	)

	files: CollectionProperty(
		type        = bpy.types.OperatorFileListElement,
		options     = {'HIDDEN', 'SKIP_SAVE'}
			)

	def execute(self, context):

		try:
			dirname = os.path.dirname(self.filepath)
			for meshfile in self.files:
				img = (os.path.join(dirname, meshfile.name))
				bpy.data.images.load(img, check_existing=True)
		except: self.report({'WARNING'}, "File not found.")

		return {'FINISHED'}

	def draw(self, context): None

	def invoke(self, context, event):

		self.filepath = ""
		context.window_manager.fileselect_add(self)

		return {'RUNNING_MODAL'}

class OBJECT_OT_auto_mirror(Operator):
	'''Add mirror modifier on selected objects'''
	bl_idname = 'auto_mirror.rflow'
	bl_label = 'Auto Mirror'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def create_header(self):

		def enumerate_axis(axes):

			axis_text = ""
			for i in "XYZ":
				if axes[str(i)]: axis_text += i

			return axis_text

		axis_text = enumerate_axis(self.axes)

		if self.set_axis:
			header = ", ".join(filter(None,
				[
				"Mirror Axis: " + (axis_text.lstrip() if axis_text else "None"),
				"R: Reset axis toggles",
				"Enter/Space: Confirm",
				"Right Click/Esc: Cancel",
				]))
		else:
			header = ", ".join(filter(None,
				[
				"Left Click area to mirror",
				"Right Click/Esc: Cancel",
				]))

		return header.format()

	def pick_axis(self, context, co):

		hit, normal, face_index, _ = scene_ray_hit(context, co, ray_obj=self.mirror_obj, hit_bounds=True)

		return hit, normal, face_index

	def update_mirror(self, obj, origin):

		mesh = obj.data
		bm = bmesh.new()
		bm.from_mesh(mesh)

		pivot = Vector()
		axis = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]

		x_dir = axis[0] if origin.x > 0 else -axis[0]
		y_dir = axis[1] if origin.y > 0 else -axis[1]
		z_dir = axis[2] if origin.z > 0 else -axis[2]

		axis_dir = [x_dir if self.axes['X'] else None, \
			y_dir if self.axes['Y'] else None, \
			z_dir if self.axes['Z'] else None]

		for n in axis_dir:
			if n:
				split = bm.verts[:] + bm.edges[:] + bm.faces[:]
				bmesh.ops.bisect_plane(
					bm,
					geom        = split,
					dist        = 0.0001,
					plane_co    = pivot,
					plane_no    = n,
					clear_inner = True,
					clear_outer = False
					)

		bm.to_mesh(mesh)
		mesh.update()

		self.mirror_add(obj, self.axes['X'], self.axes['Y'], self.axes['Z'])

	def mirror_apply(self, obj):

		mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
		if mirror:
			name = mirror.name
			bpy.ops.object.modifier_move_to_index(modifier=name, index=0)
			bpy.ops.object.modifier_apply(modifier=name)

	def mirror_add(self, obj, x=False, y=False, z=False):

		mod = obj.modifiers
		md = mod.new("Mirror", "MIRROR")
		md.use_axis[0] = x
		md.use_axis[1] = y
		md.use_axis[2] = z
		md.use_clip = True
		md.use_mirror_merge = True
		md.show_expanded = False
		md.show_in_editmode = True
		md.show_on_cage = False

		bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)

	def clear_mesh_list(self):

		mirror_set = [
			self.center_axis,
			self.color_axis,
			]

		for o in mirror_set: remove_obj(o)

		for o in bpy.data.meshes:
			if not o in self.mesh_list \
				and o.users == 0: bpy.data.meshes.remove(o)

	def confirm_op(self, context):

		self.clear_mesh_list()
		context.window.cursor_modal_restore()
		bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

		if self.prev_mode == 'EDIT':
			bpy.ops.object.editmode_toggle()

	def modal(self, context, event):

		context.area.tag_redraw()
		self.mouse_co = event.mouse_region_x, event.mouse_region_y

		if event.type in {
			'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
			'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_6',
			'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_5'}:
			return {'PASS_THROUGH'}

		if not self.set_axis:
			if event.type == 'LEFTMOUSE':
				if event.value == 'PRESS':
					hit, _, _ = self.pick_axis(context, self.mouse_co)
					if hit:
						self.mirror_axis = hit
						context.window.cursor_modal_restore()
						self.set_axis = True
					else:
						self.report({'WARNING'}, ("Mirror axis not found!"))
						self.confirm_op(context)
						return {'FINISHED'}
		else:
			if event.type == 'R':
				if event.value == 'RELEASE':
					for axis in self.axes: self.axes[axis] = False

			axis_keys = ['X', 'Y', 'Z']
			if event.type in axis_keys:
				for i, x in enumerate(axis_keys):
					if event.type == x:
						if event.value == 'RELEASE':
							self.axes[axis_keys[i]] = False if self.axes[axis_keys[i]] else True

			if event.type in {'RET', 'NUMPAD_ENTER', 'SPACE'}:
				if event.value == 'PRESS':
					for obj in self.sel_obj:
						context.view_layer.objects.active = obj
						self.mirror_apply(obj)
						if next((axis for i, axis in enumerate(self.axes) \
							if self.axes[axis]), None):
							self.update_mirror(obj, self.mirror_obj.matrix_world.inverted() @ self.mirror_axis)

					context.view_layer.objects.active = self.mirror_obj
					self.confirm_op(context)

					return {'FINISHED'}

		if event.type in {'RIGHTMOUSE', 'ESC'}:
			self.confirm_op(context)

			return {'CANCELLED'}

		return {'RUNNING_MODAL'}

	def invoke(self, context, event):

		args = (self, context)

		self.mesh_list = [o for o in bpy.data.meshes]
		obj = self.mirror_obj = context.active_object
		mesh = obj.data

		self.prev_mode = obj.mode
		if mesh.is_editmode:
			bpy.ops.object.editmode_toggle()

		self.sel_obj = context.selected_objects

		self.mouse_co = []
		self.mirror_axis = Vector()
		self.set_axis = False
		self.axes = {axis:False for axis in ['X', 'Y', 'Z']}

		self.center_axis = create_temp_obj("Center Axis")
		self.color_axis = create_temp_obj("Color Axis")

		mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
		axis_toggles = []
		if mirror:
			axis_toggles = [i for i in mirror.use_axis]
			for n, axis in enumerate(self.axes):
				self.axes[axis] = axis_toggles[n]

		context.window.cursor_modal_set("EYEDROPPER")
		self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_quick_symm, args, 'WINDOW', 'POST_PIXEL')
		context.window_manager.modal_handler_add(self)

		return {'RUNNING_MODAL'}

class OBJECT_OT_extract_proxy(Operator):
	'''Extract faces from active object'''
	bl_idname = 'extr_proxy.rflow'
	bl_label = 'Extract Faces'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):

		return context.active_object is not None

	def initialize(self, context, set = True):

		if set:
			self.create_applied_mesh(context, self.orig_obj, self.orig_dup)
			context.window.cursor_modal_set("CROSSHAIR")
		else:
			self.clear_extract()
			context.area.header_text_set(None)
			context.window.cursor_modal_restore()

	def delta_increment(self, event, x, y, dim):

		delta = abs(x - y)
		incr =  dim * (0.01 * (0.1 if event.shift else 1))
		v = delta * incr

		return v

	def move_origin(self, copy_obj, obj):

		new_origin = copy_obj.matrix_world.translation
		pivot = obj.matrix_world.inverted() @ new_origin
		obj.data.transform(Matrix.Translation(pivot))

	def update_extract(self, context, obj):

		obj.data = self.orig_dup.data.copy()
		self.move_origin(self.orig_dup, obj)

		sce = context.scene
		mat = obj.matrix_world

		mesh = obj.data
		bm = bmesh.new()
		bm.from_mesh(mesh)

		bm.faces.ensure_lookup_table()

		remove_faces = []
		inset_faces = []

		for i in range(len(bm.faces)):
			if not bm.faces[i].index in self.extract_faces:
				remove_faces.append(bm.faces[i])
			else:
				inset_faces.append(bm.faces[i])

		if abs(self.inset_val) > 0:
			if self.inset_indv:
				ret = bmesh.ops.inset_individual(bm, faces=inset_faces, use_even_offset=True, thickness=self.inset_val)
			else:
				ret = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, use_even_offset=True, thickness=self.inset_val)

			remove_faces.extend(ret['faces'])

		bmesh.ops.delete(bm, geom=remove_faces, context='FACES')

		bm.to_mesh(mesh)
		mesh.update()

	def get_origin(self, context, co):

		hit, normal, face_index, _ = scene_ray_hit(context, co, ray_obj=self.orig_dup)

		return hit, normal, face_index

	def select_faces(self, context, event, add=True):

		scene = context.scene
		props = scene.rflow_props

		mouse_pos = event.mouse_region_x, event.mouse_region_y
		hit, normal, index = self.get_origin(context, mouse_pos)

		def assign_extract_faces(add, index):

			undo_index = []

			if add:
				if index not in self.extract_faces:
					self.extract_faces.append(index)
					undo_index.append(index)
			else:
				if index in self.extract_faces:
					self.extract_faces.remove(index)
					undo_index.append(index)

			return undo_index

		if hit:
			if self.select_plus or \
				self.loop_select:

				dim = self.orig_obj.dimensions.copy()
				avg_dim = sum(d for d in dim)/len(dim)

				mw = self.orig_dup.matrix_world
				mesh = self.orig_dup.data

				bm = bmesh.new()
				bm.from_mesh(mesh)

				bm.faces.ensure_lookup_table()

				if self.select_plus:
					pick_normal = bm.faces[index].normal
					active_median = bm.faces[index].calc_center_median() @ self.orig_dup.matrix_world

					result = set()
					traversal_stack = [bm.faces[index]]

					while len(traversal_stack) > 0:
						f_curr = traversal_stack.pop()
						result.add(f_curr)

						for e in f_curr.edges:
							if e.is_contiguous and e.smooth and not e.seam:
								for f_linked in e.link_faces:
									if f_linked not in result:
										if (f_linked.calc_center_median()-active_median).length <= ((avg_dim / 2) * props.select_influence):
											angle = f_curr.normal.angle(f_linked.normal, 0.0)
											if angle < radians(30): traversal_stack.append(f_linked)

					if result:
						undo_list = []
						for f in result:
							plus_selection = assign_extract_faces(add, f.index)
							undo_list.extend(plus_selection)

						if undo_list: self.undo_faces.append(undo_list)

				if self.loop_select:
					face = bm.faces[index]
					loc = None
					closest_edge = None
					start_loop = None

					def face_loop_select(start_loop, limit, reverse=False):

						indices = []
						cancel = False

						for i in range(limit):
							if not reverse:
								next_loop = start_loop.link_loop_next.link_loop_radial_next.link_loop_next
								next_edge = start_loop.link_loop_next.edge
							else:
								next_loop = start_loop.link_loop_prev.link_loop_radial_prev.link_loop_prev
								next_edge = start_loop.link_loop_prev.edge

							if next_loop.face == face or \
								len(next_loop.face.edges) != 4:
								cancel = True

							angle = next_edge.calc_face_angle(None)
							if next_edge.is_boundary or \
								next_edge.smooth == False or next_edge.seam: cancel = True

							if cancel: break

							selection = assign_extract_faces(add, next_loop.face.index)
							if selection: indices.extend(selection)

							start_loop = next_loop

						return indices

					for i, e in enumerate(face.loops):
						vloc = sum([(mw @ v.co) for v in e.edge.verts], Vector()) / len(e.edge.verts)
						coord_2d = v3d_to_v2d([vloc])
						closest_edge = (Vector((mouse_pos)) - Vector((coord_2d[0][0], coord_2d[0][1]))).length

						if not loc: loc = closest_edge
						if closest_edge <= loc:
							loc = closest_edge
							start_loop = face.loops[i-1]

					if start_loop:
						undo_list = []

						first_face = assign_extract_faces(add, start_loop.face.index)
						undo_list.extend(first_face)

						for i in range(0, 2):
							face_loops = face_loop_select(start_loop, len(bm.faces), reverse=False if i else True)
							undo_list.extend(face_loops)

						if undo_list: self.undo_faces.append(undo_list)

				bm.to_mesh(mesh)
				mesh.update()
			else:
				undo_list = assign_extract_faces(add, index)
				if undo_list: self.undo_faces.append(undo_list)

			self.update_extract(context, self.extr_obj)

	def get_closest(self, obj, hit, radius):

		mesh = obj.data

		size = len(mesh.vertices)
		kd = kdtree.KDTree(size)

		for i, v in enumerate(mesh.vertices):
			kd.insert(v.co, i)

		kd.balance()

		co_find = obj.matrix_world.inverted() @ hit

		vertices = []
		for (co, index, dist) in kd.find_range(co_find, radius):
			vertices.append(index)

		return vertices

	def create_applied_mesh(self, context, orig_obj, orig_dup):

		def apply_modifier_list(obj, apply_list):

			mod = obj.modifiers

			for m in mod:
				if m.type not in apply_list:
					mod.remove(m)

			obj.data = get_eval_mesh(obj).copy()
			obj.modifiers.clear()
			bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

		for obj in context.selected_objects:
			obj.select_set(False if obj != orig_dup else True)

		context.view_layer.objects.active = orig_dup
		orig_loc, orig_rot, orig_scale = orig_obj.matrix_world.decompose()
		orig_dup.scale = orig_scale
		orig_dup.rotation_euler = orig_rot.to_euler()
		orig_dup.location = orig_loc

		copy_modifiers([orig_obj, orig_dup])
		apply_modifier_list(orig_dup, ['MIRROR', 'SOLIDIFY', 'BOOLEAN', 'ARRAY', 'SUBSURF'])

		self.orig_dup.hide_set(True)

	def new_mesh_data(self, name):

		new_data = bpy.data.meshes.new(name)
		new_obj = bpy.data.objects.new(name, new_data)

		return new_obj

	def clear_mesh_list(self):

		for o in bpy.data.meshes:
			if o not in self.mesh_list \
				and o.users == 0:
				bpy.data.meshes.remove(o)

	def clear_extract(self):

		remove_obj(self.orig_dup)
		self.clear_mesh_list()

	def cancel_extract(self, context):

		remove_obj(self.extr_obj)
		self.clear_mesh_list()

		self.initialize(context, set=False)
		self.remove_handlers()

		self.orig_obj.select_set(True)
		context.view_layer.objects.active = self.orig_obj

	def remove_handlers(self):

		bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
		bpy.types.SpaceView3D.draw_handler_remove(self._handle1, 'WINDOW')

	def modal(self, context, event):

		context.area.tag_redraw()

		scene = context.scene
		props = scene.rflow_props
		extr_obj = self.extr_obj
		self.mouse_co = event.mouse_region_x, event.mouse_region_y

		if event.type == 'MIDDLEMOUSE':
			self.render_hit = False
		else: self.render_hit = True

		if event.type in {
			'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
			'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_6',
			'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_5'}:
			return {'PASS_THROUGH'}

		if event.type in {'TAB'}:
			if event.value == 'RELEASE':
				view = context.region_data.view_perspective
				if view == "PERSP":
					context.region_data.view_perspective = "ORTHO"
				else: context.region_data.view_perspective = "PERSP"

		if event.type == 'H':
			if event.value == 'RELEASE':
				self.help_index += 1
				if self.help_index > 2: self.help_index = 1

		if event.type == 'X':
			if event.value == 'RELEASE':
				self.draw_solid ^= True

		if not event.ctrl:
			self.draw_strips = False
			self.render_hit = True
			context.window.cursor_modal_restore()

		if event.type == 'MOUSEMOVE':
			if self.view_render_hit:
				mouse_pos = event.mouse_region_x, event.mouse_region_y
				hit, normal, index = self.get_origin(context, mouse_pos)

				if hit:
					rv3d = context.region_data
					mesh = self.orig_dup.data
					draw_face = mesh.polygons[index]

					if self.view_mat1 != rv3d.view_matrix:
						vertices = np.empty((len(mesh.vertices), 3), 'f')
						mesh.vertices.foreach_get("co", np.reshape(vertices, len(mesh.vertices) * 3))

						mwv = [self.orig_dup.matrix_world @ Vector(v) for v in vertices]
						self.hit_verts = v3d_to_v2d(mwv)

						# refresh?
						self.view_mat1 = rv3d.view_matrix.copy()

					self.hit_indices = [k for i, k in enumerate(draw_face.edge_keys)]

			if self.lmb:
				self.select_faces(context, event, True)

			if self.rmb:
				self.select_faces(context, event, False)

			if event.ctrl:
				self.draw_strips = True
				self.render_hit = False
				context.window.cursor_modal_set("CROSSHAIR")

				if extr_obj.data.polygons:
					self.draw_strips = True

					delta_x, delta_y = get_delta(context, event, extr_obj, local_center(extr_obj))
					v2 = delta_increment(event, delta_x, delta_y, self.avg_dim)

					if delta_x <= delta_y:
						self.inset_val += v2
					else:
						self.inset_val -= v2

					self.update_extract(context, extr_obj)

		if event.type == 'A':
			if event.value == 'PRESS':
				incr = 0.01 if event.shift else 0.1
				props.select_influence -= incr

		if event.type == 'D':
			if event.value == 'PRESS':
				incr = 0.01 if event.shift else 0.1
				props.select_influence += incr

		if event.type == 'LEFTMOUSE':
			if event.shift and \
				not event.alt and \
				not event.ctrl:
				self.select_plus = True
			else: self.select_plus = False

			if event.shift \
				and event.alt \
				and not event.ctrl:
					self.loop_select = True
			else: self.loop_select = False

			self.select_faces(context, event, True)
			self.lmb = event.value == 'PRESS'

		if event.type == 'RIGHTMOUSE':
			if event.shift and \
				not event.alt and \
				not event.ctrl:
				self.select_plus = True
			else: self.select_plus = False

			if event.shift \
				and event.alt \
				and not event.ctrl:
					self.loop_select = True
			else: self.loop_select = False

			self.select_faces(context, event, False)
			self.rmb = event.value == 'PRESS'

		if event.type == 'Z':
			if event.value == 'PRESS':
				select_list = self.undo_faces
				if len(select_list) > 0:
					for i in select_list[-1]:
						if i in self.extract_faces:
							self.extract_faces.remove(i)
						else:
							self.extract_faces.append(i)

					select_list.remove(select_list[-1])
					self.update_extract(context, self.extr_obj)

		if event.type == 'R':
			if event.value == 'RELEASE':
				self.inset_val = 0.0
				self.undo_faces.append([i for i in self.extract_faces])
				self.extract_faces.clear()
				self.update_extract(context, self.extr_obj)

		if event.type == 'T':
			if event.value == 'RELEASE':
				self.inset_val = 0.0
				self.update_extract(context, self.extr_obj)

		if event.type == 'V':
			if event.value == 'RELEASE': self.view_render_hit ^= True

		if event.type in {'RET', 'NUMPAD_ENTER', 'SPACE'}:
			if event.value == 'PRESS':
				if len(self.extract_faces) > 0:
					scene.collection.objects.link(extr_obj)

					extr_obj.select_set(True)
					context.view_layer.objects.active = extr_obj

					move_center_origin(self.orig_obj.matrix_world.translation, extr_obj)
					copy_rotation(self.orig_obj, extr_obj)

					self.initialize(context, set=False)
					self.remove_handlers()

					return {'FINISHED'}
				else:
					self.report({'WARNING'}, "No selected faces.")
					self.cancel_extract(context)

					return {'FINISHED'}

		if event.type in {'ESC'}:
			self.cancel_extract(context)

			return {'CANCELLED'}

		return {'RUNNING_MODAL'}

	def invoke(self, context, event):

		if context.area.type == 'VIEW_3D':
			args = (self, context)

			obj = self.orig_obj = context.active_object

			dim = obj.dimensions.copy()
			self.avg_dim = sum(d for d in dim)/len(dim)
			self.mesh_list = [o for o in bpy.data.meshes]

			self.orig_dup = duplicate_obj('Temp_Mesh', obj, get_eval=False)
			self.orig_dup.data.materials.clear()
			self.extr_obj = self.new_mesh_data("Extr_Proxy")

			self.help_index = 1

			self.extract_faces = []
			self.undo_faces = []
			self.hit_verts = []
			self.hit_indices = []

			self.lmb = False
			self.rmb = False

			self.view_mat1 = Matrix()

			self.render_hit = True
			self.view_render_hit = True
			self.loop_select = False
			self.select_plus = False

			self.draw_strips = False
			self.draw_solid = True

			self.inset_val = 0.0
			self.inset_indv = False

			self.mouse_co = []

			self.initialize(context, set=True)

			self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_draw_extract, args, 'WINDOW', 'POST_PIXEL')
			self._handle1 = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_draw_extract_shade, args, 'WINDOW', 'POST_VIEW')
			context.window_manager.modal_handler_add(self)

			return {'RUNNING_MODAL'}
		else:
			self.report({'WARNING'}, "View3D not found, cannot run operator.")

			return {'CANCELLED'}

class OBJECT_OT_apply_mesh(Operator):
	'''Apply modifiers/convert objects. Ctrl+click to apply mirror modifier only'''
	bl_idname = 'apply_mesh.rflow'
	bl_label = 'Apply Mesh'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def execute(self, context):

		objs = context.selected_objects

		for o in objs:
			context.view_layer.objects.active = o
			if o.type == 'MESH':
				mods = o.modifiers
				if o.data.materials or self.only_mirror:
					for m in mods:
						if m.type == "MIRROR":
							bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
							bpy.ops.object.modifier_apply(modifier=m.name)
						else:
							if not self.only_mirror:
								try:
									bpy.ops.object.modifier_apply(modifier=m.name)
								except:
									o.modifiers.remove(m)
				else:
					o.data = get_eval_mesh(o).copy()
					o.modifiers.clear()
			else:
				try:
					bpy.ops.object.convert(target='MESH')
				except: pass

		return {"FINISHED"}

	def draw(self, context): None

	def invoke(self, context, event):

		self.only_mirror = event.ctrl

		if not context.selected_objects:
			self.report({'WARNING'}, "No objects selected.")
			return {"FINISHED"}

		return self.execute(context)

class OBJECT_OT_join_objs(Operator):
	'''Join selected objects to a single mesh'''
	bl_idname = 'join_objs.rflow'
	bl_label = 'Join Objects'
	bl_options = {'REGISTER', 'UNDO'}

	list : StringProperty(
		name        = "Join To",
		description = "Join selected objects to this mesh"
		)
	meshes : CollectionProperty(type=PropertyGroup)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "OBJECT" \
			and context.active_object.type == "MESH"

	def verts_to_vgroup(self, obj, nsuffix):

		vg = obj.name
		nsuffix = str(nsuffix)

		if vg in [i.name for i in self.join_obj.vertex_groups]:
			vg = obj.name + "." + ("0" * (3-len(nsuffix))) + nsuffix

		group = obj.vertex_groups.get(vg) or obj.vertex_groups.new(name=vg)
		group_index = group.index

		mesh = obj.data
		bm = bmesh.new()
		bm.from_mesh(mesh)

		deform_layer = bm.verts.layers.deform.active
		if deform_layer is None: deform_layer = bm.verts.layers.deform.new()

		for v in bm.verts:
			v[deform_layer][group_index] = 1.0

		bm.to_mesh(mesh)
		bm.free()

	def execute(self, context):

		join_obj = self.join_obj = bpy.data.objects.get(self.list)

		if join_obj:
			for n, o in enumerate(context.selected_objects):
				o.select_set(True)
				context.view_layer.objects.active = o

				if o.type in ['MESH', 'CURVE']:
					if o.type == 'CURVE': bpy.ops.object.convert(target='MESH')
					if o == join_obj:
						if o.vertex_groups:
							mesh = o.data

							bm = bmesh.new()
							bm.from_mesh(mesh)

							for vg in o.vertex_groups:
								vgrp_faces = []
								for f in bm.faces:
									verts = [v.index for v in f.verts]
									vc = [vg.index in [g.group for g in mesh.vertices[i].groups] for i in verts].count(True)
									if vc == len(verts): vgrp_faces.append(f)

								linked_faces = get_linked_faces(vgrp_faces)

								if len(vgrp_faces) != len(linked_faces): o.vertex_groups.remove(vg)

							bm.free()

						if not o.vertex_groups:
							self.verts_to_vgroup(o, n)
					else:
						o.vertex_groups.clear()
						self.verts_to_vgroup(o, n)

					mods = o.modifiers
					for m in mods:
						if m.type == "MIRROR":
							bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
							bpy.ops.object.modifier_apply(modifier=m.name)
							break
				else:
					o.select_set(False)

			context.view_layer.objects.active = join_obj
			bpy.ops.object.join()

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Join To:")
		row.prop_search(
			self,
			"list",
			self,
			"meshes",
			text="",
			icon = "MESH_DATA"
			)

	def invoke(self, context, event):

		self.list = ""
		self.meshes.clear()

		objs = context.selected_objects

		if len(objs) > 1:
			for o in objs:
				if o.type in ['MESH', 'CURVE']:
					newListItem = self.meshes.add()
					newListItem.name = o.name

			if self.meshes: self.list = self.meshes[0].name

			return context.window_manager.invoke_props_dialog(self)
		else:
			self.report({'WARNING'}, "Must have two or more selections.")
			return {"FINISHED"}

class OBJECT_OT_split_mesh(Operator):
	'''Split mesh using vertex groups'''
	bl_idname = 'split_mesh.rflow'
	bl_label = 'Split Mesh'
	bl_options = {'REGISTER', 'UNDO'}

	list : StringProperty(
		name        = "Split From",
		description = "Split mesh from vertex group"
		)
	vgroups : CollectionProperty(type=PropertyGroup)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "OBJECT" \
			and context.active_object.type == "MESH"

	def execute(self, context):

		obj = context.active_object
		mesh = obj.data

		def get_verts(bm, vg):

			deform_layer = bm.verts.layers.deform.active
			group_index = vg.index

			return [v for v in bm.verts if not group_index in v[deform_layer]]

		list_objs = []
		if self.list:
			for vg in obj.vertex_groups:
				if vg.name != self.list:
					bm_split = bmesh.new()
					split_mesh = bpy.data.meshes.new(".split")
					bm_split.from_mesh(mesh)

					vlist = get_verts(bm_split, vg)
					bmesh.ops.delete(bm_split, geom=vlist, context='VERTS')

					bm_split.to_mesh(split_mesh)
					bm_split.free()

					if split_mesh.polygons:
						new_obj = bpy.data.objects.new(vg.name, split_mesh)
						orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
						new_obj.scale = orig_scale
						new_obj.rotation_euler = orig_rot.to_euler()
						new_obj.location = orig_loc
						context.scene.collection.objects.link(new_obj)
						list_objs.append(new_obj)

					obj.vertex_groups.remove(vg)

			bm = bmesh.new()
			bm.from_mesh(mesh)

			vlist = get_verts(bm, obj.vertex_groups[self.list])
			bmesh.ops.delete(bm, geom=vlist, context='VERTS')

			bm.to_mesh(mesh)
			mesh.update()
			bm.free()

			for o in list_objs:
				copy_modifiers([obj, o])

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Split From:")
		row.prop_search(
			self,
			"list",
			self,
			"vgroups",
			text="",
			icon = "GROUP_VERTEX"
			)

	def invoke(self, context, event):

		obj = context.active_object

		self.list = ""
		self.vgroups.clear()

		if len(obj.vertex_groups) > 1:
			for vg in obj.vertex_groups:
				newListItem = self.vgroups.add()
				newListItem.name = vg.name

			if self.vgroups: self.list = self.vgroups[0].name

			return context.window_manager.invoke_props_dialog(self)
		else:
			self.report({'WARNING'}, "Must have two or more vertex groups")
			return {"FINISHED"}

class OBJECT_OT_set_origin(Operator):
	'''Sets origin for scatter objects'''
	bl_idname = 'set_origin.rflow'
	bl_label = 'Set Origin'
	bl_options = {'REGISTER', 'UNDO'}

	origin : EnumProperty(
		name = "Origin",
		items = (
			('AXIS', 'Axis','Use axes for new origin'),
			('SELECTED', 'Selected','Use selected verts for new origin')),
		default = 'AXIS')
	axis : EnumProperty(
		name = "Origin",
		items = (
			('X', 'X',''),
			('Y', 'Y',''),
			('Z', 'Z','')),
		default = 'Z')
	location : EnumProperty(
		name = "Location",
		items = (
			('NEGATIVE', 'Negative','Find outermost verts in the negative axis direction'),
			('POSITIVE', 'Positive','Find outermost verts in the positive axis direction')),
		default = 'NEGATIVE')
	tolerance : FloatProperty(
		name        = "Tolerance",
		description = "Tolerance threshold for finding verts based on location",
		default     = 1e-4,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	use_farthest : BoolProperty(
		name        = "Use Farthest",
		description = "Use farthest location at this axis and do not average",
		default     = True
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH" \
			and context.active_object.mode == "OBJECT"

	def execute(self, context):

		objs = context.selected_objects

		for o in objs:
			mesh = o.data
			mat = o.matrix_world

			bm = bmesh.new()
			bm.from_mesh(mesh)

			points = []
			axis = ['X','Y','Z'].index(self.axis)
			if self.origin == 'AXIS':
				verts = sorted(bm.verts, key=lambda v: (mat @ v.co)[axis])
				if self.use_farthest:
					pos = verts[-1 if self.location == 'POSITIVE' else 0].co
					points = [Vector((pos[0] if self.axis == 'X' else 0,
						pos[1] if self.axis == 'Y' else 0,
						pos[2] if self.axis == 'Z' else 0
						))]
				else:
					pos = (verts[-1 if self.location == 'POSITIVE' else 0].co)[axis]
					points = [mat @ v.co for v in verts if abs((v.co)[axis] - pos) < self.tolerance]
			else:
				points = [mat @ v.co for v in bm.verts if v.select]
				if not points:
					self.report({'WARNING'}, "No verts selected.")

			bm.to_mesh(mesh)
			bm.free()

			if points:
				new_origin = sum(points, Vector()) / len(points)
				move_center_origin(new_origin, o)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.2, align=True)
		row.label(text="Origin:")
		row.row(align=True).prop(self, "origin", expand=True)
		col1 = col.column()
		col1.enabled = self.origin == 'AXIS'
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Axis:")
		row.row(align=True).prop(self, "axis", expand=True)
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Location:")
		row.row(align=True).prop(self, "location", expand=True)
		row = col1.row().split(factor=0.2, align=True)
		row.label(text="Tolerance:")
		row.row(align=True).prop(self, "tolerance", expand=True)
		col.separator(factor=0.5)
		col.prop(self, "use_farthest")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)

class OBJECT_OT_merge_objs(Operator):
	'''Merge selected meshes to an object'''
	bl_idname = 'merge_objs.rflow'
	bl_label = 'Merge Objects'
	bl_options = {'REGISTER', 'UNDO'}

	operand_type : EnumProperty(
		name = 'Operand Type',
		description = "Determines the method of generating islands",
		items = (
			('OBJ', 'Object','Use a mesh object as the operand for the Boolean operation'),
			('COLL', 'Collection','Use a collection of mesh objects as the operand for the Boolean operation')),
		default = 'OBJ'
		)
	list : StringProperty(
		name        = "Merge To",
		description = "Merge selected objects to this object"
		)
	meshes : CollectionProperty(type=PropertyGroup)
	offset_target : FloatProperty(
		name        = "Offset Target",
		description = "Offset target mesh vertices by this amount to fix overlap",
		default     = 0.0,
		min			= 0.0,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	offset_bool : FloatProperty(
		name        = "Offset Boolean",
		description = "Offset target mesh vertices by this amount to fix overlap",
		default     = 0.0,
		min			= 0.0,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	fill_holes : BoolProperty(
		name        = "Fill Holes",
		description = "Fill holes in the boolean meshes",
		default     = True
		)
	use_self : BoolProperty(
		name        = "Self Intersection",
		description = "Allow self-intersection in operands",
		default     = False
		)
	hole_tolr : BoolProperty(
		name        = "Hole Tolerant",
		description = "Better results when there are holes (slower)",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH" \
			and context.active_object.mode == "OBJECT"

	def group_obj(self, obj, grp):

		coll = bpy.data.collections.get(grp) or bpy.data.collections.new(grp)
		coll.objects.link(obj)

	def offset_mesh(self, obj, type='target'):

		mesh = obj.data

		bm = bmesh.new()
		bm.from_mesh(mesh)

		offset_val = self.offset_target if type == 'target' else self.offset_bool

		for v in bm.verts:
			v.co += v.normal * (v.calc_shell_factor() * offset_val)

		bm.to_mesh(mesh)
		bm.free()

	def fill_mesh(self, obj, bm=None):

		mesh = obj.data

		bm = bmesh.new()
		bm.from_mesh(mesh)

		e = [e for e in bm.edges if e.is_boundary]
		bmesh.ops.holes_fill(bm, edges=e)

		bm.to_mesh(mesh)
		bm.free()

	def apply_mesh(self, obj):

		save_data = obj.data.copy()
		obj.data.materials.clear()
		obj.data = get_eval_mesh(obj).copy()
		obj.modifiers.clear()

		for m in save_data.materials:
			obj.data.materials.append(m)

	def add_boolean(self, obj1=None, obj2=None, grp=""):

		mod = obj1.modifiers
		bool_op = mod.new('Boolean', 'BOOLEAN')
		if self.operand_type == 'OBJ':
			bool_op.operand_type = 'OBJECT'
			bool_op.object = obj2
		else:
			bool_op.operand_type = 'COLLECTION'
			bool_op.collection = bpy.data.collections[grp]
		bool_op.operation = 'UNION'
		bool_op.solver = 'EXACT'
		bool_op.use_self = self.use_self
		bool_op.use_hole_tolerant = self.hole_tolr
		bool_op.show_expanded = False

	def execute(self, context):

		merge_obj = bpy.data.objects.get(self.list)
		coll_name = "rflow_merge_objs"

		if merge_obj:
			context.view_layer.objects.active = merge_obj

			bool_objs = context.selected_objects[:]
			if not merge_obj in bool_objs: bool_objs.append(merge_obj)
			bool_objs.remove(merge_obj)

			if not bool_objs:
				self.report({'WARNING'}, "Select two or more objects.")
				return {"FINISHED"}

			if self.offset_target: self.offset_mesh(merge_obj)

			if self.operand_type == 'COLL':
				split_objs = []
				for o in bool_objs:
					if self.offset_bool: self.offset_mesh(o, type='bool')

					if o.type == 'MESH':
						o.data.materials.clear()
						o.data = get_eval_mesh(o).copy()
						o.modifiers.clear()

						mesh = o.data
						lparts = get_islands(o, None)

						if len(lparts) > 1:
							for p in lparts:
								bm = bmesh.new()
								temp_mesh = bpy.data.meshes.new(".temp")
								bm.from_mesh(mesh)

								v = [v for v in bm.verts if not v.index in p]
								bmesh.ops.delete(bm, geom=v, context='VERTS')

								if self.fill_holes:
									e = [e for e in bm.edges if e.is_boundary]
									bmesh.ops.holes_fill(bm, edges=e)

								bm.to_mesh(temp_mesh)
								bm.free()

								if temp_mesh.polygons:
									new_obj = bpy.data.objects.new(o.name, temp_mesh)
									orig_loc, orig_rot, orig_scale = o.matrix_world.decompose()
									new_obj.scale = orig_scale
									new_obj.rotation_euler = orig_rot.to_euler()
									new_obj.location = orig_loc
									bpy.context.scene.collection.objects.link(new_obj)

									self.group_obj(new_obj, coll_name)
									split_objs.append(new_obj)
						else:
							new_obj = o
							self.group_obj(new_obj, coll_name)

				coll = bpy.data.collections.get(coll_name)

				if coll and coll.objects:
					bool_objs += split_objs
					self.add_boolean(obj1=merge_obj, grp=coll_name)
					self.apply_mesh(merge_obj)
			else:
				for o in bool_objs:
					if o.type == 'MESH':
						if self.fill_holes: self.fill_mesh(o)

						if self.offset_bool: self.offset_mesh(o, type='bool')

						self.add_boolean(obj1=merge_obj, obj2=o)

				self.apply_mesh(merge_obj)

			for o in bool_objs: remove_obj(o)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.29, align=True)
		row.label(text="Operand Type:")
		row.row(align=True).prop(self, "operand_type", expand=True)
		row = col.row().split(factor=0.29, align=True)
		row.label(text="Merge To:")
		row.prop_search(
			self,
			"list",
			self,
			"meshes",
			text="",
			icon = "MESH_DATA"
			)
		row = col.row().split(factor=0.29, align=True)
		row.label(text="Offset Target:")
		row.row(align=True).prop(self, "offset_target", text="")
		row = col.row().split(factor=0.29, align=True)
		row.label(text="Offset Boolean:")
		row.row(align=True).prop(self, "offset_bool", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		if self.operand_type == 'OBJ':
			flow.prop(self, "use_self")
		flow.prop(self, "hole_tolr")
		flow.prop(self, "fill_holes")

	def invoke(self, context, event):

		self.list = ""
		self.meshes.clear()

		for o in context.selected_objects:
			if o.type == 'MESH':
				newListItem = self.meshes.add()
				newListItem.name = o.name

		return context.window_manager.invoke_props_dialog(self)

class OBJECT_OT_clear_banding(Operator):
	'''Clear subdivision banding on selected mesh'''
	bl_idname = 'clear_bands.rflow'
	bl_label = 'Clear Banding'
	bl_options = {'REGISTER', 'UNDO'}

	bvl_width : FloatProperty(
		name        = "Bevel Amount",
		description = "Bevel Amount",
		default     = 0.005,
		min         = 0,
		max         = 100,
		step        = 0.1,
		precision   = 4
		)
	bvl_segments : IntProperty(
		name        = "Bevel Segments",
		description = "Number of segments for round edges/verts",
		default     = 2,
		min         = 1,
		max         = 100,
		step        = 1
		)
	bvl_profile : FloatProperty(
		name        = "Bevel Profile",
		description = "The profile shape (0.5 = round)",
		default     = 0.5,
		min         = 0,
		max         = 1.0,
		step        = 0.1,
		precision   = 2
		)
	bvl_limit : FloatProperty(
		name        = "Angle Limit (Bevel)",
		description = "Angle above which to bevel edges",
		default     = radians(30),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE",
	)
	max_dist : FloatProperty(
		name        = "Max Distance (Data Transfer)",
		description = "Max Distance",
		default     = 0.0005,
		min         = 0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	bvl_clamp : BoolProperty(
		name        = "Clamp Overlap",
		description = "Clamp the width to avoid overlap",
		default     = True
		)
	angle : FloatProperty(
		name        = "Max Angle (Limited Dissolve)",
		description = "Angle limit",
		default     = radians(5),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def decimate_obj(self, obj):

		mesh = obj.data
		bm = bmesh.new()
		bm.from_mesh(mesh)

		bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
			use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

		bm.to_mesh(mesh)
		mesh.update()

	def clr_dt_mods(self, obj):

		mod = obj.modifiers
		for m in mod:
			if m.type in ['BEVEL', 'DATA_TRANSFER']: mod.remove(m)

	def add_dt_mods(self, obj, data_obj, object_transform=False, vertex_group=None, invert=True):

		mod = obj.modifiers

		bvl =  mod.new('Bevel', 'BEVEL')
		bvl.width = self.bvl_width
		bvl.segments = self.bvl_segments
		bvl.profile = self.bvl_profile
		bvl.angle_limit = self.bvl_limit
		bvl.use_clamp_overlap = self.bvl_clamp
		bvl.harden_normals = True
		bvl.show_expanded = False
		bvl.show_in_editmode = False

		dt = mod.new(name="DataTransfer", type='DATA_TRANSFER')
		dt.object = data_obj
		dt.use_object_transform = object_transform
		dt.use_loop_data = True
		dt.invert_vertex_group = invert
		dt.data_types_loops = {'CUSTOM_NORMAL'}
		dt.loop_mapping = 'POLYINTERP_LNORPROJ'
		dt.use_max_distance = True
		dt.max_distance = self.max_dist
		dt.show_expanded = False
		dt.show_in_editmode = False

	def clear_data_objs(self):

		dt_objs = [o.name for o in bpy.data.objects if o.users == 1 \
			and o.use_fake_user and any(x in o.name for x in ["_dt_obj"])]

		for o in bpy.context.scene.objects:
			dt = o.modifiers.get("DataTransfer")
			if dt and \
				dt.object:
				name = dt.object.name
				if name in dt_objs:
					dt_objs.remove(name)

		self.report({'INFO'}, "Removed " + str(len(dt_objs)) + " unused data transfer object(s).")
		for name in dt_objs:
			bpy.data.objects.remove(bpy.data.objects[name])

	def execute(self, context):

		for obj in context.selected_objects:
			obj.data.set_sharp_from_angle(angle=radians(30))
			self.clr_dt_mods(obj)

			data_obj = duplicate_obj(filter_name(obj, "_dt_obj"), obj, get_eval=False)
			copy_modifiers([obj, data_obj])

			data_obj.data = get_eval_mesh(data_obj).copy()

			data_obj.modifiers.clear()
			data_obj.data.materials.clear()

			self.decimate_obj(data_obj)
			self.add_dt_mods(obj, data_obj)

			data_obj.use_fake_user = True
			remove_obj(data_obj, clear_data=False)
			self.clear_data_objs()

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel Width:")
		row.row(align=True).prop(self, "bvl_width", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel Segments:")
		row.row(align=True).prop(self, "bvl_segments", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel Profile:")
		row.row(align=True).prop(self, "bvl_profile", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel Limit:")
		row.row(align=True).prop(self, "bvl_limit", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limited Dissolve:")
		row.row(align=True).prop(self, "angle", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Max Distance:")
		row.row(align=True).prop(self, "max_dist", text="")
		col.separator()
		col.prop(self, "bvl_clamp")

class OBJECT_OT_clear_dtobjs(Operator):
	'''Clear data objects used for clear banding operation'''
	bl_idname = 'clear_dtobjs.rflow'
	bl_label = 'Clear Data Objects'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):

		return context.active_object is not None

	def execute(self, context):

		dt_objs = [o.name for o in bpy.data.objects if o.use_fake_user \
			and any(x in o.name for x in ["_dt_obj"])]

		for o in context.scene.objects:
			clear_bevel = False
			mod = o.modifiers
			for m in mod:
				if m.type == 'DATA_TRANSFER':
					if m.object \
						and m.object.name in dt_objs:
						mod.remove(m)
						clear_bevel = True

			if clear_bevel:
				for m in mod:
					if m.type == 'BEVEL': mod.remove(m)

		self.report({'INFO'}, "Removed " + str(len(dt_objs)) + " data transfer object(s).")
		for name in dt_objs:
			bpy.data.objects.remove(bpy.data.objects[name])

		return {"FINISHED"}

	def draw(self, context): None

class MESH_OT_crease_sharp(Operator):
	'''Crease sharp edges based on angle threshold'''
	bl_idname = 'crease_sharp.rflow'
	bl_label = 'Crease Sharp'
	bl_options = {'REGISTER', 'UNDO'}

	sharpness : FloatProperty(
		name        = "Sharpness",
		description = "Edge sharpness",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	crease : FloatProperty(
		name        = "Factor",
		description = "Amount of creasing",
		default     = 1.0,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
		)
	selected_only : BoolProperty(
		name        = "Selected Only",
		description = "Only crease selected edges that meet the sharpness threshold",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None

	def execute(self, context):

		sel_objs = context.selected_objects

		for o in sel_objs:
			mesh = o.data

			if mesh.is_editmode:
				bm = bmesh.from_edit_mesh(mesh)
			else:
				bm = bmesh.new()
				bm.from_mesh(mesh)

			layer_float = bm.edges.layers.float
			crease_layer = layer_float.get('crease_edge', None) \
				or layer_float.new('crease_edge')

			for e in bm.edges:
				angle = e.calc_face_angle(None)
				if angle \
					and angle > self.sharpness \
					and (e.select if self.selected_only else True):
					e[crease_layer] = self.crease

			if mesh.is_editmode:
				bmesh.update_edit_mesh(mesh)
			else:
				bm.to_mesh(mesh)
				mesh.update()

		return {'FINISHED'}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Sharpness:")
		row.row(align=True).prop(self, "sharpness", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Factor:")
		row.row(align=True).prop(self, "crease", text="")
		col.separator(factor=0.5)
		col.prop(self, "selected_only")

	def invoke(self, context, event):

		return self.execute(context)

class MESH_OT_smooth_sharp(Operator):
	'''Smooth vertices that are not part of sharp edges based on angle threshold'''
	bl_idname = 'smooth_sharp.rflow'
	bl_label = 'Smooth Sharp'
	bl_options = {'REGISTER', 'UNDO'}

	sharpness : FloatProperty(
		name        = "Sharpness",
		description = "Edge sharpness",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	smooth_factor : FloatProperty(
		name        = "Smooth",
		description = "Amount of smoothing",
		default     = 1.0,
		min         = 0.0,
		soft_max    = 2.0,
		step        = 0.1,
		precision   = 4
		)
	smooth_iter : IntProperty(
		name        = "Repeat",
		description = "Number of times to repeat smoothing",
		default     = 1,
		min         = 1,
		soft_max    = 100,
		step        = 1
		)
	offset : FloatProperty(
		name        = "Offset",
		description = "Offset smoothed vertices",
		default     = 0.0,
		soft_min    = -1.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 4
		)
	smooth_boundary : BoolProperty(
		name        = "Smooth Boundary",
		description = "Smooth boundary vertices",
		default     = False
		)
	selected_only : BoolProperty(
		name        = "Selected Only",
		description = "Only smooth sharp selected area",
		default     = False
		)
	invert : BoolProperty(
		name        = "Invert",
		description = "Invert the area of influence",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None

	def execute(self, context):

		sel_objs = context.selected_objects

		for o in sel_objs:
			mesh = o.data

			if mesh.is_editmode:
				bm = bmesh.from_edit_mesh(mesh)
			else:
				bm = bmesh.new()
				bm.from_mesh(mesh)

			init_edges = ([e for e in bm.edges if e.select] if not self.invert \
				else [e for e in bm.edges if not e.select]) if self.selected_only else bm.edges

			smooth_verts = set()

			for e in init_edges:
				for v in e.verts:
					if not any(e for e in v.link_edges if e.calc_face_angle(None) and e.calc_face_angle(None) > self.sharpness):
						if (not v.is_boundary if not self.smooth_boundary else True):
							smooth_verts.add(v)

			for i in range(0, self.smooth_iter):
				bmesh.ops.smooth_vert(bm, verts=list(smooth_verts), factor=self.smooth_factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)

			if self.offset:
				for v in smooth_verts:
					v.co += v.normal * (v.calc_shell_factor() * self.offset)

			if mesh.is_editmode:
				bmesh.update_edit_mesh(mesh)
			else:
				bm.to_mesh(mesh)
				mesh.update()

		return {'FINISHED'}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Sharpness:")
		row.row(align=True).prop(self, "sharpness", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Smooth:")
		row.row(align=True).prop(self, "smooth_factor", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Repeat:")
		row.row(align=True).prop(self, "smooth_iter", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		row.row(align=True).prop(self, "offset", text="")
		col.separator(factor=0.5)
		col.prop(self, "smooth_boundary")
		col.prop(self, "selected_only")
		if self.selected_only:
			col.prop(self, "invert")

	def invoke(self, context, event):

		return self.execute(context)

class MESH_OT_filter_select(Operator):
	'''Select faces based on minimum edge length'''
	bl_idname = 'filter_select.rflow'
	bl_label = 'Filter Select'
	bl_options = {'REGISTER', 'UNDO'}

	select_limit : EnumProperty(
		name = 'Limit',
		items = (
			('NONE', 'None','No limit on selection'),
			('NONMF', 'Non Manifold','Do not include faces that have boundary edges'),
			('ONLYNONMF', 'Only Non Manifold','Only select faces that have boundary edges')),
		default = 'NONE'
		)
	edg_length : FloatProperty(
		name        = "Minimum Length",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 3
		)
	get_linked : BoolProperty(
		name        = "Linked Flat Faces",
		description = "Select linked flat faces from selection",
		default     = False
		)
	link_angle : FloatProperty(
		name        = "Sharpness",
		description = "Select flat linked faces sharpness limit",
		default     = radians(15),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	select_invert : BoolProperty(
		name        = "Select Invert",
		description = "Invert current selection",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "EDIT"

	def execute(self, context):

		obj = context.active_object
		mesh = obj.data

		bm = bmesh.from_edit_mesh(mesh)

		for f in bm.faces:
			if f.select:
				bounds_e = ( e.is_boundary for e in f.edges )
				check_bounds = not True in bounds_e if self.select_limit == 'NONMF' \
					else True in bounds_e if self.select_limit == 'ONLYNONMF' else True
				f.select = True if not any(e for e in f.edges if e.calc_length() <= self.edg_length) \
					and check_bounds else False

		if self.get_linked:
			linked_faces = get_linked_faces([f for f in bm.faces if f.select], angle_limit=True, \
				use_local=True, local_angle=self.link_angle)
			for f in linked_faces: f.select = True

		if self.select_invert:
			for f in bm.faces:
				f.select = not f.select

		bmesh.update_edit_mesh(mesh)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.23, align=True)
		row.label(text="Limit:")
		row.column(align=True).prop(self, "select_limit", expand=True)
		row = col.row().split(factor=0.23, align=True)
		row.label(text="Length:")
		row.row(align=True).prop(self, "edg_length", text="")
		col.separator(factor=0.5)
		col.prop(self, "get_linked")
		if self.get_linked:
			col.prop(self, "link_angle")
		col.prop(self, "select_invert")

	def invoke(self, context, event):

		obj = context.active_object
		obj.update_from_editmode()

		has_face = count_selected_faces(obj)

		if has_face:
			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class MESH_OT_straight_uv(Operator):
	'''Unwrap mesh based on uv marked edges and generate straight uv islands.'''
	bl_idname = 'straight_uv.rflow'
	bl_label = 'Straight UV'
	bl_options = {'REGISTER', 'UNDO'}

	limit : EnumProperty(
		name = 'Limit',
		items = (
			('UV', 'UV','Unwrap using UVs'),
			('SHARP', 'Sharp Edges', 'Unwrap by making uv islands based on sharp edges')),
		default = 'UV'
		)
	sharpness : FloatProperty(
		description = "Edge sharpness",
		name        = "Sharpness",
		default     = radians(30),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	edg_length_mode : EnumProperty(
		name = 'Edge Length Mode',
		items = (
			('EVEN', 'Even','Space all UVs evenly'),
			('LENGTH', 'Length','Average space UVs edge length of each loop'),
			('LENGTH_AVERAGE', 'Average', 'Average space UVs edge length of each loop')),
		default = 'EVEN'
		)
	edg_length : FloatProperty(
		name        = "Minimum Length",
		description = "Minimum edge length to be considered as active face for follow active quads",
		default     = 0.01,
		min         = 0.0,
		soft_max    = 100.0,
		step        = 0.1,
		precision   = 3
		)
	face_seed : IntProperty(
		name        = "Face Seed",
		description = "Randomize active face selection for follow active quads",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	margin : FloatProperty(
		name        = "Margin",
		description = "Space between islands",
		default     = 0.001,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 3,
		subtype     = "FACTOR"
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def get_sharp(self, edges):

		sharp_edges = set()

		for e in edges:
			angle = e.calc_face_angle(None)
			if angle and \
				angle > self.sharpness:
				if e.smooth: sharp_edges.add(e)
				e.smooth = False

		return sharp_edges

	def execute(self, context):

		sce = context.scene
		obj = context.active_object

		save_mode = obj.mode

		if obj.mode == "OBJECT":
			bpy.ops.object.editmode_toggle()

		mesh = obj.data

		bm = bmesh.from_edit_mesh(mesh)

		faces = { f: f.index for f in bm.faces if f.select }

		list_f = list(faces.keys())
		list_i = list(faces.values())

		uv_islands = []
		sharp_edges = set()

		if self.limit == 'SHARP':
			list_e = [e for e in bm.edges if e.select]
			sharp_edges = self.get_sharp(list_e)

		if list_f != None:
			while list_f:
				linked_faces = []
				traversal_stack = [list_f.pop()]

				while len(traversal_stack) > 0:
					f_curr = traversal_stack.pop()
					linked_faces.append(f_curr)

					for e in f_curr.edges:
						limit = not e.seam if self.limit == 'UV' else e.smooth
						if e.is_contiguous and limit:
							for f_linked in e.link_faces:
								if f_linked not in linked_faces:
									traversal_stack.append(f_linked)
									if f_linked in list_f: list_f.remove(f_linked)

				uv_islands.append(linked_faces)

		for e in sharp_edges: e.smooth = True

		bmesh.update_edit_mesh(mesh)

		save_sync = sce.tool_settings.use_uv_select_sync
		sce.tool_settings.use_uv_select_sync = True

		for i, fg in enumerate(uv_islands):
			bm = bmesh.from_edit_mesh(mesh)

			for f in bm.faces: f.select = False

			bm.faces.ensure_lookup_table()

			idx = None
			list_copy = fg.copy()
			fallback = []

			cc = 0

			while list_copy:
				seed(self.face_seed + cc)
				f = choice(list_copy)
				list_copy.remove(f)

				if len(f.edges) == 4:
					fallback.append(f)
					if not any(e for e in f.edges if e.calc_length() <= self.edg_length):
						idx = f.index
						break

				cc += 1

			if idx == None \
				and fallback:
				seed(self.face_seed + i)
				idx = choice(fallback).index

			if idx != None:
				bm.faces[idx].select = True
				bm.faces.active = bm.faces[idx]

				bmesh.update_edit_mesh(mesh)

				bpy.ops.uv.reset()

				bm = bmesh.from_edit_mesh(mesh)

				for f in bm.faces:
					f.select = f in fg

				bmesh.update_edit_mesh(mesh)

				try:
					bpy.ops.uv.follow_active_quads(mode=self.edg_length_mode)
				except: pass
			else:
				bmesh.update_edit_mesh(mesh)

		bpy.ops.uv.select_all(action='SELECT')

		bpy.ops.uv.average_islands_scale()
		bpy.ops.uv.pack_islands(rotate=False, margin=self.margin)

		bpy.ops.uv.select_all(action='DESELECT')

		bm = bmesh.from_edit_mesh(mesh)

		for f in bm.faces:
			f.select = f.index in list_i

		bmesh.update_edit_mesh(mesh)

		sce.tool_settings.use_uv_select_sync = save_sync

		if obj.mode != save_mode:
			bpy.ops.object.editmode_toggle()

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limit:")
		row.row(align=True).prop(self, "limit", expand=True)
		if self.limit == 'SHARP':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Edge Sharpness:")
			row.row(align=True).prop(self, "sharpness", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Edge Length Mode:")
		row.row(align=True).prop(self, "edg_length_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Min Edge Length:")
		row.row(align=True).prop(self, "edg_length", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Face Seed:")
		row.row(align=True).prop(self, "face_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)

class MESH_OT_sort_elements(Operator):
	'''Sort the indices of selected elements'''
	bl_idname = 'sort_elem.rflow'
	bl_label = 'Sort Elements'
	bl_options = {'REGISTER', 'UNDO'}

	sort_method : EnumProperty(
		name = 'Sort Method',
		items = (
			('RANDOM', 'Random','Randomly sort indices'),
			('X', 'X','Sort indices by X axis direction'),
			('Y', 'Y','Sort indices by Y axis direction'),
			('Z', 'Z','Sort indices by Z axis direction')),
		default = 'RANDOM'
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == 'MESH'

	def execute(self, context):

		mesh = context.active_object.data
		bm = bmesh.from_edit_mesh(mesh)

		sort_elements(bm.verts, self.sort_method)
		sort_elements(bm.edges, self.sort_method)
		sort_elements(bm.faces, self.sort_method)

		bmesh.update_edit_mesh(mesh)

		return {"FINISHED"}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Sort Method:")
		row.row(align=True).prop(self, "sort_method", text="")

class MESH_OT_tag_verts(Operator):
	'''Assign vertices to vertex group for use in Quad Slice and Panel Screws'''
	bl_idname = 'tag_verts.rflow'
	bl_label = 'Tag Verts'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "EDIT"

	def execute(self, context):

		obj = context.active_object
		vg_name = "tagged_verts"

		mesh = obj.data
		bm =  bmesh.from_edit_mesh(mesh)

		old_vgroup = obj.vertex_groups.get(vg_name)
		if old_vgroup: obj.vertex_groups.remove(old_vgroup)

		new_vgroup = obj.vertex_groups.new(name=vg_name)
		idx = new_vgroup.index

		deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()

		for v in bm.verts:
			if v.select: v[deform_layer][idx] = 1.0

		bmesh.update_edit_mesh(mesh)

		return {"FINISHED"}

class MESH_OT_quad_slice(Operator):
	'''Draw lines from vertices or edges using view or tangent as direction'''
	bl_idname = 'quad_slice.rflow'
	bl_label = 'Quad Slice'
	bl_options = {'REGISTER', 'UNDO'}

	direction : EnumProperty(
		name = "Direction",
		items = (
			('TANGENT', 'Tangent','Use face tangents from selected as direction'),
			('VIEW', 'View','Use view angle as direction')),
		default = 'TANGENT')
	tangent_idx : IntProperty(
		name        = "Tangent",
		description = "Tangent index",
		default     = 0,
		min         = -10000,
		max         = 10000,
		step        = 1
		)
	origin : EnumProperty(
		name = "Origin",
		items = (
			('VERT', 'Verts','Source cut lines from selected verts'),
			('EDGE', 'Edges','Source cut lines from selected edges')),
		default = 'VERT')
	geometry : EnumProperty(
		name = "Geometry",
		items = (
			('SELECT', 'Selected','Limit cut to selected/shared face'),
			('LINKED', 'Linked','Cut linked faces'),
			('ALL', 'All Faces','Cut all faces')),
		default = 'SELECT')
	limit : EnumProperty(
		name = "Limit",
		items = (
			('NONE', 'None','Limit cut to none'),
			('LINE1', 'X','Limit to cut direction X'),
			('LINE2', 'Y','Limit to cut direction Y')),
		default = 'NONE')
	bisect_dist : FloatProperty(
		name        = "Distance",
		description = "Minimum distance when testing if a vert is exactly on the plane",
		default     = 0.0001,
		min			= 0.0,
		soft_min    = 0.0001,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	slide_factor : FloatProperty(
		name        = "Factor",
		description = "Split location on selected edge",
		default     = 0.5,
		min         = 0.0,
		max         = 1.0,
		step        = 0.1,
		precision   = 4
	)
	cut_rot : FloatProperty(
		name        = "Rotation",
		description = "Rotate to X axis",
		default     = 0,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	use_tagged : BoolProperty(
		name        = "Tagged Verts Only",
		description = "Use tagged verts as cut source",
		default     = False
		)
	share_cuts : BoolProperty(
		name        = "Shared Cuts",
		description = "Sets of selected or island faces can share cuts",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == "EDIT"

	def group_linked(self, listf):

		groupf = []

		if listf != None:
			while listf:
				face = listf.pop()
				isle = [face]
				linkedf = get_linked_faces(isle)
				for f in listf.copy():
					if f in linkedf:
						isle.append(f)
						listf.remove(f)

				groupf.append(isle)

		return groupf

	def qslice(self, context, obj, bm, flist=[], elist=[], vlist=[]):

		rv3d = context.region_data
		vrot = rv3d.view_rotation

		orig_geo = []
		origin_pts = []

		if self.use_tagged:
			vg = obj.vertex_groups.get("tagged_verts")
			if vg:
				deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()
				origin_pts = [v for v in bm.verts if vg.index in v[deform_layer]]
			else:
				self.report({'WARNING'}, "Vertex group not found!")
		else:
			origin_pts = vlist

		if self.origin == 'EDGE':
			edg = [e for e in elist if all(v in origin_pts for v in e.verts)]
			ret = bmesh.ops.bisect_edges(bm, edges=edg, cuts=1, edge_percents={ e: self.slide_factor for e in edg })
			origin_pts = [v for v in ret['geom_split'] if isinstance(v, bmesh.types.BMVert)]

		if self.geometry == 'SELECT':
			fv = sum([f.verts[:] for f in flist], [])
			fe = sum([f.edges[:] for f in flist], [])
			orig_geo = fv + fe + flist

		if self.geometry == 'LINKED':
			island = get_linked_faces(flist)
			if island:
				fv = sum([f.verts[:] for f in island], [])
				fe = sum([f.edges[:] for f in island], [])
				orig_geo = fv + fe + list(island)

		if self.geometry == 'ALL':
			orig_geo = bm.verts[:] + bm.edges[:] + bm.faces[:]

		if origin_pts:
			if self.direction == 'TANGENT':
				fn = { tuple(f.normal) for f in flist }
				et = { tuple((e.verts[0].co - e.verts[1].co).normalized()) for e in elist }
				et = clean_directions(et)

				tangents = [[n, t] for n in fn for t in et]
				tangents.sort(reverse=True)

				n = len(tangents)
				t = tangents[(n + (self.tangent_idx - 1)) % n]
				normal = Vector(t[0])
				tangent = Vector(t[1])
				x = tangent
				y = x.cross(normal).normalized()
			else:
				x = vrot @ Vector((0,-1,0))
				y = vrot @ Vector((-1,0,0))

			cutdir = [x, y]
			cutdir = cutdir[:-1] if self.limit == 'LINE1' else cutdir[-1:] \
				if self.limit == 'LINE2' else cutdir

			new_geo = []
			P = x.cross(y).normalized()
			M = Matrix.Rotation(self.cut_rot, 3, P)

			for v in origin_pts:
				co = v.co
				for t in cutdir:
					t = t @ M.inverted()
					geo = undupe(orig_geo + new_geo)
					ret = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=co, plane_no=t, dist=self.bisect_dist)

					new_geo.extend(ret['geom'] + ret['geom_cut'])
					new_geo = undupe(new_geo)

			for f in new_geo:
				if isinstance(f, bmesh.types.BMFace) and not f.calc_center_median() in self.centers: f.select = True

			bm.select_mode = {'VERT', 'EDGE', 'FACE'}
			bm.select_flush_mode()

	def execute(self, context):

		obj = context.active_object

		mesh = obj.data
		bm = bmesh.from_edit_mesh(mesh)

		if not self.share_cuts \
			and self.geometry in ['SELECT', 'LINKED']:
			linked_faces = self.group_linked([f for f in bm.faces if f.select])
			for flist in linked_faces:
				elist = undupe(sum([f.edges[:] for f in flist], []))
				vlist = undupe(sum([f.verts[:] for f in flist], []))
				self.qslice(context, obj, bm, flist, elist, vlist)
		else:
			flist = [f for f in bm.faces if f.select]
			elist = undupe(sum([f.edges[:] for f in flist], []))
			vlist = undupe(sum([f.verts[:] for f in flist], []))
			self.qslice(context, obj, bm, flist, elist, vlist)

		bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
		bmesh.update_edit_mesh(mesh)

		return {'FINISHED'}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Direction:")
		row.row(align=True).prop(self, "direction", expand=True)
		if self.direction == 'TANGENT':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Tangent:")
			row.row(align=True).prop(self, "tangent_idx", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Origin:")
		row.row(align=True).prop(self, "origin", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Geometry:")
		row.row(align=True).prop(self, "geometry", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Limit:")
		row.row(align=True).prop(self, "limit", expand=True)
		if self.origin == 'EDGE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Factor:")
			row.row(align=True).prop(self, "slide_factor", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "cut_rot", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Distance:")
		row.row(align=True).prop(self, "bisect_dist", text="")
		col.separator(factor=0.5)
		col.prop(self, "use_tagged")
		col.prop(self, "share_cuts")

	def invoke(self, context, event):

		obj = context.active_object

		obj.update_from_editmode()

		self.tangent_idx = 0
		self.limit = 'NONE'
		self.cut_rot = 0
		self.slide_factor = 0.5

		mesh = obj.data
		has_face = any(f for f in mesh.polygons if f.select)
		if has_face:
			poly_co = np.empty((len(mesh.polygons), 3), 'f')
			mesh.polygons.foreach_get("center", np.reshape(poly_co, len(mesh.polygons) * 3))
			self.centers = [Vector(i) for i in poly_co]

			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected!")

			return {'FINISHED'}

class MESH_OT_grid_project(Operator):
	'''Project grid cuts on selected faces'''
	bl_idname = 'grid_project.rflow'
	bl_label = 'Grid Project'
	bl_options = {'REGISTER', 'UNDO'}

	grid_center : EnumProperty(
		name = "Center",
		items = (
			('AVERAGE', 'Average','Use average location of selected faces as grid center'),
			('PERFACE', 'Per Face','Use individual face location as grid center')),
		default = 'AVERAGE')
	direction : EnumProperty(
		name = "Direction",
		items = (
			('TANGENT', 'Tangent','Align direction to longest edge'),
			('VIEW', 'View','Align direction to view')),
		default = 'TANGENT')
	tangent_src : EnumProperty(
		name = "Source",
		items = (
			('INDIV', 'Individual','Get tangent from individual faces'),
			('SELECT', 'Select','Get tangent from specific face')),
		default = 'INDIV')
	tangent_idx : IntProperty(
		name        = "Tangent",
		description = "Tangent index",
		default     = 0,
		min         = -10000,
		max         = 10000,
		step        = 1
		)
	cut_geo : EnumProperty(
		name = "Geometry",
		items = (
			('SELECT', 'Selected','Limit cut to selected faces'),
			('LINKED', 'Linked','Cut linked faces'),
			('ALL', 'All','Cut all faces')),
		default = 'SELECT')
	cuts_amt : EnumProperty(
		name = "Cuts Amount",
		items = (
			('SAME', 'Uniform','Use same cut number for all axes'),
			('INDIV', 'Individual','Use individual cut number for x and y axis')),
		default = 'SAME')
	birth_perc : FloatProperty(
		name        = "Perc",
		description = "Percentage to determine if line is cut",
		min         = 0,
		max         = 100,
		precision   = 0,
		default     = 100,
		subtype     = "PERCENTAGE"
		)
	birth_seed : IntProperty(
		name        = "Seed",
		description = "Randomize seed for birth of grid cuts",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	cuts : IntProperty(
		name        = "X Cuts",
		description = "Number of cuts for all axes",
		default     = 10,
		min         = 0,
		soft_max    = 20,
		step        = 1
	)
	cut_xy : IntVectorProperty(
		name        = "Cuts",
		description = "Number of cuts for x and y axis",
		default     = (10,10),
		size        = 2,
		min         = 0,
		soft_max	= 20,
		step        = 1,
		subtype		= "XYZ"
		)
	offset_xy : FloatVectorProperty(
		name        = "Offset",
		description = "Offset x and y axis cuts",
		default     = (0.0, 0.0),
		size        = 2,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.01,
		precision   = 4,
		subtype		= "XYZ"
		)
	size : FloatProperty(
		name        = "Size",
		description = "Grid size",
		default     = 1,
		min         = 0.0001,
		max         = 100,
		step        = 0.1,
		precision   = 4
	)
	rot : FloatProperty(
		name        = "Rotation",
		description = "Rotate to X axis",
		default     = 0,
		min         = radians(-360),
		max         = radians(360),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	bisect_dist : FloatProperty(
		name        = "Distance",
		description = "Minimum distance when testing if a vert is exactly on the plane",
		default     = 0.0001,
		min			= 0.0,
		soft_min    = 0.0001,
		soft_max    = 1.0,
		step        = 0.01,
		precision   = 4
		)
	tri_ngons : BoolProperty(
		name        = "Triangulate Ngons",
		description = "Triangulate ngons in cut faces",
		default     = False
		)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.mode == 'EDIT'

	def cut_grid(self, bm, orig_geo, center, area, normal, tangent):

		t1 = tangent
		t2 = normal.cross(t1)
		vec = t1 - t2 * 0.00001

		P = normal
		M = Matrix.Rotation(self.rot, 3, P)
		tangent = vec @ M.inverted()

		x_proc = 0
		new_geo = []

		x = self.cuts if self.cuts_amt == 'SAME' else self.cut_xy[0]
		xdir = tangent
		center += self.offset_xy[0] * xdir
		if sum(xdir) != 0:
			for i in range(-x+1, x, 1):
				seed(self.birth_seed * i)
				if not random() > self.birth_perc/100:
					geo = undupe(orig_geo + new_geo)
					vec = ((i * (sqrt(area)/x)) * xdir) * self.size
					ret = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=center+vec, plane_no=xdir, dist=self.bisect_dist)

					new_geo.extend(ret['geom'] + ret['geom_cut'])
					new_geo = undupe(new_geo)

					x_proc += 1

		y = self.cuts if self.cuts_amt == 'SAME' else self.cut_xy[1]
		ydir = tangent.cross(normal).normalized()
		center += self.offset_xy[1] * ydir
		if sum(ydir) != 0:
			for i in range(-y+1, y, 1):
				seed(self.birth_seed * (i + x_proc))
				if not random() > self.birth_perc/100:
					geo = undupe(orig_geo + new_geo)
					vec = ((i * (sqrt(area)/y)) * ydir) * self.size
					ret = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=center+vec, plane_no=ydir, dist=self.bisect_dist)

					new_geo.extend(ret['geom'] + ret['geom_cut'])
					new_geo = undupe(new_geo)

		return new_geo

	def execute(self, context):

		obj = context.active_object

		rv3d = context.region_data
		vrot = rv3d.view_rotation

		mesh = obj.data
		bm = bmesh.from_edit_mesh(mesh)

		flist = [f for f in bm.faces if f.select]
		elist = undupe(sum([f.edges[:] for f in flist], []))
		orig_geo = []

		fn = { tuple(f.normal) for f in flist }
		et = { tuple((e.verts[0].co - e.verts[1].co).normalized()) for e in elist }
		et = clean_directions(et)
		listdir = [[n, t] for n in fn for t in et]
		listdir.sort()

		n = len(listdir)
		t = listdir[(n + (self.tangent_idx - 1)) % n]
		normal = Vector(t[0])
		tangent = Vector(t[1]) if self.direction == 'TANGENT' else vrot @ Vector((0,-1,0))
		area = sum(f.calc_area() for f in flist) / len(flist)

		cuts_geo = []
		if self.grid_center == 'PERFACE':
			for f in flist:
				center = f.calc_center_bounds()
				normal = f.normal if self.tangent_src == 'INDIV' else normal
				tangent = f.calc_tangent_edge() if self.tangent_src == 'INDIV' \
					and self.direction == 'TANGENT' else tangent
				orig_geo = f.verts[:] + f.edges[:] + [f]
				new_geo = self.cut_grid(bm, orig_geo, center, area, normal, tangent)
				cuts_geo.extend(new_geo)
		else:
			center = sum([f.calc_center_bounds() for f in flist], Vector()) / len(flist)
			if self.cut_geo == 'SELECT':
				fv = sum([f.verts[:] for f in flist], [])
				fe = sum([f.edges[:] for f in flist], [])
				orig_geo = fv + fe + flist
			elif self.cut_geo == 'ALL':
				fv = sum([f.verts[:] for f in bm.faces], [])
				fe = sum([f.edges[:] for f in bm.faces], [])
				orig_geo = fv + fe + bm.faces[:]
			else:
				island = get_linked_faces(flist)
				if island:
					fv = sum([f.verts[:] for f in island], [])
					fe = sum([f.edges[:] for f in island], [])
					orig_geo = fv + fe + list(island)

			new_geo = self.cut_grid(bm, orig_geo, center, area, normal, tangent)
			cuts_geo = new_geo

		cutsf = []
		for f in cuts_geo:
			if isinstance(f, bmesh.types.BMFace) \
				and not f.calc_center_median() in self.centers:
					f.select = True
					cutsf.append(f)

		bm.select_mode = {'VERT', 'EDGE', 'FACE'}
		bm.select_flush_mode()

		if self.tri_ngons:
			ret = bmesh.ops.triangulate(bm, faces=cutsf, quad_method='BEAUTY', ngon_method='BEAUTY')
			bmesh.ops.join_triangles(bm, faces=ret['faces'], angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

		bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
		bmesh.update_edit_mesh(mesh)

		return {'FINISHED'}

	def draw(self, context):

		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Center:")
		row.row(align=True).prop(self, "grid_center", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Direction:")
		row.row(align=True).prop(self, "direction", expand=True)
		if self.direction == 'TANGENT' \
			and self.grid_center == 'PERFACE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Tangent Basis:")
			row.row(align=True).prop(self, "tangent_src", expand=True)
			if self.tangent_src == 'SELECT':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Tangent:")
				row.row(align=True).prop(self, "tangent_idx", text="")
		if self.direction == 'TANGENT' \
			and self.grid_center == 'AVERAGE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Tangent:")
			row.row(align=True).prop(self, "tangent_idx", text="")
		if self.grid_center == 'AVERAGE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Geometry:")
			row.row(align=True).prop(self, "cut_geo", expand=True)
		if self.cuts_amt == 'SAME':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cuts:")
			row.row(align=True).prop(self, "cuts", text="")
		else:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Cuts:")
			row.row(align=True).prop(self, "cut_xy", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cuts Amount:")
		row.row(align=True).prop(self, "cuts_amt", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset:")
		row.row(align=True).prop(self, "offset_xy", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size:")
		row.row(align=True).prop(self, "size", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Proc:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "birth_perc")
		split.row(align=True).prop(self, "birth_seed")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Rotation:")
		row.row(align=True).prop(self, "rot", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Distance:")
		row.row(align=True).prop(self, "bisect_dist", text="")
		col.separator(factor=0.5)
		col.prop(self, "tri_ngons")

	def invoke(self, context, event):

		obj = context.active_object

		obj.update_from_editmode()

		self.tangent_idx = 0
		self.offset_xy = [0.0, 0.0]
		self.birth_seed = 0
		self.rot = 0

		mesh = obj.data
		has_face = any(f for f in mesh.polygons if f.select)
		if has_face:
			poly_co = np.empty((len(mesh.polygons), 3), 'f')
			mesh.polygons.foreach_get("center", np.reshape(poly_co, len(mesh.polygons) * 3))
			self.centers = [Vector(i) for i in poly_co]

			return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected!")

			return {'FINISHED'}

class MESH_OT_clean_up(Operator):
	'''Remove verts along a straight edge, clears zero area and double faces'''
	bl_idname = 'clean_up.rflow'
	bl_label = 'Clean Up'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == 'MESH'

	def get_double_faces(self, bm, faces=[]):

		face_verts = set()

		f_centers = [tuple(f.calc_center_median()) for f in faces]
		dup_centers = [k for k, v in Counter(f_centers).items() if v > 1]
		for f in faces:
			if tuple(f.calc_center_median()) in dup_centers: face_verts.update(f.verts)

		return list(face_verts)

	def get_single_verts(self, verts):

		singles = []
		for v in verts:
			if len(v.link_edges) == 2:
				if v.is_boundary:
					direction = [(e.verts[1].co - e.verts[0].co) for e in v.link_edges]
					v1 = direction[0]
					v2 = direction[1]
					a1 = v1.angle(v2)
					if a1 > pi * 0.5:
						a1 = pi - a1
					if degrees(a1) == 0: singles.append(v)
				else:
					singles.append(v)

		return singles

	def execute(self, context):

		objs = context.selected_objects
		rem_count = 0

		for o in objs:
			if o.type == 'MESH':
				mesh = o.data
				if mesh.is_editmode:
					bm = bmesh.from_edit_mesh(mesh)
				else:
					bm = bmesh.new()
					bm.from_mesh(mesh)

				vcount = len(bm.verts)

				bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)

				face_verts = self.get_double_faces(bm, bm.faces)
				bmesh.ops.remove_doubles(bm, verts=face_verts, dist=1e-4)

				singles = self.get_single_verts(bm.verts)
				bmesh.ops.dissolve_verts(bm, verts=singles)

				new_vcount = vcount - len(bm.verts)
				rem_count += new_vcount

				if mesh.is_editmode:
					bmesh.update_edit_mesh(mesh)
				else:
					bm.to_mesh(mesh)
					mesh.update()
					bm.free()

		self.report({'INFO'}, "Removed " + str(rem_count) + " vertices.")

		return {"FINISHED"}

	def draw(self, context): None

class MESH_OT_save_data(Operator):
	'''Save, use or clear saved mesh data'''
	bl_idname = 'save_data.rflow'
	bl_label = 'Save/Use/Clear'
	bl_options = {'REGISTER', 'UNDO'}

	mode : EnumProperty(
		items = (
			('SAVE', 'Save','Save mesh data to list'),
			('USE', 'Use','Use mesh data from list'),
			('CLEAR', 'Clear','Clear mesh data list')),
		default = 'SAVE')
	list : StringProperty(
		name        = "Mesh",
		description = "Mesh data"
		)
	meshes : CollectionProperty(type=PropertyGroup)

	@classmethod
	def poll(cls, context):

		return context.active_object is not None and context.active_object.type == "MESH"

	def use_save_data(self, mesh, save_mesh):

		if mesh.is_editmode:
			bm = bmesh.from_edit_mesh(mesh)
		else:
			bm = bmesh.new()
			bm.from_mesh(mesh)

		bm.clear()
		bm.from_mesh(save_mesh)

		if mesh.is_editmode:
			bmesh.update_edit_mesh(mesh)
		else:
			bm.to_mesh(mesh)
			mesh.update()

	def execute(self, context):

		obj = context.active_object

		suffix = self.suffix

		mesh = obj.data
		save = 0
		remv = 0

		if self.mode == 'SAVE':
			if obj: obj.select_set(True)
			for o in context.selected_objects:
				o.update_from_editmode()
				save_data = o.data.copy()
				if save_data.name.find(suffix) == -1:
					save_data.name += suffix
				save_data.use_fake_user = True
				save += 1

			self.report({'INFO'}, str(save) + " mesh data saved.")

		if self.mode == "USE":
			if self.list:
				save_mesh = bpy.data.meshes.get(self.list)
				if save_mesh: self.use_save_data(mesh, save_mesh)

		if self.mode == 'CLEAR':
			for m in bpy.data.meshes:
				if m.name.find(suffix) != -1 \
					and m.use_fake_user:
					m.use_fake_user = False
					if m.users < 1:
						bpy.data.meshes.remove(m)
						remv += 1

			self.report({'INFO'}, str(remv) + " saved mesh data removed.")

		return {"FINISHED"}

	def draw(self, context):

		if self.mode == 'USE':
			layout = self.layout
			col = layout.column()
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mesh Data:")
			row.prop_search(
				self,
				"list",
				self,
				"meshes",
				text="",
				icon = "MESH_DATA"
				)
			col.separator(factor=0.5)
			col.box().label(text=self.same_info, icon="INFO")
		else: None

	def invoke(self, context, event):

		obj = context.active_object

		self.list = ""
		self.meshes.clear()
		self.suffix = suffix = "_save_data"
		self.same_info = ""

		if self.mode == 'USE':
			saved_meshes = { m: get_similarity(obj, m) \
				for m in bpy.data.meshes if m.name.find(suffix) != -1 and m.use_fake_user }
			sorted_meshes = sorted(saved_meshes.items(), key=lambda item: item[1])
			same = 0
			for m in reversed(sorted_meshes):
				newListItem = self.meshes.add()
				newListItem.name = m[0].name
				if m[1] > 0: same += 1

			self.same_info = "Matches " + str(same) + " geometry from " + str(len(sorted_meshes)) + " saved mesh data."

			return context.window_manager.invoke_props_dialog(self)
		else:
			return self.execute(context)

class MESH_OT_use_info(Operator):
	'''Display important usage information'''
	bl_idname = 'use_info.rflow'
	bl_label = 'Help'

	def execute(self, context): return {"FINISHED"}

	def draw(self, context):

		margin = " " * 9
		layout = self.layout
		col = layout.column(align=False)
		col.label(text="Usage Information:", icon="INFO")
		col.separator(factor=0.5)
		col.label(text=margin + "Select faces in edit mode to use for randomizing.")
		col.label(text=margin + "Faces needs to be quads or tris for subdivision to work.")
		col.separator(factor=0.5)
		col.label(text=margin + "Press F9 to bring back redo panel when it disappears.")
		col.label(text=margin + "Performing some commands will finalize last action and scrub the redo panel from history.")
		col.label(text=margin + "In user preferences of the add-on, you can use the confirm type redo panels instead.")
		col.separator(factor=0.5)
		col.label(text="Limitations:", icon="ERROR")
		col.label(text=margin + "Be careful with using higher resolution face selections.")
		col.label(text=margin + "Most operations run recursively.")
		col.label(text=margin + "Blender can run out of memory or take a long time to compute.")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self, width=500)

classes = (
	OBJECT_OT_r_loop_extrude,
	OBJECT_OT_r_panels,
	OBJECT_OT_r_slice,
	OBJECT_OT_r_axis_extrude,
	OBJECT_OT_r_cells,
	OBJECT_OT_r_scatter,
	OBJECT_OT_r_tubes,
	OBJECT_OT_r_cables,
	OBJECT_OT_r_vertex_color,
	OBJECT_OT_r_animation,
	OBJECT_OT_bevel_node,
	OBJECT_OT_normal_picker,
	OBJECT_OT_make_flanges,
	OBJECT_OT_panel_screws,
	OBJECT_OT_panel_cloth,
	OBJECT_OT_plate_insets,
	OBJECT_OT_quick_displace,
	OBJECT_OT_partition_mesh,
	FILES_OT_append_materials,
	FILES_OT_image_browser,
	OBJECT_OT_auto_mirror,
	OBJECT_OT_extract_proxy,
	OBJECT_OT_apply_mesh,
	OBJECT_OT_join_objs,
	OBJECT_OT_split_mesh,
	OBJECT_OT_set_origin,
	OBJECT_OT_merge_objs,
	OBJECT_OT_clear_banding,
	OBJECT_OT_clear_dtobjs,
	MESH_OT_crease_sharp,
	MESH_OT_smooth_sharp,
	MESH_OT_filter_select,
	MESH_OT_straight_uv,
	MESH_OT_sort_elements,
	MESH_OT_tag_verts,
	MESH_OT_quad_slice,
	MESH_OT_grid_project,
	MESH_OT_clean_up,
	MESH_OT_save_data,
	MESH_OT_use_info,
	)

def register():

	from bpy.utils import register_class

	for cls in classes:
		register_class(cls)

def unregister():

	from bpy.utils import unregister_class

	for cls in reversed(classes):
		unregister_class(cls)
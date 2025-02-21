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

bl_info = {
	'name': 'Random Flow',
	'author': 'Ian Lloyd Dela Cruz',
	'version': (2, 8, 0),
	'blender': (3, 5, 0),
	'location': '3d View > Tool shelf',
	'description': 'Collection of random greebling functionalities',
	'warning': '',
	'wiki_url': 'https://drive.google.com/file/d/1izNy0RHt3Cpj_oZNpyDrOKv29MvwwsmS/view?usp=sharing',
	'doc_url': 'https://drive.google.com/file/d/1izNy0RHt3Cpj_oZNpyDrOKv29MvwwsmS/view?usp=sharing',
	'tracker_url': '',
	'category': 'Mesh'}

import bpy
import bgl
import blf
import gpu
import os
from gpu_extras.batch import batch_for_shader
import colorsys
import numpy as np
from random import random, randint, sample, uniform, choice, choices, seed, shuffle, triangular
from collections import Counter
import bmesh
import math
from math import *
import mathutils
from mathutils import *
from mathutils.geometry import intersect_line_plane
from mathutils.bvhtree import BVHTree
from itertools import chain, groupby
from bpy.props import *
from bpy_extras import view3d_utils
from bpy_extras.io_utils import ImportHelper
import rna_keymap_ui
from bpy.types import (
		AddonPreferences,
		PropertyGroup,
		Operator,
		Menu,
		Panel,
		)

def auto_smooth(obj, angle=radians(30), set=True):

	obj.data.use_auto_smooth = set
	obj.data.auto_smooth_angle = angle

	mesh = obj.data
	if mesh.is_editmode:
		bm = bmesh.from_edit_mesh(mesh)
	else:
		bm = bmesh.new()
		bm.from_mesh(mesh)

	for f in bm.faces:
		f.smooth = set

	if mesh.is_editmode:
		bmesh.update_edit_mesh(mesh)
	else:
		bm.to_mesh(mesh)
		mesh.update()

def get_eval_mesh(obj):

	depsgraph = bpy.context.evaluated_depsgraph_get()
	obj_eval = obj.evaluated_get(depsgraph)
	mesh_from_eval = obj_eval.to_mesh()

	return mesh_from_eval

def create_temp_obj(name):

	data = bpy.data.meshes.new(name)
	obj = bpy.data.objects.new(name, data)

	return obj

def reset_transforms(obj, loc=False, rot=False, sca=False):

	M = obj.matrix_basis
	loc_basis, rot_basis, sca_basis = M.decompose()

	I = Matrix()
	T = I if loc else Matrix.Translation(loc_basis)
	R = I if rot else rot_basis.to_matrix().to_4x4()
	S = I if sca else Matrix.Diagonal(sca_basis.to_4d())

	obj.matrix_basis = T @ R @ S

def set_origin(obj, origin):

	pivot = obj.matrix_world.inverted() @ origin
	obj.data.transform(Matrix.Translation(-pivot))
	obj.matrix_world.translation = origin

temp_mats_rflow = ["rflow_temp_mat1", "rflow_temp_mat2"]

# def assign_temp_mats(mesh, flist):

	# mats = mesh.materials
	# for i, m in enumerate(temp_mats_rflow):
		# mat = bpy.data.materials.get(m) or bpy.data.materials.new(name=m)
		# if mat:
			# mats.append(mat)
			# if i > 0:
				# mat.diffuse_color = (0.2,0.2,0.2,1.0)
				# for f in flist:
					# f.material_index = i

def inset_to_vgroup(obj, list_co=[], mat=Matrix()):

	if not list_co: return

	vname = "panel_cut_faces"

	mesh = obj.data
	if mesh.is_editmode:
		bm = bmesh.from_edit_mesh(mesh)
	else:
		bm = bmesh.new()
		bm.from_mesh(mesh)

	vgroup = obj.vertex_groups.get(vname) or obj.vertex_groups.new(name=vname)
	idx = vgroup.index

	deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()

	for v in bm.verts:
		v[deform_layer][idx] = 1.0 if mat @ v.co in list_co else 0.0

	if mesh.is_editmode:
		bmesh.update_edit_mesh(mesh)
	else:
		bm.to_mesh(mesh)
		mesh.update()

def assign_mat(self, source, target, mat_index):

	idx = mat_index
	mats = source.data.materials

	def append_mat(mat):

		if mat: target.data.materials.append(mat)

	if mats:
		if idx > -1:
			if idx <= (len(mats) - 1):
				append_mat(source.data.materials[idx])
			else:
				self.report({'WARNING'}, "Material not found.")
		else:
			append_mat(source.active_material)

def random_walk(bm, idx=set(), min_size=0, max_size=0, snum=0, sampling='WALK', notch_count=0, notch_size=0, notch_snum=0, \
	path='NONE', cut_threshold=radians(30), wrap_angle=True, only_msharp=False):

	split_edg = []
	cells = []
	counter = 0
	notch_list = set()

	bm.faces.ensure_lookup_table()

	while idx:
		seed(snum + counter)
		x = choice(list(idx))
		idx.remove(x)

		f = bm.faces[x]
		face_cell = [f]
		edge_cell = f.edges[:]
		start_verts = f.verts[:]

		walk = 0

		def add_cells(f, add=True):

			if add:
				idx.remove(f.index)
				face_cell.append(f)
				edge_cell.extend(f.edges)
			else:
				idx.add(f.index)
				if f in face_cell: face_cell.remove(f)
				for e in f.edges:
					if e in edge_cell: edge_cell.remove(e)

		size = randint(min_size, max_size)

		while walk < size:
			seed(snum + counter)
			if sampling != 'RADIAL':
				link_edges = { e: e.calc_length() for e in f.edges }
				edges = list(link_edges.keys()); lenghts = list(link_edges.values())
				for n, e in enumerate(sample(edges, len(edges))):
					length = max(lenghts) if path == 'LONGEST' \
						else min(lenghts) if path == 'SHORTEST' else 0
					if e.calc_length() != length or \
						n + 1 == len(edges):
						f = next((i for i in e.link_faces if i.index in idx), None)
						if f:
							add_cells(f)
							walk += 1
							break
				else:
					list_copy = edge_cell.copy()
					while list_copy:
						sample_edge = choice(list_copy)
						list_copy.remove(sample_edge)
						f = next((i for i in sample_edge.link_faces if i.index in idx), None)
						if f:
							add_cells(f)
							walk += 1
							break
					else: break
			else:
				new_verts = []
				for v in start_verts:
					for lf in v.link_faces:
						if lf.index in idx:
							add_cells(lf)
							new_verts.extend(lf.verts)
							walk += 1

				if new_verts:
					start_verts = new_verts
				else: break

		if notch_count > 0 and len(face_cell) > 1:
			seed(notch_snum + counter)
			size_count = 0
			stop_count = 0
			rand_count = randint(0, notch_size)
			cell_copy = face_cell.copy()
			list_copy = [f for f in cell_copy if not all(i in cell_copy for i \
						in sum([list(e.link_faces) for e in f.edges], []))]
			basisf = None
			while list_copy:
				check = False
				if size_count == 0:
					f = choice(list_copy)
					notch_count -= 1
					check = True
				else:
					linkf = sum([list(e.link_faces) for e in basisf.edges], [])
					f = next((i for i in linkf if not i in notch_list and i in list_copy), None)
					if f: check = True

				if check:
					basisf = f
					list_copy.remove(f)
					add_cells(f, add=False)
					notch_list.add(f)
					size_count += 1

				stop_count += 1
				if size_count > rand_count or stop_count > len(cell_copy): break

		edge_cell = undupe(edge_cell)

		if wrap_angle:
			recursive = True
			while recursive:
				recursive = False
				for e1 in edge_cell:
					angle1 = e1.calc_face_angle(None)
					if angle1 and angle1 >= cut_threshold:
						for lf in e1.link_faces:
							if lf.index in idx \
								and not lf in face_cell:
								add_cells(lf)
								wrap_edges = lf.edges
								for e2 in wrap_edges:
									if not all(v in e1.verts for v in e2.verts):
										angle2 = e2.calc_face_angle(None)
										if angle2 and angle2 >= cut_threshold: recursive = True

		while edge_cell:
			e = edge_cell.pop()
			check = not all(i in face_cell for i in e.link_faces)
			if check and \
				not e in split_edg:
					if only_msharp: e.seam = True; e.smooth = False
					split_edg.append(e)

		cells.append(face_cell)

		counter += 1

	return split_edg, cells

def get_tri_faces(faces=[], amt=0, seed_val=0, mode='PERCENT'):

	seed(seed_val)
	flist = sample(list(faces), len(faces))
	tri = int(len(flist) * (amt/100)) if mode == 'PERCENT' else min(amt, len(flist))

	return flist[:tri]

def get_linked_faces(faces, angle_limit=False):

	sce = bpy.context.scene
	props = sce.rflow_props

	listf = set(faces)
	linked_faces = set()

	while listf:
		traversal_stack = [listf.pop()]

		while len(traversal_stack) > 0:
			f_curr = traversal_stack.pop()
			linked_faces.add(f_curr)

			for e in f_curr.edges:
				if e.is_contiguous:
					for f_linked in e.link_faces:
						if f_linked not in linked_faces:
							if not angle_limit:
								traversal_stack.append(f_linked)
								if f_linked in listf: listf.remove(f_linked)
							else:
								angle = f_curr.normal.angle(f_linked.normal, 0.0)
								if angle < props.link_angle:
									traversal_stack.append(f_linked)
									if f_linked in listf: listf.remove(f_linked)

	return linked_faces

def get_islands(obj, bm=None):

	if bm:
		paths = {v.index:set() for v in bm.verts}
		bm.verts.ensure_lookup_table()
		for e in bm.edges:
			paths[e.verts[0].index].add(e.verts[1].index)
			paths[e.verts[1].index].add(e.verts[0].index)
	else:
		obj.update_from_editmode()
		mesh = obj.data
		paths = {v.index:set() for v in mesh.vertices}
		for e in mesh.edges:
			paths[e.vertices[0]].add(e.vertices[1])
			paths[e.vertices[1]].add(e.vertices[0])

	lparts=[]

	while True:
		try:
			i = next(iter(paths.keys()))
		except StopIteration: break

		lpart={i}
		cur={i}

		while True:
			eligible = {sc for sc in cur if sc in paths}
			if not eligible:
				break
			cur = {ve for sc in eligible for ve in paths[sc]}
			lpart.update(cur)
			for key in eligible: paths.pop(key)

		lparts.append(lpart)

	return lparts

def get_linked_flat_faces(obj):

	mesh = obj.data

	if mesh.is_editmode:
		bm = bmesh.from_edit_mesh(mesh)
	else:
		bm = bmesh.new()
		bm.from_mesh(mesh)

	linked_faces = get_linked_faces([f for f in bm.faces if f.select], angle_limit=True)
	for f in linked_faces:
		f.select = True

	if mesh.is_editmode:
		bmesh.update_edit_mesh(mesh)
	else:
		bm.to_mesh(mesh)
		mesh.update()

def sort_elements(elements, method='NONE', get_select=True):

	if method != 'NONE':
		elist = { e: e.index for e in elements if e.select } if get_select \
			else { e: e.index for e in elements }

		if method == 'RANDOM':
			new_order = list(elist.values())
			shuffle(new_order)

			for i, e in zip(new_order, elist.keys()):
				e.index = i
		else:
			axis = ['X', 'Y', 'Z']
			axis_index = axis.index(method)
			new_order = sorted(list(elist.keys()), key=lambda x: x.co[axis_index] if isinstance(x, bmesh.types.BMVert) \
				else x.calc_center_median()[axis_index] if isinstance(x, bmesh.types.BMFace)  \
				else sum((v.co for v in x.verts), Vector()).normalized()[axis_index])

			for i, e in zip(new_order, elist.values()):
				i.index = e

		elements.sort()

def clip_center(bm, obj, dist=1e-4, axis=[True, True, True]):

	mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
	thresh = 1e-4; center_faces = set()
	if mirror:
		axis_dir = ["x","y","z"]
		for v in bm.verts:
			for i, n in enumerate(axis_dir):
				if mirror.use_axis[i] and axis[i]:
					if -dist <= v.co[i] <= dist:
						setattr(v.co, n, 0)
						for f in v.link_faces:
							if -thresh <= f.calc_center_median()[i] <= thresh: center_faces.add(f)

	bmesh.ops.delete(bm, geom=list(center_faces), context='FACES')

def check_sharp_edges(obj):

	mesh = obj.data
	sharp = np.zeros(len(mesh.edges), dtype=bool)
	obj.data.edges.foreach_get('use_edge_sharp', sharp)

	return True in sharp

def count_selected_faces(obj):

	mesh = obj.data
	selected = np.zeros(len(mesh.polygons), dtype=bool)
	obj.data.polygons.foreach_get('select', selected)

	return np.count_nonzero(selected == True)

def bisect_symmetry(bm, obj):

	mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

	if mirror:
		obj.update_from_editmode()
		mesh = obj.data

		vertices = np.empty((len(mesh.vertices), 3), 'f')
		mesh.vertices.foreach_get("co", np.reshape(vertices, len(mesh.vertices) * 3))
		origin = sum([Vector(co) for co in vertices], Vector()) / len(vertices)

		pivot = Vector()
		axis = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]

		x_dir = axis[0] if origin.x > 0 else -axis[0]
		y_dir = axis[1] if origin.y > 0 else -axis[1]
		z_dir = axis[2] if origin.z > 0 else -axis[2]

		axis_dir = [x_dir if mirror.use_axis[0] else None, \
			y_dir if mirror.use_axis[1] else None, \
			z_dir if mirror.use_axis[2] else None]

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

def copy_modifiers(objs, mod_types=[]):

	sce = bpy.context.scene
	rf_props = sce.rflow_props

	orig_obj = objs[0]
	selected_objects = [o for o in objs if o != orig_obj]

	if rf_props.all_mods: mod_types.clear()

	def copy_mod_settings(obj, mSrc):

		mDst = obj.modifiers.get(mSrc.name, None) or \
			obj.modifiers.new(mSrc.name, mSrc.type)

		properties = [p.identifier for p in mSrc.bl_rna.properties
					  if not p.is_readonly]

		for prop in properties:
			setattr(mDst, prop, getattr(mSrc, prop))

	for obj in selected_objects:
		for mSrc in orig_obj.modifiers:
			if not mod_types:
				try:
					copy_mod_settings(obj, mSrc)
				except: pass
			else:
				if mSrc.type in mod_types:
					copy_mod_settings(obj, mSrc)

def remove_obj(obj, clear_data=True):

	sce = bpy.context.scene
	in_master = True

	for c in bpy.data.collections:
		if obj.name in c.objects:
			c.objects.unlink(obj)
			in_master = False
			break

	if in_master:
		if obj.name in sce.collection.objects:
			sce.collection.objects.unlink(obj)

	if clear_data: bpy.data.objects.remove(obj)

def move_center_origin(origin, obj):

	pivot = obj.matrix_world.inverted() @ origin
	obj.data.transform(Matrix.Translation(-pivot))
	obj.matrix_world.translation = origin

def select_isolate(obj):

	context = bpy.context

	for o in context.selectable_objects:
		if o == obj:
			o.select_set(True)
			context.view_layer.objects.active = o
		else: o.select_set(False)

def copy_rotation(source_obj, obj):

	mat_source = source_obj.rotation_euler.to_matrix()
	mat_source.invert()
	mat_obj = obj.rotation_euler.to_matrix()

	if obj.type == 'MESH':
		mat = mat_source @ mat_obj
		for v in obj.data.vertices:
			vec = mat @ v.co
			v.co = vec

		obj.rotation_euler = source_obj.rotation_euler

def delta_increment(event, x, y, dim):

	v1 = abs(x - y)
	p =  dim * (0.001 * (0.1 if event.shift else 1.0))
	v2 = v1 * p

	return v2

def local_center(obj):

	mesh = obj.data
	center = sum([v.co for v in mesh.vertices], Vector()) / len(mesh.vertices)

	return center

def get_delta(context, event, obj, center):

	region = context.region
	pivot = Vector((region.width / 2, region.height / 2))

	if obj.data.polygons:
		pivot = view3d_utils.location_3d_to_region_2d(context.region, \
										   context.space_data.region_3d, \
										   center.xyz)

		if pivot is None: pivot = Vector((region.width / 2, region.height / 2))

	curr_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
	prev_mouse = Vector((event.mouse_prev_x - context.region.x,
		event.mouse_prev_y - context.region.y))

	delta_x = (pivot - prev_mouse).length
	delta_y = (pivot - curr_mouse).length

	return delta_x, delta_y

def copy_loc_rot(obj, src_obj):

	loc = src_obj.matrix_world.translation
	pivot = obj.matrix_world.inverted() @ loc
	obj.data.transform(Matrix.Translation(pivot))

	rot_basis = src_obj.rotation_euler.to_matrix().to_4x4()
	rot_basis.invert()
	rot_obj = obj.rotation_euler.to_matrix().to_4x4()

	rot = (Matrix.Translation(loc) @
		rot_basis @
		rot_obj @
		Matrix.Translation(-loc))

	for v in obj.data.vertices:
		vec = rot.inverted() @ v.co
		v.co = vec

def v3d_to_v2d(points):

	context = bpy.context

	points_2d = []
	x = type(None)

	for v in points:
		co = view3d_utils.location_3d_to_region_2d(context.region, \
										   context.space_data.region_3d, \
										   v)
		points_2d.append([co.x, co.y] if not isinstance(co, x) else x)

	if x in points_2d: points_2d.clear()

	return points_2d

def scene_ray_hit(context, co, ray_obj=None, scene_ray=False, hit_bounds=False):

	scene = context.scene
	region = context.region
	rv3d = context.region_data

	view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co)
	ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, co)

	ray_target = ray_origin + view_vector

	def hit_objects_mat(objs):

		for o in objs:
			if o.type == 'MESH':
				yield (o, o.matrix_world.copy() if not o.data.is_editmode \
					else o.matrix_parent_inverse.copy())

	def scene_ray_cast(obj, matrix):

		matrix_inv = matrix.inverted()
		ray_origin_obj = matrix_inv @ ray_origin
		ray_target_obj = matrix_inv @ ray_target
		ray_direction_obj = ray_target_obj - ray_origin_obj

		if obj.data.is_editmode \
			or scene_ray:
			depsgraph = context.evaluated_depsgraph_get()
			hit, pos, normal, face_index, obj, matrix_world = scene.ray_cast(depsgraph, ray_origin_obj, ray_direction_obj)
		else:
			hit, pos, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

		if hit:
			return pos, normal, face_index, obj
		else:
			return None, None, None, None

	best_length_squared = None
	best_hit = None
	best_normal = Vector()
	best_face_index = None
	best_obj = None

	display_types = ['TEXTURED', 'SOLID']
	if hit_bounds: display_types.extend(['WIRE', 'BOUNDS'])

	for obj, matrix in hit_objects_mat([ray_obj] if ray_obj \
		else context.visible_objects):
		if obj.type == 'MESH' \
			and obj.display_type in display_types:
			pos, normal, face_index, object = scene_ray_cast(obj, matrix)
			if pos is not None:
				hit_world = matrix @ pos
				length_squared = (hit_world - ray_origin).length_squared

				if not best_length_squared:
					best_length_squared = length_squared

				if length_squared <= best_length_squared:
					best_length_squared = length_squared
					best_hit = hit_world
					best_normal = normal
					best_face_index = face_index
					best_obj = object

	return best_hit, best_normal, best_face_index, best_obj

def duplicate_obj(name, copy_obj, get_eval=True, link=True):

	new_mesh = bpy.data.meshes.new(name)
	new_obj = bpy.data.objects.new(name, new_mesh)
	new_obj.data = get_eval_mesh(copy_obj).copy() \
		if (copy_obj.type != 'MESH' or get_eval) else copy_obj.data.copy()
	new_obj.scale = copy_obj.scale
	new_obj.rotation_euler = copy_obj.rotation_euler
	new_obj.location = copy_obj.location

	if link:
		bpy.context.scene.collection.objects.link(new_obj)
		new_obj.select_set(True)

	return new_obj

def draw_helper_text(self, text):

	if self.mouse_co:
		prefs = bpy.context.preferences.addons[__name__].preferences

		mx = self.mouse_co[0]
		my = self.mouse_co[1]

		font_id = 1
		blf.size(font_id, int(round(15 * bpy.context.preferences.view.ui_scale, 0)), prefs.font_size)

		xheight = 2.1
		rect_offset = 15
		row_offset = 0

		if isinstance(text, list):
			height, row1_length, row2_length, comma = get_text_dimensions(text, xheight, font_id)

			txt_width = row1_length + row2_length + comma + rect_offset
			txt_height = height

			row_offset = row1_length + rect_offset
		else:
			txt_width = blf.dimensions(font_id, text)[0]
			txt_height = (blf.dimensions(font_id, "gM")[1] * xheight)

		xloc = mx + 30
		yloc = (my - 15) - txt_height
		offx = 15
		offy = 10

		rect_vertices = [(xloc - offx, yloc - offy), (xloc + txt_width + offx, yloc - offy), \
						 (xloc + txt_width + offx, yloc + txt_height + offy), (xloc - offx, yloc + txt_height + offy)]

		draw_shader((0.0,0.0,0.0,0.3), 'TRI_FAN', rect_vertices, 1)
		draw_string(xloc, yloc, text, xheight, row_offset, font_id)

def get_text_dimensions(text, xheight, font_id):

	row1_length = max(list(blf.dimensions(font_id, row[0])[0] for row in text))
	row2_length = max(list(blf.dimensions(font_id, row[1])[0] for row in text))
	comma = blf.dimensions(font_id, "_:_")[0]

	line_height = (blf.dimensions(font_id, "gM")[1] * xheight)

	list_height = 0
	for row in text:
		list_height += line_height

	return list_height, row1_length, row2_length, comma

def draw_string(left, bottom, text, xheight, row_offset, font_id):

	color1 = (1.0,1.0,1.0,0.7)
	color2 = (1.0,1.0,1.0,0.7)
	color3 = (1.0,1.0,1.0,0.3)

	blf.enable(font_id,blf.SHADOW)
	blf.shadow(font_id, 0, 0.0, 0.0, 0.0, 1.0)
	blf.shadow_offset(font_id, 1, -1)
	line_height = (blf.dimensions(font_id, "gM")[1] * xheight)
	y_offset = 5

	if isinstance(text, list):
		for string in reversed(text):
			if sum(len(i) for i in string) > 0:
				heading = False
				colrkey = False

				if len(string[1]) == 0: heading = True

				if string[1].find("&") != -1:
					keys_string = string[1].split("&")
					colrkey = True

				blf.position(font_id, (left), (bottom + y_offset), 0)
				blf.color(font_id, *color1)

				if heading:
					blf.draw(font_id, string[0].upper())
				else:
					blf.draw(font_id, string[0].title())

				if not heading:
					colsep = " : "
					blf.position(font_id, (left + row_offset), (bottom + y_offset), 0)
					blf.color(font_id, *color1)
					blf.draw(font_id, colsep)

					coldim = blf.dimensions(font_id, colsep)[0]
					blf.position(font_id, (left + row_offset + coldim), (bottom + y_offset), 0)
					if colrkey:
						blf.color(font_id, *color2)
						blf.draw(font_id, keys_string[0].upper())
						blf.color(font_id, *color3)
						valdim = blf.dimensions(font_id, keys_string[0].title())[0]
						blf.position(font_id, (left + row_offset + valdim + coldim), (bottom + y_offset), 0)
						blf.draw(font_id, keys_string[1].title())
					else:
						blf.draw(font_id, string[1].title())

				y_offset += line_height
	else:
		blf.position(font_id, left, (bottom + y_offset), 0)
		blf.color(font_id, *color1)
		blf.draw(font_id, text)
		y_offset += line_height

	blf.disable(font_id,blf.SHADOW)

def draw_symmetry_helpers(self, context):

	help_txt = [[" ".join("Auto Mirror"), ""]]

	if self.set_axis:

		def enumerate_axis(axes):

			axis_text = ""
			for i in "XYZ":
				if axes[str(i)]: axis_text += " " + i

			return axis_text

		axis_text = enumerate_axis(self.axes)

		help_txt.extend([
				["Mirror Axis", (axis_text.lstrip() if axis_text else "None") + "& X/Y/Z"],\
				["Reset", "&R"],\
				["Cancel", "&ESC/RMB"],\
				["Confirm", "&Space/Enter"],\
				])
	else:
		help_txt.extend([
				["Pick Area", "&LMB"],\
				["Cancel", "&ESC/RMB"],\
				])

	draw_helper_text(self, help_txt)

def draw_callback_px_quick_symm(self, context):

	draw_symmetry_helpers(self, context)

	def create_3dwidget(obj, src_obj, colored=False, axis='X'):

		mesh = obj.data
		bm = bmesh.new()

		pivot = src_obj.matrix_world.inverted() @ src_obj.matrix_world.translation
		v0 = bm.verts.new(pivot)

		v1 = []
		v2 = []

		for co in draw_axis(pivot):
			v = bm.verts.new(co)
			bm.edges.new((v0, v))
			if colored: v1.append(v)

		if colored:
			if axis == 'X':
				v2 = [v1[2], v1[3], v1[4] ,v1[5]]
			if axis == 'Y':
				v2 = [v1[0], v1[1], v1[4] ,v1[5]]
			if axis == 'Z':
				v2 = [v1[0], v1[1], v1[2] ,v1[3]]

			bmesh.ops.delete(bm, geom=v2, context='VERTS')

		bm.to_mesh(mesh)
		bm.free()

		copy_loc_rot(obj, src_obj)

	if self.set_axis:
		hit = v3d_to_v2d([self.mirror_axis])
		marker = draw_marker((hit[0][0], hit[0][1]))
		draw_shader((0, 0, 0, 0.8), 'LINES', marker, size=1)

		create_3dwidget(self.center_axis, self.mirror_obj)
		vertices, indices, loop_tris = get_draw_data(self, self.center_axis)
		draw_shader((1.0, 1.0, 1.0, 0.5), 'LINES', vertices, size=2, indices=indices)

		if self.axes['X']:
			create_3dwidget(self.color_axis, self.mirror_obj, colored=True, axis='X')
			vertices, indices, loop_tris = get_draw_data(self, self.color_axis)
			draw_shader((1.0, 0.0, 0.0, 1.0), 'LINES', vertices, size=2, indices=indices)

		if self.axes['Y']:
			create_3dwidget(self.color_axis, self.mirror_obj, colored=True, axis='Y')
			vertices, indices, loop_tris = get_draw_data(self, self.color_axis)
			draw_shader((0.0, 1.0, 0.0, 1.0), 'LINES', vertices, size=2, indices=indices)

		if self.axes['Z']:
			create_3dwidget(self.color_axis, self.mirror_obj, colored=True, axis='Z')
			vertices, indices, loop_tris = get_draw_data(self, self.color_axis)
			draw_shader((0.0, 0.0, 1.0, 1.0), 'LINES', vertices, size=2, indices=indices)

		try:
			symm_point = tuple(v3d_to_v2d([self.mirror_axis])[0])
			draw_scale_strips(context, self.mirror_obj.matrix_world.translation, symm_point, alpha=0.8)
		except: pass

def draw_marker(origin):

	x, y = origin
	offset = 5
	points = [(x-offset, y+offset), (x, y), (x+offset, y+offset), \
			(x-offset, y-offset), (x, y), (x+offset, y-offset)]

	return points

def draw_axis(co):

	rv3d = bpy.context.region_data
	view_location = rv3d.view_matrix.inverted().translation
	size = (view_location - co).length * 0.1

	x, y, z = co
	v0 = (x, y, z)
	x1 = (x + size, y, z)
	x2 = (x - size, y, z)
	y1 = (x, y + size, z)
	y2 = (x, y - size, z)
	z1 = (x, y, z + size)
	z2 = (x, y, z - size)

	return [x1, x2, y1, y2, z1 ,z2]

def draw_extract_helpers(self, context):

	scene = context.scene
	props = scene.rflow_props

	help_txt = [[" ".join("Extract Faces"), ""]]

	face_count = str(len(self.extract_faces))
	inset_val = str('% 0.2f' % self.inset_val).strip()
	influence_lvl = str('% 0.2f' % props.select_influence).strip()
	x_ray = "Off" if self.draw_solid else "On"

	if self.help_index == 1:
		help_txt.extend([
				["Select faces", face_count + "& LMB Click/Drag"],\
				["Inset faces", inset_val + "& Ctrl+Mousedrag /+Shift"],\
				["Select plus", "&Shift+LMB/RMB"],\
				["Select loop", "&Shift+Alt+LMB/RMB"],\
				["Select plus influence", influence_lvl + "& A-D /+Shift"],\
				["X-Ray", x_ray + "& X"],\
				["Toggle Help", "&H"],\
				])

	if self.help_index == 2:
		help_txt.extend([
				["Remove selection", "&RMB"],\
				["Undo selection", "&Z"],\
				["Reset Inset", "&T"],\
				["Reset selection", "&R"],\
				["Cancel", "&ESC"],\
				["Confirm", "&Space/Enter"],\
				["Toggle Help", "&H"],\
				])

	draw_helper_text(self, help_txt)

def draw_callback_px_draw_extract(self, context):

	draw_extract_helpers(self, context)

	if self.render_hit and self.view_render_hit:
		draw_shader((1.0,1.0,1.0,0.5), 'LINES', self.hit_verts, size=2, indices=self.hit_indices)

	try:
		if self.draw_strips:
			draw_scale_strips(context, local_center(self.extr_obj), self.mouse_co)
	except: pass

def draw_callback_px_draw_extract_shade(self, context):

	r, g, b = (1.0, 1.0, 1.0)

	vertices, indices, loop_tris = get_draw_data(self, self.extr_obj, convert2d=False)
	draw_shader((r, g, b, 0.1), 'TRIS', vertices, size=1, indices=loop_tris, solid=self.draw_solid)
	draw_shader((r, g, b, 0.5), 'LINES', vertices, size=2, indices=indices, solid=self.draw_solid)

def draw_scale_strips(context, coord1, coord2, alpha=0.8):

	def intermediates(p1, p2, nb_points=8):

		x_spacing = (p2[0] - p1[0]) / (nb_points + 1)
		y_spacing = (p2[1] - p1[1]) / (nb_points + 1)

		return [[p1[0] + i * x_spacing, p1[1] +  i * y_spacing]
				for i in range(1, nb_points+1)]

	pivot = tuple(v3d_to_v2d([coord1])[0])
	distance = (Vector(pivot) - Vector(coord2)).length / 5
	line = intermediates(pivot, coord2, nb_points = int(round(distance)))

	draw_shader((0, 0, 0, alpha), 'LINES', line, size=1)

def get_draw_data(self, obj, get_verts=True, get_indices=True, get_tris=True, mat_verts=False, mat_obj=None, convert2d=True):

	coord = []; indices = []; loop_tris = []

	mesh = obj.data
	if get_verts:
		vertices = np.empty((len(mesh.vertices), 3), 'f')
		mesh.vertices.foreach_get("co", np.reshape(vertices, len(mesh.vertices) * 3))

		if mat_verts:
			if not mat_obj: mat_obj = obj
			for i, loc in enumerate(vertices):
				vec = mat_obj.matrix_world @ Vector((loc))
				loc = vec
				vertices[i] = loc

		if convert2d:
			coord = v3d_to_v2d(vertices)
		else: coord = vertices

	if get_indices:
		indices = mesh.edge_keys[:]

	if get_tris:
		mesh.calc_loop_triangles()
		loop_tris = np.empty((len(mesh.loop_triangles), 3), 'i')
		mesh.loop_triangles.foreach_get("vertices", np.reshape(loop_tris, len(mesh.loop_triangles) * 3))

	return coord, indices, loop_tris

def draw_shader(color, type, coords, size=1, indices=None, solid=False):

	vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
	vert_out.smooth('FLOAT', "v_ArcLength")

	shader_info = gpu.types.GPUShaderCreateInfo()
	shader_info.push_constant('MAT4', "u_ViewProjectionMatrix")
	shader_info.push_constant('FLOAT', "u_Scale")
	shader_info.vertex_in(0, 'VEC3', "position")
	shader_info.vertex_in(1, 'FLOAT', "arcLength")
	shader_info.vertex_out(vert_out)
	shader_info.fragment_out(0, 'VEC4', "FragColor")

	shader_info.vertex_source(
		"void main()"
		"{"
		"  v_ArcLength = arcLength;"
		"  gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0f);"
		"}"
	)

	shader_info.fragment_source(
		"void main()"
		"{"
		"  if (step(sin(v_ArcLength * u_Scale), 0.5) == 1) discard;"
		"  FragColor = vec4(1.0);"
		"}"
	)

	shader = gpu.shader.create_from_info(shader_info)
	del vert_out
	del shader_info

	gpu.state.blend_set("ALPHA")
	if solid: gpu.state.depth_test_set("LESS")

	if type =='POINTS':
		gpu.state.point_size_set(size)
	else: gpu.state.line_width_set(size)

	if len(coords) > 0:
		if type != "LINE_STRIP":
			if len(coords[0]) > 2 \
				or solid:
				shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
			else:
				shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

			batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)

			shader.bind()
			shader.uniform_float("color", color)
			batch.draw(shader)
		else:
			arc_lengths = [0]
			for a, b in zip(coords[:-1], coords[1:]):
				arc_lengths.append(arc_lengths[-1] + (Vector(a) - Vector(b)).length)

			batch = batch_for_shader(
				shader, 'LINE_STRIP',
				{"position": coords, "arcLength": arc_lengths},
			)

			matrix = bpy.context.region_data.perspective_matrix @ Matrix()

			shader.bind()
			shader.uniform_float("u_ViewProjectionMatrix", matrix)
			shader.uniform_float("u_Scale", 10)
			batch.draw(shader)

	gpu.state.point_size_set(1)
	gpu.state.line_width_set(1)

	gpu.state.blend_set("NONE")
	if solid: gpu.state.depth_test_set("NONE")

def set_floater_vis(obj, vis=False):

	try:
		cycles_vis = ['visible_diffuse', 'visible_glossy', \
			'visible_transmission', 'visible_volume_scatter', 'visible_shadow']
		for p in cycles_vis: setattr(obj, p, vis)
	except:
		self.report({'WARNING'}, "Cycles render engine not detected.")

def undupe(item):
	return list(dict.fromkeys(item))

def clean_directions(listdir):

	lcopy = listdir.copy()
	while lcopy:
		v1 = Vector(lcopy.pop())
		for v2 in lcopy:
			if round(degrees(v1.angle(v2, 0)), 4) in [0, 90, 180] \
				and v2 in listdir: listdir.remove(v2)

	return listdir

def filter_name(obj, suffix=""):

	obj_name = obj.name
	list_idx = set()
	list_suffix = ["_RLExtr", "_RPanel", "_RAExtr", "_RCells", \
				"_RScatter", "_RPipes", "_Flanges", "_Screws", \
				"_PCloth"]

	for i in list_suffix:
		idx = obj_name.find(i)
		if idx != -1: list_idx.add(idx)

	if list_idx:
		obj_name = obj_name[:min(list_idx)]

	return obj_name + suffix

def init_props(self, event, ops, force=False):

	if ops == 'rloop':
		if event.ctrl or force:
			self.loop_subdv = (0,0,0,0,0); self.cuts_base = 0; self.cuts_smooth = 0.0;

	if ops == "rpanels":
		if event.ctrl or force:
			self.cuts_base = 0; self.cuts_smooth = 0.0;

	if ops == "raxis":
		if event.ctrl or force:
			self.cuts_base = 0; self.inner_cut = (2,2,2)

	if ops == "rcells":
		if event.ctrl or force:
			self.cuts_base = 0; self.cuts_smooth = 0.0;

	if ops == 'rscatter':
		if event.ctrl: self.scatter_points = 10

	if ops == 'rtubes':
		if event.ctrl or force:
			self.cuts_base = 0; self.cuts_smooth = 0.0;

	if ops == 'rvcol':
		if event.ctrl:
			self.color = (1.0,1.0,1.0); self.color_min = (0.0,0.0,0.0)

	if ops == 'pcloth' or 'ndispl':
		if event.ctrl or force:
			self.subd_lvl = 0; self.cuts_base = 0; self.cuts_smooth = 0.0;

	if ops == 'p_insets':
		if event.ctrl or force: self.cuts_base = 0

class OBJECT_OT_r_loop_extrude(Operator):
	'''Stack objects with randomized faces to create interesting shapes'''
	bl_idname = 'rand_loop_extr.rflow'
	bl_label = 'Random Loop Extrude'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	loop_objs : EnumProperty(
		name = "Loop Objects",
		description = "Loop objects 1-6",
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
		max			= 2,
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
		default     = (0.0,0.0,0.0,0.0,0.0),
		size        = 5,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	ldepth_max : FloatVectorProperty(
		name        = "Loop Depth",
		description = "Inset depth per loop",
		default     = (0.025,0.025,0.025,0.025,0.025),
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
		name        = "Smooth",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 1.0,
		step        = 0.1,
		precision   = 3
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

		orig_mesh = cont_mesh = obj.data

		loop_objs = set()
		loop_count = [int(i) for i in self.loop_objs] \
			if self.loop_objs else [0]

		use_sharp = check_sharp_edges(obj)

		ret_idx = set()
		for i in range(0, max(loop_count)):
			bm = bmesh.new()
			temp_mesh = bpy.data.meshes.new(".temp")
			bm.from_mesh(cont_mesh if not self.orig_only else orig_mesh)

			if i == 0 or \
				self.orig_only:
				bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
				bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, cuts=self.cuts_base, \
					use_grid_fill=True, use_smooth_even=True)
			else: bpy.data.meshes.remove(cont_mesh)

			if ret_idx:
				inset_faces = [f for f in bm.faces if f.index in ret_idx]
				bmesh.ops.delete(bm, geom=inset_faces, context='FACES')

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

			if self.indiv_sp:
				solvers = ["WALK", "RADIAL"]
				loop_solver = solvers[self.lsolver_num[i]-1]
				paths = ["NONE", "SHORTEST", "LONGEST"]
				loop_path = paths[self.lpath_num[i]-1]
			else:
				loop_solver = self.solver
				loop_path = self.path

			split_edg, cells = random_walk(bm, idx, min_size, max_size,(self.lratio_seed[i] + i) + self.globl_seed1, \
				sampling=loop_solver, path=loop_path, cut_threshold=self.cut_threshold, wrap_angle=self.cut_method == 'WRAP')

			if self.cut_method == 'WRAP':
				if use_sharp:
					sharp_edg = [e for e in list(set(bm.edges) - set(split_edg)) if not e.smooth]
					split_edg.extend(sharp_edg)
				bmesh.ops.split_edges(bm, edges=split_edg)
			else:
				elist = [e for e in bm.edges if e in split_edg or not e.smooth \
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
						ret = bmesh.ops.inset_region(bm, faces=cell_faces, use_boundary=True, use_even_offset=True, \
							thickness=self.lthick[i], depth=ldepth_random)['faces']
						ret_inset.extend(ret)
			else:
				seed((self.ldepth_seed[i] + i) + self.globl_seed2)
				ldepth_uniform = uniform(self.ldepth_min[i], self.ldepth_max[i])
				loop_cells = sum([x for x in cells if not x in rem_cells], [])
				ret = bmesh.ops.inset_region(bm, faces=loop_cells, use_boundary=True, use_even_offset=True, \
					thickness=self.lthick[i], depth=ldepth_uniform)['faces']
				ret_inset.extend(ret)

			if self.clear_faces != 'NONE':
				remf = list(set(bm.faces).difference(set(ret_inset))) if self.clear_faces == 'INNER' else ret_inset
				bmesh.ops.delete(bm, geom=remf, context='FACES')

			if not self.orig_only: ret_idx = [f.index for f in ret_inset if f in bm.faces]

			if self.tri_perc or self.tri_num: bmesh.ops.join_triangles(bm, faces=bm.faces, \
				angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

			if self.use_clip: clip_center(bm, obj, self.clip_dist, self.clip_axis)

			list_co = [(mat @ v.co) for v in bm.verts if not all(f in ret_inset for f in v.link_faces)] \
				if self.inset_vgroup else []

			bm.to_mesh(temp_mesh)
			bm.free()

			if not self.orig_only:
				cont_mesh = temp_mesh.copy()
				cont_mesh.materials.clear()

			if str(i+1) in self.loop_objs \
				and temp_mesh.polygons:
				new_obj = bpy.data.objects.new(filter_name(obj, "_RLExtr"), temp_mesh)
				orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
				new_obj.scale = orig_scale
				new_obj.rotation_euler = orig_rot.to_euler()
				new_obj.location = orig_loc
				new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
				new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle
				if use_sharp: new_obj.data.edges.foreach_set('use_edge_sharp', [False] * len(new_obj.data.edges))

				assign_mat(self, obj, new_obj, self.mat_index)
				copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

				context.scene.collection.objects.link(new_obj)
				inset_to_vgroup(new_obj, list_co, mat)
				loop_objs.add(new_obj)

		if self.use_dissolve:
			for o in loop_objs:
				mesh = o.data
				bm = bmesh.new()
				bm.from_mesh(mesh)

				if self.use_dissolve:
					bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
						use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

				bm.to_mesh(mesh)
				bm.free()

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
		if self.indiv_sp:
			col.label(text="Solver: 1. Walk 2. Radial")
			col.row(align=True).prop(self, "lsolver_num", text="")
			col.label(text="Path: 1. None 2. Shortest 3. Longest")
			col.row(align=True).prop(self, "lpath_num", text="")
			col.separator(factor=0.5)
		else:
			col.separator(factor=0.5)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Solver:")
			row.row(align=True).prop(self, "solver", expand=True)
			if self.solver != 'RADIAL':
				row = col.row().split(factor=0.27, align=True)
				row.label(text="Path:")
				row.row(align=True).prop(self, "path", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Size Mode:")
		row.row(align=True).prop(self, "size_mode", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
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
		flow.prop(self, "rand_inset")
		flow.prop(self, "orig_only")
		flow.prop(self, "indiv_sp")
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

		self.loop_objs = set()
		self.lratio_seed = (1,1,1,1,1)
		self.ldepth_seed = (1,1,1,1,1)
		self.globl_seed1 = 1
		self.globl_seed2 = 1

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face > 0:
			init_props(self, event, ops='rloop', force=has_face>=props.fselect_limit)
			prefs = context.preferences.addons[__name__].preferences
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
		description = "Minimum bevel offset/width",
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
		min         = 0.0,
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
	cells_height_min : FloatProperty(
		name        = "Min",
		description = "Minimum randomized cell height",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	cells_height_max : FloatProperty(
		name        = "Max",
		description = "Maximum randomized cell height",
		default     = 0.0,
		min         = 0.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
		)
	height_seed : IntProperty(
		name        = "Height Seed",
		description = "Height randomize seed",
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
			('TOP', 'Top','Sharpen top plate area')),
		default = 'NONE'
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
	merge_pnl : BoolProperty(
		name        = "Merge Panel",
		description = "Merge panel to original object",
		default     = False
		)
	floater_set : BoolProperty(
		name        = "Floater",
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

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.type == "MESH"

	def execute(self, context):
		obj = context.active_object
		obj.update_from_editmode()

		mat = obj.matrix_world
		list_co = []

		use_sharp = False
		self.use_merge = True if self.clear_faces == 'NONE' else False
		limit_smooth = self.limit_smooth != 'NONE'

		orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=self.cuts_smooth, cuts=self.cuts_base, \
			use_grid_fill=True, use_smooth_even=True)

		if self.tri_perc \
			or self.tri_num:
			tval = self.tri_perc if self.size_mode == 'PERCENT' else self.tri_num
			tris = get_tri_faces(bm.faces, tval, self.edge_seed, mode=self.size_mode)
			bmesh.ops.triangulate(bm, faces=tris, quad_method=choice(['BEAUTY', 'FIXED']))

		idx = set([f.index for f in bm.faces])
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
			cut_threshold=self.cut_threshold, wrap_angle=self.cut_method == 'WRAP', only_msharp=self.only_msharp)

		if not self.only_msharp:
			if self.panel_amount < 100:
				tot = len(cells)
				amt = int(tot * (self.panel_amount/100))
				cells = cells[:amt] if not self.invert_panel_amount else cells[(tot-amt):]
				cells_flat = list(chain.from_iterable(cells))
				split_edg = [e for e in split_edg if any(f in cells_flat for f in e.link_faces)]
				if self.remove_panels: bmesh.ops.delete(bm, geom=list(set(bm.faces) - set(cells_flat)), context='FACES')

			if self.cut_method == 'WRAP':
				if check_sharp_edges(obj):
					use_sharp = True
					sharp_edg = [e for e in list(set(bm.edges) - set(split_edg)) if not e.smooth]
					split_edg.extend(sharp_edg)
				bmesh.ops.split_edges(bm, edges=split_edg)
			else:
				elist = [e for e in bm.edges if e in split_edg or not e.smooth \
						or (e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)]
				bmesh.ops.split_edges(bm, edges=elist)

			if sum([self.bvl_offset_min, self.bvl_offset_max]) > 0:
				self.use_merge = False
				for i, c in enumerate(cells):
					old_faces = []
					new_faces = []
					for x, f in enumerate(c):
						corner_verts = [v for v in f.verts if v.is_boundary and v.calc_edge_angle(None) \
							and v.calc_edge_angle(None) >= self.bvl_angle]
						if corner_verts:
							old_faces.append(f)
							bvl_verts = []
							for y, v in enumerate(corner_verts):
								seed(self.bvl_seed + i + x + y)
								bvl = bmesh.ops.bevel(
									bm,
									geom            = [v],
									offset          = uniform(self.bvl_offset_min, self.bvl_offset_max),
									offset_type     = 'OFFSET',
									segments        = self.bvl_seg,
									profile         = 0.5,
									affect          = 'VERTICES',
									clamp_overlap	= True
									)
								if bvl['verts']:
									new_faces.append(bvl['verts'][0].link_faces[0])
									bvl_verts.extend(bvl['verts'])
							bmesh.ops.remove_doubles(bm, verts=bvl_verts, dist=1e-4)

					for f in old_faces: cells[i].remove(f)
					cells[i].extend([f for f in new_faces if f in bm.faces])
					cells[i] = undupe((cells[i]))

			margin_faces = []
			if self.margin:
				margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
					use_even_offset=True, thickness=self.margin)['faces']
				if not self.use_merge \
					or not self.merge_pnl:
					bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

			ret_inset = []
			inset_faces = []

			if self.cut_method == 'WRAP' \
				and sum([self.cells_height_min, self.cells_height_max]) > 0:
				for i, face_cells in enumerate(cells):
					seed(self.height_seed + i)
					up = uniform(self.cells_height_min, self.cells_height_max)
					inset_faces = face_cells if not self.use_merge else [f for f in face_cells if not f in margin_faces]
					ret = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, use_even_offset=True, \
						thickness=self.thickness, depth=self.depth + up)['faces']
					ret_inset.extend(ret)
			else:
				inset_faces = bm.faces if not self.use_merge else [f for f in bm.faces if not f in margin_faces]
				ret_inset = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, use_even_offset=True, \
					thickness=self.thickness, depth=self.depth)['faces']

				if sum([self.cells_height_min, self.cells_height_max]) > 0:
					for i, faces in enumerate(cells):
						seed(self.height_seed + i)
						up = uniform(self.cells_height_min, self.cells_height_max)
						fv = undupe(sum((list(f.verts) for f in faces), []))
						for v in fv:
							normals = [f.normal for f in v.link_faces if f in faces]
							n = sum(normals, Vector()) / len(normals)
							v.co += up * n

			if limit_smooth:
				inset_edges = set(sum([list(f.edges) for f in ret_inset], []))
				for e in inset_edges:
					e.smooth = True
					if self.limit_smooth == 'BASE':
						if len([lf for lf in e.link_faces if lf in inset_faces]) == 0 \
							and len([lf for lf in e.link_faces if lf in ret_inset]) == 1: e.smooth = False
					else:
						if len([lf for lf in e.link_faces if lf in inset_faces]) == 1 \
							and len([lf for lf in e.link_faces if lf in ret_inset]) == 1: e.smooth = False

			if self.clear_faces != 'NONE':
				remf = list(set(bm.faces).difference(set(ret_inset))) if self.clear_faces == 'INNER' else ret_inset
				bmesh.ops.delete(bm, geom=remf, context='FACES')

			if self.tri_perc or self.tri_num: bmesh.ops.join_triangles(bm, faces=bm.faces, \
				angle_face_threshold=radians(180), angle_shape_threshold=radians(180))

			if self.use_dissolve: bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
				use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

			if self.use_clip: clip_center(bm, obj, self.clip_dist, self.clip_axis)

			list_co = [(mat @ v.co) for v in bm.verts if not all(f in ret_inset for f in v.link_faces)] \
				if self.inset_vgroup else []

		bm.to_mesh(temp_mesh)

		link_obj = True
		if self.merge_pnl and \
			self.use_merge:
			if orig_mesh.is_editmode:
				bm_src = bmesh.from_edit_mesh(orig_mesh)
			else:
				bm_src = bmesh.new()
				bm_src.from_mesh(orig_mesh)

			listf = [f for f in bm_src.faces if f.select]

			if limit_smooth:
				edges = set(sum([list(f.edges) for f in listf], []))
				for e in edges:
					if not all(f in listf for f in e.link_faces): e.smooth = False

			bmesh.ops.delete(bm_src, geom=listf, context='FACES')
			bmesh.ops.subdivide_edges(bm_src, edges=bm_src.edges, smooth=self.cuts_smooth, cuts=self.cuts_base, \
				use_grid_fill=True, use_smooth_even=True)

			bm_src.from_mesh(temp_mesh)
			link_obj = False

			new_vrt = [ v.co for v in bm.verts ]
			doubles = [ v for v in bm_src.verts if v.co in new_vrt ]
			bmesh.ops.remove_doubles(bm_src, verts=doubles, dist=1e-4)

			if orig_mesh.is_editmode:
				bmesh.update_edit_mesh(orig_mesh)
			else:
				bm_src.to_mesh(orig_mesh)
				bm_src.free()

		bm.free()

		if link_obj:
			new_obj = bpy.data.objects.new(filter_name(obj, "_RPanel"), temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc
			new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
			new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

			if use_sharp \
				and not limit_smooth:
				new_obj.data.edges.foreach_set('use_edge_sharp', [False] * len(new_obj.data.edges))

			assign_mat(self, obj, new_obj, self.mat_index)
			copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			context.scene.collection.objects.link(new_obj)

			if not self.only_msharp:
				inset_to_vgroup(new_obj, list_co, mat)

				if self.floater_set \
					and self.clear_faces != 'NONE': set_floater_vis(new_obj)
			else:
				select_isolate(new_obj)
		else:
			old_vgroup = obj.vertex_groups.get("panel_cut_faces")
			if old_vgroup: obj.vertex_groups.remove(old_vgroup)
			inset_to_vgroup(obj, list_co, mat)

		return {"FINISHED"}

	def draw(self, context):
		props = context.scene.rflow_props
		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Solver:")
		row.row(align=True).prop(self, "solver", expand=True)
		if self.solver != 'RADIAL':
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
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Inset:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "thickness")
		split.row(align=True).prop(self, "depth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cells_height_min")
		split.row(align=True).prop(self, "cells_height_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height Seed:")
		row.row(align=True).prop(self, "height_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Method:")
		row.row(align=True).prop(self, "cut_method", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Cut Angle:")
		row.row(align=True).prop(self, "cut_threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bevel Offset:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "bvl_offset_min")
		split.row(align=True).prop(self, "bvl_offset_max")
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
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Material Index:")
		row.row(align=True).prop(self, "mat_index", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
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

	def invoke(self, context, event):
		obj = context.active_object
		props = context.scene.rflow_props

		self.notch_seed = 1
		self.edge_seed = 1
		self.bvl_seed = 1
		self.height_seed = 1
		self.use_merge = True
		self.only_msharp = False

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face > 0:
			init_props(self, event, ops='rpanels', force=has_face>=props.fselect_limit)
			prefs = context.preferences.addons[__name__].preferences
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
		default     = (1,1,1),
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
		default     = (0,0,0),
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
	single_obj : BoolProperty(
		name        = "Single Object",
		description = "Make the extrusions part of the source mesh",
		default     = False
		)
	hit_self : BoolProperty(
		name        = "Hit Self",
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

		mesh = obj.data

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
							(vec - f.normal).length < thresh[n] \
							or (vec + f.normal).length < thresh[n]]

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
			new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
			new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

			assign_mat(self, obj, new_obj, self.mat_index)
			copy_modifiers([obj, new_obj], mod_types=['MIRROR'])

			context.scene.collection.objects.link(new_obj)

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
		flow.prop(self, "hit_self")
		flow.prop(self, "cut_symm")
		if context.active_object.mode == 'OBJECT': flow.prop(self, "single_obj")

	def invoke(self, context, event):
		obj = context.active_object
		props = context.scene.rflow_props

		self.loop_seed = (1,1,1)
		self.depth_seed = (1,1,1)
		self.globl_seed = 1
		self.mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face > 0:
			init_props(self, event, ops='raxis', force=has_face>=props.fselect_limit)
			prefs = context.preferences.addons[__name__].preferences
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
		default     = 0.0,
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
	margin : FloatProperty(
		name        = "Margin",
		description = "Margin from boundary edges",
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
		name        = "Floater",
		description = "Set cycles render visibility to make it look like resulting mesh is part of source mesh",
		default     = False
		)
	clear_adj : BoolProperty(
		name        = "Clear Adjacent Faces",
		description = "Clear adjacent faces from the original face pool",
		default     = False
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.type == "MESH"

	def execute(self, context):
		obj = context.active_object
		obj.update_from_editmode()

		if not self.use_mirror:
			orig_mesh = get_eval_mesh(obj)
		else:
			orig_mesh = obj.data

		use_sharp = False

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		if self.margin:
			bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if e.calc_face_angle(None) \
				and e.calc_face_angle(None) >= radians(5)])
			margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, \
				use_even_offset=True, thickness=self.margin)['faces']
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
			pfc = undupe(plus_faces.copy()); plus_faces.clear()
			for f in pfc:
				e = choice(f.edges[:])
				plus_faces.append(choice(e.link_faces[:]))
			init_faces.extend(plus_faces)

		remf = list(set(bm.faces).difference(set(init_faces)))
		bmesh.ops.delete(bm, geom=remf, context='FACES')

		if self.cut_method == 'INDIV':
			bmesh.ops.split_edges(bm, edges=bm.edges)

		def offset_verts(verts, offset):

			for v in verts:
				v.co += v.normal * (v.calc_shell_factor() * offset)

		if self.offset_mode == 'INDIV' or (self.offset_mode == 'CONST' and self.cut_method == 'INDIV'):
			if self.offset_mode == 'CONST':
				seed(self.offset_seed)
				offset = uniform(0, self.offset)

			isles = [[bm.verts[i] for i in n] for n in get_islands(None, bm)] \
				if self.cut_method == 'SHARP' else [f.verts[:] for f in bm.faces]

			for i, verts in enumerate(isles):
				if self.offset_mode == 'INDIV':
					seed(self.offset_seed + i)
					offset = uniform(0, self.offset)

				offset_verts(verts, offset)

				seed(self.depth_seed + i)
				depth = uniform(0, self.depth)
				fv = undupe(sum((list(v.link_faces) for v in verts), []))
				bmesh.ops.inset_region(bm, faces=fv, use_boundary=True, \
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
		new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
		new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

		assign_mat(self, obj, new_obj, self.mat_index)
		if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
		if self.floater_set: set_floater_vis(new_obj)

		context.scene.collection.objects.link(new_obj)

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
		row.label(text="Subdivision:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "cuts_base")
		split.row(align=True).prop(self, "cuts_smooth")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
		row.row(align=True).prop(self, "margin", text="")
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

	def invoke(self, context, event):
		obj = context.active_object
		props = context.scene.rflow_props

		self.pool_seed = 0
		self.offset_seed = 0
		self.depth_seed = 0

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face > 0:
			init_props(self, event, ops='rcells', force=has_face>=props.fselect_limit)
			prefs = context.preferences.addons[__name__].preferences
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

	def point_on_triangle(self, face):
		'''https://blender.stackexchange.com/a/221597'''

		a, b, c = map(lambda v: v.co, face.verts)
		a2b = b - a
		a2c = c - a
		height = triangular(low=0.0, high=1.0, mode=0.0)

		return a + a2c*height + a2b*(1-height) * random(), face.normal, face.calc_center_median()

	def add_scatter(self, obj, data):

		if not data.polygons: return

		new_obj = bpy.data.objects.new(filter_name(obj, "_RScatter"), data)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc
		new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
		new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

		assign_mat(self, obj, new_obj, self.mat_index)

		if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
		bpy.context.scene.collection.objects.link(new_obj)

	def execute(self, context):
		obj = context.active_object
		obj.update_from_editmode()

		if not self.use_mirror:
			orig_mesh = get_eval_mesh(obj)
		else:
			orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)
		bm.to_mesh(temp_mesh)

		bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')

		if self.use_dissolve: bmesh.ops.dissolve_limit(bm, angle_limit=self.angle, \
			use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})

		if self.margin:
			bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if e.calc_face_angle(None) \
				and e.calc_face_angle(None) >= radians(5)])
			margin_faces = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin, depth=0.0)['faces']
			bmesh.ops.delete(bm, geom=margin_faces, context='FACES')

		if self.offset:
			for v in bm.verts:
				v.co -= v.normal * (v.calc_shell_factor() * self.offset)

		triangles = bmesh.ops.triangulate(bm, faces=bm.faces)['faces']
		surfaces = map(lambda t: t.calc_area(), triangles)
		seed(self.scatter_seed)
		listp = choices(population=triangles, weights=surfaces, k=self.scatter_points)
		points = map(self.point_on_triangle, listp)

		def get_rot(obj, track="Z", normal=Vector()):

			quat = normal.to_track_quat(track, 'Y')
			mat = obj.matrix_world @ quat.to_matrix().to_4x4()
			rot = mat.to_3x3().normalized()

			return rot

		cont = True
		scatter_obj = None
		scatter_type = self.scatter_type
		matlist = []
		single_obj = self.single_scatter

		for i, p in enumerate(list(points)):
			bm_scatter = bmesh.new()
			scatter_data = bpy.data.meshes.new(".temp_scatter")

			loc = p[0]
			normal = p[1]
			center = p[2]

			if scatter_type == 'CUBE':
				seed(self.size_seed + i)
				scatter_verts = bmesh.ops.create_cube(bm_scatter, size=uniform(self.size_min, self.size_max) \
					if not self.sca_mode == 'UNIFORM' else self.uni_size)['verts']
				rot = get_rot(obj, '-Z', normal)
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
					rot = get_rot(scatter_obj, 'Z', normal)
				else: cont = False

			if cont:
				loc += ((center-loc) * self.cluster)
				if sum([self.explode_min, self.explode_max]) > 0:
					seed(self.explode_seed + i)
					loc += normal * uniform(self.explode_min, self.explode_max)

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
									for x in range(int(360/v)):
										rot_quotient.append(v * (x+1))
									axis[n] = choice(rot_quotient)
						else: axis[n] = v
						seed(0)

					return Euler(Vector(axis))

				x, y, z = self.rot_axis
				rot_axis = rot_seed(x, y, z)
				_, orig_rot, _ = obj.matrix_world.decompose()
				bmesh.ops.rotate(
					bm_scatter,
					verts   = scatter_verts,
					cent    = loc,
					matrix  = orig_rot.to_matrix().inverted() @ rot @ rot_axis.to_matrix()
					)

			if self.use_mirror: bisect_symmetry(bm_scatter, obj)

			bm_scatter.to_mesh(scatter_data)
			bm_scatter.free()

			if not single_obj:
				if scatter_data.polygons: self.add_scatter(obj, scatter_data)
			else:
				bm.from_mesh(scatter_data)
				bpy.data.meshes.remove(scatter_data)

		if single_obj: bmesh.ops.delete(bm, geom=triangles, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		if not single_obj:
			bpy.data.meshes.remove(temp_mesh)
		else:
			self.add_scatter(obj, temp_mesh)

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
		flow.prop(self, "single_scatter")
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

			prefs = context.preferences.addons[__name__].preferences
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
		default     = 6,
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

		if not self.use_mirror:
			orig_mesh = get_eval_mesh(obj)
		else:
			orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		face_sel = [f for f in bm.faces if not f.select]
		bmesh.ops.delete(bm, geom=face_sel, context='FACES')

		bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)

		if self.margin > 0:
			margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin, depth=0.0)['faces']
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
		indices = [e.index for e in bm.edges]
		cells = []

		pnum = 0
		while indices and pnum < self.panel_num:
			seed(self.edg_seed)
			x = choice(indices)
			indices.remove(x)

			bm.edges.ensure_lookup_table()
			edg = bm.edges[x]
			cell = [x]
			walk = 0

			cell_e = set()
			last_v = None

			def add_body_limit(edge, vert):

				ov = edge.other_vert(vert)
				for link_e in ov.link_edges:
					if not link_e in cell_e: cell_e.add(link_e)

			t_count = self.turn_count
			while walk < (self.edg_length_max-1):
				prev_e = edg
				curr_v = prev_e.verts[0]
				dir1 = prev_e.verts[0].co - prev_e.verts[1].co

				if walk == 0:
					e_verts = sample(list(prev_e.verts), len(prev_e.verts))
					curr_v = choice(e_verts)
				else:
					curr_v = prev_e.other_vert(last_v)

				add_body_limit(prev_e, curr_v)
				lnk_edges = list(curr_v.link_edges); shuffle(lnk_edges)
				edge_list = { e.index: e.calc_length() for e in lnk_edges }

				fallback = None
				if len(set(list(edge_list.keys())).intersection(set(cell))) < 2:
					for n, curr_e in enumerate(lnk_edges):
						dir2 = curr_e.verts[0].co - curr_e.verts[1].co
						angle = dir1.angle(dir2)

						edge_length = list(edge_list.values())
						length_solver = min(edge_length) if self.path == 'LONGEST' \
							else max(edge_length) if self.path == 'SHORTEST' else 0.0

						if curr_e.index in indices and \
							curr_e.calc_length() != length_solver:
							if not curr_e in cell_e: fallback = curr_e

						if t_count == 0:
							t_angle = angle >= self.turn_angle
							t_count = self.turn_count
						else: t_angle = angle < self.turn_angle

						last_e = n+1 == len(lnk_edges)

						if t_angle or last_e:
							if curr_e.index in indices and \
								curr_e.calc_length() != length_solver:
								if not curr_e in cell_e:
									idx = curr_e.index
									edg = bm.edges[idx]
									indices.remove(idx)
									cell.append(idx)
									last_v = curr_v
									walk += 1
									break
							else:
								if fallback and last_e:
									idx = fallback.index
									edg = bm.edges[idx]
									indices.remove(idx)
									cell.append(idx)
									last_v = curr_v
									walk += 1
									break

					t_count -= 1

				if prev_e.index == cell[-1]:
					break

			if cell:
				for i in cell:
					x = False
					if not self.limit_body:
						if i == cell[0] or i == cell[-1]: x = True
					else: x = True

					if x:
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
				vrt_offset = uniform(self.edg_offset_min, self.edg_offset_max)
				for v in newv:
					origv = [v0 for v0 in oldv if v0.co == v.co]
					if origv:
						v1 = origv[0]
						v.co += (v1.normal * (v1.calc_shell_factor() * vrt_offset))
				seed(0)

		bmesh.ops.delete(bm, geom=oldv, context='VERTS')

		if sum([self.bvl_offset_min, self.bvl_offset_max]) > 0:
			for i, v in enumerate(bm.verts):
				angle = v.calc_edge_angle(None)
				if angle and \
					angle >= self.bvl_angle:
					seed(self.bvl_seed + i)
					bmesh.ops.bevel(
						bm,
						geom            = [v],
						offset          = uniform(self.bvl_offset_min, self.bvl_offset_max),
						offset_type     = 'OFFSET',
						segments        = self.bvl_seg,
						profile         = 0.5,
						affect          = 'VERTICES',
						clamp_overlap	= True
						)
					bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

		bm.to_mesh(temp_mesh)
		bm.free()

		if temp_mesh.vertices:
			new_obj = bpy.data.objects.new(filter_name(obj, "_RPipes"), temp_mesh)
			orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
			new_obj.scale = orig_scale
			new_obj.rotation_euler = orig_rot.to_euler()
			new_obj.location = orig_loc
			new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
			new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle

			context.scene.collection.objects.link(new_obj)

			select_isolate(new_obj)
			self.curve_convert(new_obj, self.width, self.resnum, self.smooth_shade)
			if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
			assign_mat(self, obj, new_obj, self.mat_index)
			select_isolate(obj)
		else:
			bpy.data.meshes.remove(temp_mesh)

		return {"FINISHED"}

	def draw(self, context):
		props = context.scene.rflow_props
		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
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
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "edg_offset_min")
		split.row(align=True).prop(self, "edg_offset_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset Seed:")
		row.row(align=True).prop(self, "offset_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Curve:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "width")
		split.row(align=True).prop(self, "resnum")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Bvl Offset:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "bvl_offset_min")
		split.row(align=True).prop(self, "bvl_offset_max")
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
		flow.prop(self, "smooth_shade")

	def invoke(self, context, event):
		obj = context.active_object
		props = context.scene.rflow_props

		self.edg_seed = 1
		self.offset_seed = 1

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face > 0:
			init_props(self, event, ops='rtubes', force=has_face>=props.fselect_limit)
			prefs = context.preferences.addons[__name__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

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
		precision   = 4
		)
	norm_offset_max : FloatProperty(
		name        = "Max",
		description = "Maximum normal offset for curve",
		default     = 1.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 4
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

	def add_curve_object(
				self,
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

		bpy.context.scene.collection.objects.link(curve)
		curve.data.resolution_u = resolution_u
		curve.data.fill_mode = 'FULL'
		curve.data.bevel_depth = bevel
		curve.data.bevel_resolution = bevel_resolution
		curve.data.extrude = extrude
		curve.data.twist_mode = twist_mode
		curve.data.twist_smooth = twist_smooth
		curve.matrix_world = matrix

		return curve

	def execute(self, context):
		obj = context.active_object
		sel_objs = context.selected_objects

		limit = self.island_limit != 'NONE'
		rf_props = context.scene.rflow_props

		def set_data_origin(obj, data, origin):

			pivot = obj.matrix_world.inverted() @ origin
			data.transform(Matrix.Translation(-pivot))

		bm = bmesh.new()

		sel_objs = sorted(sel_objs, key=lambda o: o.name)
		for o in sel_objs:
			o.update_from_editmode()
			clone_data = get_eval_mesh(o).copy() if not self.use_mirror else o.data.copy()
			set_data_origin(o, clone_data, obj.matrix_world.translation)
			bm.from_mesh(clone_data)
			bmesh.ops.delete(bm, geom=[f for f in bm.faces if not f.select], context='FACES')
			bpy.data.meshes.remove(clone_data)

		if not bm.faces:
			self.report({'WARNING'}, "No faces selected.")
			bm.free()
			return {"FINISHED"}

		if self.offset:
			for v in bm.verts:
				v.co -= v.normal * (v.calc_shell_factor() * self.offset)

		if self.margin:
			margin = bmesh.ops.inset_region(bm, faces=bm.faces, use_boundary=True, use_even_offset=True, \
				thickness=self.margin, depth=0.0)['faces']
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
					points = [p1, o + self.manual_offset + (rf_props.normal_guide * offset), p2]

					temp_curve = self.add_temp_curve(points)
					coords = self.get_curve_points(temp_curve.splines[0])
					bpy.data.curves.remove(temp_curve)

					for n, v in enumerate(coords):
						if n != 0 and n != len(coords) - 1:
							coords[n] = v + Vector([uniform(-self.wiggle_noise,self.wiggle_noise) for n in range(3)])

				seed(self.radius_seed)
				curve = self.add_curve_object(
						coords,
						Matrix(),
						'RCables',
						self.spline_type,
						self.res_u,
						self.bvl_depth,
						self.bvl_res,
						self.extrude,
						self.r_radius,
						self.twist_mode,
						self.twist_smooth,
						self.tilt
						)
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

			bpy.ops.object.mode_set(mode=save_mode)

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

	def invoke(self, context, event):
		self.points_seed = 1
		self.slack_seed = 1
		self.offset_vector = (0,0,0)

		if event.alt:
			for o in context.selected_objects:
				get_linked_flat_faces(o)

		prefs = context.preferences.addons[__name__].preferences
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
	use_seams : BoolProperty(
		name        = "Use Seams",
		description = "Also use seams as island limit",
		default     = False
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
		return context.active_object is not None and context.active_object.type == "MESH"

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

				color_layer = mesh.vertex_colors.get(layer) \
					or mesh.vertex_colors.new(name=layer)

				mesh.attributes.active_color = mesh.attributes[layer]

				bm = bmesh.new()
				bm.from_mesh(mesh)

				color_layer = bm.loops.layers.color.get(layer) \
					or bm.loops.layers.color.new(layer)

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
									edge_mark = e.smooth if not self.use_seams else (e.smooth and not e.seam)
									if e.is_contiguous and edge_mark:
										for f_linked in e.link_faces:
											if f_linked not in linked_faces:
												traversal_stack.append(f_linked)
												loops_color_layer(f_linked, vertex_color)
												if f_linked in listf: listf.remove(f_linked)

							offset += 1
							if offset == self.offset:
								i += 1
								offset = 0

				bm.to_mesh(mesh)
				bm.free()
				mesh.update()

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
		row.label(text=(" " * 3) + "(shift+click to add multiple or remove)")
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
			col.prop(self, "use_seams")
		col.prop(self, "dirty_vc")
		if self.dirty_vc:
			col.separator(factor=0.5)
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Blur Strength:")
			row.row(align=True).prop(self, "blur_str", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Blur Iterations:")
			row.row(align=True).prop(self, "blur_iter", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Highlight Angle:")
			row.row(align=True).prop(self, "hi_angle", text="")
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Dirt Angle:")
			row.row(align=True).prop(self, "drt_angle", text="")
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

		prefs = context.preferences.addons[__name__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

class OBJECT_OT_r_animation(Operator):
	'''Create randomized animation in move/scale/rotate transforms'''
	bl_idname = 'rand_anim.rflow'
	bl_label = 'Random Animation'
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

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
		default     = 1,
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
	add_parent : BoolProperty(
		name        = "Add Parent Empty",
		description = "Add parent empty to objects",
		default     = False
		)
	face_normal : BoolProperty(
		name        = "Align To Normal",
		description = "Align parent empty to normal vector",
		default     = False
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.mode == "OBJECT"

	def set_mod_vis(self, obj, listmod=[], hide=True):

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
				if m in listmod:
					m.show_viewport = True

	def clear_parent(self, child):

		matrix_copy = child.matrix_world.copy()
		child.parent = None
		child.matrix_world = matrix_copy

	def set_parent(self, context, list_obj):

		rf_props = context.scene.rflow_props

		empty = bpy.data.objects.new("RA_Parent", None)
		context.scene.collection.objects.link(empty)
		empty.empty_display_size = self.size_empty
		empty.empty_display_type = self.type_empty

		empty.rotation_euler = context.active_object.rotation_euler.copy()

		global_loc = context.active_object.matrix_world.translation if self.loc_empty == 'ACTIVE' \
			else context.scene.cursor.location if self.loc_empty == 'CURSOR' \
			else sum([o.matrix_world.translation for o in list_obj], Vector()) / len(list_obj)

		target_local_loc = empty.matrix_world.inverted() @ global_loc
		empty.matrix_world.translation = global_loc

		listn = []
		for o in list_obj:
			old_parent = o.parent
			self.clear_parent(o)
			reset_transforms(o, False, True, True)

			o.parent = empty
			o.matrix_parent_inverse.translation -= target_local_loc
			if old_parent is not None and not old_parent.children: remove_obj(old_parent)

		if self.face_normal:
			normal = rf_props.normal_guide
			if normal != Vector:
				quat = normal.to_track_quat('Z', 'Y')
				mat = quat.to_matrix().to_4x4()
				rot = mat.to_3x3().normalized()
				empty.rotation_euler = rot.to_euler()

		if not empty.children: remove_obj(empty)

	def execute(self, context):
		list_obj = []
		for i, o in enumerate(context.selected_objects):
			if o.type == 'MESH':
				if self.pivot == 'GEOMETRY':
					listmod = self.set_mod_vis(o)
					o_data = get_eval_mesh(o)
					set_origin(o, sum([o.matrix_world @ v.co for v in o_data.vertices], Vector()) / len(o_data.vertices))
					self.set_mod_vis(o, listmod, False)
				elif self.pivot == 'CURSOR':
					set_origin(o, context.scene.cursor.location)

			frames = [self.start_frame, self.end_frame]
			frames.sort()

			def create_animation_data(o):

				o.animation_data_create()
				o.animation_data.action = bpy.data.actions.new(name="RandomAction")

			if self.clear_anim:
				reset_transforms(o, False, True, True)
				o.animation_data_clear()
				create_animation_data(o)
			else:
				if not o.animation_data \
					or not o.animation_data.action:
					create_animation_data(o)

			dpath = "rotation_euler" if self.dpath == 'ROTATE' else 'location' \
				if self.dpath == 'MOVE' else 'scale'

			for axis in self.axis:
				fcurve = o.animation_data.action.fcurves.find(dpath, index=int(axis))
				if fcurve:
					o.animation_data.action.fcurves.remove(fcurve)

				if self.anim_seed > 1:
					seed(self.anim_seed + i)
					kval1 = uniform(self.rot_min, self.rot_max) if self.dpath == 'ROTATE' \
						else o.matrix_world.translation[int(axis)] + uniform(self.val_min, self.val_max) \
						if self.dpath == 'MOVE' else uniform(self.val_min, self.val_max)
				else:
					kval1 = min(self.rot_min, self.rot_max) if self.dpath == 'ROTATE' \
						else o.matrix_world.translation[int(axis)] + min(self.val_min, self.val_max) \
						if self.dpath == 'MOVE' else min(self.val_min, self.val_max)

				fcurve = o.animation_data.action.fcurves.new(
					data_path=dpath, index=int(axis)
				)
				k1 = fcurve.keyframe_points.insert(
					frame   = frames[0],
					value   = kval1
				)
				k1.interpolation = "LINEAR"

				if self.frame_seed > 1:
					seed(self.frame_seed + i)
					end_frame = randint(frames[0], frames[1])
				else:
					end_frame = frames[1]

				if self.anim_seed > 1:
					seed((self.anim_seed + 1) + i)
					kval2 = uniform(self.rot_min, self.rot_max) if self.dpath == 'ROTATE' \
						else o.matrix_world.translation[int(axis)] + uniform(self.val_min, self.val_max) \
						if self.dpath == 'MOVE' else uniform(self.val_min, self.val_max)
				else:
					kval2 = max(self.rot_min, self.rot_max) if self.dpath == 'ROTATE' \
						else o.matrix_world.translation[int(axis)] + max(self.val_min, self.val_max) \
						if self.dpath == 'MOVE' else max(self.val_min, self.val_max)

				k2 = fcurve.keyframe_points.insert(
					frame   = end_frame,
					value   = kval2
				)
				k2.interpolation = "LINEAR"

				if self.use_cycles:
					m = fcurve.modifiers.new('CYCLES')
					m.mode_before = self.mode
					m.mode_after = self.mode

			list_obj.append(o)

		if self.add_parent and list_obj:
			self.set_parent(context, list_obj)

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.separator(factor=0.1)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Animation:")
		row.row(align=True).prop(self, "dpath", expand=True)
		if self.use_cycles:
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Mode:")
			row.row(align=True).prop(self, "mode", expand=True)
		if context.active_object.type == 'MESH':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Pivot:")
			row.row(align=True).prop(self, "pivot", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Axis:")
		row.row(align=True).prop(self, "axis", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text=" ")
		row.label(text=(" " * 3) + "(shift+click to add multiple or remove)")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Frames:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "start_frame")
		split.row(align=True).prop(self, "end_frame")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Frames Seed:")
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
		row.label(text="Animation Seed:")
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
		if self.add_parent: flow.prop(self, "face_normal")
		col.prop(self, "reset_transform")

	def invoke(self, context, event):
		self.frame_seed = 1
		self.value_seed = 1
		self.axis = set()
		self.add_parent = False

		prefs = context.preferences.addons[__name__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
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
		rf_props = sce.rflow_props

		self.mouse_co = event.mouse_region_x, event.mouse_region_y
		addon_prefs = bpy.context.preferences.addons[__name__].preferences

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
						rf_props.normal_guide = bm.faces[index].normal @ context.active_object.matrix_world.inverted()

						bm.free()
					else:
						rf_props.normal_guide = context.region_data.view_rotation @ Vector((0,0,1))
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

			def orient_to_curve(bm_cont, listv=[]):

				if not listv: listv = bm_cont.verts

				if type != 'BASIC':
					bmesh.ops.scale(
						bm_cont,
						vec     = Vector(tuple([self.radius] * 3)),
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
					radius1     = self.radius,
					radius2     = self.radius,
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
						bpy.ops.import_mesh.stl(filepath=filepath, global_scale=1.0)

						import_obj = context.selected_objects[0]
						custom_data = import_obj.data
						custom_data.name += "_rflow_mesh"

						curve.select_set(True)
						context.view_layer.objects.active = curve

						bpy.data.objects.remove(import_obj)

					orient_bmesh_data(custom_data)

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
							add_fittings(curve, bm, p3, tangent, n)

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
								add_fittings(curve, bm, p1, tangent, x)

		bm.to_mesh(temp_mesh)
		bm.free()

		obj = curve_objs[0]
		new_obj = bpy.data.objects.new(filter_name(obj, "_Flanges"), temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc
		new_obj.data.use_auto_smooth = True

		bpy.context.scene.collection.objects.link(new_obj)

		copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
		assign_mat(self, obj, new_obj, self.mat_index)

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
			row.label(text="Size:")
			split = row.split(factor=0.5, align=True)
			split.row(align=True).prop(self, "radius")
			split.row(align=True).prop(self, "depth")
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

		prefs = context.preferences.addons[__name__].preferences
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
		precision   = 4
		)
	offset : FloatProperty(
		name        = "Offset",
		description = "Offset generated screws",
		default     = 0,
		step        = 0.1,
		precision   = 4
		)
	mode : EnumProperty(
		name = 'Mode',
		items = (
			('ANGLE', 'Angle','Screws are generated based on max angle threshold of corner verts'),
			('VERTS', 'All Verts','Screws are generated for each verts')),
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
		default     = 0.25,
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

		bm_temp = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")

		type = self.mesh_type
		save_mode = obj.mode

		if type == 'BASIC':
			listv = bmesh.ops.create_cone(
				bm_temp,
				cap_ends    = True,
				segments    = self.segment,
				radius1     = self.radius,
				radius2     = self.radius,
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

		if type == 'MESH':
			mesh = bpy.data.objects.get(self.mesh_name)
			if mesh: bm_temp.from_mesh(mesh.data)

		if type == 'CUSTOM':
			if self.import_name:
				file_name = self.import_name
				custom_data = bpy.data.meshes.get(file_name + "_rflow_mesh", None)
				if not custom_data:
					if file_name.find(".stl") == -1: file_name += ".stl"
					filepath = os.path.join(os.path.dirname(
						os.path.abspath(__file__)), "./screws/" + file_name)
					bpy.ops.import_mesh.stl(filepath=filepath, global_scale=1.0)

					import_obj = context.selected_objects[0]
					custom_data = import_obj.data
					custom_data.name += "_rflow_mesh"

					obj.select_set(True)
					context.view_layer.objects.active = obj
					bpy.ops.object.mode_set(mode=save_mode)

					bpy.data.objects.remove(import_obj)

				if custom_data:
					bm_temp.from_mesh(custom_data)

		if type == 'COLLECTION':
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

		if type != 'BASIC':
			bmesh.ops.scale(
				bm_temp,
				vec     = Vector(tuple([self.radius] * 3)),
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

		if not self.use_mirror:
			orig_mesh = get_eval_mesh(obj)
		else:
			orig_mesh = obj.data

		bm = bmesh.new()
		temp_mesh = bpy.data.meshes.new(".temp")
		bm.from_mesh(orig_mesh)

		face_sel = [f for f in bm.faces if not f.select]
		bmesh.ops.delete(bm, geom=face_sel, context='FACES')

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

		vgroup = "tagged_verts"
		vg = obj.vertex_groups.get(vgroup)
		if vg: deform_layer = bm.verts.layers.deform.active or bm.verts.layers.deform.new()

		tagged_only = self.tagged_only and vg

		if self.mode == 'VERTS':
			for e in bm.edges:
				tagged = len([v for v in e.verts if vg.index in v[deform_layer]]) == len(edge.verts) \
					if tagged_only else True
				if e.is_boundary and tagged:
					length_e = e.calc_length()
					segments = length_e / max(0.001, self.spacing)
					cut_x_times = int(floor(segments - (segments / 2 )))
					bmesh.ops.subdivide_edges(bm, edges=[e], cuts=cut_x_times)

		origin_faces = bm.faces[:]

		if tagged_only:
			origin_verts = [v for v in bm.verts if vg.index in v[deform_layer]]
		else: origin_verts = bm.verts

		for i, v in enumerate(origin_verts):
			if v.is_boundary:
				proc = False
				if self.mode == 'ANGLE':
					angle = v.calc_edge_angle(None)
					if angle and angle > self.threshold: proc = True
				else: proc = True

				seed(self.birth_seed + i)
				if random() > self.birth_perc/100: proc = False

				if proc:
					normal = sum([f.normal for f in v.link_faces], Vector()) / len(v.link_faces)
					self.add_screw(context, obj, bm, v.co, normal, i)

		bmesh.ops.delete(bm, geom=origin_faces, context='FACES')

		bm.to_mesh(temp_mesh)
		bm.free()

		new_obj = bpy.data.objects.new(filter_name(obj, "_Screws"), temp_mesh)
		orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
		new_obj.scale = orig_scale
		new_obj.rotation_euler = orig_rot.to_euler()
		new_obj.location = orig_loc
		new_obj.data.use_auto_smooth = True

		context.scene.collection.objects.link(new_obj)

		if self.use_mirror: copy_modifiers([obj, new_obj], mod_types=['MIRROR'])
		assign_mat(self, obj, new_obj, self.mat_index)

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
		row.label(text="Mode:")
		row.row(align=True).prop(self, "mode", expand=True)
		if self.mode == 'ANGLE':
			row = col.row().split(factor=0.27, align=True)
			row.label(text="Threshold:")
			row.row(align=True).prop(self, "threshold", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Radius:")
		row.row(align=True).prop(self, "radius", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Position:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "margin")
		split.row(align=True).prop(self, "offset")
		if self.mode == 'VERTS':
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
		flow.prop(self, "use_split")
		flow.prop(self, "tagged_only")
		flow.prop(self, "per_face")
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

		if has_face:
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

			prefs = context.preferences.addons[__name__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

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
	indiv_effect : BoolProperty(
		name        = "Individual Seed",
		description = "Individual random effects for separate face islands",
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
	use_mirror : BoolProperty(
		name        = "Use Mirror",
		description = "Use mirror modifier from source mesh",
		default     = True
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
		mass = uniform(self.mass_min, self.mass_max)
		up_force = uniform(self.up_force_min, self.up_force_max)
		shrink_min = uniform(self.shrink_min_min, self.shrink_min_max)
		gravity = uniform(self.gravity_min, self.gravity_max)

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

		if not self.use_mirror:
			self.set_modifier_vis(obj, hide=True)
			orig_mesh = get_eval_mesh(obj)
		else:
			orig_mesh = obj.data

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

		if self.split_mode != 'NONE':
			bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if (e.seam if self.split_mode == 'SEAM' else \
				e.calc_face_angle(None) and e.calc_face_angle(None) >= self.cut_threshold)])

		if self.margin > 0:
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

		if self.remove_sel:
			fcount = self.remove_selected_faces(obj)
			if fcount == 0:
				remove_obj(obj, clear_data=False)
				keep_obj = False

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
			context.scene.collection.objects.link(new_obj)
			select_isolate(new_obj)
			self.assign_pin_group(new_obj)
			self.add_cloth_effect(new_obj, rs=self.rand_seed)
			if keep_obj: select_isolate(obj)

		if collision_list:
			for o in collision_list:
				cm = o.modifiers.get("Collision_pcloth")
				if cm: o.modifiers.remove(cm)

		if not self.use_mirror and keep_obj: self.set_modifier_vis(obj, hide=False)

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
		flow.prop(self, "smooth_shade")
		flow.prop(self, "remove_sel")
		flow.prop(self, "indiv_effect")
		flow.prop(self, "obj_collisions")
		if self.obj_collisions: flow.prop(self, "collide_source")
		flow.prop(self, "collision_self")
		flow.prop(self, "pin_cloth")
		col.prop(self, "keep_corners")
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

		if has_face > 0:
			init_props(self, event, ops='pcloth', force=has_face>=props.fselect_limit)
			prefs = context.preferences.addons[__name__].preferences
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
		min         =  0.0001,
		soft_max    = 2.0,
		step        = 0.1,
		precision   = 4
		)
	adj_mode : EnumProperty(
		name = 'Adjacent Faces',
		items = (
			('CLEAR', 'Clear',''),
			('FILL', 'Fill','')),
		default = 'CLEAR'
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
	pl_height_min : FloatProperty(
		name        = "Min",
		description = "Additional minimum inset depth value for faces",
		default     = 0.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	pl_height_max : FloatProperty(
		name        = "Max",
		description = "Additional maximum inset depth value for faces",
		default     = 0.0,
		soft_min    = -10.0,
		soft_max    = 10.0,
		step        = 0.1,
		precision   = 3
		)
	depth_seed : IntProperty(
		name        = "Seed",
		description = "Depth random seed",
		default     = 1,
		min         = 1,
		soft_max    = 10000,
		step        = 1
		)
	margin_type : EnumProperty(
		name = 'Margin Type',
		items = (
			('ALL', 'All',''),
			('INDENT', 'Indent Only','')),
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

		limit_smooth = self.limit_smooth != 'NONE'
		use_mirror = self.use_mirror
		mirror_vec = Vector()

		mesh = obj.data
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
				use_even_offset=True, thickness=self.pl_margin_outer)['faces']
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
			r_depth = self.pl_depth + uniform(self.pl_height_min, self.pl_height_max)

			if self.rev_depth:
				seed(self.rev_seed + seed_counter)
				r_depth = r_depth if int(ceil(random() * 100)) > self.rev_depth else -r_depth

			margin_inner = []
			if self.pl_margin_inner:
				if (r_depth < 0 and self.margin_type == 'INDENT') \
					or self.margin_type == 'ALL':
					margin_inner = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, \
						use_even_offset=True, thickness=self.pl_margin_inner)['faces']

			ret_inset = bmesh.ops.inset_region(bm, faces=inset_faces, use_boundary=True, \
				use_even_offset=True, thickness=self.pl_thick, depth=r_depth)['faces']

			if limit_smooth:
				inset_edges = set(sum([list(f.edges) for f in ret_inset], []))
				for e in inset_edges:
					e.smooth = True; e.seam = False
					limit_area = r_depth < 0 if self.limit_smooth == 'BASE' else r_depth > 0
					if limit_area:
						if len([lf for lf in e.link_faces if lf in inset_faces]) == 1: e.smooth = False
					else:
						if len([lf for lf in e.link_faces if lf in ret_inset]) == 1 \
							and len([lf for lf in e.link_faces if lf in inset_faces]) == 0: e.smooth = False

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

		bmesh.ops.remove_doubles(bm_src, verts=bm_src.verts, dist=1e-4)
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
		row.label(text="Thickness:")
		row.row(align=True).prop(self, "pl_thick", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Depth:")
		row.row(align=True).prop(self, "pl_depth", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height:")
		split = row.split(factor=0.5, align=True)
		split.row(align=True).prop(self, "pl_height_min")
		split.row(align=True).prop(self, "pl_height_max")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Height Seed:")
		row.row(align=True).prop(self, "depth_seed", text="")
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin Type:")
		row.row(align=True).prop(self, "margin_type", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Margin:")
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
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Plating Seed:")
		row.row(align=True).prop(self, "pl_seed", text="")
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

		self.pl_seed = 0
		self.depth_seed = 0
		self.rev_seed = 0

		if event.alt: get_linked_flat_faces(obj)

		obj.update_from_editmode()
		has_face = count_selected_faces(obj)

		if has_face > 0:
			init_props(self, event, ops='p_insets', force=has_face>=props.fselect_limit)
			self.has_mirror = next((m for m in obj.modifiers if m.type == 'MIRROR'), None)
			prefs = context.preferences.addons[__name__].preferences
			if prefs.use_confirm:
				return context.window_manager.invoke_props_dialog(self)
			else:
				return context.window_manager.invoke_props_popup(self, event)
		else:
			self.report({'WARNING'}, "No faces selected.")
			return {"FINISHED"}

class OBJECT_OT_quick_displacement(Operator):
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

		init_props(self, event, ops='ndispl', force=len(obj.data.polygons)>=props.fselect_limit)
		prefs = context.preferences.addons[__name__].preferences
		if prefs.use_confirm:
			return context.window_manager.invoke_props_dialog(self)
		else:
			return context.window_manager.invoke_props_popup(self, event)

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
		kd = mathutils.kdtree.KDTree(size)

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
	'''Apply modifiers/convert objects'''
	bl_idname = 'apply_mesh.rflow'
	bl_label = 'Apply Mesh'
	bl_options = {'REGISTER', 'UNDO'}

	only_mirror : BoolProperty(
		name        = "Apply Mirror Only",
		description = "Apply only mirror modifiers",
		default     = False
		)

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

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, "only_mirror")

	def invoke(self, context, event):
		self.only_mirror = False

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
						new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
						new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle
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

			point = []
			axis = ['X','Y','Z'].index(self.axis)
			if self.origin == 'AXIS':
				verts = sorted(bm.verts, key=lambda v: (mat @ v.co)[axis])
				pos = (verts[-1 if self.location == 'POSITIVE' else 0].co)[axis]
				point = [mat @ v.co for v in verts if abs((v.co)[axis] - pos) < self.tolerance]
			else:
				point = [mat @ v.co for v in bm.verts if v.select]
				if not point:
					self.report({'WARNING'}, "No verts selected.")

			bm.to_mesh(mesh)
			bm.free()

			if point:
				new_origin = sum(point, Vector()) / len(point)
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

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self)

class OBJECT_OT_merge_objs(Operator):
	'''Merge selected meshes to an object'''
	bl_idname = 'merge_objs.rflow'
	bl_label = 'Merge Objects'
	bl_options = {'REGISTER', 'UNDO'}

	opr_type : EnumProperty(
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
	offset : FloatProperty(
		name        = "Offset Target",
		description = "Offset merge to object by this amount to fix overlap",
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

	def offset_mesh(self, obj):

		mesh = obj.data

		bm = bmesh.new()
		bm.from_mesh(mesh)

		for v in bm.verts:
			v.co += v.normal * (v.calc_shell_factor() * self.offset)

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
		if self.opr_type == 'OBJ':
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

			if self.offset > 0:
				self.offset_mesh(merge_obj)

			if self.opr_type == 'COLL':
				split_objs = []
				for obj in bool_objs:
					if obj.type == 'MESH':
						obj.data.materials.clear()
						obj.data = get_eval_mesh(obj).copy()
						obj.modifiers.clear()

						mesh = obj.data
						lparts = get_islands(obj, None)

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
									new_obj = bpy.data.objects.new(obj.name, temp_mesh)
									orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
									new_obj.scale = orig_scale
									new_obj.rotation_euler = orig_rot.to_euler()
									new_obj.location = orig_loc
									new_obj.data.use_auto_smooth = obj.data.use_auto_smooth
									new_obj.data.auto_smooth_angle = obj.data.auto_smooth_angle
									bpy.context.scene.collection.objects.link(new_obj)

									self.group_obj(new_obj, coll_name)
									split_objs.append(new_obj)
						else:
							new_obj = obj
							self.group_obj(new_obj, coll_name)

				coll = bpy.data.collections.get(coll_name)
				if coll and coll.objects:
					bool_objs += split_objs
					self.add_boolean(obj1=merge_obj, grp=coll_name)
					self.apply_mesh(merge_obj)
			else:
				for obj in bool_objs:
					if obj.type == 'MESH':
						mesh = obj.data
						bm = bmesh.new()
						bm.from_mesh(mesh)

						if self.fill_holes:
							e = [e for e in bm.edges if e.is_boundary]
							bmesh.ops.holes_fill(bm, edges=e)

						bm.to_mesh(mesh)
						bm.free()

						self.add_boolean(obj1=merge_obj, obj2=obj)

				self.apply_mesh(merge_obj)

			for o in bool_objs: remove_obj(o)

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Operand Type:")
		row.row(align=True).prop(self, "opr_type", expand=True)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Merge To:")
		row.prop_search(
			self,
			"list",
			self,
			"meshes",
			text="",
			icon = "MESH_DATA"
			)
		row = col.row().split(factor=0.27, align=True)
		row.label(text="Offset Target:")
		row.row(align=True).prop(self, "offset", text="")
		col.separator(factor=0.5)
		flow = col.column_flow(columns=2, align=True)
		if self.opr_type == 'OBJ':
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

class MESH_OT_auto_smooth(Operator):
	'''Smooth shade active object and use auto-smooth'''
	bl_idname = 'auto_smooth.rflow'
	bl_label = 'Shade Smooth'
	bl_options = {'REGISTER', 'UNDO'}

	angle : FloatProperty(
		name        = "Angle",
		description = "Maximum angle between face normals that will be considered as smooth",
		default     = radians(30),
		min         = 0,
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)
	use_auto_smooth : BoolProperty(
		name        = "Auto Smooth",
		description = "Enable automatic smooth based on smooth/sharp faces/edges and angle between faces",
		default     = True
		)
	clear_cnormals : BoolProperty(
		name        = "Clear Custom Split Normals Data",
		description = "Remove the custom split normals layer, if it exists",
		default     = False
		)

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.type == 'MESH'

	def execute(self, context):
		objs = context.selected_objects

		for o in objs:
			context.view_layer.objects.active = o
			mesh = o.data
			auto_smooth(o, self.angle, self.use_auto_smooth)
			o.update_from_editmode()

			if self.clear_cnormals and mesh.has_custom_normals:
				bpy.ops.mesh.customdata_custom_splitnormals_clear()

			mesh.update()

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, "angle")
		col.separator()
		col.prop(self, "use_auto_smooth")
		col.prop(self, "clear_cnormals")

	def invoke(self, context, event):
		self.use_auto_smooth = True
		self.clear_cnormals = False

		return self.execute(context)

class MESH_OT_sort_elem(Operator):
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
	'''Assign vertices to vertex group for use in Quad Slice'''
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
			('LINKED', 'Linked Faces','Cut linked faces'),
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
		name        = "Use Tagged Verts",
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
		listdir.sort(reverse=True)

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

	def get_corner_verts(self, verts):

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

				singles = self.get_corner_verts(bm.verts)
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
	bl_label = 'Save/Use/Clear Mesh Data'
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

	def get_similarity(self, orig, comp_mesh):

		orig.update_from_editmode()
		mesh1 = orig.data
		p1 = np.empty((len(mesh1.vertices), 3), 'f')
		mesh1.vertices.foreach_get("co", np.reshape(p1, len(mesh1.vertices) * 3))

		mesh2 = comp_mesh
		p2 = np.empty((len(mesh2.vertices), 3), 'f')
		mesh2.vertices.foreach_get("co", np.reshape(p2, len(mesh2.vertices) * 3))

		p1 = list(map(tuple, p1))
		p2 = list(map(tuple, p2))

		similarity = len((set(p2).intersection(set(p1))))/len(p2) * 100

		return similarity

	def execute(self, context):
		obj = context.active_object
		suffix = self.suffix

		mesh = obj.data

		if self.mode == 'SAVE':
			if obj: obj.select_set(True)
			for o in context.selected_objects:
				o.update_from_editmode()
				mesh_data = get_eval_mesh(obj).copy()
				if mesh_data.name.find(suffix) == -1:
					mesh_data.name += suffix
				mesh_data.use_fake_user = True
				self.report({'INFO'}, "Mesh data saved.")

		if self.mode == "USE":
			if self.list:
				save_mesh = bpy.data.meshes.get(self.list)
				if save_mesh: self.use_save_data(mesh, save_mesh)

		if self.mode == 'CLEAR':
			rem_count = 0
			for m in bpy.data.meshes:
				if m.name.find(suffix) != -1 \
					and m.use_fake_user:
					m.use_fake_user = False
					if m.users < 1:
						rem_count += 1
						bpy.data.meshes.remove(m)

			self.report({'INFO'}, str(rem_count) + " saved mesh data removed.")

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
		self.list = ""
		self.meshes.clear()
		self.suffix = suffix = "_save_data"
		self.same_info = ""

		if self.mode == 'USE':
			saved_meshes = { m: self.get_similarity(context.active_object, m) \
				for m in bpy.data.meshes if m.name.find(suffix) != -1 and m.use_fake_user }
			sorted_meshes = sorted(saved_meshes.items(), key=lambda item: item[1])
			same = 0
			for m in reversed(sorted_meshes):
				newListItem = self.meshes.add()
				newListItem.name = m[0].name
				if m[1] > 0: same += 1

			self.same_info = "Found " + str(same) + " matching geometry."

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
		col.label(text=margin + "Go back to object mode to use random operators.")
		col.label(text=margin + "Faces needs to be quads or tris for subdivision to work.")
		col.separator(factor=0.5)
		col.label(text=margin + "Press F9 to bring back redo panel when it disappears.")
		col.label(text=margin + "Performing some commands will finalize last action and scrub the redo panel from history.")
		col.label(text=margin + "In user preferences of the add-on, you can use the confirm type redo panels instead.")
		col.separator(factor=0.5)
		col.label(text="Limitations:", icon="ERROR")
		col.label(text=margin + "Be careful with using higher resolution face selections.")
		col.label(text=margin + "(Most operations run recursively)")
		col.label(text=margin + "(It can run out of memory and take a long time to compute)")

	def invoke(self, context, event):

		return context.window_manager.invoke_props_dialog(self, width=500)

class UI_MT_random_flow(Menu):
	bl_label = "Random Flow"
	bl_idname = "UI_MT_random_flow"

	def draw(self, context):
		obj = context.active_object
		prefs = context.preferences.addons[__name__].preferences

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("rand_loop_extr.rflow", icon="ORIENTATION_NORMAL")
		layout.operator("rand_panels.rflow", icon="MESH_GRID")
		layout.operator("rand_axis_extr.rflow", icon="SORTBYEXT")
		layout.operator("rand_cells.rflow", icon="MOD_MASK")
		layout.operator("rand_scatter.rflow", icon="OUTLINER_OB_POINTCLOUD")
		layout.operator("rand_tubes.rflow", icon="IPO_CONSTANT")
		layout.operator("rand_cables.rflow", icon="FORCE_CURVE")
		if obj \
			and obj.type == 'MESH' \
			and not obj.data.is_editmode:
			layout.operator("rand_vcol.rflow", icon="COLORSET_10_VEC")
		layout.operator("rand_anim.rflow", icon="RENDER_ANIMATION")
		layout.separator()
		layout.menu("UI_MT_rflow_utility")
		layout.separator()
		layout.operator("n_picker.rflow", icon='SNAP_NORMAL')
		layout.separator()
		if obj \
			and obj.type == 'MESH':
			if not obj.data.is_editmode:
				layout.operator("img_browser.rflow", icon='FILE_FOLDER')
				layout.separator()
			else:
				layout.operator("tag_verts.rflow", icon="VERTEXSEL")
				layout.separator()
		layout.menu("UI_MT_rflow_mesh")
		layout.menu("UI_MT_rflow_data")
		layout.separator()
		layout.menu("UI_MT_rflow_extras")
		layout.menu("UI_MT_rflow_settings")
		if prefs.show_helper:
			layout.separator()
			layout.operator("use_info.rflow", text="Usage Info", icon="INFO")

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

class UI_MT_rflow_mesh(Menu):
	bl_label = "Mesh"
	bl_idname = "UI_MT_rflow_mesh"

	def draw(self, context):
		obj = context.active_object

		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("auto_smooth.rflow", text="Auto Smooth", icon="NORMALS_VERTEX_FACE")
		if obj \
			and obj.type == 'MESH' \
			and obj.data.is_editmode:
			layout.operator("sort_elem.rflow", icon="SORTBYEXT")
			layout.operator("grid_project.rflow", icon="MESH_GRID")
			layout.operator("quad_slice.rflow", icon="GRID")
		if obj \
			and obj.type in { 'MESH', 'CURVE' } \
			and not obj.data.is_editmode:
			layout.operator("auto_mirror.rflow", icon="MOD_MIRROR")
			layout.operator("extr_proxy.rflow", icon="FACESEL")
			layout.operator("apply_mesh.rflow", icon="IMPORT")

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
		sce = context.scene
		rf_props = sce.rflow_props

		layout = self.layout
		layout.prop(rf_props, "all_mods")
		layout.separator()
		layout.prop(rf_props, "fselect_limit")
		layout.prop(rf_props, "link_angle")

class UI_PT_rflow_addon_pref(AddonPreferences):
	bl_idname = __name__

	font_size : IntProperty(
		description = "Helper font size when using modal operations",
		name        = "Helper Font Size",
		default     = 60,
		min         = 1,
		max         = 1000,
		step        = 1
		)
	use_confirm : BoolProperty(
		default     = False,
		name        = "Use confirm menu for random operators",
		description = "Use confirm type adjust last action menu for random operators."
		)
	show_helper : BoolProperty(
		default     = True,
		name        = "Show Usage Info button",
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

	addon_prefs = bpy.context.preferences.addons[__name__].preferences

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

	select_influence : FloatProperty(
		description = "Select influence value for Extract Proxy",
		name        = "Select Influence",
		default     = 1.0,
		min         = 0,
		max         = 1.0
		)
	fselect_limit : IntProperty(
		name        = "Face Select Limit",
		description = "Number of faces selected before resetting subdivision cuts",
		default     = 50,
		min         = 0,
		soft_max    = 10000,
		step        = 1
		)
	all_mods : BoolProperty(
		default     = False,
		name        = "Copy All Modifiers",
		description = "Copy all modifiers from source object to random objects"
		)
	normal_guide : FloatVectorProperty(
		subtype     = 'TRANSLATION',
		description = "Normal guide for random animation mesh rotation"
		)
	link_angle : FloatProperty(
		name        = "Linked Select Sharpness",
		description = "Select flat linked faces sharpness limit",
		default     = radians(15),
		min         = radians(1),
		max         = radians(180),
		step        = 10,
		precision   = 3,
		subtype     = "ANGLE"
		)

classes = (
	OBJECT_OT_r_loop_extrude,
	OBJECT_OT_r_panels,
	OBJECT_OT_r_axis_extrude,
	OBJECT_OT_r_cells,
	OBJECT_OT_r_scatter,
	OBJECT_OT_r_tubes,
	OBJECT_OT_r_cables,
	OBJECT_OT_r_vertex_color,
	OBJECT_OT_r_animation,
	OBJECT_OT_normal_picker,
	OBJECT_OT_make_flanges,
	OBJECT_OT_panel_screws,
	OBJECT_OT_panel_cloth,
	OBJECT_OT_plate_insets,
	OBJECT_OT_quick_displacement,
	FILES_OT_image_browser,
	OBJECT_OT_auto_mirror,
	OBJECT_OT_extract_proxy,
	OBJECT_OT_apply_mesh,
	OBJECT_OT_join_objs,
	OBJECT_OT_split_mesh,
	OBJECT_OT_set_origin,
	OBJECT_OT_merge_objs,
	MESH_OT_auto_smooth,
	MESH_OT_sort_elem,
	MESH_OT_tag_verts,
	MESH_OT_quad_slice,
	MESH_OT_grid_project,
	MESH_OT_clean_up,
	MESH_OT_save_data,
	MESH_OT_use_info,
	UI_MT_random_flow,
	UI_MT_rflow_utility,
	UI_MT_rflow_mesh,
	UI_MT_rflow_data,
	UI_MT_rflow_extras,
	UI_MT_rflow_settings,
	UI_PT_rflow_addon_pref,
	USERPREF_OT_change_hotkey,
	RFlow_Props,
	)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.rflow_props = PointerProperty(
		type        = RFlow_Props,
		name        = "Random Flow Properties",
		description = ""
		)

	add_hotkey()

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	del bpy.types.Scene.rflow_props

	remove_hotkey()

if __name__ == '__main__':
	register()
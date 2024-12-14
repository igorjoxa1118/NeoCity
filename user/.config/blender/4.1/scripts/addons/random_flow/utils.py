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
import blf
import gpu
from gpu_extras.batch import batch_for_shader
import numpy as np
from random import random, randint, sample, uniform, choice, choices, seed, shuffle, triangular
import bmesh
from math import *
from mathutils import *
from bpy_extras import view3d_utils
from addon_utils import check as mod_check, paths as mod_paths

from .preferences import *

def get_eval_mesh(obj):

	depsgraph = bpy.context.evaluated_depsgraph_get()
	obj_eval = obj.evaluated_get(depsgraph)
	mesh_from_eval = obj_eval.to_mesh()

	return mesh_from_eval

def set_sharp(obj1, obj2):

	mesh = get_eval_mesh(obj1).copy()

	if "sharp_edge" in mesh.attributes:
		obj2.data.set_sharp_from_angle(angle=radians(30))
		obj2.data.update()

	bpy.data.meshes.remove(mesh)

def mesh_smooth(bm, verts=[], smooth=0, iter=1):

	for i in range(0, iter):
		bmesh.ops.smooth_vert(bm, verts=verts, factor=smooth, \
			mirror_clip_x=True, mirror_clip_y=True, mirror_clip_z=True, \
			use_axis_x=True, use_axis_y=True, use_axis_z=True)

def check_sharp_edges(mesh):

	edges = np.zeros(len(mesh.edges), dtype=bool)
	mesh.edges.foreach_get('use_edge_sharp', edges)

	return True in edges

def check_center(mirror=[], co=Vector(), thresh=1e-4):

	is_center = False

	for i in range(0, 3):
		if mirror[i]:
			if -thresh <= co[i] <= thresh:
				is_center = True
				break

	return is_center

def create_temp_obj(name):

	data = bpy.data.meshes.new(name)
	obj = bpy.data.objects.new(name, data)

	return obj

def reset_data(obj, data2):

	meshes = bpy.data.meshes

	old_data = obj.data
	obj.data = data2

	if old_data.name in meshes \
		and old_data.users == 0: meshes.remove(old_data)

def set_parent(parent, child):

	for col in parent.users_collection:
		if not child.name in col.objects: col.objects.link(child)

	if bpy.context.scene.rflow_props.parent_result:
		if parent.name.find("PMesh") != -1:
			if parent.parent:
				parent = parent.parent

		child.parent = parent
		child.matrix_parent_inverse = parent.matrix_world.inverted()

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

def guided_rot(obj, track="Z", normal=Vector()):

	quat = normal.to_track_quat(track, 'Y')
	mat = obj.matrix_world.inverted() @ quat.to_matrix().to_4x4()
	rot = mat.to_3x3().normalized()

	return rot

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

	vname = "inset_faces"

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
	path='NONE', cut_threshold=radians(30), wrap_angle=True, mark_sharp=False, mark_seam=False):

	split_edg = []
	cells = []
	counter = 0
	notch_list = set()

	bm.faces.ensure_lookup_table()

	def face_loop_select(face, start_loop, limit):

		face_loops = { face }
		limit = max(int(ceil(limit * 0.5)), 1)

		for i in range(limit):
			next_loop = start_loop.link_loop_next.link_loop_radial_next.link_loop_next

			if len(next_loop.face.edges) > 4: break

			start_loop = next_loop
			face_loops.add(next_loop.face)

		return face_loops

	while idx:
		seed(snum + counter)
		x = choice(list(idx))
		idx.remove(x)

		init_f = bm.faces[x]
		face_cell = [init_f]
		edge_cell = init_f.edges[:]
		start_verts = init_f.verts[:]

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
			if sampling == 'WALK':
				link_edges = { e: e.calc_length() for e in init_f.edges }
				edges = list(link_edges.keys()); lenghts = list(link_edges.values())
				for n, e in enumerate(sample(edges, len(edges))):
					length = max(lenghts) if path == 'LONGEST' \
						else min(lenghts) if path == 'SHORTEST' else 0
					if e.calc_length() != length or \
						n + 1 == len(edges):
						init_f = next((i for i in e.link_faces if i.index in idx), None)
						if init_f:
							add_cells(init_f)
							walk += 1
							break
				else:
					list_copy = edge_cell.copy()
					while list_copy:
						sample_edge = choice(list_copy)
						list_copy.remove(sample_edge)
						init_f = next((i for i in sample_edge.link_faces if i.index in idx), None)
						if init_f:
							add_cells(init_f)
							walk += 1
							break
					else: break
			elif sampling in ['RADIAL', 'SQUARE']:
				if sampling == 'RADIAL' \
					or len(init_f.edges) == 3:
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
				else:
					start_loop1 = choice(init_f.loops)
					start_loop2 = None

					size1 = randint(min_size, max_size)
					face_loops = face_loop_select(init_f, start_loop1, size1)

					for v in start_loop1.edge.verts:
						for e in v.link_edges:
							if init_f in e.link_faces \
								and e != start_loop1.edge:
								start_loop2 = choice([i for i in init_f.loops if i.edge == e])
								break

					if start_loop2:
						size2 = randint(min_size, max_size)
						face_loops.update(face_loop_select(init_f, start_loop2, size2))

						list_f = list(face_loops)
						while True:
							cc = False
							while list_f:
								f = list_f.pop()
								for v in f.verts:
									count_f = len([x for x in v.link_faces if x in face_loops])
									if (count_f == 3 if len(v.link_faces) == 4 else count_f >= 4):
										for lf in v.link_faces:
											if not lf in face_loops:
												list_f.append(lf); face_loops.add(lf)
												cc = True

							if cc == False: break

					for f in face_loops:
						if f.index in idx:
							add_cells(f)

					break

		if notch_count > 0 and len(face_cell) > 1:
			size_count = 0
			stop_count = 0

			seed(notch_snum + counter)
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
					if mark_seam: e.seam = True
					if mark_sharp: e.smooth = False
					split_edg.append(e)

		cells.append(face_cell)

		counter += 1

	return split_edg, cells

def get_tri_faces(faces=[], amt=0, seed_val=0, mode='PERCENT'):

	seed(seed_val)
	flist = sample(list(faces), len(faces))
	tri = int(len(flist) * (amt/100)) if mode == 'PERCENT' else min(amt, len(flist))

	tri_faces = []
	for f in flist[:tri]:
		if not any(e for e in f.edges if e.calc_face_angle(None) \
			and e.calc_face_angle(None) > radians(30)): tri_faces.append(f)

	return tri_faces

def get_linked_faces(faces, angle_limit=False, use_local=False, local_angle=radians(15)):

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
								link_angle = props.link_angle if not use_local else local_angle
								if angle < link_angle:
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
	props = sce.rflow_props

	orig_obj = objs[0]
	selected_objects = [o for o in objs if o != orig_obj]

	if props.all_mods: mod_types.clear()

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
		prefs = bpy.context.preferences.addons[__package__].preferences

		mx = self.mouse_co[0]
		my = self.mouse_co[1]

		font_id = 1
		if bpy.app.version < (4,0,0):
			blf.size(font_id, int(round(15 * bpy.context.preferences.view.ui_scale, 0)), prefs.font_size)
		else:
			blf.size(font_id, int(round(prefs.font_size_1 * bpy.context.preferences.view.ui_scale, 0)))

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
				if bpy.app.version < (4,0,0):
					shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
				else:
					shader = gpu.shader.from_builtin('UNIFORM_COLOR')
			else:
				if bpy.app.version < (4,0,0):
					shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
				else:
					shader = gpu.shader.from_builtin('UNIFORM_COLOR')

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
    
def get_similarity(comp_mesh, comp_data, mat1=Matrix(), mat2=Matrix(), use_matrix=False):

	comp_mesh.update_from_editmode()

	mesh1 = comp_mesh.data
	p1 = np.empty((len(mesh1.vertices), 3), 'f')
	mesh1.vertices.foreach_get("co", np.reshape(p1, len(mesh1.vertices) * 3))

	mesh2 = comp_data
	p2 = np.empty((len(mesh2.vertices), 3), 'f')
	mesh2.vertices.foreach_get("co", np.reshape(p2, len(mesh2.vertices) * 3))

	p1 = list(map(tuple, p1))
	p2 = list(map(tuple, p2))

	if use_matrix:
		p1 = [tuple(mat1 @ Vector(i)) for i in p1]
		p2 = [tuple(mat2 @ Vector(i)) for i in p2]

	return len((set(p2).intersection(set(p1))))/len(p2) * 100

def refresh_vcolor(obj):

	mesh = obj.data
	layer = "Vertex Color"

	if mesh.attributes.get(layer):
		mesh.attributes.active_color = mesh.attributes[layer]
	else:
		for i in mesh.attributes:
			if i.data_type.find("COLOR") != -1:
				mesh.attributes.active_color = i
				break

def set_floater_vis(obj, vis=False):

	try:
		cycles_vis = ['visible_diffuse', 'visible_glossy', \
			'visible_transmission', 'visible_volume_scatter', 'visible_shadow']
		for p in cycles_vis: setattr(obj, p, vis)
	except:
		self.report({'WARNING'}, "Cycles render engine not detected.")

def clear_select(obj):

	mesh = obj.data
	if mesh.is_editmode:
		bm = bmesh.from_edit_mesh(mesh)
	else:
		bm = bmesh.new()
		bm.from_mesh(mesh)

	geo = bm.verts[:] + bm.edges[:] + bm.faces[:]

	for p in geo:
		p.select = False

	bm.select_flush_mode()

	if mesh.is_editmode:
		bmesh.update_edit_mesh(mesh)
	else:
		bm.to_mesh(mesh)
		mesh.update()

def undupe(item):

	return list(dict.fromkeys(item))

def list_aux_addons():

	addon_list = []

	try:
		paths_list = mod_paths()
		for path in paths_list:
			for mod_name, mod_path in bpy.path.module_names(path):
				is_enabled, is_loaded = mod_check(mod_name)
				if is_enabled:
					addon_list.append(mod_name)
	except: pass

	return addon_list

def clean_directions(list_dir):

	lcopy = list_dir.copy()
	while lcopy:
		v1 = Vector(lcopy.pop())
		for v2 in lcopy:
			if round(degrees(v1.angle(v2, 0)), 4) in [0, 90, 180] \
				and v2 in list_dir: list_dir.remove(v2)

	return list_dir

def filter_name(obj, suffix=""):

	obj_name = obj.name
	list_idx = set()
	list_suffix = ["_RLExtr", "_RPanel", "_RAExtr", "_RCells", \
				"_RScatter", "_RPipes", "_Flanges", "_Screws", \
				"_PCloth", "_PMesh"]

	for i in list_suffix:
		idx = obj_name.find(i)
		if idx != -1: list_idx.add(idx)

	if list_idx:
		obj_name = obj_name[:min(list_idx)]

	return obj_name + suffix

def init_props(self, event, ops, force=False):

	if ops == 'rloop':
		if event.ctrl or force:
			self.loop_subdv = (0,0,0,0,0); self.cuts_base = 0;

	if ops == "rpanels":
		if event.ctrl or force:
			self.cuts_base = 0

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

	if ops == 'pcloth' or ops == 'ndispl':
		if event.ctrl or force:
			self.subd_lvl = 0; self.cuts_base = 0; self.cuts_smooth = 0.0;

	if ops == 'p_insets':
		if event.ctrl or force: self.cuts_base = 0
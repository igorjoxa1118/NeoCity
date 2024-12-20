/*
 * Adapted from code Copyright 2009-2010 NVIDIA Corporation,
 * and code copyright 2009-2012 Intel Corporation
 *
 * Modifications Copyright 2011-2014, Blender Foundation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* This is a template BVH traversal function for volumes, where
 * various features can be enabled/disabled. This way we can compile optimized
 * versions for each case without new features slowing things down.
 *
 * BVH_INSTANCING: object instancing
 * BVH_HAIR: hair curve rendering
 * BVH_MOTION: motion blur rendering
 *
 */

ccl_device uint BVH_FUNCTION_FULL_NAME(QBVH)(KernelGlobals *kg,
                                             const Ray *ray,
                                             Intersection *isect_array,
                                             const uint max_hits,
                                             const uint visibility)
{
	/* TODO(sergey):
	 * - Test if pushing distance on the stack helps.
	 * - Likely and unlikely for if() statements.
	 * - Test restrict attribute for pointers.
	 */

	/* Traversal stack in CUDA thread-local memory. */
	QBVHStackItem traversalStack[BVH_QSTACK_SIZE];
	traversalStack[0].addr = ENTRYPOINT_SENTINEL;

	/* Traversal variables in registers. */
	int stackPtr = 0;
	int nodeAddr = kernel_data.bvh.root;

	/* Ray parameters in registers. */
	const float tmax = ray->t;
	float3 P = ray->P;
	float3 dir = bvh_clamp_direction(ray->D);
	float3 idir = bvh_inverse_direction(dir);
	int object = OBJECT_NONE;
	float isect_t = tmax;

#if BVH_FEATURE(BVH_MOTION)
	Transform ob_itfm;
#endif

	uint num_hits = 0;
	isect_array->t = tmax;

#ifndef __KERNEL_SSE41__
	if(!isfinite(P.x)) {
		return false;
	}
#endif

#if BVH_FEATURE(BVH_INSTANCING)
	int num_hits_in_instance = 0;
#endif

	ssef tnear(0.0f), tfar(isect_t);
	sse3f idir4(ssef(idir.x), ssef(idir.y), ssef(idir.z));

#ifdef __KERNEL_AVX2__
	float3 P_idir = P*idir;
	sse3f P_idir4 = sse3f(P_idir.x, P_idir.y, P_idir.z);
#else
	sse3f org = sse3f(ssef(P.x), ssef(P.y), ssef(P.z));
#endif

	/* Offsets to select the side that becomes the lower or upper bound. */
	int near_x, near_y, near_z;
	int far_x, far_y, far_z;

	if(idir.x >= 0.0f) { near_x = 0; far_x = 1; } else { near_x = 1; far_x = 0; }
	if(idir.y >= 0.0f) { near_y = 2; far_y = 3; } else { near_y = 3; far_y = 2; }
	if(idir.z >= 0.0f) { near_z = 4; far_z = 5; } else { near_z = 5; far_z = 4; }

	IsectPrecalc isect_precalc;
	triangle_intersect_precalc(dir, &isect_precalc);

	/* Traversal loop. */
	do {
		do {
			/* Traverse internal nodes. */
			while(nodeAddr >= 0 && nodeAddr != ENTRYPOINT_SENTINEL) {
				ssef dist;
				int traverseChild = qbvh_node_intersect(kg,
				                                        tnear,
				                                        tfar,
#ifdef __KERNEL_AVX2__
				                                        P_idir4,
#else
				                                        org,
#endif
				                                        idir4,
				                                        near_x, near_y, near_z,
				                                        far_x, far_y, far_z,
				                                        nodeAddr,
				                                        &dist);

				if(traverseChild != 0) {
					float4 cnodes = kernel_tex_fetch(__bvh_nodes, nodeAddr*BVH_QNODE_SIZE+6);

					/* One child is hit, continue with that child. */
					int r = __bscf(traverseChild);
					if(traverseChild == 0) {
						nodeAddr = __float_as_int(cnodes[r]);
						continue;
					}

					/* Two children are hit, push far child, and continue with
					 * closer child.
					 */
					int c0 = __float_as_int(cnodes[r]);
					float d0 = ((float*)&dist)[r];
					r = __bscf(traverseChild);
					int c1 = __float_as_int(cnodes[r]);
					float d1 = ((float*)&dist)[r];
					if(traverseChild == 0) {
						if(d1 < d0) {
							nodeAddr = c1;
							++stackPtr;
							kernel_assert(stackPtr < BVH_QSTACK_SIZE);
							traversalStack[stackPtr].addr = c0;
							traversalStack[stackPtr].dist = d0;
							continue;
						}
						else {
							nodeAddr = c0;
							++stackPtr;
							kernel_assert(stackPtr < BVH_QSTACK_SIZE);
							traversalStack[stackPtr].addr = c1;
							traversalStack[stackPtr].dist = d1;
							continue;
						}
					}

					/* Here starts the slow path for 3 or 4 hit children. We push
					 * all nodes onto the stack to sort them there.
					 */
					++stackPtr;
					kernel_assert(stackPtr < BVH_QSTACK_SIZE);
					traversalStack[stackPtr].addr = c1;
					traversalStack[stackPtr].dist = d1;
					++stackPtr;
					kernel_assert(stackPtr < BVH_QSTACK_SIZE);
					traversalStack[stackPtr].addr = c0;
					traversalStack[stackPtr].dist = d0;

					/* Three children are hit, push all onto stack and sort 3
					 * stack items, continue with closest child.
					 */
					r = __bscf(traverseChild);
					int c2 = __float_as_int(cnodes[r]);
					float d2 = ((float*)&dist)[r];
					if(traverseChild == 0) {
						++stackPtr;
						kernel_assert(stackPtr < BVH_QSTACK_SIZE);
						traversalStack[stackPtr].addr = c2;
						traversalStack[stackPtr].dist = d2;
						qbvh_stack_sort(&traversalStack[stackPtr],
						                &traversalStack[stackPtr - 1],
						                &traversalStack[stackPtr - 2]);
						nodeAddr = traversalStack[stackPtr].addr;
						--stackPtr;
						continue;
					}

					/* Four children are hit, push all onto stack and sort 4
					 * stack items, continue with closest child.
					 */
					r = __bscf(traverseChild);
					int c3 = __float_as_int(cnodes[r]);
					float d3 = ((float*)&dist)[r];
					++stackPtr;
					kernel_assert(stackPtr < BVH_QSTACK_SIZE);
					traversalStack[stackPtr].addr = c3;
					traversalStack[stackPtr].dist = d3;
					++stackPtr;
					kernel_assert(stackPtr < BVH_QSTACK_SIZE);
					traversalStack[stackPtr].addr = c2;
					traversalStack[stackPtr].dist = d2;
					qbvh_stack_sort(&traversalStack[stackPtr],
					                &traversalStack[stackPtr - 1],
					                &traversalStack[stackPtr - 2],
					                &traversalStack[stackPtr - 3]);
				}

				nodeAddr = traversalStack[stackPtr].addr;
				--stackPtr;
			}

			/* If node is leaf, fetch triangle list. */
			if(nodeAddr < 0) {
				float4 leaf = kernel_tex_fetch(__bvh_leaf_nodes, (-nodeAddr-1)*BVH_QNODE_LEAF_SIZE);
				int primAddr = __float_as_int(leaf.x);

#if BVH_FEATURE(BVH_INSTANCING)
				if(primAddr >= 0) {
#endif
					int primAddr2 = __float_as_int(leaf.y);
					const uint type = __float_as_int(leaf.w);
					const uint p_type = type & PRIMITIVE_ALL;
					bool hit;

					/* Pop. */
					nodeAddr = traversalStack[stackPtr].addr;
					--stackPtr;

					/* Primitive intersection. */
					switch(p_type) {
						case PRIMITIVE_TRIANGLE: {
							for(; primAddr < primAddr2; primAddr++) {
								kernel_assert(kernel_tex_fetch(__prim_type, primAddr) == type);
								/* Only primitives from volume object. */
								uint tri_object = (object == OBJECT_NONE)? kernel_tex_fetch(__prim_object, primAddr): object;
								int object_flag = kernel_tex_fetch(__object_flag, tri_object);
								if((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
									continue;
								}
								/* Intersect ray against primitive. */
								hit = triangle_intersect(kg, &isect_precalc, isect_array, P, visibility, object, primAddr);
								if(hit) {
									/* Move on to next entry in intersections array. */
									isect_array++;
									num_hits++;
#if BVH_FEATURE(BVH_INSTANCING)
									num_hits_in_instance++;
#endif
									isect_array->t = isect_t;
									if(num_hits == max_hits) {
#if BVH_FEATURE(BVH_INSTANCING)
#if BVH_FEATURE(BVH_MOTION)
										float t_fac = 1.0f / len(transform_direction(&ob_itfm, dir));
#else
										Transform itfm = object_fetch_transform(kg, object, OBJECT_INVERSE_TRANSFORM);
										float t_fac = 1.0f / len(transform_direction(&itfm, dir));
#endif
										for(int i = 0; i < num_hits_in_instance; i++) {
											(isect_array-i-1)->t *= t_fac;
										}
#endif  /* BVH_FEATURE(BVH_INSTANCING) */
										return num_hits;
									}
								}
							}
							break;
						}
#if BVH_FEATURE(BVH_MOTION)
						case PRIMITIVE_MOTION_TRIANGLE: {
							for(; primAddr < primAddr2; primAddr++) {
								kernel_assert(kernel_tex_fetch(__prim_type, primAddr) == type);
								/* Only primitives from volume object. */
								uint tri_object = (object == OBJECT_NONE)? kernel_tex_fetch(__prim_object, primAddr): object;
								int object_flag = kernel_tex_fetch(__object_flag, tri_object);
								if((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
									continue;
								}
								/* Intersect ray against primitive. */
								hit = motion_triangle_intersect(kg, isect_array, P, dir, ray->time, visibility, object, primAddr);
								if(hit) {
									/* Move on to next entry in intersections array. */
									isect_array++;
									num_hits++;
#if BVH_FEATURE(BVH_INSTANCING)
									num_hits_in_instance++;
#endif
									isect_array->t = isect_t;
									if(num_hits == max_hits) {
#if BVH_FEATURE(BVH_INSTANCING)
#  if BVH_FEATURE(BVH_MOTION)
										float t_fac = 1.0f / len(transform_direction(&ob_itfm, dir));
#  else
										Transform itfm = object_fetch_transform(kg, object, OBJECT_INVERSE_TRANSFORM);
										float t_fac = 1.0f / len(transform_direction(&itfm, dir));
#endif
										for(int i = 0; i < num_hits_in_instance; i++) {
											(isect_array-i-1)->t *= t_fac;
										}
#endif  /* BVH_FEATURE(BVH_INSTANCING) */
										return num_hits;
									}
								}
							}
							break;
						}
#endif
#if BVH_FEATURE(BVH_HAIR)
						case PRIMITIVE_CURVE:
						case PRIMITIVE_MOTION_CURVE: {
							for(; primAddr < primAddr2; primAddr++) {
								kernel_assert(kernel_tex_fetch(__prim_type, primAddr) == type);
								/* Only primitives from volume object. */
								uint tri_object = (object == OBJECT_NONE)? kernel_tex_fetch(__prim_object, primAddr): object;
								int object_flag = kernel_tex_fetch(__object_flag, tri_object);
								if((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
									continue;
								}
								/* Intersect ray against primitive. */
								if(kernel_data.curve.curveflags & CURVE_KN_INTERPOLATE)
									hit = bvh_cardinal_curve_intersect(kg, isect_array, P, dir, visibility, object, primAddr, ray->time, type, NULL, 0, 0);
								else
									hit = bvh_curve_intersect(kg, isect_array, P, dir, visibility, object, primAddr, ray->time, type, NULL, 0, 0);
								if(hit) {
									/* Move on to next entry in intersections array. */
									isect_array++;
									num_hits++;
#if BVH_FEATURE(BVH_INSTANCING)
									num_hits_in_instance++;
#endif
									isect_array->t = isect_t;
									if(num_hits == max_hits) {
#if BVH_FEATURE(BVH_INSTANCING)
#  if BVH_FEATURE(BVH_MOTION)
										float t_fac = 1.0f / len(transform_direction(&ob_itfm, dir));
#  else
										Transform itfm = object_fetch_transform(kg, object, OBJECT_INVERSE_TRANSFORM);
										float t_fac = 1.0f / len(transform_direction(&itfm, dir));
#endif
										for(int i = 0; i < num_hits_in_instance; i++) {
											(isect_array-i-1)->t *= t_fac;
										}
#endif  /* BVH_FEATURE(BVH_INSTANCING) */
										return num_hits;
									}
								}
							}
							break;
						}
#endif
					}
				}
#if BVH_FEATURE(BVH_INSTANCING)
				else {
					/* Instance push. */
					object = kernel_tex_fetch(__prim_object, -primAddr-1);
					int object_flag = kernel_tex_fetch(__object_flag, object);

					if(object_flag & SD_OBJECT_HAS_VOLUME) {

#if BVH_FEATURE(BVH_MOTION)
						bvh_instance_motion_push(kg, object, ray, &P, &dir, &idir, &isect_t, &ob_itfm);
#else
						bvh_instance_push(kg, object, ray, &P, &dir, &idir, &isect_t);
#endif

						if(idir.x >= 0.0f) { near_x = 0; far_x = 1; } else { near_x = 1; far_x = 0; }
						if(idir.y >= 0.0f) { near_y = 2; far_y = 3; } else { near_y = 3; far_y = 2; }
						if(idir.z >= 0.0f) { near_z = 4; far_z = 5; } else { near_z = 5; far_z = 4; }
						tfar = ssef(isect_t);
						idir4 = sse3f(ssef(idir.x), ssef(idir.y), ssef(idir.z));
#ifdef __KERNEL_AVX2__
						P_idir = P*idir;
						P_idir4 = sse3f(P_idir.x, P_idir.y, P_idir.z);
#else
						org = sse3f(ssef(P.x), ssef(P.y), ssef(P.z));
#endif
						triangle_intersect_precalc(dir, &isect_precalc);
						num_hits_in_instance = 0;
						isect_array->t = isect_t;

						++stackPtr;
						kernel_assert(stackPtr < BVH_QSTACK_SIZE);
						traversalStack[stackPtr].addr = ENTRYPOINT_SENTINEL;

						nodeAddr = kernel_tex_fetch(__object_node, object);
					}
					else {
						/* Pop. */
						object = OBJECT_NONE;
						nodeAddr = traversalStack[stackPtr].addr;
						--stackPtr;
					}
				}
			}
#endif  /* FEATURE(BVH_INSTANCING) */
		} while(nodeAddr != ENTRYPOINT_SENTINEL);

#if BVH_FEATURE(BVH_INSTANCING)
		if(stackPtr >= 0) {
			kernel_assert(object != OBJECT_NONE);

			/* Instance pop. */
			if(num_hits_in_instance) {
				float t_fac;
#if BVH_FEATURE(BVH_MOTION)
				bvh_instance_motion_pop_factor(kg, object, ray, &P, &dir, &idir, &t_fac, &ob_itfm);
#else
				bvh_instance_pop_factor(kg, object, ray, &P, &dir, &idir, &t_fac);
#endif
				triangle_intersect_precalc(dir, &isect_precalc);
				/* Scale isect->t to adjust for instancing. */
				for(int i = 0; i < num_hits_in_instance; i++) {
					(isect_array-i-1)->t *= t_fac;
				}
			}
			else {
				float ignore_t = FLT_MAX;
#if BVH_FEATURE(BVH_MOTION)
				bvh_instance_motion_pop(kg, object, ray, &P, &dir, &idir, &ignore_t, &ob_itfm);
#else
				bvh_instance_pop(kg, object, ray, &P, &dir, &idir, &ignore_t);
#endif
				triangle_intersect_precalc(dir, &isect_precalc);
			}

			if(idir.x >= 0.0f) { near_x = 0; far_x = 1; } else { near_x = 1; far_x = 0; }
			if(idir.y >= 0.0f) { near_y = 2; far_y = 3; } else { near_y = 3; far_y = 2; }
			if(idir.z >= 0.0f) { near_z = 4; far_z = 5; } else { near_z = 5; far_z = 4; }
			tfar = ssef(isect_t);
			idir4 = sse3f(ssef(idir.x), ssef(idir.y), ssef(idir.z));
#ifdef __KERNEL_AVX2__
			P_idir = P*idir;
			P_idir4 = sse3f(P_idir.x, P_idir.y, P_idir.z);
#else
			org = sse3f(ssef(P.x), ssef(P.y), ssef(P.z));
#endif
			triangle_intersect_precalc(dir, &isect_precalc);
			isect_t = tmax;
			isect_array->t = isect_t;

			object = OBJECT_NONE;
			nodeAddr = traversalStack[stackPtr].addr;
			--stackPtr;
		}
#endif  /* FEATURE(BVH_INSTANCING) */
	} while(nodeAddr != ENTRYPOINT_SENTINEL);

	return num_hits;
}

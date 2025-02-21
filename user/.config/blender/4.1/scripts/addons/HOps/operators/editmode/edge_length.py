import bpy, bmesh
from ... utility import addon


DESC = """Set edge length of selected edges rings;

The interaction with edge strips or adjacent rings is ill-defined.
"""

class HOPS_OT_EDGE_LEN(bpy.types.Operator):
    bl_idname = 'hops.edge_len'
    bl_label = 'Set Edge Length'
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = DESC


    edge_length : bpy.props.FloatProperty(
    name='Length',
    description='Edge length',
    default=0.1,
    )

    flip_dir : bpy.props.BoolProperty(
    name='Flip',
    description='Scale non-disconnected edges from different vert',
    default=False,
    )



    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        self.layout.prop(self, 'edge_length')
        self.layout.prop(self, 'flip_dir')

    def execute (self, context):
        self.edit_objects = [o for o in context.objects_in_mode_unique_data]
        self.notify = lambda val, sub='': bpy.ops.hops.display_notification(info=val, subtext=sub) if addon.preference().ui.Hops_extra_info else lambda val, sub=None: None

        counter = 0
        for obj in self.edit_objects:
            bm = bmesh.from_edit_mesh(obj.data)
            selected_edges = [(edge, edge.verts[0].co - edge.verts[1].co) for edge in bm.edges if edge.select]

            if not selected_edges: continue
            affected_verts = set()

            #identify loops rings
            candidates = []
            for edge, _ in selected_edges:

                for f in edge.link_faces:
                    if len(f.verts) == 4:
                        candidates.append(edge)
                        break

            vert_pairs = []

            while len(candidates) > 0:
                edge = candidates.pop()

                if edge.tag: continue
                edge.tag = True

                start_loop = edge.link_loops[0]
                v1 = start_loop.vert
                v2 = edge.other_vert(v1)
                vert_pairs.append((v2, v1, v1.co - v2.co))

                for loop in RingIter(start_loop):
                    if not loop.edge.select or loop.edge.tag: continue

                    loop.edge.tag = True
                    v1 = loop.vert
                    v2 = loop.edge.other_vert(v1)
                    vert_pairs.append((v1, v2, v2.co - v1.co))
                    if loop.edge.is_boundary:
                        break

                if len(edge.link_loops) > 1:
                    #non-manifold cases are ambiguous, so ignore
                    start_loop = edge.link_loops[1]

                    for loop in RingIter(start_loop):
                        if not loop.edge.select or loop.edge.tag: continue

                        loop.edge.tag = True
                        v1 = loop.vert
                        v2 = loop.edge.other_vert(v1)
                        vert_pairs.append((v2, v1, v1.co - v2.co))
                        if loop.edge.is_boundary:
                            break

            # set edge length of acquired rings
            oi = 0
            mi = 1
            sign = 1
            if self.flip_dir:
                oi = 1
                mi = 0
                sign = -1
            for pair in vert_pairs:
                origin = pair[oi]
                move = pair[mi]
                normal = pair[2] * sign
                normal.normalize()

                if move not in affected_verts:
                    move.co = origin.co + (normal * self.edge_length)

                elif origin not in affected_verts:
                    origin.co = move.co - (normal * self.edge_length)

                affected_verts.add(origin)
                affected_verts.add(move)


            # process chains
            selected_edges = [t for t in selected_edges if not t[0].tag]
            for edge, normal in selected_edges:
                linked_edges = [e for v in edge.verts for e in v.link_edges if e.select and e is not edge]

                # if not linked_edges:
                #     center = (edge.verts[0].co + edge.verts[1].co) / 2

                #     for v in edge.verts:
                #         d = v.co - center
                #         d.length = self.edge_length /2
                #         v.co = center + d

                #     continue

                origin, move = edge.verts

                if self.flip_dir:
                    move, origin = edge.verts

                if origin not in affected_verts:
                    origin.co = move.co + (normal * self.edge_length)

                elif move not in affected_verts:
                    normal.negate()
                    move.co = origin.co + (normal * self.edge_length)


                affected_verts.update(edge.verts)

            bmesh.update_edit_mesh(obj.data)
            counter += 1

        if not counter: self.notify('CANCELLED', 'No edges selected')

        self.notify(f'Edge Length: {self.edge_length:.3}', f'{get_redo_last(context)} for redo')

        return {'FINISHED'}



def get_redo_last(context):
    kmi = context.window_manager.keyconfigs.user.keymaps['Screen'].keymap_items.get('screen.redo_last', '')

    if not kmi: 'Redo Last is not bound; Click on the box'

    s = ''

    if kmi.ctrl: s += 'CTRL'
    if kmi.shift: s+= 'SHIFT'
    if kmi.alt: s+= 'ALT'
    if kmi.oskey: s+= 'OSKEY'
    if kmi.key_modifier != 'NONE': s += kmi.key_modifier


    s+= kmi.type

    return s

class RingIter:
    '''Iterable over Loop rings excluding input\n
    The Loops yielded have opposite orientation to input loop e.g. start->next->next\n
    The input loop is excluded\n
    Doesnt stop at boundary loops and goes backwards'''
    start_edge = None
    current = None
    stop = True
    def __init__(self, start):
        self.current = start
        self.start_edge = start.edge
        self.stop = False

    def __iter__(self):
        return self

    def __next__(self):
        next = self.current.link_loop_next.link_loop_next

        if self.stop: raise StopIteration

        self.stop = len(next.link_loop_radial_next.face.verts) !=4 or next.edge is self.start_edge
        self.current = next.link_loop_radial_next

        return next
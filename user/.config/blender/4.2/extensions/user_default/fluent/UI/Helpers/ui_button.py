from mathutils import Vector

from .shapes import *


class FLUENT_Ui_Button:
    def __init__(self, name=None):
        self.position = (0, 0)
        self.align = 'CENTER'
        self.dimensions = [100, 100]
        self.text_dimensions = [0, 0]
        self.margin = 12
        self.default_bg_color = get_addon_preferences().bg_color
        color = get_addon_preferences().highlight_text
        self.hover_bg_color = (color[0]*0.6, color[1]*0.6, color[2]*0.6, color[3])
        self.active_bg_color = get_addon_preferences().active_bg_color
        self.show = True
        self.order = 0

        self.shape = 'RECTANGLE'

        self.id = name

        self.text = 'Button'
        self.text_size = get_addon_preferences().font_size
        self.text_color = (1.0, 1.0, 1.0, 1.0)
        self.text_position = []

        self.input_name = None
        self.input_min = None
        self.input_max = None

        self.icon = None

        try:
            self.icon_size = [int(get_addon_preferences().icon_size), int(get_addon_preferences().icon_size)]
        except:
            self.icon_size = [32, 32]

        self.state = 0  # 1→hover 2→press
        self.is_active = False

        self.action = None

        self.tool_tip_text = ''
        self.tool_tip_text_dimensions = 0
        self.display_tool_tip = False

        self.pie_parent = None

    def set_order(self, order):
        self.order = order

    def get_order(self):
        return self.order

    def set_align(self, a):
        self.align = a

    def get_align(self):
        return self.align

    def set_margin(self, a):
        self.margin = a

    def get_margin(self):
        return self.margin

    def set_text_size(self, a):
        self.text_size = a
        self.refresh_size()

    def get_text_size(self):
        return self.text_size

    def get_id(self):
        return self.id

    def set_pie_parent(self, a):
        self.pie_parent = a

    def get_pie_parent(self):
        return self.pie_parent

    def set_tool_tip(self, string):
        self.tool_tip_text = string
        if bpy.app.version >= (4, 0, 0):
            blf.size(0, self.text_size)
        else:
            blf.size(0, self.text_size, 72)
        self.tool_tip_text_dimensions = blf.dimensions(0, string)

    def get_tool_tip(self):
        return self.tool_tip_text

    def set_default_color(self, color):
        self.default_bg_color = color

    def set_icon(self, image_name):
        icons = load_icons()
        self.icon = icons[image_name]['texture']
        self.refresh_size()

    def set_show(self, value):
        self.show = value

    def refresh_size(self):
        if self.text == '' and self.icon:
            self.dimensions = [self.icon_size[0] + self.margin * 2, self.icon_size[1] + self.margin * 2]
        elif self.text:
            if bpy.app.version >= (4, 0, 0):
                blf.size(0, self.text_size)
            else:
                blf.size(0, self.text_size, 72)
            self.text_dimensions = text_dimensions = blf.dimensions(0, self.text)
            if not self.icon:
                self.dimensions = [text_dimensions[0] + self.margin * 2, text_dimensions[1] + self.margin * 2]
            else:
                self.dimensions = [text_dimensions[0] + self.icon_size[0] + self.margin * 3, self.icon_size[1] + self.margin * 2]
        elif not self.text and not self.icon:
            self.dimensions = [32, 32]

    def set_shape(self, shape):
        self.shape = shape
        if shape == 'CIRCLE':
            self.dimensions[1] = self.dimensions[0]

    def get_shape(self):
        return self.shape

    def set_action(self, action):
        self.action = action

    def get_action(self):
        return self.action

    def set_text(self, text):
        self.text = text
        self.refresh_size()

    def get_text(self):
        return self.text

    def set_input_name(self, input_name):
        self.input_name = input_name

    def get_input_name(self):
        return self.input_name

    def set_input_min(self, input_min):
        self.input_min = input_min

    def get_input_min(self):
        return self.input_min

    def set_input_max(self, input_max):
        self.input_max = input_max

    def get_input_max(self):
        return self.input_max

    def set_text_position(self, position):
        self.text_position = position

    def set_position(self, pos):
        self.position = pos

    def get_position(self):
        return self.position

    def set_colors(self):
        color = self.default_bg_color

        # hover
        if self.state in  [1, 2]:
            color = self.hover_bg_color

        # press, active
        elif self.state == 3:
            color = self.active_bg_color

        if self.is_active:
            color = self.hover_bg_color

        return color

    def outline_color(self):
        color = self.set_colors()
        R = color[0] * 2
        if R > 1:
            R = 1
        V = color[1] * 2
        if V > 1:
            V = 1
        B = color[2] * 2
        if B > 1:
            B = 1

        return R, V, B, 1

    def set_state(self, a):
        self.state = a

    def get_state(self):
        return self.state

    def set_active(self, a):
        self.is_active = a

    def get_active(self):
        return self.is_active

    def set_dimensions(self, d):
        self.dimensions = d

    def get_dimensions(self):
        return self.dimensions

    def draw(self, events):
        if self.show:
            self.is_hover(events)
            if self.shape == 'RECTANGLE':
                if self.state in [1, 2, 3]:
                    draw_rounded_rectangle(x=self.position[0], y=self.position[1], width=self.dimensions[0], height=self.dimensions[1], color=self.outline_color(), align=self.align, radius=8, resolution=6)
                    draw_rounded_rectangle(x=self.position[0], y=self.position[1], width=self.dimensions[0]-4, height=self.dimensions[1]-4, color=self.set_colors(), align=self.align, radius=6, resolution=6)
                else:
                    draw_rounded_rectangle(x=self.position[0], y=self.position[1], width=self.dimensions[0], height=self.dimensions[1], color=self.set_colors(), align=self.align, radius=8, resolution=6)
            elif self.shape == 'CIRCLE':
                if self.state in [1, 2, 3]:
                    draw_circle_full(cx=self.position[0], cy=self.position[1], r=self.dimensions[0] / 2, color=self.outline_color(), segments=64)
                    draw_circle_full(cx=self.position[0], cy=self.position[1], r=self.dimensions[0] / 2 - 2, color=self.set_colors(), segments=64)
                else:
                    draw_circle_full(cx=self.position[0], cy=self.position[1], r=self.dimensions[0] / 2, color=self.set_colors(), segments=64)

            if self.icon:
                if not self.text:
                    draw_image(texture=self.icon, position=[self.position[0] - self.icon_size[0] / 2,
                                                            self.position[1] - self.icon_size[1] / 2], size=self.icon_size)
                else:
                    draw_image(texture=self.icon, position=[self.position[0] - self.dimensions[0] / 2 + self.margin,
                                                            self.position[1] - self.dimensions[1] / 2 + self.margin], size=self.icon_size)
                    draw_text(
                        text=self.text,
                        text_pos=[
                            self.position[0] - self.dimensions[0] / 2 + 2 * self.margin + self.icon_size[0],
                            self.position[1]
                        ],
                        text_size=self.text_size,
                        text_color=self.text_color,
                        align='CENTER LEFT'
                    )
            else:
                if self.text:
                    draw_text(text=self.text, text_pos=self.position, text_size=self.text_size, text_color=self.text_color, align='CENTER')

            if self.display_tool_tip and self.tool_tip_text:
                if not self.text_position:
                    draw_text(text=self.tool_tip_text, text_pos=[self.position[0], self.position[1] + self.dimensions[1] / 2 + self.tool_tip_text_dimensions[1]+self.margin], text_size=self.text_size, text_color=self.text_color, align=self.align)
                else:
                    draw_text(text=self.tool_tip_text, text_pos=[self.text_position[0], self.text_position[1]],text_size=self.text_size, text_color=self.text_color, align=self.align)

    def is_hover(self, events):
        if self.show:
            x_min = self.position[0] - self.dimensions[0]/2
            x_max = self.position[0] + self.dimensions[0]/2
            y_min = self.position[1] - self.dimensions[1]/2
            y_max = self.position[1] + self.dimensions[1]/2

            if self.pie_parent:
                pie_center = self.pie_parent.get_pie_center()
                if pie_center == [0, 0]:
                    pie_center = [events['mouse_x'], events['mouse_y']]
                vec = Vector((events['mouse_x'] - pie_center[0], events['mouse_y'] - pie_center[1], 0))
                if vec.length > 32:
                    vec_2 = vec.normalized()
                    vec_2 = vec_2 * self.pie_parent.get_rayon_du_pie()
                    events['mouse_x'] = pie_center[0] + vec_2.x
                    events['mouse_y'] = pie_center[1] + vec_2.y
            if x_min < events['mouse_x'] < x_max and y_min < events['mouse_y'] < y_max:
                self.state = 1
                self.display_tool_tip = True
                if get_addon_preferences().fluent_menu_hold:
                    if events['value'] == 'RELEASE' and events['type'] == 'LEFTMOUSE' or 'MENU' in self.action:
                        self.state = 2
                else:
                    if events['value'] == 'PRESS' and events['type'] == 'LEFTMOUSE':
                        self.state = 2
            else:
                self.display_tool_tip = False
                self.state = 0
        else:
            self.state = 0


class FLUENT_Ui_Layout:
    def __init__(self, id, title='', subtitle=''):
        self.id = id
        self.title = title
        self.subtitle = subtitle
        self.title_dim = blf.dimensions(0, title)
        self.subtitle_dim = blf.dimensions(0, subtitle)
        self.layout = 'ROW'
        self.button_list = []
        self.position = ['BOTTOM', 'CENTER']
        self.margin = 16
        self.rayon_du_pie = 150 * int(get_addon_preferences().icon_size) / 32
        self.nombre_de_partie_du_pie = 1
        self.decalage = 0
        self.pie_center = [0, 0]
        self.column_layout_width = 0
        self.text_size = get_addon_preferences().font_size

        self.obj = None
        self.has_overlay = False
        self.overlay_margin = 12

    def set_pie_center(self, a):
        self.pie_center = a

    def get_pie_center(self):
        return self.pie_center

    def set_margin(self, a):
        self.margin = a

    def get_margin(self):
        return self.margin

    def set_decalage(self, a):
        self.decalage = a

    def get_id(self):
        return self.id

    def add_item(self, item, index=None):
        if self.layout == 'PIE':
            item.set_pie_parent(self)

        if index is not None:
            self.button_list.insert(index, item)
            return

        self.button_list.append(item)

    def remove_item(self, item):
        for i, b in enumerate(self.button_list):
            if type(b) is FLUENT_Ui_Button and b.get_id() == item:
                self.button_list.pop(i)
                break

    def get_items(self):
        return [b for b in self.button_list if b != 'SEPARATOR']

    def set_obj(self, obj):
        self.obj = obj

    def get_obj(self):
        return self.obj

    def add_separator(self):
        self.button_list.append('SEPARATOR')

    def set_rayon_du_pie(self, rayon):
        self.rayon_du_pie = rayon

    def get_rayon_du_pie(self):
        return self.rayon_du_pie

    def pie_to_column(self):
        self.layout = 'COLUMN'
        self.has_overlay = True
        for b in self.button_list:
            if b != 'SEPARATOR':
                b.set_shape('RECTANGLE')

    def set_layout(self, layout):
        self.layout = layout
        if get_addon_preferences().menu_type == 'VERTICAL' and layout == 'PIE':
            self.pie_to_column()

    def get_layout(self):
        return self.layout

    def set_has_overlay(self, a):
        self.has_overlay = a

    def get_has_overlay(self):
        return self.has_overlay

    def get_column_layout_width(self):
        return self.column_layout_width

    def spread(self, mouse_x=0, mouse_y=0):
        if self.layout == 'ROW':
            self.row_layout()
        elif self.layout == 'COLUMN_LEFT':
            self.column_left_layout()
        elif self.layout == 'PIE':
            self.pie_layout(mouse_x, mouse_y)
        elif self.layout == 'COLUMN':
            self.column_layout(mouse_x, mouse_y)
        elif self.layout in ['MIRROR', 'TAPER'] and self.obj:
            self.mirror_taper_layout()

    def column_layout(self, mouse_x, mouse_y):
        # remove separator
        button_list = [b for b in self.button_list if b != 'SEPARATOR']
        # reorder buttons
        button_list = sorted(button_list, key=lambda b: b.get_order())

        t_panel_width = 0
        n_panel_width = 0
        self.margin = 0

        for region in bpy.context.area.regions:
            if region.type == 'TOOLS':
                t_panel_width = region.width
            if region.type == 'UI':
                n_panel_width = region.width
        largeur_fenetre = bpy.context.area.width - t_panel_width - n_panel_width

        menu_width = button_height = 0
        for index, b in enumerate(button_list):
            if b == 'SEPARATOR':
                continue
            if b.get_shape() == 'CIRCLE':
                b.set_shape('RECTANGLE')
                if not b.get_text() and b.get_tool_tip():
                    b.set_text(b.get_tool_tip())
                    b.set_tool_tip('')
            if b.get_dimensions()[0] > menu_width:
                menu_width = b.get_dimensions()[0]
            if b.get_dimensions()[1] > button_height:
                button_height = b.get_dimensions()[1]

        self.pie_center = [mouse_x, mouse_y]
        pos_x = mouse_x + (menu_width / 2)
        start_pos_y = mouse_y - (button_height / 2)
        pos_y = start_pos_y

        # gestion de la sortie de fenêtre par en bas
        delta = pos_y - button_height * len(button_list)
        if delta < 0:
            start_pos_y += math.fabs(delta)
            pos_y = start_pos_y
            self.pie_center[1] = mouse_y + math.fabs(delta)

        # gestion de la sortie de fenêtre par la droite
        delta = largeur_fenetre - (pos_x + menu_width/2)
        if delta < 0:
            pos_x -= math.fabs(delta)
            self.pie_center[0] = mouse_x - math.fabs(delta)

        # gestion de la sortie de fenêtre par la gauche
        delta = pos_x - menu_width / 2
        if delta < 0:
            pos_x += math.fabs(delta)
            self.pie_center[0] = mouse_x + math.fabs(delta)

        # Positionne les boutons
        for index, b in enumerate(button_list):
            if b == 'SEPARATOR':
                continue
            b.set_dimensions([menu_width, button_height])

            if index == 0:
                b.set_position([pos_x, start_pos_y])
                pos_y -= button_height + self.margin * 2
            else:
                b.set_position([pos_x, pos_y])
                pos_y -= button_height + self.margin * 2

        self.column_layout_width = menu_width

    def pie_layout(self, mouse_x, mouse_y):
        self.pie_center = [mouse_x, mouse_y]
        # gestion du dépassement de la fenêtre
        t_panel_width = 0
        n_panel_width = 0
        for region in bpy.context.area.regions:
            if region.type == 'TOOLS':
                t_panel_width = region.width
            if region.type == 'UI':
                n_panel_width = region.width
            if region.type == 'HEADER':
                header_height = region.height
            if region.type == 'TOOL_HEADER':
                tool_header_height = region.height
        largeur_fenetre = bpy.context.area.width - t_panel_width - n_panel_width
        hauteur_fenetre = bpy.context.area.height - header_height - tool_header_height
        # dépassement à droite
        if self.pie_center[0] + self.rayon_du_pie > largeur_fenetre:
            self.pie_center[0] =  largeur_fenetre - self.rayon_du_pie
        # dépassement à gauche
        if self.pie_center[0] - self.rayon_du_pie < 0:
            self.pie_center[0] = self.rayon_du_pie
        # dépassement en bas
        if self.pie_center[1] - self.rayon_du_pie < 0:
            self.pie_center[1] = self.rayon_du_pie
        # dépassement en haut
        if self.pie_center[1] + self.rayon_du_pie > hauteur_fenetre:
            self.pie_center[1] = hauteur_fenetre - self.rayon_du_pie


        nombre_de_boutton = len(self.button_list)
        if nombre_de_boutton:
            angle = math.radians(360 / nombre_de_boutton)
        else:
            angle = 0
        for index, b in enumerate(self.button_list):
            try:
                b.set_position([self.pie_center[0] + self.rayon_du_pie * math.cos(angle * index + self.decalage * angle), self.pie_center[1] + self.rayon_du_pie * math.sin(angle * index + self.decalage * angle)])
                b.set_text_position([self.pie_center[0], self.pie_center[1]])
            except:
                pass

    def column_left_layout(self):
        hauteur_total = 0
        for b in self.button_list:
            hauteur_total += b.get_dimensions()[1]
        hauteur_total += self.margin * (len(self.button_list) - 1)

        overlap = bpy.context.preferences.system.use_region_overlap
        t_panel_width = 0
        n_panel_width = 0
        for region in bpy.context.area.regions:
            if region.type == 'TOOLS':
                t_panel_width = region.width
            if region.type == 'UI':
                n_panel_width = region.width

        largeur_fenetre = bpy.context.area.width - t_panel_width - n_panel_width
        hauteur_fenetre = bpy.context.area.height
        if overlap:
            decal = 0
        else:
            decal = 64

        pos_x = (largeur_fenetre - self.button_list[0].get_dimensions()[0] - decal)
        start_pos_y = (hauteur_fenetre + hauteur_total) / 2
        pos_y = start_pos_y
        for index, b in enumerate(self.button_list):
            if index == 0:
                b.set_position([pos_x, start_pos_y])
                pos_y -= b.get_dimensions()[0] + self.margin
            else:
                b.set_position([pos_x, pos_y])
                pos_y -= b.get_dimensions()[0] + self.margin

    def row_layout(self):
        largeur_total = 0
        for b in self.button_list:
            largeur_total += b.get_dimensions()[0]
        largeur_total += self.margin * (len(self.button_list) - 1)
        t_panel_width = 0
        n_panel_width = 0
        overlap = bpy.context.preferences.system.use_region_overlap
        if overlap:
            for region in bpy.context.area.regions:
                if region.type == 'TOOLS':
                    t_panel_width = region.width
                if region.type == 'UI':
                    n_panel_width = region.width
        largeur_fenetre = bpy.context.area.width - t_panel_width - n_panel_width
        start_pos_x = (largeur_fenetre - largeur_total) / 2
        pos_x = start_pos_x
        for index, b in enumerate(self.button_list):
            if index == 0:
                b.set_position([start_pos_x, b.get_dimensions()[1]])
                pos_x += b.get_dimensions()[0] + self.margin
            else:
                b.set_position([pos_x, b.get_dimensions()[1]])
                pos_x += b.get_dimensions()[0] + self.margin

    def mirror_taper_layout(self):
        if self.layout == 'MIRROR':
            try:
                location_3d = self.obj.modifiers[fluent_modifiers_name['mirror']].mirror_object.location
                matrix = self.obj.modifiers[fluent_modifiers_name['mirror']].mirror_object.matrix_world
            except:
                location_3d = self.obj.location
                matrix = self.obj.matrix_world
        elif self.layout == 'TAPER':
            location_3d = self.obj.location
            matrix = self.obj.matrix_world

        region = bpy.context.region
        rv3d = bpy.context.region_data

        location_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, location_3d)
        self.pie_center = [location_2d.x, location_2d.y]

        for index, b in enumerate(self.button_list):
            if 'VALIDATE' in b.get_action():
                b.set_position([location_2d[0], location_2d[1]])

        x_length_x = x_length_y = y_length_x = y_length_y = z_length_x = z_length_y = radius = 0

        while max(x_length_x, x_length_y, y_length_x, y_length_y, z_length_x, z_length_y) < 300:
            radius += 0.05

            x = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ Vector((radius, 0, 0)))
            xx = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ Vector((-radius, 0, 0)))
            x_length_x = math.fabs(x.x - xx.x)
            x_length_y = math.fabs(x.y - xx.y)

            y = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ Vector((0, radius, 0)))
            yy = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ Vector((0, -radius, 0)))
            y_length_x = math.fabs(y.x - yy.x)
            y_length_y = math.fabs(y.y - yy.y)

            z = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ Vector((0, 0, radius)))
            zz = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ Vector((0, 0, -radius)))
            z_length_x = math.fabs(z.x - zz.x)
            z_length_y = math.fabs(z.y - zz.y)

        for index, b in enumerate(self.button_list):
            if '+X' in b.get_action():
                b.set_position(x)
            elif '-X' in b.get_action():
                b.set_position(xx)
            elif '+Y' in b.get_action():
                b.set_position(y)
            elif '-Y' in b.get_action():
                b.set_position(yy)
            elif '+Z' in b.get_action():
                b.set_position(z)
            elif '-Z' in b.get_action():
                b.set_position(zz)

    def draw_overlay(self):
        layout_dim_x = layout_dim_y = 0
        for b in self.button_list:
            if b == 'SEPARATOR':
                continue
            layout_dim_y += b.get_dimensions()[1] + self.margin

            if layout_dim_x < b.get_dimensions()[0]:
                layout_dim_x = b.get_dimensions()[0]

        draw_rounded_rectangle(
            self.pie_center[0] + layout_dim_x / 2,
            self.pie_center[1] - layout_dim_y / 2,
            layout_dim_x + 2 * self.overlay_margin,
            layout_dim_y + 2 * self.overlay_margin,
            get_addon_preferences().overlay_color,
            align='LEFT'
        )
        draw_rounded_rectangle(
            self.pie_center[0] + layout_dim_x / 2,
            self.pie_center[1] - layout_dim_y / 2,
            layout_dim_x,
            layout_dim_y,
            get_addon_preferences().bg_color,
            align='LEFT'
        )

    def draw(self, events):
        if self.layout == 'PIE' and events['show_menu'] and not (
                bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
            vec = Vector((events['mouse_x'] - self.pie_center[0], events['mouse_y'] - self.pie_center[1], 0))

            coords = [
                (self.pie_center[0] + vec.x, self.pie_center[1] + vec.y),
                (self.pie_center[0] + vec.x * 0.5, self.pie_center[1] + vec.y * 0.5)
            ]
            draw_circle_full(self.pie_center[0], self.pie_center[1], self.rayon_du_pie, (.5, .5, .5, .66), segments=64)
            draw_circle(self.pie_center[0], self.pie_center[1], self.rayon_du_pie, (1, 1, 1, 1), segments=64)
            draw_line(coords, thickness=2, color=(1, 1, 1, .5))

            if self.title and not self.subtitle:
                draw_text(text=self.title, text_pos=(self.pie_center[0], self.pie_center[1]), text_size=self.text_size,
                          text_color=(1, 1, 1, 1), align='CENTER')
            if self.subtitle and not self.title:
                draw_text(text=self.subtitle, text_pos=(self.pie_center[0], self.pie_center[1]), text_size=self.text_size,
                          text_color=(1, 1, 1, 1), align='CENTER')
            if self.subtitle and self.title:
                draw_text(text=self.title, text_pos=(self.pie_center[0], self.pie_center[1] + self.title_dim[1] * 2),
                          text_size=self.text_size, text_color=(1, 1, 1, 0.5), align='CENTER')
                draw_text(text=self.subtitle,
                          text_pos=(self.pie_center[0], self.pie_center[1] - self.subtitle_dim[1] * 2), text_size=self.text_size,
                          text_color=(1, 1, 1, 0.5), align='CENTER')
        elif self.layout in ['MIRROR', 'TAPER'] and self.obj:
            self.spread()
            if self.layout == 'MIRROR':
                try:
                    location_3d = self.obj.modifiers[fluent_modifiers_name['mirror']].mirror_object.location
                except:
                    location_3d = self.obj.location
            elif self.layout == 'TAPER':
                location_3d = self.obj.location
            region = bpy.context.region
            rv3d = bpy.context.region_data
            location_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, location_3d)
            for b in self.button_list:
                coords = [
                    location_2d,
                    (b.get_position()[0], b.get_position()[1])
                ]
                if 'X' in b.get_action():
                    color = (.9, 0, 0, 1)
                elif 'Y' in b.get_action():
                    color = (0, .9, 0, 1)
                elif 'Z' in b.get_action():
                    color = (0, 0, .9, 1)
                else:
                    color = (1, 1, 1, 1)
                draw_line(coords = coords, thickness = 2, color = color)

        if self.layout == 'COLUMN' and events['show_menu'] \
            and not (bpy.context.active_object and bpy.context.active_object.mode == 'EDIT') \
                and self.has_overlay:
            self.draw_overlay()

        for b in self.button_list:
            if b != 'SEPARATOR':
                b.draw(events)
import bpy
from ....utility.screen import dpi_factor
from ... graphics.draw import render_text, draw_border_lines, render_quad
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from . import Dims, Tips


class Row:
    def __init__(self):
        self.elements = []
        self.max_height = 0
    

    def add_element(self, element):
        self.elements.append(element)


class Scroll_Group:
    def __init__(self):
        self.rows = []


    def clear(self, context):
        for row in self.rows:
            for element in row.elements:
                element.shut_down(context)
        self.rows = []


    def row(self):
        return Row()


    def row_insert(self, row):
        self.rows.append(row)


class Scroll_Box:
    def __init__(self, width=0, height=0, scroll_group=None, view_scroll_enabled=False):
        '''20px is reserved for the scroll bar'''

        self.dims = Dims()
        self.width = width * dpi_factor(min=0.5)
        self.__height = height * dpi_factor(min=0.5)
        self.scroll_group = scroll_group if scroll_group else Scroll_Group()
        self.view_scroll_enabled = view_scroll_enabled
        self.bar = Bar(height=height)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        # State
        self.mouse_over = False
        self.locked = False
        # Slice
        self.pages = []
        self.page_index = 0

        # Preserve
        self.prev_pages = None

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, val):
        self.__height = val * dpi_factor(min=0.5)


    def build(self, db, x_offset, h_offset):
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border

        self.bar.height = self.__height

        # Dims
        self.dims.max_height = self.__height
        self.dims.max_width = self.width

        bot_x = x_offset
        bot_y = h_offset
        w = self.dims.max_width
        h = self.dims.max_height
        self.dims.bot_left  = (bot_x    , bot_y)
        self.dims.top_left  = (bot_x    , bot_y + h)
        self.dims.top_right = (bot_x + w, bot_y + h)
        self.dims.bot_right = (bot_x + w, h_offset)

        # Rows
        bot_x = self.dims.bot_left[0]
        bot_y = self.dims.bot_left[1]
        for index, row in enumerate(reversed(self.scroll_group.rows)):
            height = 0
            width = 0
            for element in row.elements:
                element.build(db, bot_x + width, bot_y)
                height = element.dims.max_height if element.dims.max_height > height else height
                width += element.dims.max_width
            row.max_height = height
            bot_y += height

        self.__build_pages()

        if self.pages != self.prev_pages or self.prev_pages == None:
            self.prev_pages = self.pages
            self.page_index = 0

        self.__build_rows(db)

        # Bar
        self.bar.build(db, self.dims, self.page_index, self.pages)


    def update(self, context, event, db):
        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)

        self.bar.update(context, event, db)
        if self.bar.handle.locked:
            self.locked = True
            db.locked_element = self
            return
        
        can_scroll = self.bar.mouse_over
        if self.view_scroll_enabled:
            if self.mouse_over and db.clicked == False:
                can_scroll = True

        if can_scroll:
            # Scroll
            if db.increment > 0:
                self.__scroll(db, direction=1)
            elif db.increment < 0:
                self.__scroll(db, direction=-1)

            # Jump To
            if self.bar.handle.mouse_over == False and db.clicked:
                if len(self.pages) > 1:
                    self.page_index = self.bar.handle.jump_to(db.mouse_pos[1], self.pages, self.bar.dims)
                    self.__build_rows(db)

        if len(self.pages) == 0: return
        start, end = self.pages[self.page_index]
        for index, row in enumerate(reversed(self.scroll_group.rows)):
            if index < start: continue
            if index > end: break

            for element in row.elements:
                element.update(context, event, db)


    def locked_update(self, context, event, db):

        self.locked = True
        if event.value == 'RELEASE':
            self.locked = False
            self.bar.handle.locked = False
            db.locked_element = None
            return

        self.page_index = self.bar.handle.locked_update(context, event, db, self.page_index, self.pages, self.bar.dims)
        self.__build_rows(db)


    def __build_pages(self):
        self.pages = []
        
        if len(self.scroll_group.rows) == 0: return

        def fit_after_index(start=0):
            height = 0
            for index, row in enumerate(reversed(self.scroll_group.rows)):
                if index < start: continue
                if row.max_height + height >= self.__height:
                    if round(row.max_height + height, 4) > round(self.__height, 4):
                        return index - 1
                    return index
                height += row.max_height
            return None

        for index, row in enumerate(reversed(self.scroll_group.rows)):
            end = fit_after_index(index)
            if end != None:
                self.pages.append((index, end))
            else:
                if index == 0:
                    self.pages.append((index, len(self.scroll_group.rows)))
                    return


    def __scroll(self, db, direction=0):
        if len(self.pages) == 0: return

        self.page_index += direction
        if self.page_index > len(self.pages) - 1:
            self.page_index = len(self.pages) - 1
        if self.page_index < 0:
            self.page_index = 0
        
        self.bar.handle.set_location(self.page_index, self.pages, self.bar.dims)
        self.__build_rows(db)


    def __build_rows(self, db):

        bot_x = self.dims.bot_left[0]
        bot_y = self.dims.bot_left[1]

        if len(self.pages) == 0: return
        start, end = self.pages[self.page_index]
        for index, row in enumerate(reversed(self.scroll_group.rows)):
            if index < start: continue
            if index > end: break

            height = 0
            width = 0
            for element in row.elements:
                element.build(db, bot_x + width, bot_y)
                height = element.dims.max_height if element.dims.max_height > height else height
                width += element.dims.max_width
            bot_y += height


    def draw(self, db):

        if len(self.pages) == 0:
            if self.dims.max_height == 0:
                return

        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color, width=2)

        self.bar.draw(db, self.pages)

        if len(self.pages) == 0: return
        start, end = self.pages[self.page_index]
        for index, row in enumerate(reversed(self.scroll_group.rows)):
            if index < start: continue
            if index > end: break

            for element in row.elements:
                element.draw(db)


    def draw_tips(self, db):
        if len(self.pages) == 0: return
        start, end = self.pages[self.page_index]
        for index, row in enumerate(reversed(self.scroll_group.rows)):
            if index < start: continue
            if index > end: break

            for element in row.elements:
                element.draw_tips(db)


    def shut_down(self, context):
        for index, row in enumerate(reversed(self.scroll_group.rows)):
            for element in row.elements:
                element.shut_down(context)


class Bar:
    def __init__(self, height):
        self.dims = Dims()
        self.width = 20 * dpi_factor(min=0.5)
        self.height = height * dpi_factor(min=0.5)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.mouse_over = False

        self.handle = Handle()


    def build(self, db, dims, page_index, pages):
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border

        self.dims.max_width = self.width
        self.dims.max_height = self.height

        bot_x = dims.bot_right[0]
        bot_x -= self.width
        bot_y = dims.bot_right[1]
        w = self.dims.max_width
        h = self.dims.max_height

        self.dims.bot_left  = (bot_x    , bot_y)
        self.dims.top_left  = (bot_x    , bot_y + h)
        self.dims.top_right = (bot_x + w, bot_y + h)
        self.dims.bot_right = (bot_x + w, bot_y)

        self.handle.build(db, dims, page_index, pages)


    def update(self, context, event, db):
        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)
        self.handle.update(context, event, db)


    def draw(self, db, pages):
        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color)

        if len(pages) > 1:
            self.handle.draw(db)


class Handle:
    def __init__(self):
        self.dims = Dims()
        self.width = 20 * dpi_factor(min=0.5)
        self.max_h = 10 * dpi_factor(min=0.5)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.mouse_over = False
        # Locked
        self.locked = False
        self.start_y = 0
        self.diff = 0


    def build(self, db, dims, page_index, pages):
        # Color
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border
        
        # Build Dims
        self.dims.max_width = self.width
        self.set_location(page_index, pages, dims)


    def update(self, context, event, db):
        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)

        if self.mouse_over: self.bg_color = db.color.mouse_over
        else: self.bg_color = db.color.cell_background

        if self.mouse_over and db.clicked:
            self.locked = True
            self.start_y = db.mouse_pos[1]
            self.diff = self.start_y - self.dims.bot_left[1]


    def locked_update(self, context, event, db, page_index, pages, dims):
        # Mouse
        mouse_y = db.mouse_pos[1]
        if mouse_y > dims.top_left[1]:
            mouse_y = dims.top_left[1]
        elif mouse_y < dims.bot_left[1]:
            mouse_y = dims.bot_left[1]

        # Row Height
        rows = len(pages) if len(pages) > 0 else 1
        row_h = self.__row_height(rows, dims)

        # Index
        normalize = mouse_y - dims.bot_left[1]
        page_index = int(normalize / row_h)
        page_index = self.__clamp_page_index(page_index, pages)

        self.set_location(page_index, pages, dims)
        return page_index


    def jump_to(self, y, pages, dims):
        rows = len(pages) if len(pages) > 0 else 1
        row_h = self.__row_height(rows, dims)

        if y > dims.top_left[1]:
            y = dims.top_left[1]
        elif y < dims.bot_left[1]:
            y = dims.bot_left[1]

        normalize = abs(y - dims.bot_left[1])
        page_index = int(normalize / row_h)
        page_index = self.__clamp_page_index(page_index, pages)
        self.set_location(page_index, pages, dims)
        return page_index


    def set_location(self, page_index, pages, dims):
        bot_x = dims.bot_right[0]
        bot_x -= self.width
        bot_y = dims.bot_right[1]
        w = self.dims.max_width
        rows = len(pages) if len(pages) > 0 else 1

        row_h = self.__row_height(rows, dims)
        bot_y += row_h * page_index

        # Clamp : Size
        top_y = dims.top_left[1]
        if row_h < self.max_h:
            row_h = self.max_h
        
        # Clamp : Loc Top
        if bot_y + row_h > top_y:
            bot_y = top_y - row_h

        # Clamp : Loc Bottom
        if bot_y < dims.bot_right[1]:
            bot_y = dims.bot_right[1]


        self.dims.bot_left  = (bot_x    , bot_y)
        self.dims.top_left  = (bot_x    , bot_y + row_h)
        self.dims.top_right = (bot_x + w, bot_y + row_h)
        self.dims.bot_right = (bot_x + w, bot_y)     


    def __row_height(self, rows, dims):
        row_h = dims.max_height / rows
        if row_h < self.max_h:
            over = self.max_h - row_h
            row_h = (dims.max_height - over) / rows

        return row_h


    def __clamp_page_index(self, page_index, pages):
        if page_index > len(pages) - 1:
            page_index = len(pages) - 1
        if page_index < 0:
            page_index = 0
        return page_index


    def draw(self, db):
        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color)





from .form import Form
from .elements import setup_image_group
from .elements.label import Label
from .elements.button import Button
from .elements.input import Input
from .elements.spacer import Spacer
from .elements.dropdown import Dropdown
from .elements.color import Color
from .elements.scroll_box import Scroll_Box, Scroll_Group
from .elements.popup import Popup
from .elements.text_input import Text_Input


# --- User Utils --- #

def shortened_text(text="", width=0, font_size=12, with_dots=True):
    from .. utils.geo import get_blf_text_dims
    from ...utility.screen import dpi_factor

    width = width * dpi_factor(min=0.5)
    new_text = text
    slice_end = len(text)

    while True:
        if with_dots:
            if get_blf_text_dims(new_text + "...", font_size)[0] < width:
                if slice_end == len(text):
                    return new_text
                return new_text + "..."
        else:
            if get_blf_text_dims(new_text, font_size)[0] < width:
                return new_text
        slice_end -= 1
        if slice_end <= 0: return text
        new_text = text[:slice_end]





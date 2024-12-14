import bpy, time
from .. utility import addon


def collapse_3D_view_panels(tool_shelf=False, n_panel=False, force=False):
    '''Collapses N-Panel and Tool Panel\n
    Returns (original_tool_shelf, original_n_panel) '''
    
    original_tool_shelf = False
    original_n_panel = False

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:

                    if hasattr(space, 'show_region_toolbar'):
                        if hasattr(space, 'show_region_ui'):

                            # --- GET --- #
                            original_tool_shelf = space.show_region_toolbar
                            original_n_panel = space.show_region_ui

                            # --- SET --- #
                            if addon.preference().ui.Hops_auto_hide_t_panel == True or force:
                                if tool_shelf != space.show_region_toolbar:
                                    space.show_region_toolbar = tool_shelf

                            if addon.preference().ui.Hops_auto_hide_n_panel == True or force:
                                if n_panel != space.show_region_ui:
                                    space.show_region_ui = n_panel
                        
    return (original_tool_shelf, original_n_panel)
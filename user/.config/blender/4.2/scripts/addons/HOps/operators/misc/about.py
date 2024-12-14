import bpy
from ... utility import addon

from ...ui_framework.operator_ui import Master
from ... import bl_info

class HOPS_OT_About(bpy.types.Operator):
    bl_idname = "hops.about"
    bl_label = "Display About Information"
    bl_options = {'REGISTER',}
    bl_description = f'''Display About Information \n

    {bl_info['description']}

    LMB - About
    Shift - Addon List
    Ctrl - Pong Credits
    Alt - Logo Adjust
    Ctrl + Shift - Tips Screen Saver

    Version {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}_{bl_info['version'][3]}\n

    '''
    called_ui = False

    def __init__(self):

        HOPS_OT_About.called_ui = False

    def invoke(self, context, event):

        if event.shift and event.ctrl:
            bpy.ops.hops.draw_screen_saver_launcher('INVOKE_DEFAULT')

        elif event.shift:
            if not HOPS_OT_About.called_ui:
                HOPS_OT_About.called_ui = True

                ui = Master()
                draw_data = [
                    [f"Addon List ({len(bpy.context.preferences.addons.keys())})"],
                    [f"HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}_{bl_info['version'][3]}", " "]]

                draw_data.append(["..."])
                _addons = bpy.context.preferences.addons.keys()

                _new_addons = []
                for _addon in _addons:
                    _addon = _addon.strip()
                    if _addon[:2] != "io":
                        _new_addons.append(_addon)

                index = 0
                error_out_count = 100
                while True:
                    if index + 1 < len(_new_addons):
                        left_side = _new_addons[index]
                        right_side = _new_addons[index + 1]
                        draw_data.append([left_side, right_side])
                        index += 2
                    else:
                        break

                    if index >= error_out_count:
                        break


                draw_data.append(["Addons Used ", " "])

                ui.receive_draw_data(draw_data=draw_data)
                ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        elif event.ctrl:
            bpy.ops.hops.pong('INVOKE_DEFAULT')

        elif event.alt:
            bpy.ops.hops.adjust_logo('INVOKE_DEFAULT')

        else:
            if addon.preference().needs_update:  # and not 'Connection Failed':
                text = "Needs Update"
            elif addon.preference().needs_update == 'Connection Failed':
                text = "Unknown Status"
            elif not addon.preference().check_update:
                text = "Update Query disabled"
            else:
                text = "Current Version"

            if not HOPS_OT_About.called_ui:
                HOPS_OT_About.called_ui = True
                ui = Master()
                draw_data = [
                    [f"{bl_info['description']}"],
                    [f"HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}_{bl_info['version'][3]}", text]]

                draw_data.append(["..."])
                authors = bl_info['author'].split(",")

                authors = authors[:7]
                for author in reversed(authors):
                    author = author.strip()
                    draw_data.append([author])

                draw_data.append(["Authors ", " "])

                ui.receive_draw_data(draw_data=draw_data)
                ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}

import bpy
from .. utils.addons import addon_exists

used_addons = [
    ('kitops' or 'Kit_OPS', 'Kitops',           'https://www.kit-ops.com/'),
    ('Cablerator',          'Cablerator',       'https://gumroad.com/l/cblrtr/operative'),
    ('PowerSave',           'PowerSave',        'https://gumroad.com/l/powersave'),
    ('Boxcutter',           'Boxcutter',        'https://gumroad.com/l/BoxCutter/iamanoperative'),
    ('mira_tools',          'Mira Tools',       'https://blenderartists.org/t/miratools/637385'),
    ('MESHmachine',         'MESHmachine',      'https://gumroad.com/l/MESHmachine/decalarmy'),
    ("DECALmachine",        "DECALmachine",     'https://gumroad.com/l/DECALmachine/'),
    ('batch_ops',           'Batch_OPS',        'https://gum.co/batchops'),
    ('conform_object',      'Conform Object',   'https://blendermarket.com/products/conform-object'),

]

recommended_addons = [
    ("GroupPro",            "Group Pro",        "https://gumroad.com/l/GroupPro/for_operatives#"),
    ('mesh_shaper',         'Mesh Shaper',      'https://gumroad.com/l/bezier_mesh_shaper'),
    ("power_snapping_pies", "Snapping Pies",    "https://github.com/mx1001/power_snapping_pies"),
    ('zen_uv',           'Zen UV',              'https://gumroad.com/l/ZenUV/HOPscutter')
]

def draw_addon_diagnostics(layout, columns = 4):
    box = layout.box()
    box.label(text="Recommended Addons")
    box = box.box()
    draw_addon_table(box, used_addons, columns, True)

    box = layout.box()
    box.label(text="Additional Addons")
    box = box.box()
    draw_addon_table(box, recommended_addons, columns, False)


def draw_addon_table(layout, addons, columns, show_existance):
    col = layout.column()
    for i, (identifier, name, url) in enumerate(addons):
        if i % columns == 0: row = col.row()
        icon = addon_icon(identifier, show_existance)
        if icon == "FILE_TICK":
            row.operator("hops.display_notification", text=name, icon = icon).info = name +' Active'
        else:
            row.operator("wm.url_open", text=name, icon = icon).url = url

    if len(addons) % columns != 0:
        for i in range(0, columns - len(addons) % columns):
            row.label(text="")

def addon_icon(addon_identifier, show_existance):
    if show_existance:
        if addon_exists(addon_identifier): return "FILE_TICK"
        else: return "ERROR"
    else:
        return "NONE"

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
	'version': (3, 1, 0),
	'blender': (4, 1, 0),
	'location': '3d View > Tool shelf',
	'description': 'Collection of random greebling functionalities',
	'warning': '',
	'wiki_url': '',
	'doc_url': 'https://www.blenderguppy.com/add-ons/random-flow',
	'tracker_url': 'https://www.blenderguppy.com/add-ons/help-and-support',
	'category': 'Mesh'}

from . import operators
from . import utils
from . import ui
from . import preferences

def register():

	operators.register()
	ui.register()
	preferences.register()

def unregister():

	preferences.unregister()
	ui.unregister()
	operators.unregister()
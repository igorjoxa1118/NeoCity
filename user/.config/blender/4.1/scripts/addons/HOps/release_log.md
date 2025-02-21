## 0.0.9.8.6. MercuryX_19
	- DecalMachine Edit Mode support
		○ Edit Mode Support
		○ Ctrl + click for blank mat + decal assign
	- Mirror Improvement
		○ Multiobject visual bug resolved
	- Boolscroll Error for Dead Mod Resolved
	- Smooth
		○ Edit mode support for smooth
		○ Super smooth arc complete
	- EM Macro
		○ Multi directional support
	- Dice V2 
		○ Additional options added to helper
		○ S now capable of recalculating dice
	- Wire Fade (toggle in opt ins)
		- Csharp
		- Smart Apply
		- Mirror
		- Voxelizer 
		- Decimate (sculpt)
		- Mod Scroll 
		- Boolscroll
		- Subsurf (mod)
		- To Shape
		
	Fixes
	- Boolean Helper fix for dead mods
	- DM window individual for edit mode
	- Bool scroll no object error
Solid (shift) sets sstatus to undefined

## 0.0.9.8.6. MercuryX_18
	- New circle algorithm alternative (edit mode)
		○ Delegated to shift
		○ No looptool requirement
		○ Unique
		○ Supports more cases than ever
	- UV Project capable of unifying on ctrl click
		○ Ctrl + shift to load custom image
	- UI Default Change (grey event)
	- Mat Scroll Viewport Color Tooltip Updated
		○ Now supports both blank and scroll
	- Prefix pref
		- Helps add modifier stay under (A)
	- Shade Solid (shift)
		- Adds objects to proper collection
	- Bevel 
		- Default Segment Count Added to preferences
	- EM Macro / Knurl 
		- Unlocked for both directions to exit
	- Subdivision 
		- Alt click is capable of adding first to object
	- Lattice
		- Re-adds lattice to dead modifier eliminating dead end
	- Bevel / Solidify
		- No longer error when active obj is not selected
	- Selection To Mesh / Collection Support
	- Boolscroll / Collection Support Extended
	- 2.91 New Boolean Toggle for Exact / Fast
	- Boolean Subpanel added to Bevel Helper
	- UV Draw return / UV Display return
		- Ctrl click to display UVs
		- Lazy Selection Support
		- Prefs for adjustments
	- Smooth Improvements
		- Merged with laplacian (swappable)
		- Vgroup scrolling
		- T (toggle mod) V (vertex group) I (invert vgroup) Alt Scrll (cycle groups)
	- Decalmachine 2 support for asset loader
	- Blank light replacive improvements
	
	- Fixes
		○ HOPSdots speedup optimization 1 implemented
		○ Blank Scroll error when no materials is present
		○ Lattice added before WN
		○ Topbar toggle present in Q menu 
		○ Grid tooltip updated
		○ Custom profile support for 2.83
		○ Auto Unwrap fix for 2.91

## 0.0.9.8.6. MercuryX_17
	- Operator display fix for screen lock
	- Josh Added to links
	- Folder fixes for bevel and blank light
	- Material to viewport full support
		○ Blank material extended
	- Hopstool - Grate / Grid
		○ Circle Shape (nonsmart)
		○ Shift to intersect w/ boolshape
			§ Allows for grid to selection via hopstool
				□ F9 for options
	- Ctrl + click voxelize to set voxelization
	- Array V2 
		○ E to exit to empty. 
			§ Rotate to adjust count
	- Smart Apply Gate increased to 3 for bevel from 2.
		○ Smart apply fix for curves and non meshes to be ignored

	- Fixes
		○ Tooltip fix for matcut
		○ Hops_helper fix for probes
Dice typos fixed and micro ui adjusted

## 0.0.9.8.6. MercuryX_16
986_16 (Mercury X)
	- Fix typo in vertex align
		○ Ctrl for arc not alt.
	- To_Shape Expansion
		○ Decap Shape
			§ Array Compatible
			§ Endcap Creation
		○ Convex Hull Shape
	- Ponte Added to Links 
	- Boolean Branch Compatibility
	- 2.9 Compatibility Improvements
	- Constraint Panel 2.9 Improved Support

## 0.0.9.8.6. MercuryX_15
986_15 (Mercury X)
	- Kitops 2 Support
		○ Digital Loader Updated
			§ Ctrl will continue to load materials
	- Vertex Align tool (prototype)
		○ To_Arc / To_Linear 
		○ Flow Menu 
			§ Shift + Space
			§ Single Hotkey needed
	- Bevel Custom Profile Support
		○ Shift + P - scroll custom profiles
		○ Ctrl + P - toggle profile
		○ Help Consolidation (slight)
	- Selection To Boolean
		○ Flow prototype (shift + space) test
Fixes
	- 2.9 Support
		○ Circle Fix
		○ Panel (e ) fix
	- Bevel Profile Improvements
		○ Save / Load Profile (hopstool)
		○ + - Save Window buttons added
	- Transformation Constraint 
		○ Support in helper popup
	- Smart Apply 
		○ Bevel improvement w/ apply
	- OBJ to selection (edit mode multiselect)
		○ Now working

## 0.0.9.8.6. MercuryX_14
986_14 (Mercury X)
	- Continuous Operator draw
Allows for rapid fire notifications without issue

## 0.0.9.8.6. MercuryX_13
986_13 (Mercury X)
	- Addon Support
		○ Cablerator
		○ Zen UV
		○ Kitops2 
	- BC Notfication Expansion
		○ wedge 
		○ grid units 
		○ origin (.)
		○ show shape (L)
		○ Recut (Alt + X)
		○ Dimension (drag) 
	- Notification Added to Blank Mat general
		○ Default use behavior constant
	- UV Project Support
		○ HOPS UV Project Name For mod stack
	- Bevel Profile Sort Improvements
		○ No longer breaking the handles on boolean
	- 2.9x fixes
		○ Bevel 
		○ Mirror
	- Selection To boolean V2
		○ Interactive
		○ Improved Workflow
	- Selection Modal
		○ Added to 
			§ Align / flatten 
				□ Under shift
		○ Edit mode under ST3 Mesh Tools
	- Lattice 
		○ Now supports more shapes
			§ Fonts
			§ Curves
			§ Surfaces
	- Bevel profile segement count
		○ Set to profile point count on load
	- Defaults adjusted
		○ Border / BG on for operator draw on by default
			§ Color Change for modals
	
	- Bugfixes
		○ Major
			§ Powersave Backspace
		○ Minor / QOL
			§ LTS Fixes
			§ Bevel Mod 2.9 Error
			§ Infobar fix in new API
			§ Mirror 
				□ Ctrl /Alt + scroll fix for options
			§ 2.9 mods for 2.83 removed
Errors and api changes

## 0.0.9.8.6. MercuryX_12
986_12 (Mercury X)
	- Manage 
		- Unify / Evict / Sync / Collect unified
			§ Collect
				- Collects renderable items into a collection for quick linking.
				- Exported as external class for PL (if used)
			- More to come.
	- Array V2
		- Remembers last axis for resuming
		- Set to default
	- Blank Light
		- Reversion on right click
		- Backwards / Forwards support
		- Config save / load support
		- Expanded improvements
		- E for light types in scroll
		- Scroll over type in expanded to change
		- Algorithm Adjustments for light count / quantity 
		- Contraint Opt In
	- Powerlink Support 
		- ST3 Powerlink Loader 
	- Powersave
		- Ctrl + click for save dialog window
	- To_Shape
		- Cylinder
			- Radius only (equalized radius)
		- Parenting improvements
			- Custom profile support for first bevel (cube) 
	- Additive Scroll Improvements
		- Additive now a viable option since it had behaviors in place 
			- For all enabled
			- None enabled
	- Blank Material 
		- Cycles bevel shader
	- Curve U
		- Adjustable modal
	

	- Bugfixes
		- Displace 
			- Right click bug
		- Mirror
			- Help bug resolved for mod apply / symmetry
		- Q menu
			- Edit mode fix for non-meshes
			- Asset loader logic refinement 
		- Q Menu Curve
			- Curve Modifier From hopsTool added
		- AR Mod Fixes for 2.9 / greasepencil
			- Array mod not able to be closed
			- Grease pencil mods now showing
			- Mir 3 support for grease pencil
		- QOT support for edit mode restored
			- Sorry QD gang
3d Cursor used for blank light / camera

## 0.0.9.8.6. Mercury8 - 12
986_8
	- View Align
		- Roll view added
		- Default view / behavior adjusted
		- Integration Improvements
			- Added to edit mode
				□ Meshtools
			- Hopstool
				□ Topbar next to mirror
			- Alt + V
	- Mod Scroll Toggle
		- Bugfix for alt
	- Cycles Improvements 
		- V_lookdev (same as eevee)
		- Added to hopsbutton cursory
	- Bevel Profile Improvements
		- Bevel keeping points vector in 2.9
	
	- Blank Light
		- Replace lights not positions

986_9
	- View Align
		- Alt + Z support
		- Numerical support
		- Additional improvements
	- Mirror
		- Tab for advanced / simple mode
		- V for view
		- Help Panel

986_10_11
	- Bool Scroll switch
		- Added to prefs
			- Additive / Classic Scroll
	- Mirror 
		- Bugfix for multi
		- Order adjustment
		- Mod list added
		- Shift + click
			- Showtime Support
	- Curve Fix
	- Multimirror bugfix
	- Preferences bugfix
	- View align
		- Empty alignment system V1
			- Notification for empty display
		- Object mode no intial jump allowing for positioning
		- F to flip view / Similar to numpad 9
		- A and Period to Focus on Selection
	- Blank Light
		- Non-destructive blank light
	- Material Scroll 
		- UI Improvement for Micro
	- Displace
		- 0 - set to 0 during modal
	- Notification Additions
		- Meshtool Uni
		- Array V2
		- Decimate 
		- Smooth / Lsmooth
		- Blank Material
		- 
		
986_12 (Mercury X)
	- Array V2
		- Remembers last axis for resuming
	- Blank Light
		- Reversion on right click
		- Backwards / Forwards support
	- Curve U
		- Adjustable modal
	- Powerlink Support 
		- ST3 Powerlink Loader 
	- Manage 
		- Unify / Evict / Sync / Collect unified
			§ Collect
				- Collects renderable items into a collection for quick linking.
				- Exported as external class for PL (if used)
			- More to come.
	- To_Light
		- Config save support
	- To_Shape
		- Radius only (equalized radius)
		- Parenting improvements
			- Custom profile support for first bevel (cube) 
	- Additive Scroll Improvements
		- Additive now a viable option since it had behaviors in place 
			- For all enabled
			- None enabled
	- Blank Material 
		- Cycles bevel shader
	- Subdivision
		- Alt + click to place at start of stack instead of end
	- Lattice
		- Will replace dead lattice mod in stack with new one. 

	- Bugfixes
		- Displace 
			- Right click bug
		- Mirror
			- Help bug resolved for mod apply / symmetry
		- Q menu
			- Edit mode fix for non-meshes
			- Asset loader logic refinement 
		- Q Menu Curve
			- Curve Modifier From hopsTool added
		- AR Mod Fixes for 2.9 / greasepencil
			- Array mod not able to be closed
			- Grease pencil mods now showing
			- Mir 3 support for grease pencil
		- QOT support for edit mode restored
			- Sorry QD gang
		- 3d Cursor used for blank light / camera
		- Powerlink should start list at the last file not the first one. 
I have to scroll every time to get to the first entries. 

## 0.0.9.8.6. Mercury7
986_7
	- Bevel
		- Save / Load Profile
			§ Hopstool dots
			§ Bevel Helper
		- Extra notifications
	- Scupt Dynamic Popup
		- Brush list
	- Simple Deform 
		- X to change axis
	- Mirror fix for error in certain scenarios
	- Recursive Late Parent
		- Extends to booleans children as well
	- Lattice Q menu count added
	- Reset Axis / Flatten
		- Repaired for edit mode
		- Notification for xyz
	- Voxelizer / Decimate Notification Text
		- Decimate multi ratio toggle key
	- View Align Tool
		- Added w/ Flatten in object / edit
	- Curve fix 
		- Continuous saga
	- Verbiage fixes
		- Array promoted to use V2 as main.
		- Custom veribaige corrected
	- Extra notifications
		§ Added to bevel for the following
			□ 1,2,3
			□ Limit method change
			□ Bevel half
			□ Vgroup bevel 
			□ 2d Bevel
		§ Simple Deform Notifications
		§ Setframe end notification text
		§ Displace 
			- Notification Text added
	- Tooltips updated
		- Pizza ops
Booleans

## 0.0.9.8.6. Mercury6
	- Blank light
		- Shift + Scroll for scale
	- ST3 Array V2 is default
	- Custom Profile Patch
		- 2.83 works properly
			§ Support for even lengths and straight edges
		- 2.9x requires api updates from #b3d
	- EM Macro Video Prep work
		- Added support for emulate numpad
		- Grate threshold fixed
		- Tooltip updated
	- Curve fix for active curve in adjust curve
	- Smart Apply added to apply modifiers with ctrl
	- Cutter collection disabled error fixed
	- Tooltips updated massively
	- Boolean collection fix bypass
	

Minor
	- Destructive Bug resolved
	- Typo fixed for ridge
	- Camera context error fixed
	- Smart apply notification added to dice
Tooltips updated slightly

## 0.0.9.8.6. Mercury5
986_5
	- Custom Profile Support
	- Border Drawing 4k Optimizations 
		○ Retina Support
		○ Fitted border
		○ Properly spaced text
	- To_Rope
		○ Supports selection
		○ Supports curves
			§ Added to Q menu for curves
	- Sync tooltip updated
		- Sync is purely modifier based
			§ Nothing to do with render settings.
	- Mirror 
		- Ctrl scrolls classic list
		- Alt scrolls full list
	- Pizza Ops V2

Minor
	- Smart Apply Improvements

## 0.0.9.8.6. Mercury4
986_4
	- ST3 array swap support
		○ Modifiers
		○ HOPS Button
	- Hshape (rope)
	- Screw X to change axis
		○ Help updated for hotkeys
	- Unify / Evict / SYNC
		○ Sync 
			§ Sets modifiers to reflect viewport
	- Border Retina Improvements
		○ Added to BC Notifications
	- Keymap popup extended to Preference Popup
	- Mirror 
		○ Notification Text Per Option Change
Minor
	- HOPStool error
		○ Fix for dots w/ light and mesh selected
	- Border Improvements for retina display 
		○ Sizing improvements
			§ Now Encompassing entire wordbase

## 0.0.9.8.6. Mercury3
986_3
	- Voxelization added to helper
		○ Notification text on voxelization
	- ST3 Array V2
		○ TAB Freezes array
		○ Array fixed parenting / Scale issues
	- Sharp Marking Fixed
	- Smart Apply Vgroup Fix
Minor
	- Bevel fix for auto-smooth on 1 for edit mode
	- Logo X toggle on Off
	-  Pong Credits text scale for high DPI
	- Addon list title for about / addon list
	- Extra notification toggle 
		○ Apply modifiers added

## 0.0.9.8.6. Mercury2
986_2
	- Camera Fix
		○ Marker support 
	- Gizmo space for high dpi displays
	- Lights tracked to empty for blank light

Minor
	- Add cam default to view
	- Bugfix for twist 360 duplicate


## 0.0.9.8.6. Mercury 1
UI
- SHOWTIME MODE
- Update notification system
	○ Button / About icon color reflects update
	○ Info in prefs 
	○ Keymap tab in button displays status
	○ Out of date in Q menu
	○ Help area also lists market links
		§ And update status
- Button hotkey display in button
	○ Ctrl + K - hotkey configuration utility
		§ Located under settings above about in Q menu
	○ Does not update on keymap changes. Only for defaults.
- BC Notifications
	○ Experimental tracking system for bc to display notifications
	○ Limited to the modal state. 
- Q Menu Cleanup
	○ Opt - In added for Stacked Q menu
	○ Alt + V Submenu Cleanup
	○ Modifier List Cleanup
	○ Settings Cleanup
- Modifier Helper Update for 2.9
	○ No drag and drop capabilities
	○ Toggle for 2.83 to use 2.9 style
- Opt-Ins Updated (separate video)
	○ Wrap 
	○ T/N Panel Closure
	○ Additional options 
		§ Do full overview

Meshtools
- Edit Mode Multi Tool
	○ EM Macro (interactive)
		§ Knurl / Grate
		§ Panel
			□ Edge
			□ Face
				® Show case vs alt + S push
- Multi Curve Extract
	○ Extract curve from multiple meshes at the same time
- Mirror
	○ Behavior notification on launch.
	○ Alt Scroll to change type
- ST3 Array V2
	○ Ctrl + Click about
	○ Array w/ 2d / 3d 
	○ Array between
		§ Freeze with F press 1 and shift 1 and X to change axis
		§ Press V and toggle 2d and 3d modes of array

Material
- Helper / New Material 
	○ Blank Fix
		§ No longer replaces all indices on a model
		§ Now capable of replacing an indice with a blank
	- Adds new entries
		§ Glass 
		§ Emission 
- Mat Panel List Count Pref
	- In pref option for alt + M max list count
- Material cut support
	○ Blank Material Cut
		§ Bool Shift 
		§ Bool Modal
		§ Material Knife
			□ Also supported in shift and modal 
Behavioral
- BoolModal / Scroll
	○ Support for T to adjust inset / outset 
- Modifier Scroll Apply
	○ Mod scroll apply
		§ Ctrl to apply visible mods
		§ Shift to duplicate and remove leftover mods
		§ Help test updated
- To Cam (Frontal / View)
	○ Toggle expanded in prefs and opt ins
- Blank Lights
	○ FAS Mode Mouse Orbit
	○ Expanded UI
		§ Light Panel
		§ Fog World
	○ Bloom toggle with Q 
- Viewport + 
	○ To_Light (T)
		§ T for blank light afterwards
	○ Blur fix for 283
- Custom Mouse Wrap
- T and N panel removal on modals
- About button improvements
	○ Pong on Ctrl Added
	○ Logo adjust on Alt Added
		§ Emulate numpad impacts alt clicking buttons.
	
Minor
- reset sstatus on boolshape duplicate
- Wire / Solid for all objs selected
	○ Show Solid
		○ Fix for cycles
- Normal Panel helper dropdown fixed
- Notification text added to knife
- boolshape sstatus assigned on selection to Boolean
- Dpi scale improvements
	○ If you are using a 50k retina display the fast ui should now display correctly.
- 2d Curve Improvements
- UV Project Modifier
	○ Shift Click for grid setup
	○ Aimed for UE4 quick mapping
- Viewport Lookdev Blur fixed for 2.83
- Hops button fixes for helper and options
- Smart Apply / Csharp Remove Cutters Separated
- Shift + Q Pie ST3 Array swap support
- Bweight able be unassigned in sharp options
- Apply Modifier Notification Text
- Extra Info Toggle
	○ New bevel added operator notification
	○ Toggle available
- Notification text for modscroll multi
- Weight Edit Mode Mark Support
- Hopstool fixes 
	○ Ctrl + right mouse click dots
	○ 2.9 support 
- Solidify 
	○ Expanded UI (experimental)
- Material Improvements
	○ Grease Pencil material filtered
	○ Filtering for Grease Materials
		○ Filtering for _name for decals in scroll
		§ Material Scroll 
			□ Decals ignored from DM
		§ Alt + M GP Materials not listed
	○ Carpaint group changed for stability
		§ Clearcoat set to 1
- Fast UI Improvements
	○ Dice Smart Apply prompt to fast ui
	○ High retina display improvements
- Material Knife
- Ctrl + Shift + L - Logo Adjust
	○ A to center
	○ Q to reset
Scroll for scale

## 0.0.9.8.5. Neodymium_24
- Kitops alt for ST3
- Verbiage fixed for eevee HQ / LQ
- Removal of modifiers from spacebar menu
- R3MappR fix (ST3)
- Material Scroll material display bug
	- .name mats no longer show
- Image removal bug
	- Half bevel icon bug w/ x on bwidth
- Spherecast drawing
- To / Shape - To_Empty
	- On shift as well
- INTERNAL - bevel half drawing
- Smart Apply keep vgroup bevels
- Dice 
	- W for wireframe
- Displace 
	- X rapid axis change
	- Roll wheel for extras
- Classic Array restore state
- Custom viewport environment support
- Lookdev + 
	- To_Render [R]
- Camera Rig added to alt + V
	- Camera height is at 12
- Screw - Intermediate adjustment
	- Shift support
- OSKEY support for ctrl 
	- Allowing for scroll mods on mac with cmd
	- And WIN on winders
	- NOT ST3
- ST3 Array Toggle 
	- Optional opt-in in prefs
- To_Camera jump pref
	- Allows for jump to cam on ad
- To_Render for lookdev
	- Automatically sets lookdev to render
- Left Handed Adjustments
	- Classic Array
	- Circle 
	- Displace
- Active-Tool Icon Version Info
	- V1 - NLN
- Flatten (local rotation support)
- ST3 Mesh Tools V1
- Triangulate multiple mod bug fixed
- Scroll support for the following
	- Minus and plus
		§ Numpad and non
	- Arrow keys
	- Intended to support non scroll users (mac)
- Opt-In panel
	- Ctrl + ~ helper
	- Mini Helper
- About in settings
	- Authors list 
- Settings options shows in Q when an object is deselected.
- Mini helper revamp
	Object / Edit mode options added

- Material Scroll V2
	- Destructive Scroll
	- New Emissive 
- HOPS Button Changes
- BC / HOPS logo swap
- Twist Edit Mode toggle w/ Render
	- Under Opt-In
- Mirror Mod Info Area
- € Operator draw BG and Border
Edit > Selection To Boolean

## 0.0.9.8.5. Neodymium_19-21
- Smart Apply fixed
- Non/Destructive info added to Booleans
- Dice Help Updated
- Full support for tilde remap
	- Classic array
	- Simple deform
	- Smooth
	- Weld
	- Wireframe
	- Radial Array
	- Reset Axis
	- Cast 
	- Displace
	- L Smooth
	- Bool Scroll 
	- Regular Scroll
	- Material Scrolls
	- Twist360
	- Solidify
- Boolshape logo (classic) opacity
- Cycles fixes
- Help Scale
- Modal color to helper
- Lookdev Prefixed with V
	- Alt + V >> V  - fast access
- Radial / Twist 360
	- Default toggles for renderability
- Mirror no longer jump from edit mode
- Sharpness edit mode hops dropdown error fixed

_23
- Circle (loof)
	- Circle pre-options removed
	- Circle promoted from E 
- Kitops Helper fix
- Sharpness bug in mini helper resolved
- Mirror adjustments for apply and edit mode toggling
- Shift + arrow support for moving mods up and down stack in addition to previous.
- Edit Mode Q Menu Adjustments
	- Modifiers added to main
	- To shape added to operators
- Display Mark capable of off/on toggling
- Re-mapper Additional support
	- Bevel sensitivity to Percent
	- More legacy input replaced
	- Re-mapper fully assimilated
Bounce Cam fix on shift fixed

## 0.0.9.8.5. Neodymium_16
- Dice 
	- T to twist
		§ w/ Smart apply
	- S to smart apply
- Lookdev+ 
	- Right click for solid
	- LMB to keep lookdev
	- W to cycle from HQ to LQ
	- Cycles support (lookdev)
	- Enviro list
	- Ctrl + M to blank material
- Smart Apply 
	- Cutter Removal
	- Clone smart apply omission
- Autosmooth
	- Added to sharpen
	- Bevel add with A 
	- A to toggle between bevel and autosmoothing
- Boolshift
	- Instant Shift
- Bevel
	- A to adjust angle in angle
	- Alt + scroll to adjust angle on the fly
	- Alt + A for scanner V1 concept
	- Smarter help V1
- Half Bevel
	- Weighted normal sort
- Mirror
	- Region overlap fix
		§ Fixes unclickable ui
	- Panel in N panel
	- Discuss D menu for mirror (in-depth)
- HopsTool
	- Array Y and Z bug resolved
- Weld 
	- Show wireframes
- 2.9x fixes
	- Hops helper fixes for blank panel
- To_shape
	- Cleanup and optimization
- UI Cleanup
	- Ctrl + ~ helper cleanup
		§ Operation Options
	- Pref cleanup 
		§ Options reshuffled
- Decimate 
	- Unsubdivide
- Sharpen: Csharpen
	- More information
- Tilda Remapper
	- Added to inputs
- UniversalInput V1
	- Formalized input system test V1
		§ Starting small soon to encompass all.
	- Curve / Screw / Bevel affected so far 
		§ Allows for free rotation. 
	- Left / Right handed preference added
		§ Added to ctrl + ~ helper.

PANEL OPTIONS TO POWERSAVE
- Brought to you by PowerSave

- Blank Material
	- Hotkeys added 
		§ Ctrl - unique
		§ Alt - Pulse / Emission
		§ Shift - Glass
	- General / Carpaint hidden for now
		§ Will have to revisit on the L3
		§ Pending system B for grouping and VP control
- Mark
	- Ctrl - Bevel 
	- Shift - Weld
	- Show tooltip
Evict / Unify 

## 0.0.9.8.5. Neodymium_14 / 15
-  lattice fixes
-  adjust viewport improvements w/ changing bgs on numpad
-  weld (edit mode) vgroup support 
-  mirror improvement w/ empty creation
	-  mirror mesh machine support for normals (mod and apply)
-  curve extract / material keep
-  camera bounce v1

-  adjust viewport fixes
	-  W toggle eevee LQ and HQ
-  autosmooth added to sharpen
	-  replacing shift 
	-  ctrl + shift is now resharp by default
-  modal autosmooth 
	-  s to sharpen
	-  r to resharp
	-  a toggle autosmooth
-  weld roll wheel to adjust merge
-  sharpen info display adjustments
-  default bevel back to 30°
-  blank material hotkeys
	-  ctrl - unique material
	-  shift - glass material
	-  alt - emission material
-  default bevel patched back to 30° from 60°
cycles disabled addon fixes

## 0.0.9.8.5. Neodymium_13
- adjust viewport improvements w/ changing bgs on numpad
- weld (edit mode) vgroup support 
- mirror improvement w/ empty creation

## 0.0.9.8.5. Neodymium_12

To_shape
- To Sphere added
- Bevelled cube based on selection / Angle filter
	§ Bevelled slice fix.
Autosmooth Modal Test
- Alt /shift/ctrl autosmooth prefs.
Powersave option in settings for users.
- Now shows name and dir.
Viewport Adjust / Lookdev+ (alt + V) 
- Only supporting built in environments at this time.
- Quick jump into material scroll
Material scroll
- Able to jump back into viewport+
Settings fix for cycles.
Mirror V3 
- Remade by the AR once again
- Rectifies all issues from before.
Curve/Extract
- Extracts solid from boolshapes now
Smart Apply curve
- X to cancel like old right click


## 0.0.9.8.5. Neodymium_11
- lattice improvements (lF)
- to_box improvements (lF)
- ~ to toggle viewport off
- material scroll
- blank material edit mode
- late parent proper (lF)
- bevel vert in edit mode adjustment

## 0.0.9.8.5. Neodymium_10

	- Add Camera Improvements
		○ F9 Window
		○ Rotation Parameter
		○ Added to neutral Q menu
		○ Frontal positioning by default
		○ B7 System to avoid driver complaints
		○ Toggle for set to active cam (also on CTRL)
		○ (TRACK TO CONSTRAINT IS NOT NEEDED) maybe remove
	- Radial Array Improvements
		○ Cursor resume adjustment now more graceful
		○ Functionality Improvements
	- To Plane
		○ Active Selection on addition
	- To Box
		○ Awaiting improvements
	- Bevel Improvements
		○ X - sets to half of last bevel mod present
		○ Alt + X - sets bevel to half of active bevel
	- Step Improvements
		○ Rebuilt for Weight workflow
			§ Due to lack of sstate the previous workflow remains incomplete.
		○ Bevel half for angle workflow
	- HOPStool cleanup
		○ Verbiage
		○ Curve tool error
	- Icons re-vamp P1
		○ More icons to come
	- Alt + V improvements
		○ Solid / Texture toggle added to alt + V
	-  Sharpen Improvements
		○ WN to tooltip
	- Smart Apply Modifier Improvements
		○ Shift + Click will apply all while removing last bevel and WN. Useful for surface extraction.
	- Menu Adjustments
		○ Clear Sharp re-added (sorry about that)
	- Clear Sharp Improvements
		○ Option for clear mesh data.
Spacebar option to clear custom normal data

## 0.0.9.8.4.2
- Dice V2
  ○ Intersect or knife behavior
  ○ Helper options for pre-emptive behavior
- Radial Array v3
  ○ All in one.
  ○ Capable of repeat working in an area w/ cursor
- Blank Material (ramp / carpaint)
  ○ Ramp shader w/ special controls
  ○ Carpaint w/ special controls
- Camera Turntable
  ○ Perfect turntable
- Bugfixes
Random errors w/ bevel, mirror, array.

## 0.0.9.8.4.1
- Atwist 361
Dice V1 (concept)
- Step (nondestructive)
- Bevel
  ○ C (clamp overlap) / shift + C loop slide.
- Direct shift (pie)
- Smart apply improvements
- Blank Material Expanded V3
  ○ Emission Pulse / Glass
- HOPStool improvements
  ○ Text / text size
  ○ Boolshape parent
  ○ D helper (temp)
    § Cursor snap box
  ○ Smart shape improvements (2.82+)
  ○ Vertex shape
  ○ Array 1, 2, 3 hotkey in modal w/ dot
- Menu Changes

## 0.0.9.8.4

HOPS 984
	- Curve res added to Q menu
	- Interior bevel support
	- Edit Mode Slice Added
		○ Knife Added
		○ Inset Added
	- Object Mode Inset Added
			§ Alt + shift + numpad slash hotkey
		○ Outset toggle
		○ Slice Added
	- Sort V3 added w/ sync
	- 2.82 Array and mirror gizmo fixed
	- Bevel Helper angle fix
	- Weighted normal multi support +
	- Lazy Support for mod modals
	- Radial Array Ctrl fix for displacement mod
	- Lamp options added to Q menu and pie
	- Random material V2
	- 2d bevel to bevel w/ weld support
	- Late Parent
	- Reset Axis
	- Sharpen
	- Array Support for plane
	- To Box V1 added
	- Ctrl + Shift + B
		○ Smart Key
			§ Boolshape
				□ Boolshift
			§ Bevel
				□ Helper
			§ Pend Bool
				□ BoolScroll
			§ 2 Ob
				□ Diff
			§ 3 Ob
				□ Slash
	- Interactive Boolean Operation
	- Smooth / Laplacian Mod support
		○ Shift Support for special sharp vgroup
	- Meta ball to helper
	- Mirror / Array consolidation
	- Boolean bypass
	- Hotkey corrections for sort
	- Smart apply V2
	- Directors Cut
		○ Bool auto sort WN
		○ hT - 2d bevel weld sort ignore
		○ Sharpen out of boolshapes menu
		○ Boolscroll out of edit mode (unstable) (experimental)
		○ Union fix
		○ Sharp Manager to default bevel helper
X Toggles shape in modscroll

- Weld support added to 2d bevel along w/ clamp overlap
- Radial Array Ctrl fix for displacement mod w/ 3d cursor
- Lamp options added to Q menu and pie
- Random material V2 (random mats per object w/ toolbox)
- Shift Bool added
- Sharpen consolidation
- Scroll consolidation
- mirror / array consolidation
- Hops tool boolean ring
- displace disabled for ctrl w/ radial array 3d cursor
- bevel WN sort behavior
- boolean sort override toggle and hotkey
- bwidth dimension check to replace 2d bevel
- knife / knife project support
- knife dimension check to toggle knife project

12/11/19
- Curve res added to Q menu
- Interior bevel support
- Edit Mode Slice Added
  - Knife Added
  - Inset Added
- Object Mode Inset Added
    - Alt + shift + numpad slash hotkey
  - Outset toggle
  - Slice Added
- Sort V3 added w/ sync
- 2.82 Array and mirror gizmo fixed
- Bevel Helper angle fix
- Weighted normal multi support +
- Lazy Support for mod modals

### 0.0.9.8.3
- curve res added to Q menu
- hops helper curve fixed
- mod toggle working on all selected objects
- bisect shift option on mirror
- csharp no longer applies last bevel not / mod updated
- array fixes
- circle dot fix
- boolean dots show for only active object
- new options added to shift + G
- Eevee LQ / HQ lvl 2
- 2.82 topbar label fix
- blank material V2

- hardFlow panel
	○ Dot Modifiers
- hardShape system V1
- Scroll fixes
- Boolshapes for active object only in hopstool
Helper support for curve and text

### 0.0.9.5
    - loop slide option for Bweight added (helper)
- modal mirror operator added
    - fix for auto smooth overwrite
- default for auto smooth changed to 180
- fix for brush preview error
- MESHmachine integration in edit mode operations
    - shrinkwrap refresh is hidden for now
- boolean operators added to edit mode under operations
- mir2 cstep support
- spherecast V1 added to meshtools
- QArray supports multiple objects
- TThick supports multiple objects
- misc panel has options for Qarray and Tthick
- Boolean scroll systems added
- basic Kitops support for Csharpen

### 0.0.9.4
- tooltip update
- added hotkeys for edit mode booleans
- rewrite of mirror operator
- new operator added allowing to swap green/red boolshape status (in pie/menu when boolshape is selected)
    -red / green boolean system
        -still needs a smash all booleans bypassing the red/green system
- new boolshape status added allowing to skip applying boolean modifiers
- brush selector added to sculpt menu
- bwidth limit is unlocked for undefined meshes

### 0.0.9.3
- pie menu missing options added
- cut-in operator added
    -cut in added to Q menu. Still needs hotkey
    -context for cut in fixed no single select option
- all inserts now use principal shaders as proxies
- fixed B-width Z wire show mode
- additional icons added
- renderset1 fix for filmic official
- material helper fix for new materials
- relink mirror options added
- figet support added
- new clean mesh operator (options in helper)
- adaptive width mode addeded
- adaptive segments mode adeded

### 0.0.9.2
- hoteys can be set in options hotkey tab
- scale option for modal operators was added
- booleans solver is global now can be set helper
- ssharp, cstep, csharp work on multi objects now (old multi operators removed)
- bool options added to menu/panel
- added 'reset axis' operator
- version bump.
- all operators support step workflow fromn ow on
- s/cstep operators removed and replaced by step
- wire options added to HOPS Helper
- sharpness angle for sharp operator is now global (acces via Tpanel/helper/F6)
- mesh display toggle added to edtimode >> meshtools
- pro mode switches clean ssharp with demote for reason....
- machin3 decal support added

### 0.0.8.7
- Multiple object support for B-Width
- New operator 'bevel multiplier' added
- Hud indicator moved from text to logo by default
	1. logo in corner added
	2. text status disabled by default
	3. added preferences to enable/disable logo/statustext (logo under extra / pro mode)
	4. preferences to change logo color/placement
- new operator - sharp manager was added
- csharpen uses global sharps now
- ssharpen uses global sharps now
- set sharp uses global sharps now
- added new global way to define what sharp edges to use (T-panel/ helper-misc)
- SUB-d status removed from all operators (use global statuses now)
- bweight can now select all other bweight edges in object while in modal state by presing A
- BOOLSHAPE objects are hiden to renderer now (outliner icon)
- slash assigns boolshape status for cutters now
- panels/menus/pie updated with correct operators
- added option for slash to refresh origin of cutters (in F6)
- Slice and rebbol operators replaces with slash
- fixes for material cutting
- renderset C created (speed preset)
- fix for register bug (hotkeys duplication)
- pie menu and menu uses same hotkey now (Q) it can be chosen in preferences

# Changelog

For the source of each release, see [releases](https://github.com/njshockey/all-blue-theme/releases).

## v1.2.0 (Aug. 8, 2023)

Mostly a maintenance release, but with a few nice tweaks for better readability.

- Adjusted Status Bar. [#002540](https://github.com/njshockey/all-blue-theme/issues/002540) -> #001E33
- Adjusted sidebar section headers. [#002540](https://github.com/njshockey/all-blue-theme/issues/002540) -> #001E33
- Active tab background now uses what was previously the status bar background color for better contrast. [#002138](https://github.com/njshockey/all-blue-theme/issues/002138) -> [#002540](https://github.com/njshockey/all-blue-theme/issues/002540)
- Adjusted inlay hints
  - Foreground color. #ffffff -> [#006680](https://github.com/njshockey/all-blue-theme/issues/006680)
  - Background color. #001E33 -> [#002138](https://github.com/njshockey/all-blue-theme/issues/002138)
  - Parameter foreground. #0892D0 -> [#006680](https://github.com/njshockey/all-blue-theme/issues/006680)
- Adjusted editor suggest widget selected foreground. [#003459](https://github.com/njshockey/all-blue-theme/issues/003459) -> #003A63
- Definition keywords now use the operator color (#00CCFF, #8BC6FC) to be more consistent with JSON.
  - This effects several file types like editorconfig, toml, gitattributes, etc.
- Several Rust keywords now use the operator color.
- Added download links to the readme.

## v1.1.1 (Feb. 9, 2023)

- Active line number now uses the foreground color. #D8DEE9 -> #63C5DA
- Suggest widget is now themed.
- Codelens foreground is now themed.
- Settings side bar headings have a better highlight color.
- Settings focused headings are much more visible.

## v1.1.0 (Feb. 4, 2023)

- The themes are now generated through TypeScript instead of
being manually edited by hand.
    - This brings a lot more consistency and fixes a lot of minor issues.
    - Also it's way less annoying to make changes. (The important part.)
- Terminal colors are now themed.
- Swapped around editor background colors.
    - Editor background:  [#002540](https://github.com/njshockey/all-blue-theme/issues/002540) -> [#002138](https://github.com/njshockey/all-blue-theme/issues/002138)
    - Side Bar background: [#002138](https://github.com/njshockey/all-blue-theme/issues/002138) -> #001E33
    - Status Bar background: #001E33 -> [#002540](https://github.com/njshockey/all-blue-theme/issues/002540)
    - Current line: [#003154](https://github.com/njshockey/all-blue-theme/issues/003154) -> #002C4C
- Changed Waves pink: #FF80DD -> #F77FBE
- Changed Calm yellow: #FFFC79 -> #FEF08A
- Changed error/deleted color from Calm red to Waves red.
- Booleans and numbers are now *italic*.
- Tweaked All Blue bracket colors.
- Properties now use the tag color. (Red in variants.)
- Escape characters now use the function color. (Blue in variants.)
- JS Constants and Objects now use the component color. (Green in variants.)
- Tabs now have a bottom border when active.
- Reworked selection highlighting.
- Keybindings menu is now themed.
- Along with other various changes to make the look and feel more cohesive.

## v1.0.2 (Jan. 25, 2023)

- Improved editor word highlighting.
- Reduced extension size by removing screenshots from VSIX.

## v1.0.1 (Jan. 23, 2023)

- Debug toolbar is now themed in Waves and Calm.

## v1.0.0 (Jan. 22, 2023)

- Initial release

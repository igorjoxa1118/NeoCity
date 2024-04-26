# All Blue

A VS Code theme that's a little too obsessed with a certain primary color.

## Screenshots

Default theme
![All Blue screenshot](https://github.com/njshockey/all-blue-theme/raw/HEAD/img/default-preview.png "All Blue screenshot")

Calm
![All Blue screenshot](https://github.com/njshockey/all-blue-theme/raw/HEAD/img/calm-preview.png "Calm screenshot")

Waves
![All Blue screenshot](https://github.com/njshockey/all-blue-theme/raw/HEAD/img/waves-preview.png "Waves screenshot")

The editor font used is [JetBrains Mono](https://www.jetbrains.com/lp/mono/)
with ligatures turned off.
The file icons are [Material Icons](https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme).

I'm also shilling my other projects from the screenshots:

- [My resume site](https://github.com/njshockey/njshockey-resume)
- [Keysmith](https://github.com/njshockey/keysmith-rs), a Rust keygen library
- [BST Graph](https://github.com/njshockey/bst-graph),
    create Pokemon Base Stat Total charts.

## Syntax Colors

![Syntax colors](https://github.com/njshockey/all-blue-theme/raw/HEAD/img/all-blue-colors.png)

The font used is [Cabin SemiCondensed](https://fonts.google.com/specimen/Cabin?query=cabin).
The Hex code font is [JetBrains Mono](https://www.jetbrains.com/lp/mono/).

For more details, head to [colors.md](https://github.com/njshockey/all-blue-theme/blob/HEAD/colors.md).

## Installation

In the extensions panel in VS Code, type in `njshockey.all-blue` or visit one of the following links.

- [VS Marketplace (recommended)](https://marketplace.visualstudio.com/items?itemName=njshockey.all-blue)
- [Open VSX Registry](https://open-vsx.org/extension/njshockey/all-blue)

### Manual

To install this extension manually, download it from one of the following places:

- [GitHub releases](https://github.com/njshockey/all-blue-theme/releases)
- [VS Marketplace](https://marketplace.visualstudio.com/items?itemName=njshockey.all-blue)
  - This is under resources -> Download Extension
- [Open VSX Registry](https://open-vsx.org/extension/njshockey/all-blue)
  - This is under resources -> Download
- [Itch](https://njshockey.itch.io/all-blue)

Then, in the extensions panel, click on the three dots(...) left of your open tabs, then click on `Install from VSIX...`.

## Demo

For a downloadable demo, check out the [All Blue demo](https://github.com/njshockey/all-blue-demo).
Or just clone it with:

```bash
git clone https://github.com/njshockey/all-blue-demo.git
```

## Building

1. Clone this repo. Usually with `git clone https://github.com/njshockey/all-blue-theme.git`.
2. Run `yarn` to download the necessary NPM packages.
3. Open this repo in [VS Code](https://code.visualstudio.com/).
   - Make changes to the base colors in `./src/colors`.
   - Make changes to the templates in `./src/templates/editorTemplate.ts`
and `./src/templates/syntaxTemplate.ts`.
4. Run `yarn build-themes` to generate the JSON theme files
and press F5 to test changes.
    - Run `yarn build-themes-ugly` to build the themes without Prettier.
This should save you a few seconds.
5. To build the extension file (VSIX), install VSCE with
`npm install -g @vscode/vsce` then run `yarn build-ext`.

## Image credit

[Temporary icon](https://www.pexels.com/photo/white-sailboat-on-water-273886/)
by Pixabay.

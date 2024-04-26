"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/web/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate
});
module.exports = __toCommonJS(extension_exports);

// src/common/terminal-link-provider.ts
var vscode = __toESM(require("vscode"));
function registerTerminalLinkProvider(context) {
  const subscriptions = context.subscriptions;
  subscriptions.push(
    vscode.window.registerTerminalLinkProvider({
      provideTerminalLinks: (context2, token) => {
        let regexp = /\(((.*?)@(\d*):(\d*)-(\d*):(\d*))\)/i;
        let matches = context2.line.match(regexp);
        if (matches !== null) {
          let startIndex = context2.line.indexOf(matches[1]);
          let length = matches[1].length;
          let data = {
            file: matches[2],
            startLine: parseInt(matches[3]),
            startColumn: parseInt(matches[4]),
            endLine: parseInt(matches[5]),
            endColumn: parseInt(matches[6])
          };
          return [
            {
              startIndex,
              length,
              data
            }
          ];
        } else {
          return [];
        }
      },
      handleTerminalLink: (link) => {
        vscode.workspace.openTextDocument(link.data.file).then(
          (document) => (
            // Show the editor
            vscode.window.showTextDocument(document)
          )
        ).then((x) => {
          let activeEditor = vscode.window.activeTextEditor;
          if (activeEditor !== void 0) {
            let range = new vscode.Range(
              new vscode.Position(
                link.data.startLine - 1,
                link.data.startColumn
              ),
              new vscode.Position(link.data.endLine - 1, link.data.endColumn)
            );
            activeEditor.selection = new vscode.Selection(
              range.start,
              range.end
            );
            activeEditor.revealRange(range);
          }
        });
      }
    })
  );
}

// src/common/template-helpers.ts
var vscode2 = __toESM(require("vscode"));
var import_util = require("util");
function registerTemplateHelperCommands(context) {
  const subscriptions = context.subscriptions;
  subscriptions.push(
    vscode2.commands.registerCommand(
      "epsilon.newEgxEglPair",
      (...args) => {
        let path = void 0;
        if (args.length > 0 && args[0].hasOwnProperty("path")) {
          path = args[0].path;
        }
        createNewEgxEglPair(path);
      }
    )
  );
}
async function createNewEgxEglPair(path) {
  if (path === void 0) {
    const prefilledPath = vscode2.workspace.workspaceFolders?.[0].uri.fsPath ?? "";
    path = await vscode2.window.showInputBox({
      title: "Path",
      prompt: "Enter the path where the new files should be created",
      value: prefilledPath,
      valueSelection: [prefilledPath.length, prefilledPath.length]
    });
    if (path?.endsWith("/") || path?.endsWith("\\")) {
      path = path.slice(0, -1);
    }
  }
  if (path === void 0) {
    vscode2.window.showInformationMessage("No path was provided");
    return;
  }
  let fileName = void 0;
  let eglContent = new Uint8Array();
  let egxPath = "";
  let eglPath = "";
  const pathUri = vscode2.Uri.file(path);
  const fileStat = await vscode2.workspace.fs.stat(pathUri);
  if (fileStat.type === vscode2.FileType.File) {
    fileName = path.split(/[\\\/]/).at(-1);
    eglContent = await vscode2.workspace.fs.readFile(pathUri);
    egxPath = path + ".egx";
    eglPath = path + ".egl";
  } else {
    fileName = await vscode2.window.showInputBox({
      title: "File Name",
      prompt: "Enter the name of the new files"
    });
    egxPath = path + "/" + fileName + ".egx";
    eglPath = path + "/" + fileName + ".egl";
  }
  if (fileName === void 0) {
    vscode2.window.showErrorMessage("No file name was provided");
    return;
  }
  const egxUri = vscode2.Uri.file(egxPath);
  const eglUri = vscode2.Uri.file(eglPath);
  const egxContentString = getEgxRule(fileName);
  const egxContent = new import_util.TextEncoder().encode(egxContentString);
  await vscode2.workspace.fs.writeFile(egxUri, egxContent);
  await vscode2.workspace.fs.writeFile(eglUri, eglContent);
}
function getEgxRule(fileName) {
  const ruleName = fileName.replace(/[^a-zA-Z0-9]/g, "_");
  return `rule ${ruleName} {
	template: '${fileName}.egl'
	target: '${fileName}'
}
`;
}

// src/web/extension.ts
function activate(context) {
  registerTerminalLinkProvider(context);
  registerTemplateHelperCommands(context);
}
function deactivate() {
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map

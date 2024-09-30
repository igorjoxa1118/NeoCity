"use strict";
/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

require("core-js/modules/es.array.includes.js");

require("core-js/modules/es.string.includes.js");

require("core-js/modules/es.regexp.exec.js");

require("core-js/modules/es.string.replace.js");

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.looksLikeMarkdownPath = looksLikeMarkdownPath;
exports.isMarkdownFile = isMarkdownFile;

var vscode_uri_1 = require("vscode-uri");

function looksLikeMarkdownPath(config, resolvedHrefPath) {
  return config.markdownFileExtensions.includes(vscode_uri_1.Utils.extname(resolvedHrefPath).toLowerCase().replace('.', ''));
}

function isMarkdownFile(document) {
  return document.languageId === 'markdown';
}
"use strict";
/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

require("core-js/modules/es.string.starts-with.js");

require("core-js/modules/es.string.ends-with.js");

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.startsWith = startsWith;
exports.endsWith = endsWith;

function startsWith(haystack, needle) {
  if (haystack.length < needle.length) {
    return false;
  }

  for (var i = 0; i < needle.length; i++) {
    if (haystack[i] !== needle[i]) {
      return false;
    }
  }

  return true;
}
/**
 * Determines if haystack ends with needle.
 */


function endsWith(haystack, needle) {
  var diff = haystack.length - needle.length;

  if (diff > 0) {
    return haystack.lastIndexOf(needle) === diff;
  } else if (diff === 0) {
    return haystack === needle;
  } else {
    return false;
  }
}
"use strict";
/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

require("core-js/modules/es.array.slice.js");

require("core-js/modules/es.function.name.js");

require("core-js/modules/es.array.from.js");

require("core-js/modules/es.symbol.js");

require("core-js/modules/es.symbol.description.js");

require("core-js/modules/es.symbol.iterator.js");

require("regenerator-runtime/runtime.js");

require("core-js/modules/es.object.to-string.js");

require("core-js/modules/es.regexp.to-string.js");

require("core-js/modules/es.array.concat.js");

require("core-js/modules/es.array.iterator.js");

require("core-js/modules/es.promise.js");

require("core-js/modules/es.string.iterator.js");

require("core-js/modules/web.dom-collections.iterator.js");

require("core-js/modules/es.array.map.js");

require("core-js/modules/es.array.join.js");

require("core-js/modules/es.map.js");

require("core-js/modules/es.regexp.exec.js");

require("core-js/modules/es.string.replace.js");

require("core-js/modules/es.regexp.constructor.js");

require("core-js/modules/web.dom-collections.for-each.js");

function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }

function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }

function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null) return Array.from(iter); }

function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }

function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it.return != null) it.return(); } finally { if (didErr) throw err; } } }; }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }

function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }

Object.defineProperty(exports, "__esModule", {
  value: true
});

var path = require("path");

var os_1 = require("os");

var node_1 = require("vscode-languageserver/node");

var vscode_languageserver_textdocument_1 = require("vscode-languageserver-textdocument");

var vscode_uri_1 = require("vscode-uri");

var customMessages_1 = require("./shared/customMessages");

var settings_1 = require("./shared/settings");

var eslint_1 = require("./eslint");

var paths_1 = require("./paths");

var diff_1 = require("./diff");

var languageDefaults_1 = require("./languageDefaults"); // The connection to use. Code action requests get removed from the queue if
// canceled.


var connection = (0, node_1.createConnection)(node_1.ProposedFeatures.all, {
  connectionStrategy: {
    cancelUndispatched: function cancelUndispatched(message) {
      // Code actions can safely be cancel on request.
      if (node_1.Message.isRequest(message) && message.method === 'textDocument/codeAction') {
        var response = {
          jsonrpc: message.jsonrpc,
          id: message.id,
          result: null
        };
        return response;
      }

      return undefined;
    }
  },
  maxParallelism: 1
}); // Set when handling the initialize request.

var clientCapabilities;
var documents = new node_1.TextDocuments(vscode_languageserver_textdocument_1.TextDocument); // The notebooks manager is using the normal document manager for the cell documents.
// So all validating will work out of the box since normal document events will fire.

var notebooks = new node_1.NotebookDocuments(documents);

function loadNodeModule(moduleName) {
  var r = typeof __webpack_require__ === 'function' ? __non_webpack_require__ : require;

  try {
    return r(moduleName);
  } catch (err) {
    if (err.stack) {
      connection.console.error(err.stack.toString());
    }
  }

  return undefined;
} // Some plugins call exit which will terminate the server.
// To not loose the information we sent such a behavior
// to the client.


var nodeExit = process.exit;

process.exit = function (code) {
  var stack = new Error('stack');
  void connection.sendNotification(customMessages_1.ExitCalled.type, [code ? code : 0, stack.stack]);
  setTimeout(function () {
    nodeExit(code);
  }, 1000);
}; // Handling of uncaught exceptions hitting the event loop.


process.on('uncaughtException', function (error) {
  var message;

  if (error) {
    if (typeof error.stack === 'string') {
      message = error.stack;
    } else if (typeof error.message === 'string') {
      message = error.message;
    } else if (typeof error === 'string') {
      message = error;
    }

    if (message === undefined || message.length === 0) {
      try {
        message = JSON.stringify(error, undefined, 4);
      } catch (e) {// Should not happen.
      }
    }
  } // eslint-disable-next-line no-console


  console.error('Uncaught exception received.');

  if (message) {
    // eslint-disable-next-line no-console
    console.error(message);
  }
});
/**
 * Infers a file path for a given URI / TextDocument. If the document is a notebook
 * cell document it uses the file path from the notebook with a corresponding
 * extension (e.g. TypeScript -> ts)
 */

function inferFilePath(documentOrUri) {
  if (!documentOrUri) {
    return undefined;
  }

  var uri = (0, paths_1.getUri)(documentOrUri);

  if (uri.scheme === 'file') {
    return (0, paths_1.getFileSystemPath)(uri);
  }

  var notebookDocument = notebooks.findNotebookDocumentForCell(uri.toString());

  if (notebookDocument !== undefined) {
    var notebookUri = vscode_uri_1.URI.parse(notebookDocument.uri);

    if (notebookUri.scheme === 'file') {
      var filePath = (0, paths_1.getFileSystemPath)(uri);

      if (filePath !== undefined) {
        var textDocument = documents.get(uri.toString());

        if (textDocument !== undefined) {
          var extension = languageDefaults_1.default.getExtension(textDocument.languageId);

          if (extension !== undefined) {
            var extname = path.extname(filePath);

            if (extname.length === 0 && filePath[0] === '.') {
              return "".concat(filePath, ".").concat(extension);
            } else if (extname.length > 0 && extname !== extension) {
              return "".concat(filePath.substring(0, filePath.length - extname.length), ".").concat(extension);
            }
          }
        }
      }
    }
  }

  return undefined;
}

eslint_1.ESLint.initialize(connection, documents, inferFilePath, loadNodeModule);
eslint_1.SaveRuleConfigs.inferFilePath = inferFilePath;
documents.onDidClose( /*#__PURE__*/function () {
  var _ref = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee(event) {
    var document, uri;
    return regeneratorRuntime.wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            document = event.document;
            uri = document.uri;
            eslint_1.ESLint.removeSettings(uri);
            eslint_1.SaveRuleConfigs.remove(uri);
            eslint_1.CodeActions.remove(uri);
            eslint_1.ESLint.unregisterAsFormatter(document);

          case 6:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  }));

  return function (_x) {
    return _ref.apply(this, arguments);
  };
}());

function environmentChanged() {
  eslint_1.ESLint.clearSettings();
  eslint_1.RuleSeverities.clear();
  eslint_1.SaveRuleConfigs.clear();
  eslint_1.ESLint.clearFormatters();
  connection.languages.diagnostics.refresh().catch(function () {
    connection.console.error('Failed to refresh diagnostics');
  });
}

var CommandIds;

(function (CommandIds) {
  CommandIds.applySingleFix = 'eslint.applySingleFix';
  CommandIds.applySuggestion = 'eslint.applySuggestion';
  CommandIds.applySameFixes = 'eslint.applySameFixes';
  CommandIds.applyAllFixes = 'eslint.applyAllFixes';
  CommandIds.applyDisableLine = 'eslint.applyDisableLine';
  CommandIds.applyDisableFile = 'eslint.applyDisableFile';
  CommandIds.openRuleDoc = 'eslint.openRuleDoc';
})(CommandIds || (CommandIds = {}));

connection.onInitialize(function (params, _cancel, progress) {
  var _clientCapabilities$t, _clientCapabilities$t2, _clientCapabilities$t3;

  progress.begin('Initializing ESLint Server');
  var syncKind = node_1.TextDocumentSyncKind.Incremental;
  clientCapabilities = params.capabilities;
  progress.done();
  var capabilities = {
    textDocumentSync: {
      openClose: true,
      change: syncKind,
      willSaveWaitUntil: false,
      save: {
        includeText: false
      }
    },
    workspace: {
      workspaceFolders: {
        supported: true
      }
    },
    executeCommandProvider: {
      commands: [CommandIds.applySingleFix, CommandIds.applySuggestion, CommandIds.applySameFixes, CommandIds.applyAllFixes, CommandIds.applyDisableLine, CommandIds.applyDisableFile, CommandIds.openRuleDoc]
    },
    diagnosticProvider: {
      identifier: 'eslint',
      interFileDependencies: false,
      workspaceDiagnostics: false
    }
  };

  if (((_clientCapabilities$t = clientCapabilities.textDocument) === null || _clientCapabilities$t === void 0 ? void 0 : (_clientCapabilities$t2 = _clientCapabilities$t.codeAction) === null || _clientCapabilities$t2 === void 0 ? void 0 : (_clientCapabilities$t3 = _clientCapabilities$t2.codeActionLiteralSupport) === null || _clientCapabilities$t3 === void 0 ? void 0 : _clientCapabilities$t3.codeActionKind.valueSet) !== undefined) {
    capabilities.codeActionProvider = {
      codeActionKinds: [node_1.CodeActionKind.QuickFix, "".concat(node_1.CodeActionKind.SourceFixAll, ".eslint")]
    };
  }

  return {
    capabilities: capabilities
  };
});
connection.onInitialized(function () {
  var _clientCapabilities$w, _clientCapabilities$w2, _clientCapabilities$w3;

  if (((_clientCapabilities$w = clientCapabilities.workspace) === null || _clientCapabilities$w === void 0 ? void 0 : (_clientCapabilities$w2 = _clientCapabilities$w.didChangeConfiguration) === null || _clientCapabilities$w2 === void 0 ? void 0 : _clientCapabilities$w2.dynamicRegistration) === true) {
    connection.onDidChangeConfiguration(function (_params) {
      environmentChanged();
    });
    void connection.client.register(node_1.DidChangeConfigurationNotification.type, undefined);
  }

  if (((_clientCapabilities$w3 = clientCapabilities.workspace) === null || _clientCapabilities$w3 === void 0 ? void 0 : _clientCapabilities$w3.workspaceFolders) === true) {
    connection.workspace.onDidChangeWorkspaceFolders(function (_params) {
      environmentChanged();
    });
  }
});
var emptyDiagnosticResult = {
  kind: node_1.DocumentDiagnosticReportKind.Full,
  items: []
};
connection.languages.diagnostics.on( /*#__PURE__*/function () {
  var _ref2 = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee2(params) {
    var document, settings, start, diagnostics, timeTaken, status, _iterator, _step, handler;

    return regeneratorRuntime.wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            document = documents.get(params.textDocument.uri);

            if (!(document === undefined)) {
              _context2.next = 3;
              break;
            }

            return _context2.abrupt("return", emptyDiagnosticResult);

          case 3:
            _context2.next = 5;
            return eslint_1.ESLint.resolveSettings(document);

          case 5:
            settings = _context2.sent;

            if (!(settings.validate !== settings_1.Validate.on || !eslint_1.TextDocumentSettings.hasLibrary(settings))) {
              _context2.next = 8;
              break;
            }

            return _context2.abrupt("return", emptyDiagnosticResult);

          case 8:
            _context2.prev = 8;
            start = Date.now();
            _context2.next = 12;
            return eslint_1.ESLint.validate(document, settings);

          case 12:
            diagnostics = _context2.sent;
            timeTaken = Date.now() - start;
            void connection.sendNotification(customMessages_1.StatusNotification.type, {
              uri: document.uri,
              state: customMessages_1.Status.ok,
              validationTime: timeTaken
            });
            return _context2.abrupt("return", {
              kind: node_1.DocumentDiagnosticReportKind.Full,
              items: diagnostics
            });

          case 18:
            _context2.prev = 18;
            _context2.t0 = _context2["catch"](8);

            if (settings.silent) {
              _context2.next = 44;
              break;
            }

            status = undefined;
            _iterator = _createForOfIteratorHelper(eslint_1.ESLint.ErrorHandlers.single);
            _context2.prev = 23;

            _iterator.s();

          case 25:
            if ((_step = _iterator.n()).done) {
              _context2.next = 32;
              break;
            }

            handler = _step.value;
            status = handler(_context2.t0, document, settings.library, settings);

            if (!status) {
              _context2.next = 30;
              break;
            }

            return _context2.abrupt("break", 32);

          case 30:
            _context2.next = 25;
            break;

          case 32:
            _context2.next = 37;
            break;

          case 34:
            _context2.prev = 34;
            _context2.t1 = _context2["catch"](23);

            _iterator.e(_context2.t1);

          case 37:
            _context2.prev = 37;

            _iterator.f();

            return _context2.finish(37);

          case 40:
            status = status || customMessages_1.Status.error;
            void connection.sendNotification(customMessages_1.StatusNotification.type, {
              uri: document.uri,
              state: status
            });
            _context2.next = 46;
            break;

          case 44:
            connection.console.info(eslint_1.ESLint.ErrorHandlers.getMessage(_context2.t0, document));
            void connection.sendNotification(customMessages_1.StatusNotification.type, {
              uri: document.uri,
              state: customMessages_1.Status.ok
            });

          case 46:
            return _context2.abrupt("return", emptyDiagnosticResult);

          case 47:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2, null, [[8, 18], [23, 34, 37, 40]]);
  }));

  return function (_x2) {
    return _ref2.apply(this, arguments);
  };
}());
connection.onDidChangeWatchedFiles( /*#__PURE__*/function () {
  var _ref3 = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee4(params) {
    return regeneratorRuntime.wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            // A .eslintrc has change. No smartness here.
            // Simply revalidate all file.
            eslint_1.RuleMetaData.clear();
            eslint_1.ESLint.ErrorHandlers.clearNoConfigReported();
            eslint_1.ESLint.ErrorHandlers.clearMissingModuleReported();
            eslint_1.ESLint.clearSettings(); // config files can change plugins and parser.

            eslint_1.RuleSeverities.clear();
            eslint_1.SaveRuleConfigs.clear();
            _context4.next = 8;
            return Promise.all(params.changes.map( /*#__PURE__*/function () {
              var _ref4 = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee3(change) {
                var fsPath, dirname, data, eslintClass;
                return regeneratorRuntime.wrap(function _callee3$(_context3) {
                  while (1) {
                    switch (_context3.prev = _context3.next) {
                      case 0:
                        fsPath = inferFilePath(change.uri);

                        if (!(fsPath === undefined || fsPath.length === 0 || (0, paths_1.isUNC)(fsPath))) {
                          _context3.next = 3;
                          break;
                        }

                        return _context3.abrupt("return");

                      case 3:
                        dirname = path.dirname(fsPath);

                        if (!dirname) {
                          _context3.next = 18;
                          break;
                        }

                        data = eslint_1.ESLint.ErrorHandlers.getConfigErrorReported(fsPath);

                        if (!(data !== undefined)) {
                          _context3.next = 18;
                          break;
                        }

                        _context3.next = 9;
                        return eslint_1.ESLint.newClass(data.library, {}, data.settings);

                      case 9:
                        eslintClass = _context3.sent;
                        _context3.prev = 10;
                        _context3.next = 13;
                        return eslintClass.lintText('', {
                          filePath: path.join(dirname, '___test___.js')
                        });

                      case 13:
                        eslint_1.ESLint.ErrorHandlers.removeConfigErrorReported(fsPath);
                        _context3.next = 18;
                        break;

                      case 16:
                        _context3.prev = 16;
                        _context3.t0 = _context3["catch"](10);

                      case 18:
                      case "end":
                        return _context3.stop();
                    }
                  }
                }, _callee3, null, [[10, 16]]);
              }));

              return function (_x4) {
                return _ref4.apply(this, arguments);
              };
            }()));

          case 8:
            connection.languages.diagnostics.refresh().catch(function () {
              connection.console.error('Failed to refresh diagnostics');
            });

          case 9:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4);
  }));

  return function (_x3) {
    return _ref3.apply(this, arguments);
  };
}());

var CodeActionResult = /*#__PURE__*/function () {
  function CodeActionResult() {
    _classCallCheck(this, CodeActionResult);

    this._actions = new Map();
  }

  _createClass(CodeActionResult, [{
    key: "get",
    value: function get(ruleId) {
      var result = this._actions.get(ruleId);

      if (result === undefined) {
        result = {
          fixes: [],
          suggestions: []
        };

        this._actions.set(ruleId, result);
      }

      return result;
    }
  }, {
    key: "fixAll",
    get: function get() {
      if (this._fixAll === undefined) {
        this._fixAll = [];
      }

      return this._fixAll;
    }
  }, {
    key: "all",
    value: function all() {
      var result = [];

      var _iterator2 = _createForOfIteratorHelper(this._actions.values()),
          _step2;

      try {
        for (_iterator2.s(); !(_step2 = _iterator2.n()).done;) {
          var actions = _step2.value;
          result.push.apply(result, _toConsumableArray(actions.fixes));
          result.push.apply(result, _toConsumableArray(actions.suggestions));

          if (actions.disable) {
            result.push(actions.disable);
          }

          if (actions.fixAll) {
            result.push(actions.fixAll);
          }

          if (actions.disableFile) {
            result.push(actions.disableFile);
          }

          if (actions.showDocumentation) {
            result.push(actions.showDocumentation);
          }
        }
      } catch (err) {
        _iterator2.e(err);
      } finally {
        _iterator2.f();
      }

      if (this._fixAll !== undefined) {
        result.push.apply(result, _toConsumableArray(this._fixAll));
      }

      return result;
    }
  }, {
    key: "length",
    get: function get() {
      var result = 0;

      var _iterator3 = _createForOfIteratorHelper(this._actions.values()),
          _step3;

      try {
        for (_iterator3.s(); !(_step3 = _iterator3.n()).done;) {
          var actions = _step3.value;
          result += actions.fixes.length;
        }
      } catch (err) {
        _iterator3.e(err);
      } finally {
        _iterator3.f();
      }

      return result;
    }
  }]);

  return CodeActionResult;
}();

var Changes = /*#__PURE__*/function () {
  function Changes() {
    _classCallCheck(this, Changes);

    this.values = new Map();
    this.uri = undefined;
    this.version = undefined;
  }

  _createClass(Changes, [{
    key: "clear",
    value: function clear(textDocument) {
      if (textDocument === undefined) {
        this.uri = undefined;
        this.version = undefined;
      } else {
        this.uri = textDocument.uri;
        this.version = textDocument.version;
      }

      this.values.clear();
    }
  }, {
    key: "isUsable",
    value: function isUsable(uri, version) {
      return this.uri === uri && this.version === version;
    }
  }, {
    key: "set",
    value: function set(key, change) {
      this.values.set(key, change);
    }
  }, {
    key: "get",
    value: function get(key) {
      return this.values.get(key);
    }
  }]);

  return Changes;
}();

var CommandParams;

(function (CommandParams) {
  function create(textDocument, ruleId, sequence) {
    return {
      uri: textDocument.uri,
      version: textDocument.version,
      ruleId: ruleId,
      sequence: sequence
    };
  }

  CommandParams.create = create;

  function hasRuleId(value) {
    return value.ruleId !== undefined;
  }

  CommandParams.hasRuleId = hasRuleId;
})(CommandParams || (CommandParams = {}));

var changes = new Changes();
var ESLintSourceFixAll = "".concat(node_1.CodeActionKind.SourceFixAll, ".eslint");
connection.onCodeAction( /*#__PURE__*/function () {
  var _ref5 = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee5(params) {
    var result, uri, textDocument, createCodeAction, getDisableRuleEditInsertionIndex, escapeStringRegexp, createDisableLineTextEdit, createDisableSameLineTextEdit, createDisableFileTextEdit, getLastEdit, settings, problems, only, isSource, isSourceFixAll, textDocumentIdentifier, edits, fixes, documentVersion, allFixableRuleIds, kind, _iterator4, _step4, _loop, sameProblems, _iterator5, _step5, editInfo, same;

    return regeneratorRuntime.wrap(function _callee5$(_context5) {
      while (1) {
        switch (_context5.prev = _context5.next) {
          case 0:
            getLastEdit = function _getLastEdit(array) {
              var length = array.length;

              if (length === 0) {
                return undefined;
              }

              return array[length - 1];
            };

            createDisableFileTextEdit = function _createDisableFileTex(textDocument, editInfo) {
              // If first line contains a shebang, insert on the next line instead.
              var shebang = textDocument.getText(node_1.Range.create(node_1.Position.create(0, 0), node_1.Position.create(0, 2)));
              var line = shebang === '#!' ? 1 : 0;
              var block = languageDefaults_1.default.getBlockComment(textDocument.languageId);
              return node_1.TextEdit.insert(node_1.Position.create(line, 0), "".concat(block[0], " eslint-disable ").concat(editInfo.ruleId, " ").concat(block[1]).concat(os_1.EOL));
            };

            createDisableSameLineTextEdit = function _createDisableSameLin(textDocument, editInfo) {
              var lineComment = languageDefaults_1.default.getLineComment(textDocument.languageId);
              var blockComment = languageDefaults_1.default.getBlockComment(textDocument.languageId);
              var currentLine = textDocument.getText(node_1.Range.create(node_1.Position.create(editInfo.line - 1, 0), node_1.Position.create(editInfo.line - 1, node_1.uinteger.MAX_VALUE)));
              var disableRuleContent;
              var insertionIndex; // Check if there's already a disabling comment. If so, we ignore the settings here
              // and use the comment style from that specific line.

              var matchedLineDisable = new RegExp("".concat(lineComment, " eslint-disable-line")).test(currentLine);
              var matchedBlockDisable = new RegExp("".concat(blockComment[0], " eslint-disable-line")).test(currentLine);

              if (matchedLineDisable) {
                disableRuleContent = ", ".concat(editInfo.ruleId);
                insertionIndex = getDisableRuleEditInsertionIndex(currentLine, lineComment);
              } else if (matchedBlockDisable) {
                disableRuleContent = ", ".concat(editInfo.ruleId);
                insertionIndex = getDisableRuleEditInsertionIndex(currentLine, blockComment);
              } else {
                // We're creating a new disabling comment.
                var commentStyle = settings.codeAction.disableRuleComment.commentStyle;
                disableRuleContent = commentStyle === 'line' ? " ".concat(lineComment, " eslint-disable-line ").concat(editInfo.ruleId) : " ".concat(blockComment[0], " eslint-disable-line ").concat(editInfo.ruleId, " ").concat(blockComment[1]);
                insertionIndex = node_1.uinteger.MAX_VALUE;
              }

              return node_1.TextEdit.insert(node_1.Position.create(editInfo.line - 1, insertionIndex), disableRuleContent);
            };

            createDisableLineTextEdit = function _createDisableLineTex(textDocument, editInfo, indentationText) {
              var lineComment = languageDefaults_1.default.getLineComment(textDocument.languageId);
              var blockComment = languageDefaults_1.default.getBlockComment(textDocument.languageId); // If the concerned line is not the first line of the file

              if (editInfo.line - 1 > 0) {
                // Check previous line if there is a eslint-disable-next-line comment already present.
                var prevLine = textDocument.getText(node_1.Range.create(node_1.Position.create(editInfo.line - 2, 0), node_1.Position.create(editInfo.line - 2, node_1.uinteger.MAX_VALUE))); // For consistency, we ignore the settings here and use the comment style from that
                // specific line.

                var matchedLineDisable = new RegExp("".concat(escapeStringRegexp(lineComment), " eslint-disable-next-line")).test(prevLine);

                if (matchedLineDisable) {
                  var insertionIndex = getDisableRuleEditInsertionIndex(prevLine, lineComment);
                  return node_1.TextEdit.insert(node_1.Position.create(editInfo.line - 2, insertionIndex), ", ".concat(editInfo.ruleId));
                }

                var matchedBlockDisable = new RegExp("".concat(escapeStringRegexp(blockComment[0]), " eslint-disable-next-line")).test(prevLine);

                if (matchedBlockDisable) {
                  var _insertionIndex = getDisableRuleEditInsertionIndex(prevLine, blockComment);

                  return node_1.TextEdit.insert(node_1.Position.create(editInfo.line - 2, _insertionIndex), ", ".concat(editInfo.ruleId));
                }
              } // We're creating a new disabling comment. Use the comment style given in settings.


              var commentStyle = settings.codeAction.disableRuleComment.commentStyle;
              var disableRuleContent;

              if (commentStyle === 'block') {
                disableRuleContent = "".concat(indentationText).concat(blockComment[0], " eslint-disable-next-line ").concat(editInfo.ruleId, " ").concat(blockComment[1]).concat(os_1.EOL);
              } else {
                // commentStyle === 'line'
                disableRuleContent = "".concat(indentationText).concat(lineComment, " eslint-disable-next-line ").concat(editInfo.ruleId).concat(os_1.EOL);
              }

              return node_1.TextEdit.insert(node_1.Position.create(editInfo.line - 1, 0), disableRuleContent);
            };

            escapeStringRegexp = function _escapeStringRegexp(value) {
              return value.replace(/[|{}\\()[\]^$+*?.]/g, '\\$&');
            };

            getDisableRuleEditInsertionIndex = function _getDisableRuleEditIn(line, commentTags) {
              var charIndex = line.indexOf('--');

              if (charIndex < 0) {
                if (typeof commentTags === 'string') {
                  return line.length;
                } else {
                  // commentTags is an array containing the block comment closing and opening tags
                  charIndex = line.indexOf(commentTags[1]);

                  while (charIndex > 0 && line[charIndex - 1] === ' ') {
                    charIndex--;
                  }
                }
              } else {
                while (charIndex > 1 && line[charIndex - 1] === ' ') {
                  charIndex--;
                }
              }

              return charIndex;
            };

            createCodeAction = function _createCodeAction(title, kind, commandId, arg, diagnostic) {
              var command = node_1.Command.create(title, commandId, arg);
              var action = node_1.CodeAction.create(title, command, kind);

              if (diagnostic !== undefined) {
                action.diagnostics = [diagnostic];
              }

              return action;
            };

            result = new CodeActionResult();
            uri = params.textDocument.uri;
            textDocument = documents.get(uri);

            if (!(textDocument === undefined)) {
              _context5.next = 13;
              break;
            }

            changes.clear(textDocument);
            return _context5.abrupt("return", result.all());

          case 13:
            _context5.next = 15;
            return eslint_1.ESLint.resolveSettings(textDocument);

          case 15:
            settings = _context5.sent;

            if (!(settings.validate !== settings_1.Validate.on || !eslint_1.TextDocumentSettings.hasLibrary(settings))) {
              _context5.next = 18;
              break;
            }

            return _context5.abrupt("return", result.all());

          case 18:
            problems = eslint_1.CodeActions.get(uri); // We validate on type and have no problems ==> nothing to fix.

            if (!(problems === undefined && settings.run === 'onType')) {
              _context5.next = 21;
              break;
            }

            return _context5.abrupt("return", result.all());

          case 21:
            only = params.context.only !== undefined && params.context.only.length > 0 ? params.context.only[0] : undefined;
            isSource = only === node_1.CodeActionKind.Source;
            isSourceFixAll = only === ESLintSourceFixAll || only === node_1.CodeActionKind.SourceFixAll;

            if (!(isSourceFixAll || isSource)) {
              _context5.next = 35;
              break;
            }

            if (!isSourceFixAll) {
              _context5.next = 33;
              break;
            }

            textDocumentIdentifier = {
              uri: textDocument.uri,
              version: textDocument.version
            };
            _context5.next = 29;
            return computeAllFixes(textDocumentIdentifier, AllFixesMode.onSave);

          case 29:
            edits = _context5.sent;

            if (edits !== undefined) {
              result.fixAll.push(node_1.CodeAction.create("Fix all fixable ESLint issues", {
                documentChanges: [node_1.TextDocumentEdit.create(textDocumentIdentifier, edits)]
              }, ESLintSourceFixAll));
            }

            _context5.next = 34;
            break;

          case 33:
            if (isSource) {
              result.fixAll.push(createCodeAction("Fix all fixable ESLint issues", node_1.CodeActionKind.Source, CommandIds.applyAllFixes, CommandParams.create(textDocument)));
            }

          case 34:
            return _context5.abrupt("return", result.all());

          case 35:
            if (!(problems === undefined)) {
              _context5.next = 37;
              break;
            }

            return _context5.abrupt("return", result.all());

          case 37:
            fixes = new eslint_1.Fixes(problems);

            if (!fixes.isEmpty()) {
              _context5.next = 40;
              break;
            }

            return _context5.abrupt("return", result.all());

          case 40:
            documentVersion = -1;
            allFixableRuleIds = [];
            kind = only !== null && only !== void 0 ? only : node_1.CodeActionKind.QuickFix;
            _iterator4 = _createForOfIteratorHelper(fixes.getScoped(params.context.diagnostics));

            try {
              _loop = function _loop() {
                var editInfo = _step4.value;
                documentVersion = editInfo.documentVersion;
                var ruleId = editInfo.ruleId;
                allFixableRuleIds.push(ruleId);

                if (eslint_1.Problem.isFixable(editInfo)) {
                  var workspaceChange = new node_1.WorkspaceChange();
                  workspaceChange.getTextEditChange({
                    uri: uri,
                    version: documentVersion
                  }).add(eslint_1.FixableProblem.createTextEdit(textDocument, editInfo));
                  changes.set("".concat(CommandIds.applySingleFix, ":").concat(ruleId), workspaceChange);
                  var action = createCodeAction(editInfo.label, kind, CommandIds.applySingleFix, CommandParams.create(textDocument, ruleId), editInfo.diagnostic);
                  action.isPreferred = true;
                  result.get(ruleId).fixes.push(action);
                }

                if (eslint_1.Problem.hasSuggestions(editInfo)) {
                  editInfo.suggestions.forEach(function (suggestion, suggestionSequence) {
                    var workspaceChange = new node_1.WorkspaceChange();
                    workspaceChange.getTextEditChange({
                      uri: uri,
                      version: documentVersion
                    }).add(eslint_1.SuggestionsProblem.createTextEdit(textDocument, suggestion));
                    changes.set("".concat(CommandIds.applySuggestion, ":").concat(ruleId, ":").concat(suggestionSequence), workspaceChange);
                    var action = createCodeAction("".concat(suggestion.desc, " (").concat(editInfo.ruleId, ")"), node_1.CodeActionKind.QuickFix, CommandIds.applySuggestion, CommandParams.create(textDocument, ruleId, suggestionSequence), editInfo.diagnostic);
                    result.get(ruleId).suggestions.push(action);
                  });
                }

                if (settings.codeAction.disableRuleComment.enable && ruleId !== eslint_1.RuleMetaData.unusedDisableDirectiveId) {
                  var _workspaceChange = new node_1.WorkspaceChange();

                  if (settings.codeAction.disableRuleComment.location === 'sameLine') {
                    _workspaceChange.getTextEditChange({
                      uri: uri,
                      version: documentVersion
                    }).add(createDisableSameLineTextEdit(textDocument, editInfo));
                  } else {
                    var lineText = textDocument.getText(node_1.Range.create(node_1.Position.create(editInfo.line - 1, 0), node_1.Position.create(editInfo.line - 1, node_1.uinteger.MAX_VALUE)));
                    var matches = /^([ \t]*)/.exec(lineText);
                    var indentationText = matches !== null && matches.length > 0 ? matches[1] : '';

                    _workspaceChange.getTextEditChange({
                      uri: uri,
                      version: documentVersion
                    }).add(createDisableLineTextEdit(textDocument, editInfo, indentationText));
                  }

                  changes.set("".concat(CommandIds.applyDisableLine, ":").concat(ruleId), _workspaceChange);
                  result.get(ruleId).disable = createCodeAction("Disable ".concat(ruleId, " for this line"), kind, CommandIds.applyDisableLine, CommandParams.create(textDocument, ruleId));

                  if (result.get(ruleId).disableFile === undefined) {
                    _workspaceChange = new node_1.WorkspaceChange();

                    _workspaceChange.getTextEditChange({
                      uri: uri,
                      version: documentVersion
                    }).add(createDisableFileTextEdit(textDocument, editInfo));

                    changes.set("".concat(CommandIds.applyDisableFile, ":").concat(ruleId), _workspaceChange);
                    result.get(ruleId).disableFile = createCodeAction("Disable ".concat(ruleId, " for the entire file"), kind, CommandIds.applyDisableFile, CommandParams.create(textDocument, ruleId));
                  }
                }

                if (settings.codeAction.showDocumentation.enable && result.get(ruleId).showDocumentation === undefined) {
                  if (eslint_1.RuleMetaData.hasRuleId(ruleId)) {
                    result.get(ruleId).showDocumentation = createCodeAction("Show documentation for ".concat(ruleId), kind, CommandIds.openRuleDoc, CommandParams.create(textDocument, ruleId));
                  }
                }
              };

              for (_iterator4.s(); !(_step4 = _iterator4.n()).done;) {
                _loop();
              }
            } catch (err) {
              _iterator4.e(err);
            } finally {
              _iterator4.f();
            }

            if (result.length > 0) {
              sameProblems = new Map(allFixableRuleIds.map(function (s) {
                return [s, []];
              }));
              _iterator5 = _createForOfIteratorHelper(fixes.getAllSorted());

              try {
                for (_iterator5.s(); !(_step5 = _iterator5.n()).done;) {
                  editInfo = _step5.value;

                  if (documentVersion === -1) {
                    documentVersion = editInfo.documentVersion;
                  }

                  if (sameProblems.has(editInfo.ruleId)) {
                    same = sameProblems.get(editInfo.ruleId);

                    if (!eslint_1.Fixes.overlaps(getLastEdit(same), editInfo)) {
                      same.push(editInfo);
                    }
                  }
                }
              } catch (err) {
                _iterator5.e(err);
              } finally {
                _iterator5.f();
              }

              sameProblems.forEach(function (same, ruleId) {
                if (same.length > 1) {
                  var sameFixes = new node_1.WorkspaceChange();
                  var sameTextChange = sameFixes.getTextEditChange({
                    uri: uri,
                    version: documentVersion
                  });
                  same.map(function (fix) {
                    return eslint_1.FixableProblem.createTextEdit(textDocument, fix);
                  }).forEach(function (edit) {
                    return sameTextChange.add(edit);
                  });
                  changes.set(CommandIds.applySameFixes, sameFixes);
                  result.get(ruleId).fixAll = createCodeAction("Fix all ".concat(ruleId, " problems"), kind, CommandIds.applySameFixes, CommandParams.create(textDocument));
                }
              });
              result.fixAll.push(createCodeAction("Fix all auto-fixable problems", kind, CommandIds.applyAllFixes, CommandParams.create(textDocument)));
            }

            return _context5.abrupt("return", result.all());

          case 47:
          case "end":
            return _context5.stop();
        }
      }
    }, _callee5);
  }));

  return function (_x5) {
    return _ref5.apply(this, arguments);
  };
}());
var AllFixesMode;

(function (AllFixesMode) {
  AllFixesMode["onSave"] = "onsave";
  AllFixesMode["format"] = "format";
  AllFixesMode["command"] = "command";
})(AllFixesMode || (AllFixesMode = {}));

function computeAllFixes(_x6, _x7) {
  return _computeAllFixes.apply(this, arguments);
}

function _computeAllFixes() {
  _computeAllFixes = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee8(identifier, mode) {
    var uri, textDocument, settings, filePath, problems, originalContent, start, _result, saveConfig, offRules, overrideConfig, _iterator6, _step6, ruleId;

    return regeneratorRuntime.wrap(function _callee8$(_context8) {
      while (1) {
        switch (_context8.prev = _context8.next) {
          case 0:
            uri = identifier.uri;
            textDocument = documents.get(uri);

            if (!(textDocument === undefined || identifier.version !== textDocument.version)) {
              _context8.next = 4;
              break;
            }

            return _context8.abrupt("return", undefined);

          case 4:
            _context8.next = 6;
            return eslint_1.ESLint.resolveSettings(textDocument);

          case 6:
            settings = _context8.sent;

            if (!(settings.validate !== settings_1.Validate.on || !eslint_1.TextDocumentSettings.hasLibrary(settings) || mode === AllFixesMode.format && !settings.format)) {
              _context8.next = 9;
              break;
            }

            return _context8.abrupt("return", []);

          case 9:
            filePath = inferFilePath(textDocument);
            problems = eslint_1.CodeActions.get(uri);
            originalContent = textDocument.getText();
            start = Date.now(); // Only use known fixes when running in onSave mode. See https://github.com/microsoft/vscode-eslint/issues/871
            // for details

            if (!(mode === AllFixesMode.onSave && settings.codeActionOnSave.mode === settings_1.CodeActionsOnSaveMode.problems)) {
              _context8.next = 19;
              break;
            }

            _result = problems !== undefined && problems.size > 0 ? new eslint_1.Fixes(problems).getApplicable().map(function (fix) {
              return eslint_1.FixableProblem.createTextEdit(textDocument, fix);
            }) : [];
            connection.tracer.log("Computing all fixes took: ".concat(Date.now() - start, " ms."));
            return _context8.abrupt("return", _result);

          case 19:
            if (!(filePath !== undefined && mode === AllFixesMode.onSave)) {
              _context8.next = 25;
              break;
            }

            _context8.next = 22;
            return eslint_1.SaveRuleConfigs.get(uri, settings);

          case 22:
            _context8.t0 = _context8.sent;
            _context8.next = 26;
            break;

          case 25:
            _context8.t0 = undefined;

          case 26:
            saveConfig = _context8.t0;
            offRules = saveConfig === null || saveConfig === void 0 ? void 0 : saveConfig.offRules;

            if (offRules !== undefined) {
              overrideConfig = {
                rules: Object.create(null)
              };
              _iterator6 = _createForOfIteratorHelper(offRules);

              try {
                for (_iterator6.s(); !(_step6 = _iterator6.n()).done;) {
                  ruleId = _step6.value;
                  overrideConfig.rules[ruleId] = 'off';
                }
              } catch (err) {
                _iterator6.e(err);
              } finally {
                _iterator6.f();
              }
            }

            return _context8.abrupt("return", eslint_1.ESLint.withClass( /*#__PURE__*/function () {
              var _ref7 = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee7(eslintClass) {
                var result, reportResults, fixedContent, diffs, _iterator7, _step7, diff;

                return regeneratorRuntime.wrap(function _callee7$(_context7) {
                  while (1) {
                    switch (_context7.prev = _context7.next) {
                      case 0:
                        // Don't use any precomputed fixes since neighbour fixes can produce incorrect results.
                        // See https://github.com/microsoft/vscode-eslint/issues/1745
                        result = [];
                        _context7.next = 3;
                        return eslintClass.lintText(originalContent, {
                          filePath: filePath
                        });

                      case 3:
                        reportResults = _context7.sent;
                        connection.tracer.log("Computing all fixes took: ".concat(Date.now() - start, " ms."));

                        if (Array.isArray(reportResults) && reportResults.length === 1 && reportResults[0].output !== undefined) {
                          fixedContent = reportResults[0].output;
                          start = Date.now();
                          diffs = (0, diff_1.stringDiff)(originalContent, fixedContent, false);
                          connection.tracer.log("Computing minimal edits took: ".concat(Date.now() - start, " ms."));
                          _iterator7 = _createForOfIteratorHelper(diffs);

                          try {
                            for (_iterator7.s(); !(_step7 = _iterator7.n()).done;) {
                              diff = _step7.value;
                              result.push({
                                range: {
                                  start: textDocument.positionAt(diff.originalStart),
                                  end: textDocument.positionAt(diff.originalStart + diff.originalLength)
                                },
                                newText: fixedContent.substr(diff.modifiedStart, diff.modifiedLength)
                              });
                            }
                          } catch (err) {
                            _iterator7.e(err);
                          } finally {
                            _iterator7.f();
                          }
                        }

                        return _context7.abrupt("return", result);

                      case 7:
                      case "end":
                        return _context7.stop();
                    }
                  }
                }, _callee7);
              }));

              return function (_x9) {
                return _ref7.apply(this, arguments);
              };
            }(), settings, overrideConfig !== undefined ? {
              fix: true,
              overrideConfig: overrideConfig
            } : {
              fix: true
            }));

          case 30:
          case "end":
            return _context8.stop();
        }
      }
    }, _callee8);
  }));
  return _computeAllFixes.apply(this, arguments);
}

connection.onExecuteCommand( /*#__PURE__*/function () {
  var _ref6 = _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee6(params) {
    var workspaceChange, commandParams, edits, textChange, url;
    return regeneratorRuntime.wrap(function _callee6$(_context6) {
      while (1) {
        switch (_context6.prev = _context6.next) {
          case 0:
            commandParams = params.arguments[0];

            if (!(params.command === CommandIds.applyAllFixes)) {
              _context6.next = 8;
              break;
            }

            _context6.next = 4;
            return computeAllFixes(commandParams, AllFixesMode.command);

          case 4:
            edits = _context6.sent;

            if (edits !== undefined && edits.length > 0) {
              workspaceChange = new node_1.WorkspaceChange();
              textChange = workspaceChange.getTextEditChange(commandParams);
              edits.forEach(function (edit) {
                return textChange.add(edit);
              });
            }

            _context6.next = 9;
            break;

          case 8:
            if ([CommandIds.applySingleFix, CommandIds.applyDisableLine, CommandIds.applyDisableFile].indexOf(params.command) !== -1) {
              workspaceChange = changes.get("".concat(params.command, ":").concat(commandParams.ruleId));
            } else if ([CommandIds.applySuggestion].indexOf(params.command) !== -1) {
              workspaceChange = changes.get("".concat(params.command, ":").concat(commandParams.ruleId, ":").concat(commandParams.sequence));
            } else if (params.command === CommandIds.openRuleDoc && CommandParams.hasRuleId(commandParams)) {
              url = eslint_1.RuleMetaData.getUrl(commandParams.ruleId);

              if (url) {
                void connection.sendRequest(customMessages_1.OpenESLintDocRequest.type, {
                  url: url
                });
              }
            } else {
              workspaceChange = changes.get(params.command);
            }

          case 9:
            if (!(workspaceChange === undefined)) {
              _context6.next = 11;
              break;
            }

            return _context6.abrupt("return", null);

          case 11:
            return _context6.abrupt("return", connection.workspace.applyEdit(workspaceChange.edit).then(function (response) {
              if (!response.applied) {
                connection.console.error("Failed to apply command: ".concat(params.command));
              }

              return null;
            }, function () {
              connection.console.error("Failed to apply command: ".concat(params.command));
              return null;
            }));

          case 12:
          case "end":
            return _context6.stop();
        }
      }
    }, _callee6);
  }));

  return function (_x8) {
    return _ref6.apply(this, arguments);
  };
}());
connection.onDocumentFormatting(function (params) {
  var textDocument = documents.get(params.textDocument.uri);

  if (textDocument === undefined) {
    return [];
  }

  return computeAllFixes({
    uri: textDocument.uri,
    version: textDocument.version
  }, AllFixesMode.format);
});
documents.listen(connection);
notebooks.listen(connection);
connection.listen();
connection.console.info("ESLint server running in node ".concat(process.version));
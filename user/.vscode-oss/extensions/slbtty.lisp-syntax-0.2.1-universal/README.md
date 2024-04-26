# Lisp-Syntax

> Minimum Lisp syntax for vscode

This extension stripped keyword highlights from the original extension and keep only minimum highlight for those reasons:

+ [Lisp family of languages](https://en.wikipedia.org/wiki/List_of_Lisp-family_programming_languages) have beautiful and structured syntax in natural. 
+ Lisp languages let the user to construct things as powerful as the language it self. Highlight some [special forms](https://github.com/norvig/paip-lisp/blob/main/docs/chapter1.md#13-special-forms) might be useful but they are mostly visual distractions.
+ VSCODE cannot load custom rc file or user config like Emacs or Vim. Thus, i have to publish this to microsoft server to enable those basic things.
+ To define VSCODE a file type called lisp and thus the built-in rainbow bracket can be used.

## License: MIT

The ancestor of this extension lives in

https://github.com/mattn/vscode-lisp

This extension use a file that bradrobertson's sublime-packages to enable syntax on vscode.

<https://github.com/bradrobertson/sublime-packages/tree/master/Lisp>

## Author

- Yasuhiro Matsumoto (a.k.a. mattn)
- Shenlebantongying (a.k.a. slbtty)

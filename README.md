Nim
===

The official Nim Programming Language plugin for Sublime Text.

Features
--------

* Syntax highlighting.
* Snippets.
* Automatic continuation of doc comments.

Installation
------------

1. Run `Package Control: Install Package` from the command palette.
2. Choose `Nim`.

It is also recommended to install [LSP-nimlangserver](https://packagecontrol.io/packages/LSP-nimlangserver)
to enjoy IDE-like features.

Settings
--------

See Preferences -> Package Settings -> Nim

Contributing
------------

Pull requests are welcome! See DEVELOPMENT.md for an overview of Nim's design.

Clone the repository in your Sublime package directory.

Install the [PackageDev](https://github.com/SublimeText/PackageDev).

Modify the `.YAML-tmLanguage` files and regenerate the `.tmLanguage` files
by summoning the command palette and selecting the `Convert (YAML, JSON, PLIST) to...`
command. Don't modify the `.tmLanguage` files, they will be overwritten!

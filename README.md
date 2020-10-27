## Introduction

A Haxe Syntax for [Sublime Text 3](http://www.sublimetext.com/3) based on [Haxe Bundle](https://github.com/clemos/haxe-sublime-bundle).

## Features

Unlike [Haxe Bundle](https://github.com/clemos/haxe-sublime-bundle), which tries to turn **Sublime Text** into full-featured IDE with code completion, builds inside editor and custom keyboard shortcuts, this package contains only syntax highlighter with some snippets.

### Removed

- Settings;
- Code completion;
- Code formatting;
- Custom commands;
- Custom keyboard shortcuts;
- Builds inside editor;
- Support for **erazor** (`.erazor`, `.ehtml`, `.erazor.html`);
- Support for **HSS** (`.hss`);
- Support for `NMML` (`.nmml`);

### Added and fixed

- **Haxe:** syntax highlighting fixed for `#elseif`;
- **Haxe:** syntax highlighting improved to support Haxe 4 features (maybe not all of them);
- **Haxe:** snippets reworked:
    - Whitespaces before and after brackets are hardcoded (instead of taken from the settings);
    - Lambda function (`() -> {}`) is used instead of anonimous function (`function () {}`) in `fun` snipped (former `f` snippet);
    - Snippets for functions and variables created from scratch to be more in my taste;
    - All other snippets slightly reworked;
- **Hxml:** syntax highlighting improved to support Haxe 4 features (maybe not all of them);

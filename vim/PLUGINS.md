# Vim Plugin User Manual

This guide covers the usage and shortcuts for the plugins configured in this dotfiles repository.

## 📦 Plugin Management (Vim-plug)

Plugins are managed using [vim-plug](https://github.com/junegunn/vim-plug).

- **Install Plugins:** Open Vim and run `:PlugInstall`
- **Update Plugins:** Run `:PlugUpdate`
- **Clean Unused Plugins:** Run `:PlugClean`
- **Check Status:** Run `:PlugStatus`

---

## 🔍 CtrlP (Fuzzy Finder)

_Fuzzy file, buffer, mru, tag, etc. finder._

- **Shortcut:** `Ctrl + P`
- **Usage:** Start typing to find a file. Use `Ctrl + j/k` to navigate results, `<Enter>` to open.
- **Switch Modes:** `Ctrl + f` and `Ctrl + b` to cycle between search modes (Files, Buffers, MRU).

---

## 🌳 NERDTree (File Explorer)

_Project drawer for easy file navigation._

- **Open/Close:** `Ctrl + n` (or `:NERDTreeToggle`)
- **Usage:**
  - `o`: Open file/directory.
  - `i`: Open in split.
  - `s`: Open in vertical split.
  - `t`: Open in new tab.
  - `R`: Refresh root directory.

---

## 🚀 ALE (Asynchronous Lint Engine)

_Real-time linting and fixing._

- **Gutter Signs:**
  - `>>`: Error
  - `--`: Warning
- **Shortcuts:**
  - `,an`: Jump to **n**ext error/warning.
  - `,ap`: Jump to **p**revious error/warning.
  - `,af`: Manually trigger **f**ixing (`:ALEFix`).
- **Commands:**
  - `:ALEInfo`: See active linters and their status.
- **Supported Linters/Fixers:**
  - **Python:** `ruff` (lint and fix), `ruff_format` (format)
  - **C/C++:** `clangd` (lint/LSP), `clang-format` (fix)
  - **Markdown:** `markdownlint` (lint, MD013 disabled), `prettier` (fix)

Configured fixers run automatically on save and manually with `,af`.
Prettier formats Markdown while preserving meaningful hard breaks.
Filetypes without an explicit fixer list use the fallback whitespace fixers.
Ruff fixes supported lint issues and formats valid Python; syntax errors still
need manual correction.

To verify this checkout without changing your HOME symlinks, start Vim with
`vim -u /Users/fei-mba/Docs/dotfiles/stow/vim/.vimrc your-file.md`
(use a `.py` file for Python). Existing Vim sessions keep their loaded settings;
check `:echo $MYVIMRC` to see which configuration they loaded.
Keep `markdownlint` as a linter only: ALE's Markdownlint fixer can return CLI
help text instead of corrected buffer contents.

---

## ⌨️ General Mappings (Leader = `,`)

- `,w`: Save file.
- `,bd`: Close current buffer (legacy mapping may discard unsaved changes).
- `,ba`: Close all buffers.
- `,ss`: Toggle spell checking.
- `,pp`: Toggle paste mode.
- `jk`: Escape (Insert mode).
- `<Space>`: Search forwards.
- `Ctrl + Space`: Search backwards.

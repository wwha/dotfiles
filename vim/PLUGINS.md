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
  - **Python:** `flake8` (lint, max-line-length=88), `black` (fix)
  - **C/C++:** `clangd` (lint/LSP), `clang-format` (fix)
  - **Shell:** `shellcheck` (lint)
  - **JavaScript:** `eslint` (lint)
  - **Markdown:** `markdownlint` (lint, MD013 disabled), `prettier` (fix)

---

## 🤖 Codeium (AI Autocomplete)

_Free AI coding assistant._

- **Accept Suggestion:** `Ctrl + g`
- **Next Suggestion:** `Ctrl + ;`
- **Previous Suggestion:** `Ctrl + ,`
- **Clear Suggestion:** `Ctrl + x`
- **Status:** Shown in the status line.

---

## ⌨️ General Mappings (Leader = `,`)

- `,w`: Save file.
- `,bd`: Close current buffer (safe).
- `,ba`: Close all buffers.
- `,ss`: Toggle spell checking.
- `,pp`: Toggle paste mode.
- `jk`: Escape (Insert mode).
- `<Space>`: Search forwards.
- `Ctrl + Space`: Search backwards.

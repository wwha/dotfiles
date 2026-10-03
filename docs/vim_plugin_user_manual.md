# Vim Plugin User Manual

This guide covers the usage and shortcuts for the plugins configured in this dotfiles repository.

## 📦 Plugin Management (Vim-plug)

Plugins are managed using [vim-plug](https://github.com/junegunn/vim-plug).

- **Install Plugins:** Open Vim and run `:PlugInstall`
- **Update Plugins:** Run `:PlugUpdate`
- **Clean Unused Plugins:** Run `:PlugClean`
- **Check Status:** Run `:PlugStatus`

---

## 🔍 fzf.vim (Files, Content, and Buffers)

The base fzf runtime and executable come from Homebrew; vim-plug installs
`junegunn/fzf.vim`. CtrlP is replaced. After installing, `:PlugClean` can remove
its unused checkout.

- `Ctrl-p` / `:Files`: Find files with fd, including hidden files but excluding
  `.git` and respecting ignore rules.
- `,rg` / `:Rg PATTERN`: Search file contents with ripgrep, then select a match
  and open its file at the matching line. Ripgrep keeps its normal ignore and
  hidden-file behavior.
- `,b` / `:Buffers`: Select an open buffer.
- Inside the picker, Enter opens the selection; Ctrl-x, Ctrl-v, and Ctrl-t open
  it in a split, vertical split, or tab. Esc cancels.

Start Vim from the project directory to search that project. Preview uses the
plugin's default behavior; bat is optional and is not required by this setup.

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

Only explicitly configured linters run; unlisted filetypes do not activate
automatic linting. Configured fixers run automatically on save and manually
with `,af`.
Prettier formats Markdown while preserving meaningful hard breaks.
Filetypes without an explicit fixer list are not changed automatically.
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
- `,bd`: Close current buffer while retaining the window; unsaved changes remain protected.
- `,ba`: Close all buffers.
- `,tl`: Return to the last tab; if its remembered window was closed, do nothing.
- Visual `*` / `#`: Search the selection without replacing yank registers.
- `,ss`: Toggle spell checking.
- `,pp`: Toggle paste mode.
- `jk`: Escape (Insert mode).
- `<Space>`: Search forwards.
- `Ctrl + Space`: Search backwards.

## Vim and tmux navigation

Install `christoomey/vim-tmux-navigator` with `:PlugInstall` (or the dependency
installation command). Use `Ctrl-h/j/k/l` to move left/down/up/right through Vim
splits and then into an adjacent tmux pane. `Ctrl-\` returns to the previous
split/pane. In a zoomed tmux pane, navigation stays inside Vim. In a shell,
`Ctrl-a Ctrl-l` sends the original clear-screen key.

Use tmux windows for separate tasks and Vim buffers/splits for related files;
keep tmux panes for a nearby shell or test output when useful. Navigation does
not save modified buffers automatically.

## Clipboard over SSH

In Vim, `,y` copies the current line in Normal mode or the selected text in Visual
mode to the attached terminal's clipboard via OSC 52. Ordinary `y` remains a Vim
register operation. In tmux copy-mode (`Ctrl-a [`), select with `v` and copy with
`y` or Enter; mouse selection also copies. Use the client's normal paste action
to paste into Vim, and `Ctrl-a ]` to paste the tmux buffer into a pane. OSC 52
sets the clipboard; it does not read clipboard contents back into Vim.

The iTerm2 client must permit applications to access the clipboard (Preferences
or Settings → General → Selection). Remote `pbcopy` is not used. tmux allows
passthrough for Vim's explicitly generated OSC 52 sequence and uses
`set-clipboard external` for its own selections.

## Terminal fzf shortcuts

In iTerm2, `Alt-c` requires the active profile's Option key mapping to send
`Esc+`: open **Settings → Profiles → Keys** and set the left or right Option
key you use (or both) to `Esc+`. This is profile-specific. With that setting,
Option-c sends the Esc-c sequence used by fzf's directory picker.

## Terminal colors and recovery

The shared configuration targets iTerm2 with `xterm-256color` outside tmux,
`tmux-256color` inside tmux, and RGB color enabled in tmux and Vim. Every host
running applications with that TERM needs the corresponding terminfo entry;
check with `infocmp tmux-256color`. Apple Terminal's color capabilities differ;
do not assume its `xterm-256color` value implies RGB support.

The shared `xterm-256color:RGB` override targets the verified iTerm2 client;
it also matches other clients advertising that TERM, so use this configuration
with iTerm2 for RGB support. Inside tmux, applications see `tmux-256color`.

tmux forwards focus events to Vim so its existing `FocusGained` handler can
check for external file changes. After enabling this option, detach and attach
the client again; with automatic SSH tmux attachment, reconnect SSH. Esc timing
uses tmux's default rather than a custom override.

Vim keeps swap files and write-backup protection; persistent undo is not enabled. Display wrapping is enabled,
while the general `textwidth=0` avoids inserting hard breaks; filetype or project
settings and configured formatters may specify their own formatting width.


## Configuration behavior

The configuration inherits the shell locale and uses filetype indentation with
a four-space fallback. `softtabstop=-1` follows `shiftwidth` when a filetype
changes its indentation width. Automatic title templates and the separate
whitespace-trimming hook are removed; use project templates and the configured
formatters instead. New Shell, Python, and C++ files remain empty; no shebang
or other template content is inserted automatically.

Configuration autocommands use named groups, so sourcing the same configuration
again does not accumulate copies. After upgrading from the older ungrouped
configuration, restart Vim once to discard its previously registered hooks.
`,bd` refuses modified buffers and replaces a closed buffer in every displaying
window, preserving the split layout.

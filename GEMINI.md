# Project Context: Dotfiles Configuration

This repository contains personal configuration files (dotfiles) and management scripts designed for consistent development environment setup across macOS and Linux.

## Project Overview
- **Purpose:** Centralized management of shell, editor, and tool configurations.
- **Key Technologies:** Zsh (primary shell), Vim (primary editor), Tmux (terminal multiplexer), Git (version control), Homebrew (macOS package manager).
- **Architecture:** Configuration files are stored in subdirectories and symlinked to the user's home directory (`$HOME`) via an installation script.

## Key Files & Directories
- **`install.sh`**: The main setup script. It installs dependencies (Homebrew on macOS), configures Oh-My-Zsh, Vim-plug, and creates all necessary symlinks.
- **`backup.sh`**: Provides backup and recovery functionality for the dotfiles themselves.
- **`zsh/zshrc`**: Zsh configuration using Oh-My-Zsh. Includes plugins like `git`, `z`, `zsh-autosuggestions`, `vi-mode`, and `zsh-syntax-highlighting`. It also handles automatic Tmux attachment.
- **`vim/vimrc`**: Comprehensive Vim configuration forked from `amix/vimrc`. Uses `vim-plug` for plugin management (`CtrlP`, `Codeium`). Leader key is set to `,`.
- **`tmux/tmux.conf`**: Terminal multiplexer configuration.
- **`git/`**: Contains `git-config` (with local override support via `.gitconfig.local`) and a template directory for hooks (e.g., trailing whitespace check) and global ignore patterns.
- **`scripts/`**: A collection of utility scripts. `new-script.sh` is a helper to create new scripts using a standardized template.

## Usage & Operations

### Installation
To set up a new machine:
```bash
./install.sh
```
This script will:
1. Detect the OS (macOS or Linux).
2. Install missing core packages (Git, Vim, Tmux, Zsh).
3. Set up Oh-My-Zsh and custom plugins.
4. Configure Git with a local identity file.
5. Create symlinks for all configuration files.
6. Install Vim plugins via Vim-plug.

**Safety Features:**
- **Automatic Backups:** If a file or directory already exists at a target symlink location (and is not a symlink), it is automatically backed up to `~/.dotfiles_backups/` before being replaced.
- **Remote Execution Warnings:** The script provides clear warnings before downloading and executing scripts from remote sources (Oh-My-Zsh, Homebrew, Vim-plug).

### Script Management
Create new utility scripts with the standardized template:
```bash
new-script <name> "Optional description"
```
Scripts are stored in `scripts/` and symlinked to `~/.local/bin/`.

**Security Features:**
- **Input Sanitization:** Script descriptions are sanitized to prevent shell and `sed` injection attacks.
- **Safe Delimiters:** Uses robust delimiters in `sed` commands to handle complex input safely.

### Backup and Recovery
Manage dotfiles versions:
- `backup.sh -b`: Create a timestamped backup of current dotfiles.
- `backup.sh -r`: Restore from a previous backup.
- `backup.sh -l`: List available backups.

## Development Conventions
- **Shell Scripts:** Use `zsh` as the interpreter with strict mode (`set -euo pipefail`).
- **Git Hooks:** A pre-commit hook is used to prevent trailing whitespace in non-markdown files.
- **Local Overrides:** Machine-specific settings should be placed in `~/.gitconfig.local` or `~/.api_keys` to avoid committing sensitive or specific data.
- **Vim Bindings:** Leader is `,`. Use `jk` in insert mode for `<Esc>`.
- **Security First:** Always prioritize non-destructive operations and validated inputs in automated scripts.

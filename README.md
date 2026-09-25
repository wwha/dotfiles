# Dotfiles Configuration

## Directory Structure
```
dotfiles/
├── git/
│   ├── git-config
│   └── git-template/
│       ├── commit-template
│       ├── gitignore
│       └── hooks/
│           ├── post-commit
│           ├── pre-commit
│           └── prepare-commit-msg
├── scripts/
│   ├── new-script.sh
│   ├── script-template.sh
│   └── set-wifi-dns.sh
├── ssh/
│   └── ssh-config
├── tmux/
│   └── tmux.conf
├── vim/
│   └── vimrc
├── zsh/
│   └── zshrc
├── backup.sh
├── install.sh
├── LICENSE
└── README.md
```

## Overview
This repository contains my personal dotfiles and configuration management system, designed to streamline development environments and ensure consistent setup across machines.

## Git Configuration

### Pre-commit Hook
- Located at `git/git-template/hooks/pre-commit`
- Automatically checks and removes trailing whitespace from staged files except for:
    - Markdown files
### Gitignore
- Defines global ignore patterns for version control
- Prevents committing unnecessary files like:
  - System files (`.DS_Store`)
  - IDE-specific files
  - Temporary files
  - Dependency directories
## Scripts
- Collection of shell scripts for various tasks
- Use `new-script <name> <description>` to create a new script
## Tmux

## Vim
- Forked from https://github.com/amix/vimrc.
- Uses ALE (Asynchronous Lint Engine) for real-time linting.
  - **`.env` Exclusion**: `.env` files are excluded from linting using `g:ale_pattern_options` to prevent `shellcheck` from displaying noisy warnings (e.g., about missing shebangs or variable exports).

## Zsh

## Installation

### Setup Script
```bash
# Clone the dotfiles repository
git clone git@github.com:wwha/dotfiles.git

# Run installation script and create symlinks to the dotfiles
./install.sh

# Run backup script
./backup.sh
```

## Customization
- Fork this repository
- Modify configurations to suit your workflow
- Add personal customizations
- Consider contributing back to the community

## Security
- Never commit sensitive information
- Use environment variables for secrets
- Regularly update and audit configurations

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push and create a pull request

## License
[MIT]


## Supported platform and recovery

Personal installation supports **macOS only**. Run `./install.sh --help` or
`./install.sh --version` without changing the machine. Installation is interactive;
existing identity and local override files are preserved. Review installation
before running it: it installs packages and links configuration into your HOME.
Run `:PlugInstall` in Vim after installation to install editor plugins.

`./backup.sh -b` creates a uniquely named repository backup under
`~/dotfiles_backup`. `./backup.sh -r` asks for a backup directory name and first
saves current files in a `pre-recovery-*` directory. It then overlays the backup,
preserving `.git` and additional files. This is not an exact mirror restore.
If a restore fails partway through, use the printed pre-recovery backup to recover.
Backups may contain ignored local files: keep them private and outside the repository.

## Checks and cloud workflow

```sh
zsh tests/check.zsh --static  # Cloud: Zsh syntax and Git config parsing
zsh tests/check.zsh --all     # macOS: also run isolated behavior tests
```

Behavior tests use temporary directories and substitute external commands. They
verify file operations without installing packages or changing real system
settings. They do not validate live Homebrew downloads or a complete new-Mac setup.
GitHub Actions runs the `macos-checks` job on PRs and pushes to `main`.

In Codex Cloud, create an environment for `wwha/dotfiles` with `main` as its base.
Use this setup script to prepare the Linux development container:

```sh
set -eu
if ! command -v zsh >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y zsh
fi
```

Leave agent internet access off. No personal secrets, dotfiles installation, or
Git hook installation is needed. Cloud edits and runs static checks; macOS CI
runs behavior tests. Linux personal installation is unsupported.

After the CI workflow has run successfully, configure protection for `main`:

- Require a pull request and the `macos-checks` status check.
- Require the branch to be up to date before merging.
- Apply protection to administrators; disallow force pushes and branch deletion.
- Do not require another reviewer's approval (this is a single-maintainer repo).
- Keep auto-merge disabled and retain any existing stricter protections.

Start a small README task in the Cloud environment, review its diff, and create
its PR (using the task's PR button if needed). Confirm `macos-checks` passes before
manually merging. This workflow requires no local computer or self-hosted runner
online. Updating and installing configuration on your Mac remains a separate,
manual operation. Local unpushed commits are unavailable to Cloud.

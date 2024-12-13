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


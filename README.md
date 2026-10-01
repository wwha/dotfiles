# Personal macOS dotfiles

This public repository manages shared preferences for the owner's Apple Silicon
Macs. Git synchronizes committed configuration; GNU Stow links it into `$HOME`.
The repository is personal-use software, not a general macOS installer.

Keep credentials, private SSH keys, internal hosts and network details, work
identity, local overrides, caches and application data outside Git. Use a password
manager for secrets that need to move between devices. Generate SSH keys per Mac.
Never treat `.gitignore` as a substitute for checking the staged diff and history.

## New Mac

Install Homebrew and GNU Stow, clone this repository to a permanent location, and
review the commands before running them:

```sh
git clone git@github.com:wwha/dotfiles.git
cd dotfiles
./install.sh --dry-run
./install.sh
./install.sh deps
```

The default Stow packages are `zsh`, `git`, `vim` and `tmux`. SSH is opt-in:

```sh
./install.sh --dry-run --ssh
./install.sh --ssh
```

Stow uses explicit source and target paths with `--no-folding`, leaving HOME
directories available for private files. Correct links are left alone. A preview
lists conflicts; installation stops without changing anything unless `--backup`
is explicit. Backups go under a private `~/.dotfiles_backups` directory. Review
each path and keep backups outside the repository.

## Dependencies and updates

`install.sh deps` installs missing Homebrew formulae from the curated Brewfile and
does not upgrade packages already installed. `install.sh update` updates
Homebrew formulae, Oh My Zsh when present, and Vim plugins when vim-plug is
installed. Vim's plugin declarations use upstream's latest versions. Neither
command links configuration; linking does not download software.

The Brewfile contains command-line tools used by the shared configurations and
their checks. It is a selected list, not a snapshot of the machine or a version
lock. macOS's built-in Zsh is used. Homebrew LLVM is keg-only, so its commands
are not linked into Homebrew's shared `bin` directory. The shared Zsh config
adds LLVM's `bin` directory to `PATH` when LLVM is installed.
Vim plugin details are in [the Vim guide](vim/PLUGINS.md).

## Shared and private settings

Zsh loads the common Conda and NVM initializers when installed in their
conventional locations, keeps the Tailscale command alias, and loads the manual
Rime update helper. Rime updates do not run at shell startup.

Git identity is private and required. Set it in `~/.gitconfig.local`; shared Git
configuration uses `user.useConfigOnly` so a commit fails until name and email are
configured. GitHub users can choose their GitHub noreply address. SSH private keys
are generated per device; private host entries go in `~/.ssh/config.local`.

Local files are optional and must not be copied into this repository:

| File | Purpose |
| --- | --- |
| `~/.gitconfig.local` | Git identity and private Git settings |
| `~/.ssh/config.local` | Private hosts and per-device SSH settings |
| `~/.api_keys` | Private secrets, if used by local shell configuration |

The legacy `new-script` and `script-template` tools are no longer part of the
default setup. During the first migration, existing links remain available until
you complete the device migration. Move `set-wifi-dns` to `~/.local/bin/` if you
still need it; it is device-specific and is not linked by Stow. Review its help
and provide network values locally.

## Sync and recovery

On each Mac, review local changes, commit and push; on another Mac, review its
changes, pull, then run `install.sh` after adding or removing package paths.
There is no background synchronization. Resolve concurrent edits through Git.

Git stores committed shared configuration only. Keep a separate private backup
for local overrides, credentials, uncommitted work and other HOME data. The
legacy `backup.sh` remains during the migration phase; it snapshots repository
files, including ignored files, so its output must stay private. Installer
conflict backups preserve displaced filesystem objects, but do not copy the
contents behind symlinks.

## Security checks

Gitleaks scans staged changes before commits and scans the full Git history in
GitHub Actions. Enable GitHub push protection for the repository as an additional
credential check. These tools do not replace manual review for internal hostnames,
addresses, paths or identity information. If a real credential appears in Git,
revoke or rotate it first, then clean the history.

## Verification and contribution

```sh
zsh tests/check.zsh --static  # syntax and Git configuration parsing
zsh tests/check.zsh --all     # macOS isolated behavior tests
```

Never test installation or restoration against your real HOME. Behavior tests
use temporary directories and command substitutes. Cloud runs static checks;
macOS CI runs the behavior suite. Follow the repository's branch-protection
workflow below before merging changes.

In Codex Cloud, create an environment for `wwha/dotfiles` with `main` as its base.
Use this setup script to prepare the Linux development container:

```sh
set -eu
if ! command -v zsh >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y zsh
fi
```

Leave agent internet access off. No personal secrets or dotfiles installation is
needed. Cloud runs static checks only; passing them does not establish macOS
behavior. Before merging, wait for GitHub's `macos-checks` job to succeed.

After CI succeeds, configure protection for `main`: require a pull request and
`macos-checks`, require the branch to be up to date, apply protection to
administrators, disallow force pushes and branch deletion, and keep auto-merge
disabled. Do not require another reviewer's approval for this single-maintainer
repository. Retain any stricter existing protection.

## License

[MIT](LICENSE). Vim configuration derives from [amix/vimrc](https://github.com/amix/vimrc).

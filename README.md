# Personal macOS dotfiles

Shared Zsh, Vim, tmux, Git and SSH configuration, installed with symlinks.
Personal installation supports **macOS only**; Linux is a development environment.

**Existing users:** read [the compatibility migration guide](docs/migration.md)
before updating an active checkout or running installation. A Git pull in a
checkout linked from HOME can activate changes immediately. Merging a PR and
activating it on a Mac are separate operations.

## Installation on a new Mac

Clone into a permanent location. Review the scripts before running them:

```sh
git clone git@github.com:wwha/dotfiles.git
cd dotfiles
./install.sh --dry-run  # Preview links and conflicts; writes nothing
./install.sh            # Offline; stops if any target would be displaced
```

Correct links are left alone. Conflicts stop the entire link operation before any
changes. To explicitly displace conflicts into a private backup directory, review
the preview and pass `--backup`. SSH configuration is opt-in with `--ssh`; review
`ssh/ssh-config` before linking it. The installer never overwrites `*.local` files.

Fresh installations create `~/.git-template` with only an ignore file and commit
message template. Existing template links, files and hooks are preserved; missing
ignore/commit-template entries in a real directory are filled on rerun. No scripts
from `scripts/` are automatically installed.

## Optional dependency setup

Install [Homebrew](https://brew.sh) and put it on PATH following its installer
instructions. Then, explicitly run:

```sh
./install-deps.sh
```

This runs `brew bundle --file=Brewfile`. It preserves an existing `.zshrc`, does
not change the login shell, and does not link configuration. Homebrew may install
or upgrade listed packages; the Brewfile is not a version lock or whole-machine
restore. It does not execute remote shell installers or clone floating branches.
Vim plugins remain an explicit action inside Vim: review the `Plug` declarations,
then run `:PlugInstall`. Basic Vim settings load without vim-plug.

LLVM is keg-only. If Vim needs its `clangd` and `clang-format`, add the following
to `~/.zshrc.local` after dependency setup:

```zsh
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

ESLint remains a project-provided dependency. Conda, NVM, Rime and Tailscale
are machine-specific and are not initialized by the shared shell config.

## Local configuration

These files stay outside Git and are never overwritten by the installer:

| File | Purpose |
| --- | --- |
| `~/.gitconfig.local` | Git identity and overrides; included after shared defaults |
| `~/.ssh/config.local` | Private hosts and per-machine SSH settings |
| `~/.zshrc.local` | Shell overrides, loaded after existing initialization |
| `~/.vimrc.local` | Vim overrides, loaded last |
| `~/.tmux.conf.local` | tmux overrides, loaded last |
| `~/.api_keys` | Private secrets file; source it from `~/.zshrc.local` if needed |

For a fresh Git identity, use `git config --file ~/.gitconfig.local user.name`
and `git config --file ~/.gitconfig.local user.email` with your values, then
`chmod 600 ~/.gitconfig.local`. Local files need not exist until needed.

Machine-specific initialization, automatic tmux startup and the Rime prompt have
been removed from shared startup. Move needed initialization into local files.
Vim swap/recovery stays enabled; save-time formatting, new-file templates and
OSC52 clipboard writes are opt-in through `~/.vimrc.local`. See
[Vim plugin usage](vim/PLUGINS.md).

Example local Zsh settings:

```zsh
# ~/.zshrc.local; enable only the tools installed on this Mac.
export NVM_DIR="$HOME/.nvm"
[[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"
[[ -r "$HOME/.api_keys" ]] && source "$HOME/.api_keys"
# Uncomment if you use Conda installed at this path:
# eval "$($HOME/miniconda3/bin/conda shell.zsh hook)"
```

Manual Rime update, when needed: `source /path/to/dotfiles/zsh/rime-ice-update.zsh`
then run `rime_ice_update`. The helper is no longer sourced automatically.

`scripts/set-wifi-dns.sh` requires explicit network values. Review `--help` and
provide the intended interface, IP, router and DNS addresses; it does not contain
the original owner's network settings.

Bun initialization is no longer part of shared configuration. Bun itself is not
uninstalled, but a new terminal may no longer find `bun` or `bunx` if they are only
in `~/.bun/bin`. To opt in on a particular Mac, add this to `~/.zshrc.local`:

```zsh
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
[ -s "$BUN_INSTALL/_bun" ] && source "$BUN_INSTALL/_bun"
```

ShellCheck is no longer installed or invoked by this repository. Shell ALE
linters are disabled; Zsh syntax checks remain. Existing ShellCheck installations
and hooks already copied into other projects are not modified.

## Recovery and retained legacy tools

Git stores **committed shared configuration**, not unsaved edits or private files.
Use a separate, verified private backup for local overrides, credentials, other
HOME data and uncommitted work. This repository does not configure or verify a
system backup. Installer conflict backups preserve displaced objects, but are
not complete machine backups and do not snapshot the targets of symlinks.

`backup.sh`, `scripts/` and `git/git-template/hooks/` remain for existing users
until migration is confirmed. `backup.sh -b` snapshots the working directory
under `~/dotfiles_backup`, excluding `.git`; `-r` saves a `pre-recovery-*` copy
then overlays the selected snapshot. It preserves extra files and Git metadata,
but does not back up HOME's identity or SSH files. Snapshots may include ignored
private files; keep them private. Existing backups are never deleted by setup.

The retained network script changes IP settings as well as DNS when explicitly
invoked. The retained Git hooks may edit working files, alter commit messages and notify the desktop.
Neither is run as part of installation or verification against the real HOME.
Migration and per-file rollback steps are in [the guide](docs/migration.md).

## Checks and cloud workflow

```sh
zsh tests/check.zsh --static  # Cloud: Zsh syntax and Git config parsing
zsh tests/check.zsh --all     # macOS: also run isolated behavior tests
```

Behavior tests use temporary directories and substitute external commands. They
verify file operations without installing packages or changing real system
settings. The tmux test uses a private socket and requires tmux (3.2 or newer)
and permission to create Unix sockets; CI installs tmux if missing. Tests do not
validate live Homebrew downloads or a complete new-Mac setup.
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
Git hook installation is needed. Cloud runs static checks only; passing them does
not mean the macOS behavior tests passed. Before merging, wait for GitHub's
`macos-checks` job to succeed. Linux personal installation is unsupported.

After the CI workflow has run successfully, configure protection for `main`:

- Require a pull request and the `macos-checks` status check.
- Require the branch to be up to date before merging.
- Apply protection to administrators; disallow force pushes and branch deletion.
- Do not require another reviewer's approval (this is a single-maintainer repo).
- Keep auto-merge disabled and retain any existing stricter protections.

Start a small README task in the Cloud environment, review its diff, and create
its PR (using the task's PR button if needed). This workflow requires no local
computer or self-hosted runner online. Updating and installing configuration on
your Mac remains a separate, manual operation. Local unpushed commits are
unavailable to Cloud.

## License

[MIT](LICENSE). Vim configuration derives from [amix/vimrc](https://github.com/amix/vimrc).

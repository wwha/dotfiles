# Personal macOS dotfiles

This public repository manages shared preferences for the owner's Apple Silicon
Macs. Git synchronizes committed configuration; GNU Stow links it into `$HOME`.
The repository is personal-use software, not a general macOS installer.

Keep credentials, private SSH keys, internal hosts and network details, work
identity, local overrides, caches and application data outside Git. Use a password
manager for secrets that need to move between devices. Generate SSH keys per Mac.
Never treat `.gitignore` as a substitute for checking the staged diff and history.

## New Mac

Install Homebrew, clone this repository to a permanent location, and
review the commands before running them:

```sh
git clone git@github.com:wwha/dotfiles.git
cd dotfiles
./install.sh deps
./install.sh --dry-run
./install.sh
```

The default Stow packages are `zsh`, `git`, `vim` and `tmux`. SSH is opt-in:

```sh
./install.sh --dry-run --ssh
./install.sh --ssh
```

Dependency setup installs GNU Stow and uv along with the other declared tools.
It also prepares Oh My Zsh, its custom plugins, vim-plug and Vim plugins before
linking. Git identity and private SSH settings still require manual setup.

Stow uses explicit source and target paths with `--no-folding`, leaving HOME
directories available for private files. Correct links are left alone. A preview
lists conflicts; installation stops without changing anything unless `--backup`
is explicit. Backups go under a private `~/.dotfiles_backups` directory. Review
each path and keep backups outside the repository.

## Dependencies and updates

`install.sh deps` installs missing Homebrew formulae from the curated Brewfile and
does not upgrade packages already installed. `install.sh update` updates
Homebrew formulae, Oh My Zsh and its Git-installed custom plugins when present,
and Vim plugins when vim-plug is
installed. Vim's plugin declarations use upstream's latest versions. Neither
command links configuration; linking does not download software.

`deps` clones `zsh-users/zsh-autosuggestions` and
`zsh-users/zsh-syntax-highlighting` from GitHub into
`${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins` when absent, preserving existing
installations. Oh My Zsh loads both through `plugins`, with syntax highlighting
last. `update` uses `git pull --ff-only` for existing plugin Git checkouts.

The Brewfile contains command-line tools used by the shared configurations and
their checks. It is a selected list, not a snapshot of the machine or a version
lock. macOS's built-in Zsh, Git and Vim are used. Homebrew LLVM is keg-only, so its commands
are not linked into Homebrew's shared `bin` directory. The shared Zsh config
adds LLVM's `bin` directory to `PATH` and keeps PATH entries unique.
Vim plugin details are in [the Vim guide](docs/vim_plugin_user_manual.md).

## Shared and private settings

Oh My Zsh lazily loads NVM from `~/.nvm/nvm.sh` on the first `nvm`, `node`,
`npm`, or other supported Node command. Node shebang scripts do not trigger
these shell wrappers. Zsh keeps the Tailscale command alias. zoxide provides `z` for directory jumping, replacing the Oh My
Zsh `z` plugin. Oh My Zsh manages completion initialization. Conda and the Rime
update helper are no longer initialized by the shared configuration.

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

The legacy `new-script`, `script-template` and `set-wifi-dns` tools have been
removed. Set network preferences directly in macOS System Settings.

## Sync and recovery

On each Mac, review local changes, commit and push; on another Mac, review its
changes, pull, then run `install.sh` after adding or removing package paths.
There is no background synchronization. Resolve concurrent edits through Git.

Git stores committed shared configuration only. Keep a separate private backup
for local overrides, credentials, uncommitted work and other HOME data. Installer
conflict backups preserve displaced filesystem objects, but do not copy the
contents behind symlinks.

## Security checks

`install.sh` installs a Git template hook for newly initialized and cloned
repositories. It scans staged changes with Gitleaks, then runs repository-owned
checks when `.pre-commit-config.yaml` is present. The hook runs Gitleaks even
when the repository configuration does not list it. `install.sh deps` installs
both tools; if either is missing, the hook allows the commit and prints its
Homebrew installation command. A detected secret or failed repository check
blocks the commit.

Existing repositories are unchanged. During installation, an existing private
`~/.git-template/hooks/pre-commit` is preserved as `pre-commit.local` and runs
after the shared checks. Do not run `pre-commit install` in a repository using
this template: it would replace the shared hook. Add repository-specific checks
to `.pre-commit-config.yaml` instead.

Gitleaks scans the fetched reachable Git history in GitHub Actions. GitHub Push
Protection should remain enabled as the final credential check before a push.
These tools do not replace manual review for internal hostnames, addresses,
paths or identity information. If a real credential appears in Git, revoke or
rotate it first, then clean the history.

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

## Git preferences

Delta is the default terminal pager for Git diffs, with line numbers and `n`/`N`
navigation. `git d` is an alias for `git diff`; use `git difftool` or
`git mergetool` for Vim. Interactive staging uses `delta --color-only`.
Use `git --no-pager diff` for plain output or
`git -c delta.side-by-side=true diff` for a one-off side-by-side view.

`git pull` only fast-forwards. When local and remote history diverge, choose an
explicit reconciliation such as `git pull --rebase`. Automatic stashing is off;
commit or stash work before rebasing. Conflicts use `zdiff3` to show the base.
Rerere records resolutions and can reuse them for matching conflicts, but does
not automatically stage the result. Review the diff and run `git add`; use
`git rerere forget <path>` to discard a resolution for the current conflict.
These records stay local to each repository.

The global ignore covers system/editor temporary files and private environment,
local configuration, and key files. Build outputs, dependency directories, IDE
project settings, archives, and public certificates belong in each project's
`.gitignore` when appropriate. Ignore rules do not replace Gitleaks scanning.
Settings in `~/.gitconfig.local` override the shared defaults.

## Terminal sessions

Local terminals start in Zsh without automatically entering tmux. Start a new
session with `tmux new-session`, or resume a named workspace with
`tmux new-session -A -s main`.

Use sessions to separate workspaces or projects, and windows for tasks such as
editing, running a service, and viewing logs. Use panes when simultaneous views
are useful; they are optional, not the main way to organize work. Multiple
clients attached to one session share its current window and running programs.

The shared SSH configuration requires a client supporting `Match command`.
Ordinary `ssh host` requests a terminal and runs the server's login shell to
create or attach to its `main` tmux session. Detaching ends the SSH connection,
while the session and its programs remain running. The server must have tmux
installed and available in the login shell's PATH. For Zsh, `-l -c` reads
`.zshenv`, `.zprofile`, and `.zlogin`, but not `.zshrc`; set the required PATH in
the server's login environment. Missing tmux or a missing terminal causes an
error; this configuration does not fall back to a shell.

Explicit commands such as `ssh -t host zsh -l` and SFTP bypass automatic tmux.
For a regular login using the server's default shell, use
`ssh -o RemoteCommand=none -t host`, or define a raw alias in the private
`~/.ssh/config.local`:

```sshconfig
Host server server-raw
  HostName server.example.com
  User your-user

Host server-raw
  RequestTTY yes
  RemoteCommand none
```

Use your server's actual address, user, and existing key settings. Private
settings take precedence over shared defaults. With `ssh server-raw`, manually
starting tmux and then detaching returns to the remote shell without closing SSH.
Starting SSH inside local tmux nests the remote tmux; use a separate terminal
when desired. Shared keepalives use `ServerAliveInterval 30` and
`ServerAliveCountMax 3`, unless overridden by private settings.


### Vim inside tmux

Use windows for separate tasks. `Ctrl-a c` opens a window in the current pane's
working directory; `Ctrl-a v` and `Ctrl-a s` do the same for horizontal and
vertical splits. Windows and panes start at 1; closing a window renumbers the
remaining windows. Background activity is indicated in the status bar without
an activity message, and the status bar refreshes every five seconds.

Use `Ctrl-h/j/k/l` to navigate across Vim splits and tmux panes after installing
`vim-tmux-navigator` with `:PlugInstall`. Zoomed panes keep navigation within
Vim. In Vim, `,y` copies a line or visual selection to the client clipboard over
SSH; tmux copy-mode uses `y` or Enter. This requires OSC 52 clipboard access in
the client terminal. See [the Vim guide](docs/vim_plugin_user_manual.md) for iTerm2,
color capabilities, formatting, and recovery details.


### Terminal file search

Oh My Zsh's `fzf` plugin initializes shell integration. Its search commands are
configured before loading Oh My Zsh and use fd while respecting ignore rules.
Hidden files are included and `.git` is excluded.

- Type `vim `, press Ctrl-t, select files (Tab selects multiple), then press Enter
  to insert shell-quoted paths. Press Enter again to run Vim.
- Ctrl-r searches command history; Alt-c selects a directory to enter.
- In Vim, Ctrl-p finds files, `,rg` searches contents with ripgrep, and `,b`
  switches buffers. See [the Vim guide](docs/vim_plugin_user_manual.md).

For `Alt-c`, configure the active iTerm2 profile under **Settings → Profiles →
Keys** to send `Esc+` for the Option key you use (left, right, or both). This
lets Option-c send the Esc-c sequence expected by fzf. The setting is profile
specific; it was verified with the current iTerm2 setup.

### Project environments with direnv

Oh My Zsh's `direnv` plugin loads an authorized project's `.envrc` when entering
its directory or a subdirectory, and restores the previous environment when
leaving. Restart Zsh after enabling the plugin. Review each `.envrc` before
running `direnv allow`; changes to the file require authorization again.

Keep global tool paths and shell initialization in `.zshrc`, and project-specific
environment variables in `.envrc`. The latter uses Bash syntax, even in Zsh.
Keep secrets out of committed `.envrc` files; an ignored `.env` can be loaded
explicitly with `dotenv_if_exists`.

For Python, `pyproject.toml` declares dependencies and `uv.lock` locks their
versions. Run `uv sync` explicitly to create or update `.venv`. `uv run` works
without activation; to also use the project's Python directly and let tools
launched from the shell inherit it, optionally create this project `.envrc`:

```bash
export VIRTUAL_ENV="$PWD/.venv"
PATH_add "$VIRTUAL_ENV/bin"
```

Run `direnv allow` once after reviewing it. Directory changes only load or unload
the environment; they do not install dependencies. Ignore `.venv/` in the
project's Git configuration. For C++, keep shared build settings in
`CMakePresets.json` and machine-specific settings in an ignored
`CMakeUserPresets.json`.
